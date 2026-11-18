#!/usr/bin/env python3
"""Step 7 — Daily page builder (Sarangsho Plus engine v2).

Builds the daily page JSON defined in CONTRACTS.md from kept items
(Steps 3-6 output):

* "আজকের এক নজরে" — one table row per full item
  (event | date | key fact | status).
* Sections in the RULES.md order, empty ones skipped.
* Score-2 items in brief format (headline + up to 2 fact lines);
  score-3 items in longer format (headline + up to 3 fact lines +
  why_important).
* "আজকের পরিবর্তনগুলো মনে রাখুন" — items whose status is
  scheduled / proposed / forecast, or whose date is today.
* "maybe" items as headline + link only, in a collapsed list.
* Max 15 full items (score desc, then newest first).
* A Top News box (~10 best items, one dated line each).
* A GK footer (one static fact; placeholder if none is supplied).
* A ranking-triple rendering (top + bottom + Bangladesh position)
  for report/index stories, whenever the fact lines carry those
  three values.
* A মতামত (opinion) slot: one editorial of the day, passed in as
  ``editorial`` — rendered outside the 15 news items, never
  counted in them, clearly labelled opinion.

Stdlib-only Python 3. Reads section order / mapping from
rules/RULES.md at runtime via rules_loader.py. Never touches v1.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402  (parse_pubdate for newest-first ordering)

try:
    from rules_loader import parse_section_mapping, parse_section_order
except Exception:  # pragma: no cover - rules_loader is expected to exist
    parse_section_order = None
    parse_section_mapping = None

try:
    from step5_check import numbers_in
    from step4_facts import norm_bangla
except Exception:  # pragma: no cover - Step 4/5 are expected to exist
    numbers_in = None
    norm_bangla = None

# Number tokens in a headline (Latin or Bangla digits, optional
# decimal) — the same token shape Step 5's numbers_in() extracts —
# plus an optional unit suffix glued to the number ("171Cr",
# "186B"): when the number is dropped, its suffix goes with it,
# so the paragraph never reads "TkCr" or "Targets B Budget".
_HEADLINE_NUM_RE = re.compile(
    r"[0-9০-৯]+(?:[.,][0-9০-৯]+)?(?:Cr|B|M|K|bn|mn|Bn|Mn|cr)?")

MAX_ITEMS = 15
TOP_NEWS_N = 10
GK_PLACEHOLDER = "GK ফুটার: (আসন্ন সংস্করণে)"

# Fallbacks if RULES.md cannot be parsed; the loader is authoritative.
_FALLBACK_ORDER = [
    "বাংলাদেশ (রাজনীতি, আইন, প্রশাসন)",
    "অর্থনীতি ও ব্যাংকিং",
    "আন্তর্জাতিক",
    "বিজ্ঞান, প্রযুক্তি ও পরিবেশ",
    "খেলাধুলা, পুরস্কার, দিবস ও নিয়োগ",
]
_FALLBACK_MAPPING = {
    "BD-GOV": _FALLBACK_ORDER[0], "BD-NATL": _FALLBACK_ORDER[0],
    "BD-ECO": _FALLBACK_ORDER[1], "BD-BANK": _FALLBACK_ORDER[1],
    "INT-ORG": _FALLBACK_ORDER[2], "INT-REL": _FALLBACK_ORDER[2],
    "ENV": _FALLBACK_ORDER[3], "SCI": _FALLBACK_ORDER[3],
    "SPORT": _FALLBACK_ORDER[4], "PEOPLE": _FALLBACK_ORDER[4],
}

STATUS_LABELS = {
    "happened": "ঘটেছে",
    "scheduled": "নির্ধারিত",
    "proposed": "প্রস্তাবিত",
    "forecast": "পূর্বাভাস",
}
CHANGE_STATUSES = {"scheduled", "proposed", "forecast"}

# Words that mark the three legs of a ranking triple in a fact line.
_TOP_MARKERS = ("শীর্ষ", "প্রথম স্থান", "top", "first", "১ম")
_BOTTOM_MARKERS = ("সর্বনিম্ন", "সর্বশেষ", "bottom", "last")
_BD_MARKERS = ("বাংলাদেশ", "bangladesh")


def section_order():
    """Daily-page sections in RULES.md order."""
    if parse_section_order is not None:
        order = parse_section_order() or []
        if order:
            return order
    return list(_FALLBACK_ORDER)


def section_mapping():
    """{topic_id: section name} from RULES.md."""
    if parse_section_mapping is not None:
        mapping = parse_section_mapping() or {}
        if mapping:
            return mapping
    return dict(_FALLBACK_MAPPING)


def _fact_lines_of(item):
    """Fact lines as a list of strings.

    Accepts Step 6 items (``fact_lines``: [str, ...] / ``bangla_lines``)
    and Step 4 items (``facts``: [{what, value, ...}, ...]).
    """
    lines = item.get("fact_lines") or item.get("bangla_lines") or []
    if lines and isinstance(lines[0], dict):
        lines = [_fact_to_line(f) for f in lines]
    if lines:
        return [str(line).strip() for line in lines if str(line).strip()]
    facts = item.get("facts") or []
    return [_fact_to_line(f) for f in facts if isinstance(f, dict)]


def _fact_to_line(fact):
    what = (fact.get("what") or "").strip()
    value = (fact.get("value") or "").strip()
    unit = (fact.get("unit") or "").strip()
    date = (fact.get("date") or "").strip()
    parts = [p for p in (what, value, unit) if p]
    line = " ".join(parts)
    if date and date != "উল্লেখ নেই":
        line = f"{line} ({date})" if line else date
    return line


def ranking_triple_for(item, fact_lines=None):
    """Return {"top","bottom","bangladesh"} if the fact lines carry all
    three legs of a ranking triple, else None.

    Also honours an explicit ``ranking_triple`` dict on the item.
    """
    explicit = item.get("ranking_triple")
    if isinstance(explicit, dict) and all(
            explicit.get(k) for k in ("top", "bottom", "bangladesh")):
        return {k: explicit[k] for k in ("top", "bottom", "bangladesh")}
    lines = fact_lines if fact_lines is not None else _fact_lines_of(item)
    top = bottom = bd = None
    for line in lines:
        low = line.lower()
        if top is None and any(m.lower() in low for m in _TOP_MARKERS):
            top = line
        if bottom is None and any(m.lower() in low for m in _BOTTOM_MARKERS):
            bottom = line
        if bd is None and any(m.lower() in low for m in _BD_MARKERS) and (
                "তম" in line or "স্থান" in line or "rank" in low
                or "position" in low):
            bd = line
    if top and bottom and bd and len({top, bottom, bd}) == 3:
        return {"top": top, "bottom": bottom, "bangladesh": bd}
    return None


def _drop_untraceable_numbers(headline, allowed):
    """Drop number tokens from ``headline`` that are not in ``allowed``
    (the set of numbers verified to appear in the article).

    TBS-sitemap headlines are slug-derived and sometimes express a
    figure in a different unit than the body ("Tk159 Crore" in the
    headline vs "1.59 billion" in the body), so the headline number
    does not literally appear in the article. A focus paragraph may
    only carry numbers that pass the Step 5 check, so such tokens
    are removed (the headline words stay). A unit suffix glued to a
    dropped number ("171Cr", "186B") is dropped with it.
    ``allowed=None`` means no check is possible — the headline is
    returned unchanged.
    """
    if allowed is None or numbers_in is None or norm_bangla is None:
        return headline

    def _repl(match):
        # Numeric part only (strip the glued unit suffix) for the
        # membership check; the whole match is kept or dropped.
        token = norm_bangla(match.group(0)).replace(",", "")
        numeric = re.sub(r"(Cr|B|M|K|bn|mn|Bn|Mn|cr)$", "", token)
        return match.group(0) if numeric in allowed else ""

    return re.sub(r"\s+", " ", _HEADLINE_NUM_RE.sub(_repl, headline)).strip()


def build_focus_paragraph(norm):
    """Optional focus paragraph for score-3 items (Proposal 7, syllabus).

    3-4 sentences built ONLY from the item's verified fact list +
    its [পটভূমি] line, in the shape প্রসঙ্গ -> তথ্য -> বিশ্লেষণ ->
    উপসংহার. No new facts: the context sentence is the headline, the
    fact sentences are the item's own fact lines, the analysis
    sentence is the [পটভূমি] line, and the closing sentence repeats
    the key fact as a memory hook. Returns "" when the item cannot
    support 3 sentences (fewer than 1 fact line, or no why line).
    Every number in it passes the Step 5 check: fact-line numbers
    are verified facts, and headline numbers are dropped when they
    do not appear in the article body (slug-derived headlines
    sometimes use a different unit than the body). The allowed
    numbers come from ``norm["body_numbers"]`` when the item carries
    a body, else from the fact lines + date (the conservative
    fallback when no body is available).
    """
    if int(norm.get("score", 2) or 2) < 3:
        return ""
    lines = [ln for ln in (norm.get("fact_lines") or []) if str(ln).strip()]
    why = (norm.get("why_important") or "").strip()
    headline = (norm.get("headline") or "").strip()
    if not lines or not why or not headline:
        return ""
    date = (norm.get("date") or "").strip()
    if norm.get("body_numbers") is not None:
        allowed = set(norm["body_numbers"])
    elif numbers_in is not None:
        allowed = set()
        for ln in lines:
            allowed |= numbers_in(ln)
        allowed |= numbers_in(why)
        allowed |= numbers_in(date)
    else:
        allowed = None
    headline = _drop_untraceable_numbers(headline, allowed)
    s1 = headline if not date else f"{headline} ({date})"
    if not s1.endswith(("।", ".", "!", "?")):
        s1 += "।"
    # তথ্য: the key fact line (one sentence). বিশ্লেষণ: the [পটভূমি]
    # line. উপসংহার: the second fact line as a memory hook (only
    # when there is one — 1 fact gives 3 sentences, 2+ give 4).
    s2 = str(lines[0]).strip()
    sentences = [s1, s2, why]
    if len(lines) >= 2:
        sentences.append(f"মনে রাখুন: {str(lines[1]).strip()}")
    return " ".join(sentences)


def _normalise_item(item, date):
    fact_lines = _fact_lines_of(item)
    sources = item.get("sources") or []
    norm_sources = []
    for src in sources:
        if isinstance(src, dict):
            norm_sources.append({"name": src.get("name", ""),
                                 "url": src.get("url", "")})
        elif isinstance(src, str):
            norm_sources.append({"name": src, "url": ""})
    if not norm_sources and item.get("url"):
        norm_sources.append({"name": item.get("source", ""),
                             "url": item.get("url", "")})
    # Numbers verified to appear in the article body (Step 5 set) —
    # the focus paragraph drops headline numbers outside this set.
    # None when the item carries no body (test fixtures, standalone
    # use); build_focus_paragraph then falls back to the fact lines.
    body_text = item.get("body_text") or ""
    body_numbers = (sorted(numbers_in(body_text)) if body_text
                    and numbers_in is not None else None)
    return {
        "id": item.get("id", ""),
        "headline": (item.get("headline") or item.get("title") or "").strip(),
        "score": int(item.get("score", 2) or 2),
        "topic_primary": item.get("topic_primary", ""),
        "fact_lines": fact_lines,
        "why_important": (item.get("why_important")
                          or item.get("why_important_bn") or "").strip(),
        "status": (item.get("status") or "happened").strip(),
        "sources": norm_sources,
        "image_url": item.get("image_url", "") or "",
        "date": (item.get("date") or date or "").strip(),
        "published": (item.get("published") or "").strip(),
        "ranking_triple": ranking_triple_for(item, fact_lines),
        "facts_en": item.get("facts_en") or [],
        "body_numbers": body_numbers,
    }


def _sort_ts(value):
    """Sortable timestamp for newest-first ordering: an aware
    datetime, or the earliest possible time when unparsable."""
    dt = common.parse_pubdate(value or "")
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt


def _normalise_editorial(editorial):
    """The মতামত slot, as passed by run_v2: {"item": {...}|None,
    "empty_reason": str}. The item carries headline/source/url/
    summary/score/topic_primary only — never full opinion text.
    Anything else degrades to an empty slot with a reason."""
    if isinstance(editorial, dict):
        item = editorial.get("item")
        if isinstance(item, dict) and (item.get("headline") or "").strip():
            return {
                "label": "মতামত",
                "item": {
                    "headline": (item.get("headline") or "").strip(),
                    "source": (item.get("source") or "").strip(),
                    "url": item.get("url", ""),
                    "summary": (item.get("summary") or "").strip(),
                    "score": int(item.get("score", 2) or 2),
                    "topic_primary": item.get("topic_primary", ""),
                },
                "empty_reason": "",
            }
        return {
            "label": "মতামত",
            "item": None,
            "empty_reason": (editorial.get("empty_reason")
                             or "আজ কোনো সম্পাদকীয় নির্বাচিত হয়নি।"),
        }
    return {"label": "মতামত", "item": None,
            "empty_reason": "আজ কোনো সম্পাদকীয় নির্বাচিত হয়নি।"}


def _render_item(norm):
    """Brief format for score-2, longer format for score-3."""
    if norm["score"] >= 3:
        lines = norm["fact_lines"][:3]
        why = norm["why_important"]
    else:
        lines = norm["fact_lines"][:2]
        why = ""  # brief format: headline + fact lines only
    out = {
        "id": norm["id"],
        "headline": norm["headline"],
        "score": norm["score"],
        "topic_primary": norm["topic_primary"],
        "fact_lines": lines,
        "why_important": why,
        "status": norm["status"],
        "sources": norm["sources"],
        "image_url": norm["image_url"],
        "facts_en": norm.get("facts_en") or [],
    }
    if norm["ranking_triple"]:
        out["ranking_triple"] = norm["ranking_triple"]
    focus = build_focus_paragraph(norm)
    if focus:
        out["focus_paragraph"] = focus
    return out


def _normalise_maybe(maybe):
    if isinstance(maybe, dict):
        return {
            "title": (maybe.get("title") or maybe.get("headline") or "").strip(),
            "url": maybe.get("url", ""),
            "source": maybe.get("source", ""),
        }
    return {"title": str(maybe), "url": "", "source": ""}


def build_page(date, items, maybe_items=None, gk_fact=None,
               editorial=None):
    """Build the daily page JSON for ``date`` from kept ``items``.

    ``items``: list of dicts with id / headline / score /
    topic_primary / fact_lines / why_important / status / sources
    (``facts`` or ``bangla_lines`` are accepted as fact-line sources).
    ``maybe_items``: headline + link only, shown collapsed.
    ``gk_fact``: one static GK fact for the footer; if omitted the
    placeholder ``GK ফুটার: (আসন্ন সংস্করণে)`` is used.
    ``editorial``: the মতামত slot dict {"item": {...}|None,
    "empty_reason": str} (see _normalise_editorial) — rendered
    outside the 15 news items and never counted in them.
    Page order: score desc, then newest first (by published time).
    """
    order = section_order()
    mapping = section_mapping()
    norms = [_normalise_item(it, date) for it in (items or [])]
    # Max 15 full items: score desc, then newest first; collection
    # order only breaks exact ties (Decision 5).
    ranked = sorted(
        enumerate(norms),
        key=lambda p: (-p[1]["score"],
                       -_sort_ts(p[1]["published"] or p[1]["date"]).timestamp(),
                       p[0]))
    kept = [norm for _, norm in ranked[:MAX_ITEMS]]

    sections = {}
    for norm in kept:
        section = mapping.get(norm["topic_primary"]) or "অন্যান্য"
        sections.setdefault(section, []).append(_render_item(norm))
    # Emit sections in RULES.md order, empty ones skipped; an
    # "অন্যান্য" fallback section (unmapped topics only) goes last.
    ordered_sections = {s: sections[s] for s in order if s in sections}
    if "অন্যান্য" in sections:
        ordered_sections["অন্যান্য"] = sections["অন্যান্য"]

    at_a_glance = [{
        "event": norm["headline"],
        "date": norm["date"] or date,
        "key_fact": norm["fact_lines"][0] if norm["fact_lines"] else "",
        "status": norm["status"],
    } for norm in kept]

    changes = []
    for norm in kept:
        if norm["status"] in CHANGE_STATUSES or norm["date"] == date:
            label = STATUS_LABELS.get(norm["status"], norm["status"])
            changes.append(f"{norm['headline']} — {label}")

    top_news = [
        f"{norm['date'] or date}: {norm['headline']}"
        for norm in kept[:TOP_NEWS_N]
    ]

    return {
        "date": date,
        "at_a_glance": at_a_glance,
        "sections": ordered_sections,
        "changes": changes,
        "maybe_items": [_normalise_maybe(m) for m in (maybe_items or [])],
        "top_news": top_news,
        "gk_footer": gk_fact or GK_PLACEHOLDER,
        "editorial": _normalise_editorial(editorial),
    }


def _load_input(path):
    """Read a decisions+facts JSON file (several shapes accepted).

    Accepted shapes:
    * {"date": ..., "items": [...], "maybe_items": [...], "gk_fact": ...}
    * {"date": ..., "decisions": [...], "facts": {id: {...}} or [...]}
    * a bare list of items.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"date": "", "items": data, "maybe_items": [], "gk_fact": None}
    items = data.get("items")
    if items is None and "decisions" in data:
        facts = data.get("facts") or {}
        if isinstance(facts, list):
            facts = {f.get("item_id", f.get("id", "")): f for f in facts}
        items = []
        maybe = []
        for dec in data.get("decisions", []):
            if dec.get("decision") == "maybe":
                maybe.append({"title": dec.get("headline", dec.get("title", "")),
                              "url": dec.get("url", ""),
                              "source": dec.get("source", "")})
                continue
            if dec.get("decision") != "keep":
                continue
            merged = dict(dec)
            merged.update(facts.get(dec.get("id", ""), {}) or {})
            merged.setdefault("headline", dec.get("headline", dec.get("title", "")))
            items.append(merged)
        data = dict(data)
        data.setdefault("maybe_items", maybe)
    return {
        "date": data.get("date", ""),
        "items": items or [],
        "maybe_items": data.get("maybe_items") or [],
        "gk_fact": data.get("gk_fact"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a Step 7 daily page.")
    ap.add_argument("input", help="decisions+facts JSON file")
    ap.add_argument("--date", default="", help="page date YYYY-MM-DD")
    ap.add_argument("--out", default="", help="output JSON path")
    ap.add_argument("--gk-fact", default=None, help="GK footer fact")
    args = ap.parse_args(argv)

    loaded = _load_input(args.input)
    date = args.date or loaded["date"]
    if not date:
        raise SystemExit("no date: pass --date or put 'date' in the input file")
    page = build_page(date, loaded["items"], loaded["maybe_items"],
                      args.gk_fact or loaded["gk_fact"])
    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent / "runs" / date / f"page-{date}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(page, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    total = sum(len(v) for v in page["sections"].values())
    print(f"wrote {out}")
    print(f"date={date} full_items={total} "
          f"sections={list(page['sections'])} "
          f"at_a_glance={len(page['at_a_glance'])} "
          f"changes={len(page['changes'])} "
          f"maybe={len(page['maybe_items'])} "
          f"top_news={len(page['top_news'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
