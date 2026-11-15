#!/usr/bin/env python3
"""Step 4 — Fact list (engine v2).

Deterministic, stdlib-only. No LLM, no v1 imports.

extract_facts(article) takes an article dict with ``body_text`` (full
text, fetched only for Step-3-kept articles) and ``published`` (ISO
date-time string) and returns::

    {"facts": [fact, ...], "why_important": "[পটভূমি] ..."}

with each fact::

    {"what": ..., "value": ..., "unit": ..., "date": "YYYY-MM-DD" | "উল্লেখ নেই",
     "status": "happened|scheduled|proposed|forecast",
     "quote": "exact article sentence, verbatim"}

Method: split the body into sentences (span-based, so each quote is a
verbatim slice of the original text); score each sentence by
fact-density — a number and/or a date and/or a capitalised/Bangla name
AND a topic term from RULES.md (via rules_loader); take the top 3-5
distinct sentences. For each, parse the value (first number in the
sentence, Bangla digits kept as printed), the unit (adjacent to the
number), the date (absolute date in the sentence, else the article's
date line, else "উল্লেখ নেই") and the status (tense markers).
Nothing is invented: unstated fields are "উল্লেখ নেই" / "".
"কেন গুরুত্বপূর্ণ" is one generic per-topic background line, prefixed
"[পটভূমি]" — it states no fact that is not in the article.

Shared normalisation (also used by Step 5 so the two agree):
norm_bangla() — Unicode NFC, Bangla digits -> English digits,
zero-width chars removed, whitespace collapsed.
"""
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from rules_loader import load_rules
except Exception:  # rules file missing/unreadable: degrade, don't crash
    load_rules = None

# ---------------------------------------------------------------------------
# Shared normalisation (Step 5 imports this exact function)
# ---------------------------------------------------------------------------
_BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_EN_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def norm_bangla(text):
    """NFC, Bangla digits -> English digits, zero-width removed."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = text.translate(_BN_TO_EN)
    text = _ZERO_WIDTH.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def to_bangla_digits(text):
    """Western digits -> Bengali digits (Step 6 display)."""
    return str(text).translate(_EN_TO_BN)


# ---------------------------------------------------------------------------
# Numbers, units, dates
# ---------------------------------------------------------------------------
# Western branch allows 2- or 3-digit comma groups: Bangladeshi news
# prints figures in Indian grouping ("Tk22,06,462 crore", "Tk9,59,311
# crore") as well as Western grouping ("1,234,567"). Step 5 strips
# commas before checking, so the two must tokenise the same run —
# with {3} only, "22,06,462" matched as "22" and left ",06,462" in the
# fact text, which Step 5 rightly rejected (found 2026-11-15).
NUM_RE = re.compile(r"[০-৯]+(?:[,.][০-৯]+)*|[0-9]+(?:,[0-9]{2,3})*(?:\.[0-9]+)?")
YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")

UNITS_AFTER = [
    # longest first; checked as the word right after the number
    "কোটি", "লাখ", "হাজার", "টাকা", "মার্কিন ডলার", "ডলার",
    "million", "billion", "trillion", "crore", "lakh", "taka",
    "dollars", "dollar", "percent", "per cent", "megawatt", "MW", "GW",
    "tonnes", "tonne", "tons", "ton", "kilometres", "km", "bpd",
]
UNIT_BEFORE = {"$": "USD", "£": "GBP", "€": "EUR", "৳": "টাকা"}

EN_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7,
    "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12,
    "dec": 12,
}
BN_MONTHS = {
    "জানুয়ারি": 1, "ফেব্রুয়ারি": 2, "মার্চ": 3, "এপ্রিল": 4, "মে": 5,
    "জুন": 6, "জুলাই": 7, "আগস্ট": 8, "সেপ্টেম্বর": 9, "অক্টোবর": 10,
    "নভেম্বর": 11, "ডিসেম্বর": 12,
}
_MONTH_ALT = "|".join(sorted(EN_MONTHS, key=len, reverse=True))
_BN_MONTH_ALT = "|".join(BN_MONTHS)

# Absolute dates only: a month name + day + year, or ISO. A bare month
# + day with no year is completed with the article's year.
_DATE_RES = [
    re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})\s+(" + _MONTH_ALT + r")\.?,?\s+(\d{4})\b", re.I),
    re.compile(r"\b(" + _MONTH_ALT + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I),
    re.compile(r"\b(\d{1,2})\s+(" + _MONTH_ALT + r")\.?\b", re.I),
    re.compile(r"\b(" + _MONTH_ALT + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b", re.I),
    re.compile(r"([০-৯0-9]{1,2})\s+(" + _BN_MONTH_ALT + r")\s+([০-৯0-9]{4})"),
    re.compile(r"([০-৯0-9]{1,2})\s+(" + _BN_MONTH_ALT + r")"),
]


def _parse_date_match(m, article_year):
    """Return (iso_date, matched_text) or None."""
    g = [x for x in m.groups() if x is not None]
    txt = m.group(0)
    try:
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", txt.strip()):
            y, mo, d = (int(x) for x in txt.strip().split("-"))
            return datetime(y, mo, d).date().isoformat(), txt
        nums = [x for x in g if re.fullmatch(r"[০-৯0-9]+", x or "")]
        months = [x for x in g if x and (x.lower() in EN_MONTHS or x in BN_MONTHS)]
        if not months:
            return None
        mon = months[0]
        mo = EN_MONTHS.get(mon.lower(), BN_MONTHS.get(mon))
        day = int(norm_bangla(nums[0])) if nums else None
        year = int(norm_bangla(nums[1])) if len(nums) > 1 else article_year
        if day is None or year is None:
            return None
        return datetime(year, mo, day).date().isoformat(), txt
    except (ValueError, IndexError):
        return None


def find_absolute_date(sentence, article_year=None):
    """First absolute date in a sentence -> (iso, matched_text) or None."""
    found = find_absolute_date_span(sentence, article_year)
    return (found[0], found[1]) if found else None


def find_absolute_date_span(sentence, article_year=None):
    """First absolute date -> (iso, matched_text, start, end) or None."""
    for rx in _DATE_RES:
        m = rx.search(sentence)
        if m:
            parsed = _parse_date_match(m, article_year)
            if parsed:
                return parsed[0], parsed[1], m.start(), m.end()
    return None


def parse_article_date(raw):
    """ISO date-time string -> (iso_date, year) or (None, None)."""
    if not raw:
        return None, None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.date().isoformat(), dt.year
    except ValueError:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(raw))
        if m:
            return m.group(0), int(m.group(1))
    return None, None


# ---------------------------------------------------------------------------
# Sentences (span-based: quotes stay verbatim slices of the original text)
# ---------------------------------------------------------------------------
_ABBR = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "st.", "no.", "vs.", "e.g.",
    "i.e.", "u.s.", "u.k.", "ltd.", "inc.", "corp.", "sen.", "rep.",
    "gov.", "approx.", "fig.", "etc.", "dept.",
}


def split_sentences(text):
    """Return sentences as verbatim (stripped) slices of ``text``.

    Newlines are sentence boundaries too: the body cleaner keeps one
    paragraph per line, and a related-headline line (no terminal
    punctuation) must not glue onto the next article sentence.
    """
    text = str(text or "")
    if not text.strip():
        return []
    out = []
    for line in text.split("\n"):
        out.extend(_split_line(line))
    return out


def _split_line(text):
    """Punctuation-split one line (no newlines inside)."""
    text = str(text or "")
    if not text.strip():
        return []
    # Candidate boundaries: sentence-ending punctuation followed by
    # whitespace (or end of text).
    spans = []
    start = 0
    for m in re.finditer(r"[.!?।](?:\s+|$)", text):
        end = m.end()
        piece = text[start:end].strip()
        # Don't split after a known abbreviation ("Dr. Yunus ...").
        tail = piece.rsplit(None, 1)[-1].lower() if piece else ""
        if tail in _ABBR and end < len(text):
            continue
        if piece:
            spans.append(piece)
        start = end
    tail = text[start:].strip()
    if tail:
        spans.append(tail)
    return spans


# ---------------------------------------------------------------------------
# Topic terms (from RULES.md at runtime, via rules_loader)
# ---------------------------------------------------------------------------
def _topic_terms():
    """{topic_id: (strong_terms, support_terms)} — all lowercased."""
    if load_rules is None:
        return {}
    try:
        rules = load_rules()
    except Exception:
        return {}
    out = {}
    for tid, t in rules.get("topics", {}).items():
        out[tid] = (set(t.get("strong", [])), set(t.get("support", [])))
    return out


def detect_topic(text, terms=None):
    """Topic with the most strong hits (then support, then file order)."""
    terms = terms if terms is not None else _topic_terms()
    if not terms:
        return ""
    hay = norm_bangla(text).lower()
    best, best_key = "", None
    for tid, (strong, support) in terms.items():
        s = sum(1 for t in strong if t and t in hay)
        p = sum(1 for t in support if t and t in hay)
        key = (s, p)
        if best_key is None or key > best_key:
            best, best_key = tid, key
    return best if best_key and (best_key[0] or best_key[1]) else ""


# ---------------------------------------------------------------------------
# Sentence scoring
# ---------------------------------------------------------------------------
_CAP_WORD = re.compile(r"\b[A-Z][a-z]{2,}\b")
_MONTH_WORDS = set(EN_MONTHS) | {"monday", "tuesday", "wednesday",
                                 "thursday", "friday", "saturday", "sunday"}
_BN_NAME_MARKERS = ("ড.", "মো.", "মি.", "প্রধানমন্ত্রী", "মন্ত্রী", "সচিব",
                    "চেয়ারম্যান", "গভর্নর", "অধ্যাপক", "রাষ্ট্রপতি",
                    "উপদেষ্টা", "বাংলাদেশ ব্যাংক", "বিশ্বব্যাংক")


def _has_name(sentence):
    """Capitalised English name, or a Bangla name/title marker."""
    words = sentence.split()
    for i, w in enumerate(words):
        clean = w.strip(".,;:()\"'।")
        if i > 0 and _CAP_WORD.fullmatch(clean) and clean.lower() not in _MONTH_WORDS:
            return True
    return any(m in sentence for m in _BN_NAME_MARKERS)


def _sentence_score(sentence, terms, article_year):
    """(score, has_number, has_date, has_name, has_topic) for a sentence."""
    norm = norm_bangla(sentence)
    low = norm.lower()
    numbers = _number_matches(sentence)
    has_number = bool(numbers)
    has_date = find_absolute_date(sentence, article_year) is not None
    has_name = _has_name(sentence)
    strong_hit = support_hit = False
    for _tid, (strong, support) in terms.items():
        if any(t and t in low for t in strong):
            strong_hit = True
        if any(t and t in low for t in support):
            support_hit = True
    has_topic = strong_hit or support_hit
    score = 0.0
    if has_number:
        score += 2
    if has_date:
        score += 2
    if has_name:
        score += 1
    if strong_hit:
        score += 2
    elif support_hit:
        score += 1
    n_words = len(sentence.split())
    if n_words > 45:
        score -= 1
    if n_words < 4:
        score -= 1
    return score, has_number, has_date, has_name, has_topic


# ---------------------------------------------------------------------------
# Value / unit / status parsing
# ---------------------------------------------------------------------------
def _number_matches(sentence):
    """Number matches, excluding codes glued to letters ("FY27", "BPM6",
    "Q1") — a number that directly follows a letter is not a value,
    except after a currency prefix ("Tk2,244"). Time-of-day furniture
    ("07:50 pm": neither the hour nor the minute) and read-time
    furniture ("2 min read") are not values either."""
    out = []
    for m in NUM_RE.finditer(sentence):
        if m.start() > 0 and sentence[m.start() - 1].isalpha():
            if sentence[max(0, m.start() - 2):m.start()].lower() != "tk":
                continue
        after = sentence[m.end():m.end() + 4]
        if after.startswith(":") and re.match(r":\d{2}", after):
            continue  # hour part of HH:MM
        if (m.start() >= 2 and sentence[m.start() - 1] == ":"
                and sentence[m.start() - 2].isdigit()):
            continue  # minute part of HH:MM
        if re.match(r"\s*min\s+read\b", sentence[m.end():], flags=re.I):
            continue  # "2 min read"
        out.append(m)
    return out


def _first_value_number(sentence, exclude_span=None):
    """First number as printed, preferring a non-year number.
    Numbers inside ``exclude_span`` (the sentence's date phrase) are
    skipped — the day of "14 November" is the date, not a value."""
    nums = _number_matches(sentence)
    if not nums:
        return ""
    for m in nums:
        if exclude_span and exclude_span[0] <= m.start() < exclude_span[1]:
            continue
        if not YEAR_RE.fullmatch(norm_bangla(m.group(0))):
            return m.group(0)
    for m in nums:
        if exclude_span and exclude_span[0] <= m.start() < exclude_span[1]:
            continue
        if not YEAR_RE.fullmatch(norm_bangla(m.group(0))):
            return m.group(0)
    # Only a year (or years) left: a year alone is not a fact value —
    # the fact's date field already carries it.
    return ""


def _unit_for(sentence, value):
    """Unit adjacent to the value number (after it, else a prefix sign)."""
    if not value:
        return ""
    idx = sentence.find(value)
    if idx < 0:
        return ""
    after = sentence[idx + len(value):idx + len(value) + 24]
    m = re.match(r"\s*%|\s*(?:per\s+cent)", after, re.I)
    if m:
        return "%" if "%" in m.group(0) else "percent"
    m = re.match(r"\s*([A-Za-z\u0980-\u09FF]+)", after)
    if m:
        word = m.group(1)
        low = word.lower()
        for u in UNITS_AFTER:
            if low == u.lower() or low.startswith(u.lower()):
                return u
        # Two-word unit ("per cent", "US dollar") — check the pair.
        rest = after[m.end():m.end() + 12]
        m2 = re.match(r"\s*([A-Za-z]+)", rest)
        if m2:
            pair = word + " " + m2.group(1)
            for u in UNITS_AFTER:
                if pair.lower() == u.lower():
                    return u
    before = sentence[max(0, idx - 3):idx]
    for sym, unit in UNIT_BEFORE.items():
        if before.rstrip().endswith(sym):
            return unit
    return ""


_SCHEDULED = ("scheduled", "to be held", "will be held", "will take place",
              "slated", "due on", "set to", "will begin", "will start",
              "planned", "হবে", "করা হবে", "অনুষ্ঠিত হবে")
_PROPOSED = ("proposed", "proposal", "proposes", "considering",
             "plans to", "plan to", "প্রস্তাব", "প্রস্তাবিত")
_FORECAST = ("forecast", "projected", "projection", "predicted", "might",
             "পূর্বাভাস", "অনুমান করা", "প্রাক্কলন")


def _status_for(sentence):
    low = norm_bangla(sentence).lower()
    if any(w in low for w in _FORECAST):
        return "forecast"
    if any(w in low for w in _PROPOSED):
        return "proposed"
    if any(w in low for w in _SCHEDULED):
        return "scheduled"
    return "happened"


def _make_what(sentence, value, unit, date_phrase):
    """Short 'what' from the sentence: number/unit/date stripped, trimmed."""
    s = sentence
    # Time-of-day and read-time fragments ("07:50 pm", "2 min read")
    # are page furniture, not the fact: strip them before anything else.
    s = re.sub(r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b", " ", s, flags=re.I)
    s = re.sub(r"\b\d+\s*min\s+read\b", " ", s, flags=re.I)
    if date_phrase:
        s = s.replace(date_phrase, " ", 1)
    if value:
        # "15-year" -> "year": drop a hyphen glued to the removed number.
        s = s.replace(value + "-", " ", 1).replace("-" + value, " ", 1)
        s = s.replace(value, " ", 1)
        # A currency prefix left behind ("Tk50,000" -> "Tk").
        s = re.sub(r"\bTk\b", " ", s, count=1)
    if unit:
        s = re.sub(r"\b" + re.escape(unit) + r"\b", " ", s, count=1,
                   flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ,;:—-.।")
    s = re.sub(r"^(the|a|an)\s+", "", s, flags=re.I)
    # A currency sign left behind when its number was removed ("$ 442" -> "$").
    s = re.sub(r"(?<![\w\u0980-\u09FF])[$£€৳](?![\w\u0980-\u09FF])", " ", s)
    # A "%" unit leaves its sign behind; "of ," is left by a removed value.
    if unit == "%":
        s = s.replace("%", " ", 1)
    s = re.sub(r"\bof\s*,", "", s)
    s = re.sub(r"\s+,", ",", s)  # "Summit 2026," minus 2026 -> "Summit ,"
    s = re.sub(r",\s*,", ",", s)
    # Never leak a relative date into a fact line ("today" in the
    # sentence is fine in the verbatim quote, not in "what").
    s = re.sub(r"\b(today|yesterday|tomorrow)\b", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ,;:—-.।")
    words = s.split()
    if len(words) > 14:
        s = " ".join(words[:14]).strip(" ,;:")
    if len(s) < 8:  # stripping gutted it: fall back to the raw lead
        s = " ".join(sentence.split()[:12]).strip(" ,;:")
    return s


# ---------------------------------------------------------------------------
# English fact list (Proposal 8, syllabus): `facts_en` for every story
# ---------------------------------------------------------------------------
_UNIT_EN = {
    "টাকা": "taka", "কোটি": "crore", "লাখ": "lakh", "হাজার": "thousand",
    "শতাংশ": "percent", "ডলার": "dollar", "মার্কিন ডলার": "USD",
    "বিলিয়ন": "billion", "মিলিয়ন": "million",
}


def _bangla_ratio(text):
    """Fraction of Bangla-script characters among letters in text."""
    if not text:
        return 0.0
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    bn = sum(1 for ch in letters if "\u0980" <= ch <= "\u09ff")
    return bn / len(letters)


def _translate_what_en(what, glossary):
    """Glossary-based English rendering of a Bangla fact "what".

    Longest Bangla term first; plain substring replacement. Numbers,
    units and Latin-script names pass through untouched. This is a
    translator's rendering, not fluent translation — the numbers and
    names (the exam-relevant parts) stay exact, and the verbatim
    quote is kept alongside it.
    """
    out = str(what or "")
    for bn, en in sorted(glossary.items(), key=lambda kv: -len(kv[0])):
        if bn and bn in out:
            out = out.replace(bn, en)
    return out


def render_facts_en(facts, body_text):
    """English fact list for a story (Proposal 8, syllabus).

    English-language article: the same facts (already English).
    Bangla-language article: the translator's rendering — same value
    (digits normalised to English), unit (glossary-mapped), date and
    status, same verbatim quote, with "what" rendered in English via
    the glossary. "উল্লেখ নেই" dates become "not stated". Step 5
    rules apply to the result: every number and name in it must
    appear in the article (digits are normalised before comparing).
    Returns a list of fact dicts in Step 4 shape.
    """
    glossary = {}
    if load_rules is not None:
        try:
            glossary = load_rules().get("glossary", {}) or {}
        except Exception:
            glossary = {}
    is_bn = _bangla_ratio(body_text or "") > 0.3
    out = []
    for f in (facts or []):
        if not isinstance(f, dict):
            continue
        en = dict(f)
        if is_bn:
            en["what"] = _translate_what_en(f.get("what") or "", glossary)
            en["value"] = norm_bangla(str(f.get("value") or ""))
            unit = f.get("unit") or ""
            en["unit"] = _UNIT_EN.get(unit, _UNIT_EN.get(unit.lower(), unit))
        if en.get("date") == "উল্লেখ নেই":
            en["date"] = "not stated"
        out.append(en)
    return out


# ---------------------------------------------------------------------------
# "কেন গুরুত্বপূর্ণ" — generic per-topic background, no article facts
# ---------------------------------------------------------------------------
WHY_TEMPLATES = {
    "BD-GOV": "[পটভূমি] আইন, অধ্যাদেশ বা সরকারি সিদ্ধান্ত পরীক্ষায় রাষ্ট্র, আইন ও প্রশাসন অংশে জিজ্ঞাসা করা হয়।",
    "BD-ECO": "[পটভূমি] অর্থনীতির এই তথ্য বাজেট, প্রবৃদ্ধি ও বাণিজ্য সংক্রান্ত প্রশ্নের ভিত্তি।",
    "BD-BANK": "[পটভূমি] বাংলাদেশ ব্যাংকের নীতি ও ব্যাংক খাতের সিদ্ধান্ত ব্যাংক নিয়োগ পরীক্ষায় গুরুত্বপূর্ণ।",
    "BD-NATL": "[পটভূমি] জাতীয় পুরস্কার ও প্রতিষ্ঠান সংক্রান্ত তথ্য সাধারণ জ্ঞান অংশে আসে।",
    "INT-ORG": "[পটভূমি] আন্তর্জাতিক সংস্থার সিদ্ধান্ত বাংলাদেশের অর্থনীতি ও কূটনীতির সঙ্গে যুক্ত বলে পরীক্ষায় আসে।",
    "INT-REL": "[পটভূমি] প্রতিবেশী দেশ ও বৈশ্বিক সম্পর্কের খবর আন্তর্জাতিক বিষয়াবলি অংশের জন্য গুরুত্বপূর্ণ।",
    "ENV": "[পটভূমি] জলবায়ু ও দুর্যোগ সংক্রান্ত তথ্য পরিবেশ ও ভূগোল অংশে জিজ্ঞাসা করা হয়।",
    "SCI": "[পটভূমি] বিজ্ঞান ও প্রযুক্তির অগ্রগতি সাধারণ বিজ্ঞান অংশের প্রশ্নের উৎস।",
    "SPORT": "[পটভূমি] বড় টুর্নামেন্ট ও রেকর্ড খেলাধুলা বিষয়ক সাধারণ জ্ঞানে আসে।",
    "PEOPLE": "[পটভূমি] পুরস্কার, নিয়োগ ও বিশিষ্ট ব্যক্তির তথ্য পরীক্ষার সাধারণ জ্ঞান অংশে থাকে।",
}
WHY_DEFAULT = "[পটভূমি] এই খবরটি পরীক্ষার সাধারণ জ্ঞান ও সাম্প্রতিক ঘটনা অংশের জন্য প্রাসঙ্গিক।"


# Site chrome that leaks into a fetched body (nav/footer/related-news
# text): never a fact. A "|" is the giveaway for nav rails; "@" for
# footer contact blocks.
CHROME_MARKERS = ("EMAIL US", "FOLLOW US", "All rights reserved",
                  "Copyright", "MOST VIEWED", "Related News",
                  "TBS NEWS AT", "TBS World", "Privacy Policy",
                  "Comment Policy", "About Us", "Contact us",
                  "Technical Partner", "Last modified", "Last updated",
                  "Illustration:", "File photo", "Keep updated",
                  "Google news channel", "Staff Correspondent",
                  "Subscribe", "newsletter", "sponsored content")


def _core_sentence(sentence):
    """The sentence minus a trailing byline fragment ("Published:
    Nov 14, 2026", "Updated: ..."). The fragment's day-number would
    otherwise be picked as a fact value ("Published: 13" -> 13). The
    verbatim quote keeps the original; only scoring/value/date/what
    use the core."""
    core = re.split(r"Published:|Updated:", sentence, maxsplit=1)[0].strip()
    return core


def _is_chrome(sentence):
    if sentence.startswith("Photo:") or "Representational Photo" in sentence:
        return True
    if sentence.startswith(("Published:", "Published on", "Updated:",
                            "Update:")):
        return True  # byline/date line, not article text
    if "min read" in sentence:
        return True  # read-time furniture glued to a teaser/byline
    if re.match(r"\s*\d+\s*char\.?\)", sentence):
        return True  # character-count fragment ("8000 char.)")
    return (" | " in sentence or "@" in sentence
            or any(m in sentence for m in CHROME_MARKERS))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def extract_facts(article, max_facts=5):
    """Extract up to ``max_facts`` facts from an article dict.

    ``article``: {"body_text": ..., "published": "2026-11-14T...",
    "topic_primary": "..." (optional), "title": ... (optional)}.
    """
    body = (article or {}).get("body_text") or ""
    published = (article or {}).get("published") or (article or {}).get("date") or ""
    article_date, article_year = parse_article_date(published)
    topic = (article or {}).get("topic_primary") or ""
    terms = _topic_terms()
    if not topic:
        topic = detect_topic((article or {}).get("title", "") + " " + body[:2000], terms)

    sentences = split_sentences(body)
    scored = []
    for i, sent in enumerate(sentences):
        if _is_chrome(sent):
            continue
        core = _core_sentence(sent)
        if not core:
            continue
        score, has_num, has_date, has_name, has_topic = _sentence_score(
            core, terms, article_year)
        # Fact-density gate: needs a number/date/name AND a topic term.
        if not has_topic or not (has_num or has_date or has_name):
            continue
        if score <= 0:
            continue
        scored.append((-score, i, sent, core))
    scored.sort()

    facts = []
    seen = set()
    for _neg, _i, sent, core in scored:
        if len(facts) >= max_facts:
            break
        key = norm_bangla(sent)
        if key in seen:
            continue
        # Distinctness: skip near-duplicates of an already kept sentence.
        if any(_overlap(key, norm_bangla(f["quote"])) > 0.8 for f in facts):
            continue
        seen.add(key)
        found = find_absolute_date_span(core, article_year)
        if found:
            date_iso, date_phrase, d_start, d_end = found
        else:
            date_iso, date_phrase, d_start, d_end = (
                article_date or "উল্লেখ নেই"), "", None, None
        span = (d_start, d_end) if d_start is not None else None
        value = _first_value_number(core, exclude_span=span)
        unit = _unit_for(core, value)
        facts.append({
            "what": _make_what(core, value, unit, date_phrase),
            "value": value,
            "unit": unit,
            "date": date_iso,
            "status": _status_for(core),
            "quote": sent,
        })

    return {
        "facts": facts,
        "why_important": WHY_TEMPLATES.get(topic, WHY_DEFAULT),
    }


def _overlap(a, b):
    """Word-overlap ratio (0..1) between two normalised sentences."""
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


if __name__ == "__main__":
    demo = {
        "id": "demo",
        "title": "IMF board approves $442 million tranche for Bangladesh",
        "published": "2026-11-14T05:30:00+00:00",
        "topic_primary": "INT-ORG",
        "body_text": (
            "The International Monetary Fund board has approved a "
            "$442 million tranche for Bangladesh under its loan programme. "
            "The approval came on 13 November 2026 after a review of the "
            "country's economic reforms. Bangladesh's foreign exchange "
            "reserves stood at $26 billion in October 2026. The government "
            "expects the next review to be completed by June 2027."
        ),
    }
    import json
    print(json.dumps(extract_facts(demo), ensure_ascii=False, indent=2))
