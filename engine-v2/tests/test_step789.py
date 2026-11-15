#!/usr/bin/env python3
"""Test Steps 7, 8 and 9 (engine v2) on real data.

Runnable as:  python3 tests/test_step789.py   (from engine-v2/)
or:            python3 test_step789.py        (from engine-v2/tests/)

Builds one daily page from live headlines (one Bing News RSS fetch,
"Bangladesh", format=rss) with fact lines taken verbatim from the
fetched summaries — no invented facts. If the fetch fails, falls back
to a small snapshot of items fetched verbatim from the same feed on
2026-11-14 (marked FALLBACK below).

Asserts: RULES section order, empty sections absent, max 15 items,
status on every item, score-3 items carry more fact lines than
score-2 items; MCQ same-type 4 options, no forbidden options, no
negative stems, verbatim source quotes, canonical key order;
SRS intervals 1 -> 3 -> 7 -> 14, wrong answer resets to +1 day,
reported cards leave the due list.

Prints the page JSON, sample questions and the SRS schedule, then
PASS/FAIL counts. Exit code 0 only if everything passes.
"""
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date as _date, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(ENGINE))

from step7_page import build_page, build_focus_paragraph, GK_PLACEHOLDER  # noqa: E402
from step8_questions import (questions_for_item, _quote_in_text,  # noqa: E402
                             analytical_question_for_item,
                             analytical_for_items, _build_mcq,
                             _fmt_number)
from step5_check import numbers_in  # noqa: E402
from step4_facts import render_facts_en  # noqa: E402
from run_v2 import _pub_date  # noqa: E402
from step9_study import (build_cards, grade_answer, quiz_due,  # noqa: E402
                         report_card)
from rules_loader import parse_section_order  # noqa: E402

DATE = "2026-11-14"
RUNS_DIR = ENGINE / "runs" / DATE
PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


# ---------------------------------------------------------------------------
# Fixture: live Bing News RSS ("Bangladesh"), verbatim fact lines.
# ---------------------------------------------------------------------------
RSS_URL = "https://www.bing.com/news/search?q=Bangladesh&format=rss"
UA = {"User-Agent": "Mozilla/5.0 SarangshoPlus/2.0 (test fixture)"}

# Verbatim snapshot of the same feed, fetched 2026-11-14, used ONLY if
# the live fetch fails. Titles/descriptions/pubDates copied as fetched.
FALLBACK_ITEMS = [
    {"title": "Bangladesh garment-makers threaten to quit wage talks",
     "description": "Protests over wages began in October and have "
                    "sometimes turned violent, with demonstrators torching "
                    "police vehicles and damaging property this month.",
     "pubDate": "Sat, 14 Nov 2026 06:28:21 GMT", "source": "Bing News"},
    {"title": "Bangladesh says legal process complete to secure Hasina's "
              "return, decision rests with India: Reports",
     "description": "Dhaka : Bangladesh has completed all legal procedures "
                    "required to secure the return of ousted prime minister "
                    "Sheikh Hasina from India, and the next step rests with "
                    "New Delhi, Law Minister Md ...",
     "pubDate": "Sat, 14 Nov 2026 03:50:00 GMT", "source": "Bing News"},
    {"title": "Bangladesh, Saudi Arabia discuss closer Hajj and Umrah "
              "cooperation",
     "description": "Saudi Arabia has told Bangladesh it will give the "
                    "country priority for additional Hajj places if other "
                    "countries do not use their full quotas.",
     "pubDate": "Fri, 13 Nov 2026 18:33:00 GMT", "source": "Bing News"},
    {"title": "Bangladesh proposes sending skilled professionals to Kosovo",
     "description": "The proposal aims to help the southeastern European "
                    "country address shortages of skilled workers through "
                    "government-to-government cooperation.",
     "pubDate": "Fri, 13 Nov 2026 20:09:00 GMT", "source": "Bing News"},
]

KNOWN_ORGS = ["Bangladesh Bank", "World Bank", "IMF", "United Nations",
              "Asian Development Bank", "ADB", "WTO", "SAARC", "BIMSTEC",
              "Election Commission", "Supreme Court", "High Court"]


def fetch_rss_items():
    """Return [{title, description, pubDate, source}] from Bing News RSS."""
    try:
        req = urllib.request.Request(RSS_URL, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read())
    except Exception as exc:  # noqa: BLE001 - network is best-effort here
        print(f"[fixture] live RSS fetch failed ({exc}); using fallback "
              "snapshot fetched verbatim on 2026-11-14.")
        return list(FALLBACK_ITEMS), True
    ns = {"News": "https://www.bing.com/news/search?q=Bangladesh&format=rss"}
    items = []
    for it in root.iter("item"):
        src = it.find("News:Source", ns)
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "description": re.sub(r"<[^>]+>", "",
                                  it.findtext("description") or "").strip(),
            "pubDate": (it.findtext("pubDate") or "").strip(),
            "source": (src.text if src is not None else "Bing News").strip(),
        })
    return [i for i in items if i["title"]], False


def _words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _pubdate_iso(raw):
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except Exception:
        return DATE


def _topic_of(text):
    t = text.lower()
    if "bangladesh bank" in t:
        return "BD-BANK"
    if "imf" in t or "world bank" in t or "united nations" in t:
        return "INT-ORG"
    if ("cricket" in t or "football" in t or "championship" in t
            or "semifinal" in t or "live streaming" in t):
        return "SPORT"
    if ("election" in t or "ordinance" in t or "cabinet" in t
            or "court" in t or "legal" in t or "law minister" in t
            or "parliament" in t):
        return "BD-GOV"
    if ("garment" in t or "wage" in t or "economy" in t or "gas" in t
            or "export" in t or "remittance" in t or "budget" in t):
        return "BD-ECO"
    if ("india" in t or "pakistan" in t or "saudi" in t or "kosovo" in t
            or "america" in t or "hajj" in t or "umrah" in t):
        return "INT-REL"
    if "cyclone" in t or "flood" in t or "climate" in t:
        return "ENV"
    return "BD-NATL"


def _status_of(text):
    t = text.lower()
    if "propos" in t:
        return "proposed"
    if "semifinal" in t or " will " in t:
        return "scheduled"
    return "happened"


def build_fixture():
    """Live headlines -> (items, maybe_items) for Steps 7-9.

    Every fact line is a verbatim sentence from the fetched summary
    (or the fetched title); the only constructed line is a publication
    date line taken from the feed's own pubDate metadata, used to pad
    score-3 items to 3 lines.
    """
    raw, used_fallback = fetch_rss_items()
    today = _date.fromisoformat(DATE)
    fresh = [r for r in raw
             if (today - _date.fromisoformat(_pubdate_iso(r["pubDate"]))).days <= 14]
    pool = fresh if len(fresh) >= 4 else [r for r in raw if _pubdate_iso(r["pubDate"]) >= "2026-01-01"]
    if len(pool) < 4:
        pool = raw
    # Dedupe near-identical headlines (e.g. the same story in 4 papers).
    kept_raw, seen = [], []
    for r in pool:
        w = _words(r["title"])
        if any(w and len(w & s) / max(len(w | s), 1) > 0.6 for s in seen):
            continue
        seen.append(w)
        kept_raw.append(r)
        if len(kept_raw) >= 8:
            break

    items, maybe_items = [], []
    for n, r in enumerate(kept_raw, start=1):
        title, desc = r["title"], r["description"]
        if "live streaming" in title.lower():
            maybe_items.append({"title": title, "url": "",
                                "source": r["source"]})
            continue
        sentences = [s.strip() for s in re.split(r"\.\s+", desc) if s.strip()]
        sentences = [s if s.endswith((".", "!", "?")) else s for s in sentences]
        fact_lines = sentences[:3]
        if title not in fact_lines:
            fact_lines.append(title)
        pub_iso = _pubdate_iso(r["pubDate"])
        score = 3 if n <= 3 else 2
        if score == 3 and len(fact_lines) < 3:
            fact_lines.append(f"সংবাদটি প্রকাশিত হয় {pub_iso} তারিখে।")
        fact_lines = fact_lines[:3] if score == 3 else fact_lines[:2]
        text = f"{title} {desc}".strip()
        status = _status_of(text)
        facts = []
        for line in fact_lines:
            if line.startswith("সংবাদটি প্রকাশিত হয়"):
                continue
            m = re.search(r"\d+(?:,\d+)*(?:\.\d+)?", line)
            org = next((o for o in KNOWN_ORGS if o in line), None)
            if m:
                facts.append({"what": "এই তথ্যে উল্লিখিত সংখ্যা",
                              "value": m.group(0), "unit": "",
                              "date": pub_iso, "status": status,
                              "quote": line})
            elif org:
                facts.append({"what": "এই তথ্যে উল্লিখিত সংস্থা",
                              "value": org, "unit": "",
                              "date": pub_iso, "status": status,
                              "quote": line})
            else:
                facts.append({"what": line[:80], "value": "",
                              "unit": "", "date": pub_iso,
                              "status": status, "quote": line})
        # Date fact: every item gets at least one MCQ-able fact, from
        # the feed's own pubDate; the quote is the verbatim title.
        facts.append({"what": "সংবাদ প্রকাশের তারিখ", "value": pub_iso,
                      "unit": "", "date": pub_iso, "status": status,
                      "quote": title})
        items.append({
            "id": f"i{n:02d}",
            "headline": title,
            "score": score,
            "topic_primary": _topic_of(text),
            "fact_lines": fact_lines,
            "why_important": "[পটভূমি] " + (sentences[0] if sentences else title),
            "status": status,
            "sources": [{"name": r["source"], "url": ""}],
            "date": DATE,
            "facts": facts[:5],
            "source_text": f"{title} {desc}".strip(),
        })
    return items, maybe_items, used_fallback


# ---------------------------------------------------------------------------
# Step 7 — daily page
# ---------------------------------------------------------------------------
def test_step7(items, maybe_items):
    print("\n=== STEP 7 — daily page ===")
    page = build_page(DATE, items, maybe_items)
    print(json.dumps(page, ensure_ascii=False, indent=2))
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"page-{DATE}.json").write_text(
        json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")

    rule_order = parse_section_order()
    got_sections = list(page["sections"])
    check("sections in RULES.md order",
          got_sections == [s for s in rule_order if s in page["sections"]],
          f"got {got_sections}")
    check("empty sections are absent",
          all(len(v) > 0 for v in page["sections"].values())
          and set(got_sections) <= set(rule_order + ["অন্যান্য"]))
    total = sum(len(v) for v in page["sections"].values())
    check("max 15 full items", total <= 15 and total == min(len(items), 15),
          f"total={total} items={len(items)}")
    flat = [it for v in page["sections"].values() for it in v]
    check("every item has a status label",
          all(it.get("status") in
              ("happened", "scheduled", "proposed", "forecast") for it in flat),
          f"{[it.get('status') for it in flat]}")
    s3 = [len(it["fact_lines"]) for it in flat if it["score"] >= 3]
    s2 = [len(it["fact_lines"]) for it in flat if it["score"] <= 2]
    check("score-3 items have more fact lines than score-2 items",
          bool(s3) and bool(s2) and min(s3) > max(s2),
          f"score3 lines={s3} score2 lines={s2}")
    check("at-a-glance has one row per full item",
          len(page["at_a_glance"]) == total and all(
              set(r) == {"event", "date", "key_fact", "status"}
              for r in page["at_a_glance"]))
    check("changes list is non-empty (dated-today / scheduled items)",
          len(page["changes"]) > 0, f"changes={page['changes']}")
    check("maybe items are headline + link only",
          all(set(m) == {"title", "url", "source"}
              for m in page["maybe_items"]))
    check("top news box: <=10 dated one-liners",
          0 < len(page["top_news"]) <= 10 and all(
              re.match(r"^\d{4}-\d{2}-\d{2}: ", line)
              for line in page["top_news"]))
    check("GK footer present (placeholder when no fact given)",
          page["gk_footer"] == GK_PLACEHOLDER, page["gk_footer"])
    print(f"  sections: { {k: len(v) for k, v in page['sections'].items()} }")
    print(f"  at-a-glance rows: {len(page['at_a_glance'])}, "
          f"changes: {len(page['changes'])}, "
          f"maybe: {len(page['maybe_items'])}, "
          f"top_news: {len(page['top_news'])}")
    return page


def test_step7_ranking_editorial():
    """Decision 5 (rank: score desc, then newest first) and
    Decision 2 (মতামত slot: outside the 15, labelled opinion).
    Synthetic items — no network."""
    print("\n=== STEP 7 — ranking + editorial slot (synthetic) ===")

    def item(iid, score, published, headline):
        return {"id": iid, "headline": headline, "score": score,
                "topic_primary": "BD-ECO",
                "fact_lines": [f"{headline} — fact line."],
                "why_important": "[পটভূমি] important.",
                "status": "happened",
                "sources": [{"name": "Test", "url": ""}],
                "date": "2026-11-15", "published": published}

    # Ranking: score-3 first even when older; score-2 newest first.
    items = [
        item("r1", 2, "2026-11-15T09:00:00+00:00", "Newest score-2 story"),
        item("r2", 3, "2026-11-15T05:00:00+00:00", "Older score-3 story"),
        item("r3", 2, "2026-11-15T06:00:00+00:00", "Middle score-2 story"),
        item("r4", 2, "2026-11-14T20:00:00+00:00", "Oldest score-2 story"),
    ]
    page = build_page("2026-11-15", items, [])
    section_items = [it for v in page["sections"].values() for it in v]
    got = [it["headline"] for it in section_items]
    check("ranking: score-3 first, then score-2 newest first",
          got == ["Older score-3 story", "Newest score-2 story",
                  "Middle score-2 story", "Oldest score-2 story"],
          str(got))
    check("at-a-glance follows the same ranked order",
          [r["event"] for r in page["at_a_glance"]] == got,
          str([r["event"] for r in page["at_a_glance"]]))

    # Cap: 16 score-2 items, distinct times — the oldest is dropped.
    many = [item(f"c{n:02d}", 2,
                 f"2026-11-15T{n:02d}:00:00+00:00", f"Story {n:02d}")
            for n in range(16)]
    page16 = build_page("2026-11-15", many, [])
    kept16 = [it["headline"] for v in page16["sections"].values()
              for it in v]
    check("cap 15: oldest score-2 item is dropped, newest kept",
          len(kept16) == 15 and "Story 00" not in kept16
          and kept16[0] == "Story 15", str(kept16[:3]))

    # Editorial slot: filled, labelled, outside the 15.
    ed = {"item": {"headline": "Budget must protect the poor",
                   "source": "The Daily Star",
                   "url": "https://example.com/opinion/budget",
                   "summary": "The budget should protect the poor.",
                   "score": 2, "topic_primary": "BD-ECO"},
          "empty_reason": ""}
    page_ed = build_page("2026-11-15", items, [], editorial=ed)
    check("editorial slot: label is মতামত",
          page_ed["editorial"]["label"] == "মতামত",
          str(page_ed["editorial"]))
    check("editorial slot: item present with headline/source/url",
          page_ed["editorial"]["item"] is not None
          and page_ed["editorial"]["item"]["headline"]
          == "Budget must protect the poor"
          and page_ed["editorial"]["item"]["url"]
          == "https://example.com/opinion/budget",
          str(page_ed["editorial"]["item"]))
    all_text = json.dumps(page_ed["sections"], ensure_ascii=False) \
        + json.dumps(page_ed["at_a_glance"], ensure_ascii=False) \
        + json.dumps(page_ed["top_news"], ensure_ascii=False) \
        + json.dumps(page_ed["maybe_items"], ensure_ascii=False)
    check("editorial item never enters the news 15 / glance / top news",
          "Budget must protect the poor" not in all_text)
    total = sum(len(v) for v in page_ed["sections"].values())
    check("editorial does not count toward the 15",
          total == 4, f"total={total}")

    # Empty slot: no editorial passed -> item None + a reason.
    page_empty = build_page("2026-11-15", items, [])
    check("empty editorial slot: item None, reason given",
          page_empty["editorial"]["item"] is None
          and page_empty["editorial"]["empty_reason"],
          str(page_empty["editorial"]))


# ---------------------------------------------------------------------------
# Step 8 — questions
# ---------------------------------------------------------------------------
def _opt_type(value):
    text = unicodedata.normalize("NFC", str(value)).translate(
        str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))
    if re.fullmatch(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text.strip()):
        return "number"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()):
        return "date"
    return "name"


def test_step8(items):
    print("\n=== STEP 8 — questions ===")
    all_qa, all_mcq = [], []
    by_id = {}
    for item in items:
        out = questions_for_item(item)
        all_qa.extend(out["qa"])
        all_mcq.extend(out["mcq"])
        by_id[item["id"]] = item
        for q in out["qa"] + out["mcq"]:
            q["_item_id"] = item["id"]
    print(f"  generated {len(all_qa)} Q&A, {len(all_mcq)} MCQ "
          f"from {len(items)} items")
    for q in all_qa[:2]:
        print("  Q&A:", json.dumps(q, ensure_ascii=False))
    for q in all_mcq[:2]:
        print("  MCQ:", json.dumps(q, ensure_ascii=False))
    (RUNS_DIR / f"questions-{DATE}.json").write_text(
        json.dumps({"date": DATE, "qa": all_qa, "mcq": all_mcq},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    check("at least 2 Q&A generated", len(all_qa) >= 2, f"{len(all_qa)}")
    check("at least 2 MCQ generated", len(all_mcq) >= 2, f"{len(all_mcq)}")
    for i, mcq in enumerate(all_mcq):
        tag = f"mcq[{i}] {mcq['id']}"
        check(f"{tag}: exactly 4 options, keys ক খ গ ঘ",
              list(mcq["options"].keys()) == ["ক", "খ", "গ", "ঘ"],
              str(list(mcq["options"].keys())))
        check(f"{tag}: key in canonical order (ক, never shuffled)",
              mcq["key"] == "ক", f"key={mcq['key']}")
        opts = list(mcq["options"].values())
        types = {_opt_type(o) for o in opts}
        check(f"{tag}: all options same type as the key ({types})",
              len(types) == 1, str(opts))
        check(f"{tag}: no 'সবগুলো' / 'কোনোটিই নয়' option",
              not any(f in o for o in opts
                      for f in ("সবগুলো", "কোনোটিই নয়", "কোনোটিই না")))
        stem_words = set(re.findall(r"[^\s।,?]+", mcq["stem"]))
        check(f"{tag}: no negative stem",
              not (stem_words & {"নয়", "ছাড়া", "not", "নেই", "ব্যতীত"}),
              mcq["stem"])
        src = by_id[mcq["_item_id"]]["source_text"]
        check(f"{tag}: source quote verbatim in article text",
              _quote_in_text(mcq["source_quote"], src),
              mcq["source_quote"][:80])
        check(f"{tag}: why_wrong covers all 4 options",
              set(mcq.get("why_wrong", {})) == {"ক", "খ", "গ", "ঘ"})
    for i, qa in enumerate(all_qa):
        check(f"qa[{i}] {qa['id']}: has question, answer, fact_id, quote",
              all(qa.get(k) for k in
                  ("question", "answer", "fact_id", "source_quote")))
    return all_qa, all_mcq


# ---------------------------------------------------------------------------
# Step 8 — unit fix (Rudro 2026-11-15): a numeric MCQ must carry the
# same unit on all four options. Regression patterns are the 15 Nov
# dry-run flaws (Q13/Q14/Q15/Q17/Q20/Q21): the correct option alone
# carried a unit ('6.53 %' vs bare '5.9 / 7.2 / 8.2'), so the unit
# itself signalled the answer. The fix must never change the
# correct value or the correct answer.
# ---------------------------------------------------------------------------
def test_step8_unit_fix():
    print("\n=== STEP 8 — unit fix (same unit on all four options) ===")
    cases = [
        ("u1", "6.53", "%"), ("u2", "126.35", "million"),
        ("u3", "41", "%"), ("u4", "1", "billion"),
        ("u5", "৫৬০", "কোটি"), ("u6", "800", "km"),
    ]
    for item_id, value, unit in cases:
        quote = f"The figure reached {value} {unit} in the latest report."
        item = {"id": item_id, "headline": "Test headline", "score": 2,
                "topic_primary": "BD-ECO", "status": "happened",
                "date": "2026-11-15", "published": "2026-11-15",
                "body_text": quote + " More context follows here.",
                "facts": [{"what": "reported figure", "value": value,
                           "unit": unit, "date": "2026-11-15",
                           "status": "happened", "quote": quote,
                           "fact_id": f"{item_id}-f1"}]}
        mcq = _build_mcq(item, item["facts"][0], 1)
        tag = f"unit {value} {unit}"
        check(f"{tag}: MCQ built", mcq is not None)
        if mcq is None:
            continue
        opts = list(mcq["options"].values())
        check(f"{tag}: correct value unchanged",
              mcq["options"]["ক"] == f"{value} {unit}", str(opts))
        check(f"{tag}: all four options carry the unit",
              all(o.endswith(unit) for o in opts), str(opts))
        key_len = len(mcq["options"]["ক"])
        check(f"{tag}: key is not the unique longest option",
              key_len < max(len(o) for o in opts)
              or len({len(o) for o in opts}) == 1, str(opts))
    check("_fmt_number keeps 2 decimals from a 2-decimal key",
          _fmt_number(5.877, "6.53") == "5.88", _fmt_number(5.877, "6.53"))
    two = _fmt_number(113.715, "126.35")
    check("_fmt_number keeps 2 decimals (126.35 style)",
          "." in two and len(two.split(".")[1]) == 2, two)
    check("_fmt_number keeps 1 decimal from a 1-decimal key",
          _fmt_number(7.18, "6.5") == "7.2", _fmt_number(7.18, "6.5"))
    check("_fmt_number keeps int keys int",
          _fmt_number(450, "442") == "450", _fmt_number(450, "442"))


# ---------------------------------------------------------------------------
# Step 9 — SRS simulation
# ---------------------------------------------------------------------------
def test_step9(all_qa, all_mcq):
    print("\n=== STEP 9 — SRS simulation ===")
    questions = all_qa + all_mcq
    state = build_cards(questions, DATE)
    (RUNS_DIR / f"srs-{DATE}.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    check("build_cards: one card per checked question",
          len(state["cards"]) == len(questions),
          f"{len(state['cards'])} vs {len(questions)}")
    check("new cards: next_review tomorrow, interval 1, reps 0",
          all(c["next_review"] == "2026-11-15"
              and c["interval_days"] == 1 and c["repetitions"] == 0
              and c["reported"] is False for c in state["cards"]))
    check("build_cards skips unchecked questions",
          len(build_cards([{"id": "x1", "question": "q?",
                            "checked": False},
                           {"id": "x2", "question": "q?"}],
                          DATE)["cards"]) == 0)

    cards = {c["question_id"]: dict(c) for c in state["cards"]}
    ids = list(cards)
    a_id, b_id = ids[0], ids[1]

    # Card A: correct 4 times on its due dates -> 1, 3, 7, 14.
    intervals = []
    day = "2026-11-15"
    card_a = cards[a_id]
    for _ in range(4):
        card_a = grade_answer(card_a, True, day)
        intervals.append(card_a["interval_days"])
        print(f"  A correct on {day}: reps={card_a['repetitions']} "
              f"interval={card_a['interval_days']} "
              f"next={card_a['next_review']}")
        day = card_a["next_review"]
    check("correct answers follow intervals 1 -> 3 -> 7 -> 14",
          intervals == [1, 3, 7, 14], str(intervals))

    # Card B: wrong on its due date -> reset to +1 day.
    card_b = grade_answer(cards[b_id], False, "2026-11-15")
    print(f"  B wrong on 2026-11-15: reps={card_b['repetitions']} "
          f"interval={card_b['interval_days']} next={card_b['next_review']}")
    check("wrong answer resets to repetitions 0, next_review +1 day",
          card_b["repetitions"] == 0 and card_b["interval_days"] == 1
          and card_b["next_review"] == "2026-11-16",
          str(card_b))

    # Due ordering: yesterday's facts first (oldest next_review first).
    probe = [dict(cards[ids[2]], next_review="2026-11-15"),
             dict(cards[ids[3]], next_review="2026-11-13"),
             dict(cards[ids[4]], next_review="2026-11-14")]
    due = quiz_due(probe, "2026-11-15")
    check("quiz_due sorts oldest next_review first",
          [c["next_review"] for c in due]
          == ["2026-11-13", "2026-11-14", "2026-11-15"],
          str([c["next_review"] for c in due]))
    check("quiz_due on 2026-11-15 returns all new cards",
          len(quiz_due(state["cards"], "2026-11-15")) == len(state["cards"]))

    # Reported card leaves the due list.
    reported_b = report_card(card_b)
    check("report_card: reported=true, next_review=null",
          reported_b["reported"] is True
          and reported_b["next_review"] is None)
    check("reported card is not due",
          reported_b not in quiz_due([reported_b], "2026-11-16")
          and quiz_due([reported_b], "2026-11-16") == [])
    print(f"  schedule: A ends next_review={card_a['next_review']} "
          f"(reps {card_a['repetitions']}); "
          f"B reported -> out of the quiz until review.")


# ---------------------------------------------------------------------------
# Syllabus proposals 7, 8, 9 — fixed fixtures (no network)
# ---------------------------------------------------------------------------
_S3_BODY = (
    "The International Monetary Fund board has approved a $442 million "
    "tranche for Bangladesh under its loan programme. The approval came "
    "on 13 November 2026 after a review of the country's economic "
    "reforms. Bangladesh's foreign exchange reserves stood at "
    "$26 billion in October 2026.")
_S3_FACTS = [
    {"what": "IMF board approves tranche for Bangladesh", "value": "442",
     "unit": "million", "date": "2026-11-13", "status": "happened",
     "quote": "The International Monetary Fund board has approved a "
              "$442 million tranche for Bangladesh under its loan programme.",
     "fact_id": "t3-f1"},
    {"what": "foreign exchange reserves", "value": "26",
     "unit": "billion", "date": "2026-10-31", "status": "happened",
     "quote": "Bangladesh's foreign exchange reserves stood at "
              "$26 billion in October 2026.",
     "fact_id": "t3-f2"},
]
_S3_WHY = ("[পটভূমি] আন্তর্জাতিক সংস্থার সিদ্ধান্ত বাংলাদেশের অর্থনীতি "
           "ও কূটনীতির সঙ্গে যুক্ত বলে পরীক্ষায় আসে।")


def _s3_item(score=3, n_facts=2, why=_S3_WHY, status="happened", iid="t3"):
    facts = list(_S3_FACTS[:n_facts])
    lines = [
        "আইএমএফ (IMF) বোর্ড বাংলাদেশের জন্য ৪৪২ মিলিয়ন ডলারের কিস্তি "
        "অনুমোদন করেছে (২০২৬-১১-১৩)।",
        "বৈদেশিক মুদ্রার রিজার্ভ ২৬ বিলিয়ন ডলার (২০২৬-১০-৩১)।",
    ][:n_facts]
    return {
        "id": iid,
        "headline": "IMF board approves $442 million tranche for Bangladesh",
        "score": score, "topic_primary": "INT-ORG", "status": status,
        "facts": facts, "fact_lines": lines,
        "facts_en": render_facts_en(facts, _S3_BODY),
        "why_important": why,
        "sources": [{"name": "Test", "url": "https://example.test/imf"}],
        "date": "2026-11-14", "published": "2026-11-14T05:30:00+00:00",
        "body_text": _S3_BODY,
    }


def test_syllabus_step7_8():
    print("\n=== SYLLABUS PROPOSALS 7, 8, 9 (fixed fixtures) ===")
    item3 = _s3_item(score=3)
    item2 = _s3_item(score=2, iid="t2")

    # --- P7: focus_paragraph (score-3 only) ---
    page = build_page("2026-11-14", [item3, item2], [])
    by_id = {}
    for sec in page["sections"].values():
        for it in sec:
            by_id[it["id"]] = it
    p3 = by_id["t3"]
    check("P7: score-3 item carries focus_paragraph",
          "focus_paragraph" in p3, str(p3.keys()))
    n_sent = len([s for s in p3["focus_paragraph"].split("।") if s.strip()])
    check("P7: focus paragraph is 4 sentences (2 facts)",
          n_sent == 4, f"{n_sent} sentences: {p3['focus_paragraph']}")
    check("P7: paragraph opens with the headline (প্রসঙ্গ)",
          p3["focus_paragraph"].startswith(item3["headline"]),
          p3["focus_paragraph"][:60])
    check("P7: paragraph carries the [পটভূমি] line (বিশ্লেষণ)",
          "[পটভূমি]" in p3["focus_paragraph"])
    # Step 5(b) excludes the fact's date field from number-checking
    # (a date may legitimately be the article's date line), so strip
    # ISO dates from the paragraph before checking its numbers.
    para_nodates = re.sub(r"[০-৯0-9]{4}-[০-৯0-9]{2}-[০-৯0-9]{2}",
                          " ", p3["focus_paragraph"])
    check("P7: every non-date number in the paragraph appears in the article",
          all(n in numbers_in(_S3_BODY)
              for n in numbers_in(para_nodates)),
          str(numbers_in(para_nodates)))
    check("P7: score-2 item has NO focus_paragraph",
          "focus_paragraph" not in by_id["t2"])
    one_fact = build_focus_paragraph({
        "score": 3, "headline": item3["headline"], "date": "2026-11-14",
        "fact_lines": item3["fact_lines"][:1],
        "why_important": item3["why_important"]})
    check("P7: 1 fact -> 3 sentences",
          len([s for s in one_fact.split("।") if s.strip()]) == 3, one_fact)
    check("P7: 0 facts -> omitted",
          build_focus_paragraph({
              "score": 3, "headline": item3["headline"],
              "date": "2026-11-14", "fact_lines": [],
              "why_important": item3["why_important"]}) == "")
    check("P7: no why line -> omitted",
          build_focus_paragraph({
              "score": 3, "headline": item3["headline"],
              "date": "2026-11-14",
              "fact_lines": item3["fact_lines"], "why_important": ""}) == "")
    # Slug-derived headlines sometimes express a figure in a
    # different unit than the body ("Tk159 Crore" in the headline
    # vs "1.59 billion" in the body): the headline number must be
    # dropped from the paragraph, not carried as an unverified fact.
    slug_norm = {
        "score": 3,
        "headline": "Customs Detects Tk159 Crore Revenue Irregularities "
                    "Export Consignments Two Garment",
        "date": "2026-11-13",
        "fact_lines": item3["fact_lines"],
        "why_important": item3["why_important"],
        "body_numbers": ["1.59", "237", "687", "2026", "11", "13"],
    }
    slug_para = build_focus_paragraph(slug_norm)
    check("P7: slug-headline number not in the body is dropped",
          "159" not in slug_para, slug_para)
    check("P7: dropped-number paragraph still has 4 sentences",
          len([s for s in slug_para.split("।") if s.strip()]) == 4,
          slug_para)
    check("P7: dropped-number paragraph keeps the headline words",
          "Customs Detects" in slug_para, slug_para)
    check("P7: glued unit suffix goes with its dropped number",
          "TkCr" not in slug_para and "Tk " in slug_para, slug_para)
    b_norm = {
        "score": 3,
        "headline": "Govt Targets 186B Budget Support Dev Partners Fy27",
        "date": "2026-11-14",
        "fact_lines": item3["fact_lines"],
        "why_important": item3["why_important"],
        "body_numbers": ["27", "380", "3.44", "2026", "11", "14"],
    }
    b_para = build_focus_paragraph(b_norm)
    check("P7: dropped '186B' leaves no lone 'B' behind",
          "186B" not in b_para and " Targets B " not in b_para, b_para)
    check("P7: kept number keeps its context ('Fy27')",
          "Fy27" in b_para, b_para)
    fy_norm = dict(slug_norm)
    fy_norm["headline"] = ("Flawed Industrial Data Inflated Gdp Growth "
                           "Numbers Fy15 Fy19")
    fy_norm["body_numbers"] = ["15", "19", "41", "6.27", "15.16", "61.6"]
    fy_para = build_focus_paragraph(fy_norm)
    check("P7: headline number that IS in the body is kept",
          "Fy15" in fy_para and "Fy19" in fy_para, fy_para)
    # Fallback (no body): allowed numbers come from the fact lines.
    fb_norm = {
        "score": 3,
        "headline": "Customs Detects Tk159 Crore Revenue Irregularities",
        "date": "2026-11-13",
        "fact_lines": item3["fact_lines"],
        "why_important": item3["why_important"],
    }
    check("P7: fallback drops a headline number absent from the facts",
          "159" not in build_focus_paragraph(fb_norm),
          build_focus_paragraph(fb_norm))
    fb_norm2 = dict(fb_norm)
    fb_norm2["headline"] = ("IMF board approves $442 million tranche "
                            "for Bangladesh")
    check("P7: fallback keeps a headline number present in the facts",
          "442" in build_focus_paragraph(fb_norm2),
          build_focus_paragraph(fb_norm2))

    # --- P8: facts_en on every page item ---
    check("P8: score-3 page item carries facts_en (2 facts)",
          len(p3.get("facts_en") or []) == 2
          and [f["value"] for f in p3["facts_en"]] == ["442", "26"],
          str(p3.get("facts_en")))
    check("P8: score-2 page item also carries facts_en",
          len(by_id["t2"].get("facts_en") or []) == 2)

    # --- P9: analytical questions (score-3 only, max 2/edition) ---
    q = analytical_question_for_item(item3)
    check("P9: score-3 item yields one analytical question",
          q is not None and q["kind"] == "analytical"
          and q["is_analysis"] is True, str(q))
    check("P9: stem asks for an implication",
          "প্রভাব" in (q["question"] if q else ""), q["question"] if q else "")
    check("P9: answer is explicitly marked as analysis, not fact",
          (q["answer"] if q else "").startswith("বিশ্লেষণ"),
          (q["answer"] or "")[:60])
    check("P9: analytical source quote is verbatim in the article",
          q is not None and _quote_in_text(q["source_quote"], _S3_BODY))
    check("P9: every number in the analytical answer is in the article",
          q is not None and all(n in numbers_in(_S3_BODY)
                                for n in numbers_in(q["answer"])),
          str(numbers_in(q["answer"])) if q else "")
    check("P9: score-2 item yields no analytical question",
          analytical_question_for_item(item2) is None)
    check("P9: score-3 item with <2 facts yields none",
          analytical_question_for_item(_s3_item(score=3, n_facts=1)) is None)
    check("P9: proposed item gets a solution stem",
          "করা উচিত" in (analytical_question_for_item(
              _s3_item(score=3, status="proposed", iid="t3p")) or {})
          .get("question", ""))
    capped = analytical_for_items([_s3_item(score=3, iid=f"t3-{i}")
                                   for i in range(3)])
    check("P9: max 2 analytical questions per edition",
          len(capped) == 2, f"{len(capped)}")


def test_pub_date():
    """run_v2._pub_date: any pub-date format -> YYYY-MM-DD.

    Regression: the old [:10] slice turned the Financial Express
    RFC-2822 date into "Sat, 14 No", which leaked into page dates
    and focus paragraphs (and made the day number look untraceable
    to Step 5)."""
    print("\n=== run_v2._pub_date ===")
    check("pub_date: RFC-2822 -> ISO date",
          _pub_date("Sat, 14 Nov 2026 02:00:00 GMT") == "2026-11-14",
          _pub_date("Sat, 14 Nov 2026 02:00:00 GMT"))
    check("pub_date: ISO datetime -> ISO date",
          _pub_date("2026-11-14T05:30:00+00:00") == "2026-11-14",
          _pub_date("2026-11-14T05:30:00+00:00"))
    check("pub_date: bare ISO date unchanged",
          _pub_date("2026-11-14") == "2026-11-14",
          _pub_date("2026-11-14"))
    check("pub_date: unparseable -> empty (never a garbled date)",
          _pub_date("not a date") == "", _pub_date("not a date"))
    check("pub_date: empty -> empty",
          _pub_date("") == "", repr(_pub_date("")))


def main():
    items, maybe_items, used_fallback = build_fixture()
    print(f"[fixture] {len(items)} full items, "
          f"{len(maybe_items)} maybe items "
          f"({'fallback snapshot' if used_fallback else 'live RSS'})")
    for it in items:
        print(f"  {it['id']} score={it['score']} {it['topic_primary']} "
              f"{it['status']} | {it['headline'][:90]}")
    test_step7(items, maybe_items)
    test_step7_ranking_editorial()
    test_syllabus_step7_8()
    test_pub_date()
    all_qa, all_mcq = test_step8(items)
    test_step8_unit_fix()
    test_step9(all_qa, all_mcq)
    print(f"\n==== RESULT: {PASS} PASS, {FAIL} FAIL ====")
    print(f"artifacts: {RUNS_DIR}/page-{DATE}.json, "
          f"questions-{DATE}.json, srs-{DATE}.json")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
