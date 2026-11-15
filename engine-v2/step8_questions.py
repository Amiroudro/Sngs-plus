#!/usr/bin/env python3
"""Step 8 — Questions (Sarangsho Plus engine v2).

``questions_for_item(item)`` -> {"qa": [...], "mcq": [...]}.

Q&A: one fact per question; the answer comes from the fact list,
plus the source quote. Mostly recall; the why_important line yields
one analytical question (marked "kind": "analytical").

MCQ: stem + options ক খ গ ঘ + key + source quote + why each wrong
option fails. Distractors are the same type and grammar as the key
(all names, all dates, all organisations); for numbers close values
are used (e.g. key 442 -> 400, 450, 500 style neighbours); for names
only real related bodies from the built-in per-topic table are used —
never invented bodies. No "সবগুলো" / "কোনোটিই নয়" options and no
negative stems. The year or "as of" date goes in the stem for
time-sensitive facts.

Any MCQ whose source quote fails the Step 5 quote check (the quote
must be verbatim in the article text) is rejected and never emitted.

NOTE ON SHUFFLING: the engine outputs the key in canonical order
(the correct answer is always option ক) and NEVER shuffles — the
app shuffles the key position at render time.

Every emitted question carries "checked": true, meaning its source
quote passed the Step 5 verbatim check; Step 9 only builds SRS cards
from checked questions.

Stdlib-only Python 3. No publishing, no LLM.
"""
import math
import re
import unicodedata
from datetime import date as _date, timedelta

# ---------------------------------------------------------------------------
# Step 5 quote check.
# Uses step5_check.quote_in_text when available (the real Step 5(a)
# check, same normalisation); falls back to the local _quote_in_text()
# below, which duplicates it exactly, if the import fails.
# ---------------------------------------------------------------------------
_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_ZERO_WIDTH = ("\u200b", "\u200c", "\u200d", "\ufeff")


def _norm(text):
    text = unicodedata.normalize("NFC", str(text or ""))
    text = text.translate(_BN_DIGITS)
    for ch in _ZERO_WIDTH:
        text = text.replace(ch, "")
    return re.sub(r"\s+", " ", text).strip()


def _quote_in_text(quote, text):
    """Local Step 5 quote check (duplicates step5 until that module lands)."""
    q, t = _norm(quote), _norm(text)
    return bool(q) and q in t


_STEP5_FN = None
try:
    import step5_check as _step5
    for _name in ("quote_in_text", "check_quote", "quote_ok", "verify_quote"):
        if hasattr(_step5, _name):
            _STEP5_FN = getattr(_step5, _name)
            break
except Exception:
    _step5 = None


def _quote_ok(quote, text):
    if _STEP5_FN is not None:
        try:
            return bool(_STEP5_FN(quote, text))
        except Exception:
            pass
    return _quote_in_text(quote, text)


# ---------------------------------------------------------------------------
# Same-type distractors.
# ---------------------------------------------------------------------------
# Real related bodies only — never invented. Keyed by topic; the
# generic pool is used when a topic has no table.
RELATED_BODIES = {
    "BD-BANK": ["বাংলাদেশ ব্যাংক (Bangladesh Bank)", "আইএমএফ (IMF)",
                "বিশ্বব্যাংক (World Bank)", "এডিবি (ADB)"],
    "BD-ECO": ["বাংলাদেশ ব্যাংক (Bangladesh Bank)", "বিশ্বব্যাংক (World Bank)",
               "এডিবি (ADB)", "জাতিসংঘ (United Nations)"],
    "BD-GOV": ["নির্বাচন কমিশন (Election Commission)",
               "সুপ্রিম কোর্ট (Supreme Court)", "মন্ত্রিসভা (Cabinet)",
               "সংসদ (Parliament)"],
    "INT-ORG": ["জাতিসংঘ (United Nations)", "বিশ্বব্যাংক (World Bank)",
                "আইএমএফ (IMF)", "এডিবি (ADB)",
                "বিশ্ব বাণিজ্য সংস্থা (WTO)"],
    "INT-REL": ["জাতিসংঘ (United Nations)", "সার্ক (SAARC)",
                "বিমসটেক (BIMSTEC)", "আসিয়ান (ASEAN)"],
    "ENV": ["জাতিসংঘ (United Nations)", "বিশ্বব্যাংক (World Bank)",
            "এডিবি (ADB)", "আইএমএফ (IMF)"],
    "SCI": ["বিশ্ব স্বাস্থ্য সংস্থা (WHO)", "জাতিসংঘ (United Nations)",
            "বিশ্বব্যাংক (World Bank)", "এডিবি (ADB)"],
    "SPORT": ["আইসিসি (ICC)", "ফিফা (FIFA)", "অলিম্পিক কমিটি (IOC)",
              "এশিয়ান ক্রিকেট কাউন্সিল (ACC)"],
    "PEOPLE": ["নোবেল কমিটি (Nobel Committee)", "জাতিসংঘ (United Nations)",
               "বাংলা একাডেমি (Bangla Academy)", "ইউনেস্কো (UNESCO)"],
    "BD-NATL": ["বাংলা একাডেমি (Bangla Academy)", "জাতিসংঘ (United Nations)",
                "বিশ্বব্যাংক (World Bank)", "এডিবি (ADB)"],
}
_GENERIC_BODIES = RELATED_BODIES["INT-ORG"]

_FORBIDDEN_OPTIONS = ("সবগুলো", "কোনোটিই নয়", "কোনোটিই না", "সবগুলোই")
_NEGATIVE_STEM_WORDS = {"নয়", "ছাড়া", "not", "নেই", "ব্যতীত", "কখনোই"}
_OPTION_KEYS = ("ক", "খ", "গ", "ঘ")
_MONTHS_EN = {"january": 1, "february": 2, "march": 3, "april": 4,
              "may": 5, "june": 6, "july": 7, "august": 8, "september": 9,
              "october": 10, "november": 11, "december": 12}
_MONTHS_BN = {"জানুয়ারি": 1, "ফেব্রুয়ারি": 2, "মার্চ": 3, "এপ্রিল": 4,
              "মে": 5, "জুন": 6, "জুলাই": 7, "আগস্ট": 8, "সেপ্টেম্বর": 9,
              "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12}


def _parse_number(value):
    """Parse an int/float out of a value string (Bangla digits OK)."""
    text = _norm(value).replace(",", "").strip()
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        num = float(m.group(0))
    except ValueError:
        return None
    return num


def _parse_date(value):
    """Parse YYYY-MM-DD, or '14 November 2026' / Bangla month forms."""
    text = _norm(value).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
    if m:
        try:
            return _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})\s+([A-Za-z\u0980-\u09FF]+)\s+(\d{4})$", text)
    if m:
        month = _MONTHS_EN.get(m.group(2).lower())
        if month is None:
            month = _MONTHS_BN.get(m.group(2))
        if month:
            try:
                return _date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                return None
    return None


def _fact_type(value):
    """'number' | 'date' | 'name' for a fact value."""
    text = _norm(value).strip()
    if not text:
        return None
    if _parse_date(text) is not None:
        return "date"
    if _parse_number(text) is not None and re.fullmatch(
            r"-?[\d,]+(?:\.\d+)?", text):
        return "number"
    return "name"


def _fmt_number(num, like):
    """Format a distractor number in the style of the key: same
    decimal places as the key (int stays int), commas kept if the
    key had them. Distractors must be the same type and grammar as
    the key -- a key with 2 decimals ('6.53') must not get
    1-decimal distractors ('5.9'), or the key stays the unique
    longest option and the length itself signals the answer
    (Rudro 2026-11-15, Step 8 unit fix)."""
    like = _norm(like)
    if "." in like:
        decimals = len(like.split(".", 1)[1].rstrip(","))
        out = f"{num:.{decimals}f}"
    else:
        out = str(int(round(num)))
    if "," in like:
        out = f"{float(out):,.0f}" if "." not in out else f"{float(out):,}"
    return out


def _numeric_distractors(value):
    """Close values of the same type, e.g. key 442 -> 400, 450, 500."""
    num = _parse_number(value)
    if num is None:
        return []
    out = []
    if num == int(num) and abs(num) >= 10:
        n = int(num)
        mag = 10 ** max(int(math.log10(abs(n))) - 1, 0)
        step = max(mag, 10)
        cands = [n - step, n + step, n + 2 * step]
        cands = [round(c / step) * step for c in cands]
        cands += [round(n * 1.5 / step) * step,
                  round(n * 0.5 / step) * step]
        for c in cands:
            if c != n and c > 0 and c not in out:
                out.append(_fmt_number(c, value))
    elif num == int(num):
        for c in (int(num) + 1, int(num) + 2, int(num) - 1, int(num) + 3):
            if c != int(num) and c > 0 and c not in out:
                out.append(str(c))
    else:
        for f in (num * 0.9, num * 1.1, num * 1.25, num * 0.8):
            s = _fmt_number(f, value)
            if s != _norm(value) and s not in out:
                out.append(s)
    return out[:3]


def _date_distractors(value):
    """Close dates in the same format as the key."""
    day = _parse_date(value)
    if day is None:
        return []
    out = []
    for delta in (-1, 2, 7):
        d = day + timedelta(days=delta)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", _norm(value).strip()):
            out.append(d.isoformat())
        else:
            out.append(d.strftime("%d %B %Y"))
    return out


def _name_distractors(key, topic):
    """Other real bodies from the same topic's table (never invented)."""
    pool = list(RELATED_BODIES.get(topic) or _GENERIC_BODIES)
    # If the key itself is a table entry, use its own table's siblings.
    for table in RELATED_BODIES.values():
        if key in table:
            pool = list(table)
            break
    pool = [p for p in pool if _norm(p) != _norm(key)]
    return pool[:3]


def _distractors(fact, topic):
    kind = _fact_type(fact["value"])
    if kind == "number":
        return _numeric_distractors(fact["value"])
    if kind == "date":
        return _date_distractors(fact["value"])
    if kind == "name":
        return _name_distractors(fact["value"], topic)
    return []


def _stem_for(fact):
    """Open-question stem for a fact, with the year / 'as of' date for
    time-sensitive facts. Never a negative stem."""
    what = (fact.get("what") or "").strip().rstrip("?।")
    kind = _fact_type(fact.get("value", ""))
    date = (fact.get("date") or "").strip()
    if kind == "number":
        stem = f"{what} কত?"
    elif kind == "date":
        year = _norm(fact["value"]).strip()[:4]
        stem = f"{what} কবে? ({year} সালের তথ্য অনুযায়ী)"
    elif kind == "name":
        stem = f"{what} কোনটি?"
    else:
        stem = f"{what} কী?"
    if kind != "date" and date and date != "উল্লেখ নেই":
        stem = f"{stem[:-1]} ({date} অনুযায়ী)?" if stem.endswith("?") else stem
    return stem


def _stem_is_negative(stem):
    words = set(re.findall(r"[^\s।,?]+", stem))
    return bool(words & _NEGATIVE_STEM_WORDS)


def _extract_facts(item):
    """Normalise an item's facts to Step 4 shape.

    Prefers item["facts"] (structured). Otherwise derives facts from
    fact_lines: a line carrying a number -> numeric fact; a line
    carrying a known organisation name -> name fact; other lines ->
    Q&A-only facts (no usable value, so no MCQ).
    """
    facts = []
    raw = item.get("facts") or []
    if raw:
        for i, f in enumerate(raw):
            if not isinstance(f, dict):
                continue
            facts.append({
                "what": (f.get("what") or "").strip(),
                "value": (f.get("value") or "").strip(),
                "unit": (f.get("unit") or "").strip(),
                "date": (f.get("date") or "").strip(),
                "status": (f.get("status") or "").strip(),
                "quote": (f.get("quote") or "").strip(),
                "fact_id": f.get("fact_id") or f"{item.get('id', 'item')}-f{i + 1}",
            })
        return facts
    lines = item.get("fact_lines") or item.get("bangla_lines") or []
    orgs = [o for table in RELATED_BODIES.values() for o in table]
    for i, line in enumerate(lines):
        line = str(line).strip()
        if not line:
            continue
        m = re.search(r"\d+(?:,\d+)*(?:\.\d+)?", _norm(line))
        org = next((o for o in orgs if o in line or _norm(o) in _norm(line)),
                   None)
        if m:
            facts.append({"what": "এই তথ্যে উল্লিখিত সংখ্যা",
                          "value": m.group(0), "unit": "",
                          "date": item.get("date", ""),
                          "status": item.get("status", ""),
                          "quote": line,
                          "fact_id": f"{item.get('id', 'item')}-f{i + 1}"})
        elif org:
            facts.append({"what": "এই তথ্যে উল্লিখিত সংস্থা",
                          "value": org, "unit": "",
                          "date": item.get("date", ""),
                          "status": item.get("status", ""),
                          "quote": line,
                          "fact_id": f"{item.get('id', 'item')}-f{i + 1}"})
        else:
            facts.append({"what": line, "value": "", "unit": "",
                          "date": item.get("date", ""),
                          "status": item.get("status", ""),
                          "quote": line,
                          "fact_id": f"{item.get('id', 'item')}-f{i + 1}"})
    return facts


def _source_text_of(item):
    return (item.get("source_text") or item.get("article_text")
            or item.get("body_text")
            or " ".join([item.get("headline", ""), item.get("title", "")]
                        + [str(x) for x in
                           (item.get("fact_lines") or [])]))


def _build_mcq(item, fact, num):
    """Build one MCQ, or return None if any rule rejects it."""
    topic = item.get("topic_primary", "")
    quote = fact["quote"]
    source_text = _source_text_of(item)
    # Step 5 quote check: the quote must be verbatim in the article
    # text, otherwise the MCQ is rejected outright.
    if not quote or not _quote_ok(quote, source_text):
        return None
    stem = _stem_for(fact)
    if _stem_is_negative(stem):
        return None
    distractors = _distractors(fact, topic)
    if len(distractors) < 3:
        return None
    key = fact["value"]
    if fact["unit"]:
        key = f"{key} {fact['unit']}"
        if _fact_type(fact["value"]) == "number":
            # Same unit on all four options (Rudro 2026-11-15): the
            # correct option must not be the only one carrying a
            # unit ('6.53 %' vs bare '5.9 / 7.2 / 8.2'), or the unit
            # itself signals the answer. The correct value and the
            # correct answer are unchanged; only the distractors
            # gain the fact's unit.
            distractors = [f"{d} {fact['unit']}" for d in distractors]
    options = {_OPTION_KEYS[0]: key}
    for k, d in zip(_OPTION_KEYS[1:], distractors[:3]):
        options[k] = d
    if len(set(_norm(v) for v in options.values())) != 4:
        return None
    if any(any(f in v for f in _FORBIDDEN_OPTIONS)
           for v in options.values()):
        return None
    kind = _fact_type(fact["value"])
    why_wrong = {_OPTION_KEYS[0]:
                 "সঠিক উত্তর — উৎসের উদ্ধৃতিতে এই তথ্যই আছে।"}
    for k in _OPTION_KEYS[1:]:
        if kind == "number":
            why_wrong[k] = ("ভুল — উৎসের সংখ্যা এর চেয়ে আলাদা; "
                            f"সঠিক সংখ্যা {key}।")
        elif kind == "date":
            why_wrong[k] = ("ভুল — উৎসের তারিখ এর চেয়ে আলাদা; "
                            f"সঠিক তারিখ {key}।")
        else:
            why_wrong[k] = (f"ভুল — উৎসে '{options[k]}' উল্লেখ নেই; "
                            f"সঠিক উত্তর {key}।")
    return {
        "id": f"{item.get('id', 'item')}-mcq{num}",
        "stem": stem,
        "options": options,
        "key": "ক",  # canonical order; the app shuffles at render time
        "source_quote": quote,
        "why_wrong": why_wrong,
        "fact_id": fact["fact_id"],
        "kind": "analytical" if fact.get("analytical") else "recall",
        "checked": True,
    }


def questions_for_item(item):
    """Generate Q&A + MCQ for one item.

    Q&A: one per fact (answer from the fact list) plus, when the item
    carries a why_important line, one analytical question about it.
    MCQ: at most 3 per item, one per MCQ-able fact (number / date /
    name value). Any MCQ failing the Step 5 quote check is dropped.
    """
    item_id = item.get("id", "item")
    facts = _extract_facts(item)
    qa, mcq = [], []
    for i, fact in enumerate(facts[:5]):
        if not fact["what"]:
            continue
        stem = _stem_for(fact)
        answer = fact["value"]
        if fact["unit"]:
            answer = f"{answer} {fact['unit']}"
        if not answer:
            answer = fact["quote"]
        qa.append({
            "id": f"{item_id}-qa{i + 1}",
            "question": stem,
            "answer": answer,
            "fact_id": fact["fact_id"],
            "source_quote": fact["quote"],
            "kind": "recall",
            "checked": True,
        })
    why = (item.get("why_important") or item.get("why_important_bn") or "").strip()
    if why:
        qa.append({
            "id": f"{item_id}-qa{len(qa) + 1}",
            "question": "এই খবরটি কেন গুরুত্বপূর্ণ?",
            "answer": why,
            "fact_id": f"{item_id}-why",
            "source_quote": facts[0]["quote"] if facts else "",
            "kind": "analytical",
            "checked": True,
        })
    for fact in facts:
        if len(mcq) >= 3:
            break
        if not fact["value"] or _fact_type(fact["value"]) is None:
            continue
        built = _build_mcq(item, fact, len(mcq) + 1)
        if built is not None:
            mcq.append(built)
    return {"qa": qa, "mcq": mcq}


# ---------------------------------------------------------------------------
# Analytical questions (Proposal 9, syllabus): at most 2 per edition,
# only from score-3 items. The stem asks for an implication or a
# solution; the answer is grounded ONLY in the item's verified fact
# list + its [পটভূমি] line and is explicitly marked as analysis, not
# fact. Any analytical question whose answer would need a fact not in
# the list is rejected — by construction here: the answer restates
# the item's own fact quotes + its [পটভূমি] line and nothing else.
# Analytical questions are NOT SRS cards (they train analysis, not
# recall) — run_v2 keeps them out of the Step 9 card list.
# ---------------------------------------------------------------------------
_ANALYTICAL_STEMS = {
    "happened": "এই সিদ্ধান্তের বাংলাদেশের জন্য প্রভাব কী?",
    "proposed": "এই প্রস্তাব বাস্তবায়নে কী করা উচিত?",
    "scheduled": "এই নির্ধারিত সিদ্ধান্তের জন্য বাংলাদেশের কী প্রস্তুতি প্রয়োজন?",
    "forecast": "এই পূর্বাভাস অনুযায়ী বাংলাদেশের জন্য কী করা উচিত?",
}
ANALYTICAL_MAX_PER_EDITION = 2


def analytical_question_for_item(item):
    """One analytical question for a score-3 item, or None.

    Guards (any failure -> None, no question is emitted): score must
    be 3; at least 2 facts; a non-empty why_important line. The
    answer is the top two fact quotes + the [পটভূমি] line, prefixed
    "বিশ্লেষণ" so it is never mistaken for a fact.
    """
    if int(item.get("score", 2) or 2) < 3:
        return None
    facts = _extract_facts(item)
    why = (item.get("why_important")
           or item.get("why_important_bn") or "").strip()
    if len(facts) < 2 or not why:
        return None
    quotes = [(f.get("quote") or "").strip() for f in facts[:2]]
    quotes = [q for q in quotes if q]
    if not quotes:
        return None
    status = (item.get("status") or "happened").strip()
    stem = _ANALYTICAL_STEMS.get(status, _ANALYTICAL_STEMS["happened"])
    answer = ("বিশ্লেষণ (তথ্যের ভিত্তিতে, নতুন তথ্য নয়): "
              + " ".join(quotes) + " " + why)
    return {
        "id": f"{item.get('id', 'item')}-aq1",
        "question": stem,
        "answer": answer,
        "fact_id": facts[0]["fact_id"],
        "source_quote": facts[0]["quote"],
        "kind": "analytical",
        "is_analysis": True,
        "checked": True,
    }


def analytical_for_items(items, limit=ANALYTICAL_MAX_PER_EDITION):
    """Analytical questions for a list of items, in order, capped at
    ``limit`` per edition (Proposal 9)."""
    out = []
    for item in (items or []):
        if len(out) >= limit:
            break
        q = analytical_question_for_item(item)
        if q is not None:
            out.append(q)
    return out
