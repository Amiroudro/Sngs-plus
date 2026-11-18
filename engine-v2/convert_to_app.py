#!/usr/bin/env python3
"""v2 -> app converter (Sarangsho Plus engine v2).

Reads one v2 dry-run directory (page + questions + vocab + articles,
and items-<date>.json when run_v2.py persisted it) and writes
app-format edition files to a STAGING directory
(runs/<date>/app-format/ -- NEVER editions/):

  data-<date>.json   English canonical edition (v1 app contract)
  bn-<date>.json     Bengali overlay (v1 app contract)
  index-<date>.json  full index.json with the new entry appended
                     (built by copying the live editions/index.json)
  conversion-report-<date>.json / .md

Stdlib only. Never imports v1 (engine/, tools/) -- the v1 coverage
formula and the check_data.py #4 number-preservation rule are copied
here, not imported. Nothing is published, synced or switched live.

Honesty rules (see the conversion report for the full mapping table):
  * Every string traces to a v2 verified fact, a v2 question, or the
    vocab bank. EN prose is rendered from facts_en QUOTES (verbatim
    article sentences), never from the fragmentary "what" fields.
  * No fact, number, name or quote is invented. Where the v1 contract
    wants something v2 does not have (key_people, Bangla structured
    facts for 15 Nov), the field is left empty and the report says so.
  * The editorial slot carries headline/source/url/summary only, so
    its structured fields are mechanically derived from that summary
    (labelled as such in the report).

Usage:
  python3 convert_to_app.py --date 2026-11-15
  python3 convert_to_app.py --date 2026-11-15 --run-dir runs/2026-11-15 \
      --staging runs/2026-11-15/app-format
  python3 convert_to_app.py --date 2026-11-17 --learning-modules \
      --run-dir <scratch-run> --staging <scratch-staging>
      # opt-in ONLY: attach the 11-section learning_module (v2) to
      # every story (learning_module.py) and set renovation_format
      # "learning-module-v2". Default OFF -- the live daily path
      # (run_v2_daily.py) never passes the flag, so Edition 12 (18 Nov
      # 08:00) and every unproven run convert exactly as before. The
      # new format is wired into the live path only after a dry-run
      # proves gate 15/15 with it (target: Edition 13 at the earliest).
"""
import argparse
import copy
import json
import random
import re
import sys
import unicodedata
from datetime import date as _date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    import learning_module
except ImportError:  # imported from another cwd: engine-v2 dir is HERE
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import learning_module

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EDITIONS_DIR = ROOT / "editions"
MAX_STORIES = 15          # v1 contract ceiling (publish.py checklist)
N_MCQS = 25
N_VOCAB_MCQ = 10
N_PHRASE_MCQ = 2
N_CA_MCQ = 13

# v2 topic -> v1 fixed category (validate_editions.py FIXED_CATEGORIES).
# v1 has no Environment/Health or Sports bucket: ENV maps to Bangladesh
# (v2 ENV items in this corpus are Bangladesh stories); SPORT/PEOPLE map
# to Bangladesh when the headline names Bangladesh, else World.
CATEGORY_MAP = {
    "BD-GOV": "Politics", "BD-NATL": "Bangladesh",
    "BD-ECO": "Economy & Banking", "BD-BANK": "Economy & Banking",
    "INT-ORG": "World", "INT-REL": "World",
    "ENV": "Bangladesh", "SCI": "Technology",
}
EXAM_RELEVANCE = {
    "BD-GOV": "Politics, law and administration -- core BCS/Bank Bangladesh-affairs topic.",
    "BD-NATL": "Bangladesh affairs -- core BCS/Bank topic.",
    "BD-ECO": "Economy and banking -- core BCS/Bank economy topic.",
    "BD-BANK": "Banking and finance -- core BCS/Bank economy topic.",
    "INT-ORG": "International organisations -- core BCS/Bank international-affairs topic.",
    "INT-REL": "International relations -- core BCS/Bank international-affairs topic.",
    "ENV": "Environment and health -- BCS/Bank science and environment topic.",
    "SCI": "Science and technology -- core BCS/Bank science topic.",
    "SPORT": "Sports and current events -- BCS/Bank current-affairs topic.",
    "PEOPLE": "People and awards -- BCS/Bank current-affairs topic.",
    "EDITORIAL": "Editorial and opinion -- Focus Writing and BCS/Bank analysis material.",
}
TOPIC_LABEL = {
    "BD-GOV": "politics, law and administration",
    "BD-NATL": "Bangladesh affairs",
    "BD-ECO": "the economy and banking",
    "BD-BANK": "banking and finance",
    "INT-ORG": "international organisations",
    "INT-REL": "international relations",
    "ENV": "the environment and public health",
    "SCI": "science and technology",
    "SPORT": "sport and current events",
    "PEOPLE": "people and awards",
}
STOPWORDS = set("""a an the of in on at to for and or by with from as is are was were
be been it its this that these those after before over under into about has
have had will would can could should may might not no nor but if then than
so such only own same too very just also more most other some any each when
while who whom which what how why always never""".split())
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
LATIN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
BN_MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
             "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
_MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|"
    r"Nov|Dec)\b", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_RE = re.compile(
    r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(\d{4})\b", re.IGNORECASE)
_BN_SUFFIXES = ("এর", "গুলোর", "গুলো", "দের", "সহ", "থেকে", "জন্য", "মধ্যে",
                "দিয়ে", "পর", "আগে", "কে", "তে", "য়", "টি", "টা", "এ", "র")
_HYPHEN_SUFFIX_RE = re.compile(
    "[A-Za-z][A-Za-z0-9./]*[-–](?:" + "|".join(_BN_SUFFIXES) + ")"
    r"(?![\u0980-\u09FF])")
_ZERO_WIDTH = ("\u200b", "\u200c", "\u200d", "\ufeff")
_FORBIDDEN_OPTIONS = ("সবগুলো", "কোনোটিই নয়", "কোনোটিই না", "সবগুলোই")


def log(msg):
    print(f"[convert] {msg}")


def clean(text):
    """Strip zero-width chars, collapse whitespace. No content change."""
    t = unicodedata.normalize("NFC", str(text or ""))
    for ch in _ZERO_WIDTH:
        t = t.replace(ch, "")
    return re.sub(r"\s+", " ", t).strip()


def norm(text):
    """Normalised text for comparisons: NFC, Bangla->Latin digits."""
    return re.sub(r"\s+", " ", clean(text).translate(LATIN_DIGITS)).strip().lower()


def bn_sanitise(text):
    """Make a string safe for bn-*.json under tools/validate_bangla.dart.

    Mirrors lib/utils/bangla_format.dart detectors exactly: no Latin
    digits, no English months, no 'Tk', no Latin-word+hyphen+Bangla
    suffix, no $...Latin-digit figure. Conversions only -- nothing is
    added or removed except a hyphen turned into a space.
    """
    t = clean(text)
    # ISO dates -> Bangla date ("2026-11-15" -> "১৫ নভেম্বর ২০২৬").
    def _iso(m):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            _date(y, mo, d)
        except ValueError:
            return m.group(0)
        return f"{str(d).translate(BN_DIGITS)} {BN_MONTHS[mo - 1]} {str(y).translate(BN_DIGITS)}"
    t = _ISO_DATE_RE.sub(_iso, t)
    # "15 November 2026" -> Bangla date.
    def _dmy(m):
        d, mon, y = int(m.group(1)), m.group(2), m.group(3)
        idx = [e.lower() for e in EN_MONTHS].index(mon.lower())
        return f"{str(d).translate(BN_DIGITS)} {BN_MONTHS[idx]} {y.translate(BN_DIGITS)}"
    t = _DMY_RE.sub(_dmy, t)
    # Remaining English month names -> Bangla months.
    def _mon(m):
        w = m.group(0)
        low = w.lower()
        for i, name in enumerate(EN_MONTHS):
            if low == name.lower() or low in (
                    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
                    "sept", "oct", "nov", "dec"):
                if low in ("jan", "feb", "mar", "apr", "jun", "jul", "aug",
                           "sep", "sept", "oct", "nov", "dec"):
                    abbr = ["jan", "feb", "mar", "apr", "may", "jun", "jul",
                            "aug", "sep", "oct", "nov", "dec"]
                    if low in abbr:
                        return BN_MONTHS[abbr.index(low)]
                return BN_MONTHS[i]
        return w
    t = _MONTH_RE.sub(_mon, t)
    # Latin digits -> Bangla digits.
    t = t.translate(BN_DIGITS)
    # 'Tk' (not followed by a Latin letter) -> 'টাকা'.
    t = re.sub(r"Tk(?![A-Za-z])", "টাকা", t)
    # Latin word + hyphen + Bangla suffix -> space instead of hyphen.
    t = _HYPHEN_SUFFIX_RE.sub(lambda m: m.group(0).replace("-", " ", 1).replace("–", " ", 1), t)
    return t


def bn_violations(text):
    """Python re-implementation of findBanglaViolations() (Dart) for the
    converter's own self-check. Returns a list of (kind, match)."""
    out = []
    # NOTE: Dart's \d matches ASCII 0-9 only (Dart RegExp is not
    # Unicode-aware for \d), so the replica must use [0-9], not \d --
    # Python's \d would also match Bangla digits ০-৯.
    for m in re.finditer(r"[0-9][0-9,]*(?:\.[0-9]+)?", text):
        out.append(("latinDigits", m.group(0)))
    for m in _MONTH_RE.finditer(text):
        out.append(("englishMonth", m.group(0)))
    for m in re.finditer(r"\b(?:May|March|Mar)\b", text):
        out.append(("englishMonth", m.group(0)))
    for m in re.finditer(r"Tk(?![A-Za-z])", text):
        out.append(("tk", m.group(0)))
    for m in _HYPHEN_SUFFIX_RE.finditer(text):
        out.append(("hyphenSuffix", m.group(0)))
    for m in re.finditer(
            r"(?:US)?\$\s*[0-9][0-9,]*(?:\.[0-9]+)?(?:\s*[-–]\s*[0-9][0-9,]*(?:\.[0-9]+)?)?"
            r"\s*(?:মিলিয়ন|বিলিয়ন|কোটি|লাখ)", text):
        out.append(("hyphenSuffix", m.group(0)))
    return out


def parse_pubdate(raw):
    """Article published date -> datetime or None. Copied logic (v2 must
    not import v1): RFC-2822 via email.utils, ISO via fromisoformat."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def pub_date_iso(raw):
    dt = parse_pubdate(raw)
    return dt.strftime("%Y-%m-%d") if dt is not None else ""


def coverage_label(day):
    """v1 coverage formula, copied (v2 must not import v1 common.py):
    previous day 07:47 Dhaka -> date 07:47 Dhaka."""
    prev = day - timedelta(days=1)
    return (f"{prev.strftime('%d %b %Y')}, 7:47 AM to "
            f"{day.strftime('%Y-%m-%d')}, 7:47 AM (Asia/Dhaka)")


def words_of(text, limit=None):
    return (clean(text).split()[:limit] if limit else clean(text).split())


def truncate_words(text, limit):
    w = words_of(text)
    if len(w) <= limit:
        return clean(text)
    return " ".join(w[:limit]) + "…"


def first_number(text):
    m = re.search(r"\d[\d,]*(?:\.\d+)?", clean(text))
    return m.group(0).rstrip(",.") if m else ""


def content_words(text):
    toks = re.findall(r"[a-z0-9'\u0980-\u09FF]+", clean(text).lower())
    out = []
    for t in toks:
        t = t.strip("'")
        if len(t) >= 4 and t not in STOPWORDS:
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def category_for(item):
    topic = item.get("topic_primary", "")
    if topic in CATEGORY_MAP:
        return CATEGORY_MAP[topic]
    if topic in ("SPORT", "PEOPLE"):
        return ("Bangladesh" if "bangladesh" in
                clean(item.get("headline", "")).lower() else "World")
    return "Bangladesh"


def story_dates(item, article, day_iso):
    d = pub_date_iso(article.get("published", "")) or item.get("date", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d or ""):
        d = day_iso
    return d, d


def quotes_of(item):
    """facts_en quotes: verbatim article sentences, cleaned, HTML-free."""
    out = []
    for f in item.get("facts_en", []) or []:
        q = clean(f.get("quote", ""))
        if q and "<" not in q and ">" not in q:
            out.append(q)
    return out


def bn_summary_numbers_ok(en_summary, bn_summary):
    """Replica of app/tools/check_data.py section 4: every number token
    in the EN summary must appear in the BN summary (Bangla digits
    normalised back), except tokens inside Tk/US$/$ amounts and FY
    tokens. Returns a list of missing tokens."""
    to_latin = lambda s: s.translate(LATIN_DIGITS).replace("–", "-").replace("—", "-")
    bn = to_latin(bn_summary)
    # The EN side must be normalised too: for Bangla-article stories
    # facts_en is untranslated Bangla, so its number tokens are Bangla
    # digits. Python's \d matches Unicode digits, so without this the
    # tokens come out Bangla ("৫৫") while bn is Latin ("55") and every
    # such token is falsely reported missing (CA11, 2026-11-15).
    # to_latin is a 1:1 character translation, so span positions in
    # the money/FY checks below are unchanged.
    en = to_latin(en_summary)
    money = re.compile(
        r"(?:Tk|US\$|\$)\s*[\d.,]+(?:\s*[-–—]\s*[\d.,]+)?"
        r"\s*(?:bn|billion|m|million|কোটি|লাখ)?")
    spans = [(m.start(), m.end()) for m in money.finditer(en)]
    missing = []
    for m in re.finditer(r"\d[\d.,]*", en):
        tok = m.group(0).rstrip(".,")
        if not tok:
            continue
        if any(a <= m.start() < b for a, b in spans):
            continue
        if m.start() >= 2 and en[m.start() - 2:m.start()] == "FY":
            continue
        if tok not in bn:
            missing.append(tok)
    return missing


def build_story_fields(item, article, day_iso, items_by_id):
    """EN + BN story fields for one v2 page item. Returns
    (en_story, bn_story, notes)."""
    notes = []
    facts = item.get("facts_en", []) or []
    quotes = quotes_of(item)
    fact_lines = [bn_sanitise(ln) for ln in item.get("fact_lines", [])]
    bn_text = " ".join(fact_lines)
    headline = clean(item.get("headline", ""))
    topic = item.get("topic_primary", "")
    event_date, article_date = story_dates(item, article, day_iso)

    # --- EN summary: first 2 quotes whose numbers survive into the BN
    # summary (check_data.py #4); truncate to 90 words (publish gate).
    summary_quotes = []
    summary_idx = set()
    dropped_quotes = []
    for qi, q in enumerate(quotes):
        if len(summary_quotes) >= 2:
            break
        missing = bn_summary_numbers_ok(q, bn_text)
        if missing:
            dropped_quotes.append((q[:60], missing))
            continue
        summary_quotes.append(q)
        summary_idx.add(qi)
    if not summary_quotes and quotes:
        summary_quotes = [quotes[0]]
        summary_idx = {0}
        notes.append("summary uses quote 1 although its numbers are not "
                     "all in the BN summary (check_data #4 risk)")
    summary = truncate_words(" ".join(summary_quotes), 90)
    if dropped_quotes:
        notes.append(f"summary dropped {len(dropped_quotes)} quote(s) "
                     f"whose numbers are absent from the BN summary: "
                     f"{dropped_quotes}")

    # --- EN exam_facts: the quotes NOT used in the summary (new facts
    # beyond it). Falls back to the summary only when no other quote
    # exists at all.
    rest = [q for qi, q in enumerate(quotes) if qi not in summary_idx]
    exam_facts = " ".join(rest) if rest else ""
    if not exam_facts:
        exam_facts = summary
        notes.append("exam_facts repeats the summary: no further fact "
                     "quotes exist beyond the summary")
    detail = " ".join(quotes) if quotes else summary

    # --- key_facts (max 4) from the structured facts_en list.
    key_facts = []
    for f in facts[:4]:
        what = clean(f.get("what", ""))
        value = clean(f.get("value", ""))
        unit = clean(f.get("unit", ""))
        fdate = clean(f.get("date", ""))
        val = (value + " " + unit).strip()
        if not val:
            val = first_number(f.get("quote", ""))
        if not val and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fdate or ""):
            val = fdate
        label = truncate_words(what, 12) if what else "fact"
        key_facts.append({"label": label, "value": val,
                          "original": clean(f.get("quote", ""))})
    if not key_facts and quotes:
        key_facts = [{"label": "headline",
                      "value": first_number(quotes[0]) or event_date,
                      "original": quotes[0]}]
        notes.append("key_facts fell back to the headline quote: no "
                     "structured facts_en entries")

    # --- figures: value+unit per fact, else first number in the quote.
    figs = []
    for f in facts[:5]:
        value = clean(f.get("value", ""))
        unit = clean(f.get("unit", ""))
        fdate = clean(f.get("date", ""))
        if value:
            piece = (value + " " + unit).strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fdate or ""):
                piece += f" ({fdate})"
            figs.append(piece)
        else:
            num = first_number(f.get("quote", ""))
            if num:
                figs.append(num)
    seen_figs, figs_dd = set(), []
    for _f in figs:
        if _f not in seen_figs:
            seen_figs.add(_f)
            figs_dd.append(_f)
    figures = "; ".join(figs_dd[:5])
    if not figures:
        figures = f"Published {datetime.strptime(event_date, '%Y-%m-%d').strftime('%d %B %Y')}."
        notes.append("figures fell back to the publication date: no numbers "
                     "in any fact")

    # --- what_happened: one bullet per quote.
    what_happened = quotes if quotes else [summary]

    # --- exam_qa: filtered v2 Q&A (no HTML, no why-QA in EN).
    # Renovated-archive standard (GitHub "Validate renovated
    # editions", tools/validate_renovated_editions.py): exactly 2
    # short Q&A per story, EN and BN. The BN why-QA counts as one
    # of the two, so trim AFTER inserting it. Before this fix the
    # converter capped at 5 (EN) / 5+why (BN) and the editorial had
    # 0 -- the 15 Nov dry-run output would have failed the repo
    # validator with 31 errors while the 15-check gate passed it.
    qa_all = items_by_id.get("_qa", {}).get(item["id"], [])
    exam_qa_en, exam_qa_bn = [], []
    why_qa = None
    for q in qa_all:
        if q.get("id", "").endswith("-why") or \
                q.get("question", "").strip() == "এই খবরটি কেন গুরুত্বপূর্ণ?":
            why_qa = q
            continue
        qq, aa = clean(q.get("question", "")), clean(q.get("answer", ""))
        if not qq or not aa or "<" in qq or ">" in qq or "<" in aa or ">" in aa:
            continue
        if len(exam_qa_en) < 2:
            exam_qa_en.append({"q": qq, "a": aa})
        if len(exam_qa_bn) < 2:
            exam_qa_bn.append({"q": bn_sanitise(qq), "a": bn_sanitise(aa)})
    if why_qa:
        wa = clean(why_qa.get("answer", ""))
        if wa:
            exam_qa_bn.insert(0, {"q": "এই খবরটি কেন গুরুত্বপূর্ণ?",
                                  "a": bn_sanitise(wa)})
    exam_qa_en = exam_qa_en[:2]
    exam_qa_bn = exam_qa_bn[:2]

    # --- recall cards: blank the value in its quote (EN) / the Bangla
    # number in the fact line (BN). Max 2 each.
    recall_en, recall_bn = [], []
    for f in facts[:5]:
        if len(recall_en) >= 2:
            break
        value = clean(f.get("value", ""))
        quote = clean(f.get("quote", ""))
        if value and value in quote:
            recall_en.append({"cloze": quote.replace(value, "______", 1),
                              "answer": value})
        else:
            num = first_number(quote)
            if num:
                recall_en.append({"cloze": quote.replace(num, "______", 1),
                                  "answer": num})
    for ln in fact_lines:
        if len(recall_bn) >= 2:
            break
        m = re.search(r"[০-৯][০-৯,]*(?:\.[০-৯]+)?", ln)
        if m:
            recall_bn.append({"cloze": ln[:m.start()] + "______" + ln[m.end():],
                              "answer": m.group(0)})

    # --- why_it_matters.
    why_bn_raw = clean(item.get("why_important", ""))
    why_bn_raw = re.sub(r"^\[পটভূমি\]\s*", "", why_bn_raw)
    if why_bn_raw:
        bn_why = bn_sanitise(why_bn_raw)
    elif fact_lines:
        bn_why = f"মনে রাখার তথ্য: {fact_lines[0]}"
    else:
        bn_why = "মনে রাখার তথ্য: এই খবরের তথ্যগুলো পরীক্ষার জন্য গুরুত্বপূর্ণ।"
        notes.append("BN why_it_matters is a generic template: no "
                     "why_important line and no fact lines")
    en_why = (f"Key fact to remember: {quotes[0]} This is the one to carry "
              f"into BCS/Bank questions on {TOPIC_LABEL.get(topic, 'current affairs')}.") \
        if quotes else (f"This story is the one to carry into BCS/Bank "
                        f"questions on {TOPIC_LABEL.get(topic, 'current affairs')}.")

    keywords = []
    for w in content_words(headline):
        if w not in keywords:
            keywords.append(w)
        if len(keywords) >= 5:
            break

    src = (item.get("sources") or [{}])[0]
    # Story banner image: the lead image URL (og:image) Step 1
    # captured for the article — the URL only, never a downloaded
    # file. Empty string when the article has none (the app shows a
    # designed typographic banner instead). The key is always
    # present, never null. Page item first, article record fallback.
    image_url = (item.get("image_url") or article.get("image_url")
                 or "")
    en_story = {
        "id": "",  # filled by caller (CA number)
        "headline": headline,
        "category": category_for(item),
        "image_url": image_url,
        "event_date": event_date,
        "article_date": article_date,
        "summary": summary,
        "why_it_matters": en_why,
        "exam_facts": exam_facts,
        "exam_relevance": EXAM_RELEVANCE.get(topic, EXAM_RELEVANCE["BD-NATL"]),
        "key_people": "",
        "figures": figures,
        "sources": [{"publication": src.get("name", ""),
                     "headline": headline,
                     "date": article_date,
                     "url": src.get("url", "")}],
        "one_liner": truncate_words(quotes[0], 20) if quotes else truncate_words(headline, 20),
        "key_facts": key_facts,
        "what_happened": what_happened,
        "exam_qa": exam_qa_en,
        "recall_cards": recall_en,
        "keywords": keywords,
        "detail": detail,
    }
    bn_key_facts = []
    for i, kf in enumerate(key_facts):
        orig = fact_lines[i] if i < len(fact_lines) else bn_text
        bn_key_facts.append({"label": bn_sanitise(kf["label"]),
                             "value": bn_sanitise(kf["value"]),
                             "original": bn_sanitise(orig)})
    bn_story = {
        "headline": bn_sanitise(headline),
        "image_url": image_url,
        "summary": bn_text,
        "why_it_matters": bn_why,
        "exam_facts": bn_text,
        "key_people": "",
        "figures": bn_sanitise(figures),
        "one_liner": truncate_words(fact_lines[0], 20) if fact_lines else "",
        "key_facts": bn_key_facts,
        "what_happened": fact_lines,
        "exam_qa": exam_qa_bn,
        "recall_cards": recall_bn,
        "keywords": [bn_sanitise(k) for k in keywords],
        "detail": bn_sanitise(clean(item.get("focus_paragraph", ""))) or bn_text,
    }
    if not bn_story["one_liner"]:
        bn_story["one_liner"] = bn_sanitise(truncate_words(headline, 20))
        notes.append("BN one_liner fell back to the headline: no fact lines")
    return en_story, bn_story, notes


def build_editorial_story(ed_item, day_iso, ca_id):
    """The মতামত slot as a v1 story. Only headline/source/url/summary
    exist in v2, so every structured field is mechanically derived from
    that one summary sentence -- labelled in the report, no invented
    facts. event/article dates come from the matched article when the
    run dir has it, else the edition date."""
    notes = ["EDITORIAL: structured fields are mechanically derived from "
             "the slot's single summary sentence (headline/source/url/ "
             "summary is all v2 carries for the মতামত slot); no figures, "
             "no key people, no Q&A exist for it -- except the 2 exam_qa "
             "below, which are mechanically derived from the same "
             "sentence + source (renovated-archive standard: exactly 2 "
             "short Q&A per story)."]
    headline = clean(ed_item.get("headline", ""))
    summary_src = clean(ed_item.get("summary", ""))
    summary = f"Opinion: {summary_src}" if summary_src else headline
    source_name = clean(ed_item.get("source", ""))
    # Exactly 2 mechanical Q&A (renovated-archive standard): the
    # editorial's main argument (= its one summary sentence) and its
    # publication. No invented facts; if the source is missing, the
    # second Q&A falls back to the headline.
    ed_qa_en = [
        {"q": "What is the main argument of this editorial?",
         "a": summary_src if summary_src else headline},
        {"q": "Which publication carried this editorial?",
         "a": source_name if source_name else headline},
    ]
    ed_qa_bn = [
        {"q": "এই সম্পাদকীয়ের মূল বক্তব্য কী?",
         "a": bn_sanitise(summary_src) if summary_src else bn_sanitise(headline)},
        {"q": "কোন প্রকাশনা এই সম্পাদকীয়টি প্রকাশ করেছে?",
         "a": bn_sanitise(source_name) if source_name else bn_sanitise(headline)},
    ]
    article_date = ed_item.get("_article_date", day_iso)
    keywords = []
    for w in content_words(headline):
        if w not in keywords:
            keywords.append(w)
        if len(keywords) >= 5:
            break
    en_story = {
        "id": ca_id,
        "headline": headline,
        "category": "Editorial & Opinion",
        # Editorial articles are never fetched by Step 1 (they are
        # excluded from clusters), so no og:image is ever captured
        # for the মতামত slot: always "" — the app shows its
        # typographic banner. The key is always present, never null.
        "image_url": "",
        "event_date": article_date,
        "article_date": article_date,
        "summary": summary,
        "why_it_matters": (f"Opinion: {summary_src} -- the argument to carry "
                           f"into Focus Writing practice."),
        "exam_facts": summary_src + " (Opinion -- " +
                      clean(ed_item.get("source", "")) + ".)",
        "exam_relevance": EXAM_RELEVANCE["EDITORIAL"],
        "key_people": "",
        "figures": f"Published {datetime.strptime(article_date, '%Y-%m-%d').strftime('%d %B %Y')}.",
        "sources": [{"publication": clean(ed_item.get("source", "")),
                     "headline": headline,
                     "date": article_date,
                     "url": clean(ed_item.get("url", ""))}],
        "one_liner": truncate_words(summary_src, 20) if summary_src else truncate_words(headline, 20),
        "key_facts": [{"label": "opinion",
                       "value": clean(ed_item.get("source", "")),
                       "original": summary_src}],
        "what_happened": [summary_src] if summary_src else [headline],
        "exam_qa": ed_qa_en,
        "recall_cards": [],
        "keywords": keywords,
        "detail": summary_src if summary_src else headline,
    }
    bn_story = {
        "headline": bn_sanitise(headline),
        "image_url": "",
        "summary": bn_sanitise(summary_src) if summary_src else bn_sanitise(headline),
        "why_it_matters": bn_sanitise(f"মতামত: {summary_src}"),
        "exam_facts": bn_sanitise(summary_src) if summary_src else bn_sanitise(headline),
        "key_people": "",
        "figures": bn_sanitise(f"প্রকাশিত {datetime.strptime(article_date, '%Y-%m-%d').strftime('%d %B %Y')}."),
        "one_liner": bn_sanitise(truncate_words(summary_src, 20)) if summary_src else bn_sanitise(truncate_words(headline, 20)),
        "key_facts": [{"label": "মতামত",
                       "value": bn_sanitise(clean(ed_item.get("source", ""))),
                       "original": bn_sanitise(summary_src)}],
        "what_happened": [bn_sanitise(summary_src)] if summary_src else [bn_sanitise(headline)],
        "exam_qa": ed_qa_bn,
        "recall_cards": [],
        "keywords": [bn_sanitise(k) for k in keywords],
        "detail": bn_sanitise(summary_src) if summary_src else bn_sanitise(headline),
    }
    return en_story, bn_story, notes


# ---------------------------------------------------------------------------
# MCQs
# ---------------------------------------------------------------------------

def _stem_core(stem):
    core = re.sub(r"\s*\([^)]*অনুযায়ী\)\s*\??\s*$", "", clean(stem))
    core = re.sub(r"\s*(কত|কী|কবে|কোনটি)\s*\??\s*$", "", core).strip()
    return core


def mcq_filters(mcq, story, kept_stories, articles):
    """Return (usable, reason). Filters, in order:
    HTML / shape -> quote traces to this story's facts -> the quote is
    not sidebar boilerplate shared with another story -> the stem is
    not another article's headline -> no duplicate within the story."""
    stem = clean(mcq.get("stem", ""))
    if "<" in stem or ">" in stem:
        return False, "stem contains HTML"
    if not stem.endswith("?"):
        return False, "stem does not end with '?'"
    if len(stem) < 12:
        return False, "stem too short"
    opts = mcq.get("options", {}) or {}
    vals = [clean(opts.get(k, "")) for k in ("ক", "খ", "গ", "ঘ")]
    if not vals[0]:
        return False, "empty correct option"
    if len({norm(v) for v in vals}) != 4:
        return False, "duplicate options"
    if any(any(f in v for f in _FORBIDDEN_OPTIONS) for v in vals):
        return False, "forbidden option (all/none of the above)"
    quote = clean(mcq.get("source_quote", ""))
    if not quote:
        return False, "no source quote"
    story_quotes = [norm(f.get("quote", "")) for f in
                    story.get("facts_en", [])]
    qn = norm(quote)
    if not any(qn and (qn in q or q in qn) for q in story_quotes):
        return False, "source quote not in this story's facts"
    for other in kept_stories:
        if other["id"] == story["id"]:
            continue
        oq = [norm(f.get("quote", "")) for f in other.get("facts_en", [])]
        if any(qn and (qn in q or q in qn) for q in oq):
            return False, f"quote also appears in story {other['id']} (sidebar boilerplate)"
    core = _stem_core(stem)
    core_toks = set(content_words(core))
    if len(core_toks) >= 5:
        for art in articles:
            if art["id"] == story["id"]:
                continue
            title_toks = set(content_words(art.get("title", "")))
            if title_toks and len(core_toks & title_toks) / len(core_toks) >= 0.7:
                return False, f"stem matches another article's headline ({art['id']})"
    return True, ""


def select_ca_mcqs(page_items, questions, articles):
    """Select 13 Current Affairs MCQs: round-robin across stories in CA
    order, one per story first. Returns (selected, dropped, per_story)."""
    mcq_by_story = {}
    for m in questions.get("mcq", []):
        sid = m.get("id", "").rsplit("-mcq", 1)[0]
        mcq_by_story.setdefault(sid, []).append(m)
    usable, dropped = {}, []
    for story in page_items:
        pool = mcq_by_story.get(story["id"], [])
        seen_stem, seen_opts = set(), set()
        good = []
        for m in pool:
            ok, reason = mcq_filters(m, story, page_items, articles)
            if not ok:
                dropped.append({"id": m.get("id"), "story": story["id"],
                                "reason": reason})
                continue
            stem_n = norm(m.get("stem", ""))
            opts_key = tuple(norm(m.get("options", {}).get(k, ""))
                             for k in ("ক", "খ", "গ", "ঘ"))
            if stem_n in seen_stem:
                dropped.append({"id": m.get("id"), "story": story["id"],
                                "reason": "duplicate stem in story"})
                continue
            if opts_key in seen_opts:
                dropped.append({"id": m.get("id"), "story": story["id"],
                                "reason": "duplicate options in story"})
                continue
            seen_stem.add(stem_n)
            seen_opts.add(opts_key)
            good.append(m)
        usable[story["id"]] = good
    selected = []
    per_story = {s["id"]: 0 for s in page_items}
    order = [s["id"] for s in page_items]
    idx = {sid: 0 for sid in order}
    while len(selected) < N_CA_MCQ:
        progressed = False
        for sid in order:
            if len(selected) >= N_CA_MCQ:
                break
            pool = usable.get(sid, [])
            if idx[sid] < len(pool):
                selected.append((sid, pool[idx[sid]]))
                idx[sid] += 1
                per_story[sid] += 1
                progressed = True
        if not progressed:
            break
    return selected, dropped, per_story


def best_source_story(article_headline, example, page_items):
    """Best-overlap page story for a vocab/phrase MCQ's source field.
    v2 vocab traces to the 60 final items, mostly non-page articles, so
    this is best-effort provenance (logged), not an exact trace."""
    best, best_score = None, -1
    for it in page_items:
        score = len(set(content_words(article_headline)) &
                    set(content_words(it["headline"])))
        score += len(set(content_words(example)) &
                     set(content_words(" ".join(
                         f.get("quote", "") for f in it.get("facts_en", [])))))
        if score > best_score:
            best, best_score = it, score
    return best


def build_vocab_mcq(no, word, distractor_words, letter, source_id):
    """Vocabulary MCQ: 'What does 'X' mean?' -- correct = the word's
    English definition, distractors = other words' definitions.
    ``distractor_words`` are full word records so the BN overlay can
    use their Bangla meanings as the BN options."""
    headword = word.get("Headword / phrase", "")
    correct = clean(word.get("English definition", ""))
    options = {}
    letters = [L for L in "ABCD" if L != letter]
    options[letter] = correct
    for L, d in zip(letters, distractor_words):
        options[L] = clean(d.get("English definition", ""))
    bn_options = {}
    for L in "ABCD":
        bn_options[L] = (clean(word.get("Bangla meaning", "")) if L == letter
                         else "")
    for L, d in zip(letters, distractor_words):
        bn_options[L] = clean(d.get("Bangla meaning", ""))
    return {
        "no": no, "section": "Vocabulary",
        "question": f"What does '{headword}' mean?",
        "options": {L: options[L] for L in "ABCD"},
        "correct": letter,
        "explanation": (f"'{headword}' means: {correct} E.g. "
                        f"{clean(word.get('Original example', ''))}"),
        "source": source_id,
        "_bn": {
            "question": f"‘{headword}’ বলতে কী বোঝায়?",
            "options": bn_options,
            "explanation": f"‘{headword}’ মানে {clean(word.get('Bangla meaning', ''))}।",
        },
    }


def build_phrase_mcq(no, phrase, distractor_phrases, letter, source_id):
    name = phrase.get("Phrase", "")
    correct = clean(phrase.get("English explanation", ""))
    options = {}
    letters = [L for L in "ABCD" if L != letter]
    options[letter] = correct
    for L, d in zip(letters, distractor_phrases):
        options[L] = clean(d.get("English explanation", ""))
    bn_options = {}
    for L in "ABCD":
        bn_options[L] = (clean(phrase.get("Bangla meaning", "")) if L == letter
                         else "")
    for L, d in zip(letters, distractor_phrases):
        bn_options[L] = clean(d.get("Bangla meaning", ""))
    return {
        "no": no, "section": "Phrases",
        "question": f"What does the phrase '{name}' mean?",
        "options": {L: options[L] for L in "ABCD"},
        "correct": letter,
        "explanation": (f"'{name}' means: {correct} E.g. "
                        f"{clean(phrase.get('Original example 1', ''))}"),
        "source": source_id,
        "_bn": {
            "question": f"‘{name}’ বলতে কী বোঝায়?",
            "options": bn_options,
            "explanation": f"‘{name}’ বলতে {clean(phrase.get('Bangla meaning', ''))} বোঝায়।",
        },
    }


def build_ca_mcq(no, story_id, mcq, letter):
    opts_v2 = mcq.get("options", {}) or {}
    vals = [clean(opts_v2.get(k, "")) for k in ("ক", "খ", "গ", "ঘ")]
    key_text = vals[0]
    options = {}
    letters = [L for L in "ABCD" if L != letter]
    options[letter] = key_text
    for L, v in zip(letters, vals[1:]):
        options[L] = v
    quote = clean(mcq.get("source_quote", ""))
    if len(quote) > 300:
        quote = quote[:300].rstrip() + "…"
    explanation = f"Correct answer: {key_text}. Source: {quote}"
    why = (mcq.get("why_wrong", {}) or {}).get("ক", "")
    return {
        "no": no, "section": "Current Affairs",
        "question": clean(mcq.get("stem", "")),
        "options": {L: options[L] for L in "ABCD"},
        "correct": letter,
        "explanation": explanation,
        "source": story_id,
        "_bn": {
            "question": bn_sanitise(clean(mcq.get("stem", ""))),
            "options": {L: bn_sanitise(options[L]) for L in "ABCD"},
            "explanation": bn_sanitise(clean(why)) or bn_sanitise(explanation),
        },
        "_v2_id": mcq.get("id", ""),
    }


def longest_letter(mcq):
    best, best_len = "A", -1
    for letter in "ABCD":
        n = len(str(mcq["options"][letter]))
        if n > best_len:
            best, best_len = letter, n
    return best


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def pick_distractors(correct_text, pool, used=None):
    """3 distractor records from ``pool`` (records with a 'text' key).
    Prefer definitions LONGER than the correct one, so the correct
    answer is not the longest option (validator flags longest-correct
    > 10/25); among those, prefer texts not yet used as an option in
    an earlier MCQ, so the same longest definitions do not recur as
    distractors in every question; then longest first, then A-Z.
    Deterministic."""
    used = used or set()
    cands = [r for r in pool if clean(r["text"]) and
             norm(r["text"]) != norm(correct_text)]
    cands.sort(key=lambda r: (0 if len(clean(r["text"])) > len(correct_text) else 1,
                              0 if norm(r["text"]) not in used else 1,
                              -len(clean(r["text"])), r["key"]))
    seen, out = set(), []
    for r in cands:
        if norm(r["text"]) in seen:
            continue
        seen.add(norm(r["text"]))
        out.append(r)
        if len(out) == 3:
            break
    return out


def convert(date_str, run_dir, staging_dir, learning_modules=False):
    day = datetime.strptime(date_str, "%Y-%m-%d").date()
    day_iso = date_str
    run_dir = Path(run_dir)
    staging_dir = Path(staging_dir)
    report = {"date": day_iso, "mapping": [], "empty_fields": [],
              "repairs": [], "mcq": {}, "editorial": {}, "bn": {},
              "self_checks": [], "unmeetable": [], "notes": []}
    log(f"converting v2 run {run_dir} -> staging {staging_dir}")

    page = load_json(run_dir / f"page-{date_str}.json")
    questions = load_json(run_dir / f"questions-{date_str}.json")
    vocab = load_json(run_dir / f"vocab-{date_str}.json")
    articles_doc = load_json(run_dir / f"articles-{date_str}.json")
    articles = articles_doc.get("articles", [])
    by_id = {a["id"]: a for a in articles}
    items_path = run_dir / f"items-{date_str}.json"
    items_doc = load_json(items_path) if items_path.exists() else None
    items_by_id = {}
    if items_doc:
        for it in items_doc.get("items", []):
            items_by_id[it["id"]] = it
        log(f"items file present: {len(items_by_id)} final items")
    else:
        log("no items file for this run (run_v2.py persistence not yet "
            "in place for 15 Nov) -- BN key_fact labels fall back to "
            "sanitised English 'what' text; see report")
        report["notes"].append(
            "No items-<date>.json for the 15 Nov run (it was produced "
            "before run_v2.py persisted final_items). BN key_fact labels "
            "are sanitised English 'what' text; from the next run the "
            "items file supplies Bangla structured facts.")
    qa_by_story = {}
    for q in questions.get("qa", []):
        sid = q.get("id", "").rsplit("-qa", 1)[0]
        qa_by_story.setdefault(sid, []).append(q)
    items_by_id["_qa"] = qa_by_story

    # --- story order: at_a_glance order (score desc, then newest) ----
    sections = page.get("sections", {})
    flat = [it for sec in sections.values() for it in sec]
    by_headline = {it["headline"]: it for it in flat}
    ordered = []
    for row in page.get("at_a_glance", []):
        it = by_headline.get(row.get("event", ""))
        if it is not None and it not in ordered:
            ordered.append(it)
    for it in flat:  # fallback: anything missing from at_a_glance
        if it not in ordered:
            ordered.append(it)
    log(f"page order ({len(ordered)} items): "
        + ", ".join(it["id"] for it in ordered))

    # --- 14 news + 1 editorial = 15 (v1 ceiling; publish.py checklist
    # caps stories at 15 and requires an editorial story). Drop the
    # lowest-ranked page item.
    ed = (page.get("editorial") or {}).get("item")
    if ed is None:
        raise SystemExit("no editorial item in the page JSON -- cannot "
                         "fill the Editorial & Opinion slot")
    dropped_story = ordered[-1]
    news_items = ordered[:-1]
    log(f"dropping lowest-ranked page item {dropped_story['id']} "
        f"({dropped_story['headline'][:60]!r}) -- 15-story ceiling")
    report["editorial"] = {
        "decision": "14 news + 1 editorial = 15 stories",
        "why": ("validate_editions.py only requires counts == index, so "
                "16 would pass it -- but publish.py's checklist caps "
                "stories at 15 (12-15 ok) and requires an Editorial & "
                "Opinion story, and v1 Edition 9 has exactly this shape "
                "(15 stories incl. 1 editorial). Dropping a news story "
                "keeps every gate green."),
        "dropped_news_item": {
            "id": dropped_story["id"],
            "headline": dropped_story["headline"],
            "reason": "lowest-ranked page item (score desc, then newest first)",
        },
        "editorial_headline": ed.get("headline"),
        "editorial_source": ed.get("source"),
    }

    # --- decontaminate facts: a quote that appears in 2+ kept stories'
    # facts is sidebar/related-link boilerplate, not story content (the
    # 15 Nov run carries the "Islami Bank seeks Tk6,000cr..." headline
    # as a "fact" inside the jute/COP31 and other TBS stories). Drop
    # those facts, and <20-char fragment quotes ("cop 31 / Jute"), from
    # every derived field. Logged in the report.
    def _qnorm(q):
        return norm(q)
    quote_owners = {}
    for _it in ordered:
        for _f in _it.get("facts_en", []) or []:
            _q = _qnorm(_f.get("quote", ""))
            if _q:
                quote_owners.setdefault(_q, set()).add(_it["id"])
    shared = {_q for _q, _owners in quote_owners.items() if len(_owners) >= 2}
    for _it in ordered:
        kept_facts, removed = [], []
        for _f in _it.get("facts_en", []) or []:
            _q = clean(_f.get("quote", ""))
            if _qnorm(_q) in shared:
                removed.append(("shared-quote", _q[:70]))
                continue
            if len(_q) < 20:
                removed.append(("fragment-quote", _q[:70]))
                continue
            kept_facts.append(_f)
        if removed:
            report["notes"].append(
                f"{_it['id']}: dropped {len(removed)} contaminated fact(s) "
                f"from all derived fields: {removed}")
            log(f"{_it['id']}: dropped {len(removed)} contaminated fact(s)")
        _it["facts_en"] = kept_facts

    # --- build stories -------------------------------------------------
    stories_en, stories_bn, story_notes = [], {}, {}
    ca_of = {}
    for i, item in enumerate(news_items):
        ca = f"CA{i + 1:02d}"
        ca_of[item["id"]] = ca
        en, bn, notes = build_story_fields(
            item, by_id.get(item["id"], {}), day_iso, items_by_id)
        en["id"] = ca
        stories_en.append(en)
        stories_bn[ca] = bn
        story_notes[ca] = notes
    ed_ca = f"CA{len(news_items) + 1:02d}"
    ed_item = dict(ed)
    ed_art = next((a for a in articles if a.get("url") == ed.get("url")), None)
    if ed_art is not None:
        ed_item["_article_date"] = pub_date_iso(ed_art.get("published", "")) or day_iso
    else:
        ed_item["_article_date"] = day_iso
        report["notes"].append("editorial article not found in "
                               "articles file; editorial dates fall back "
                               "to the edition date")
    en_ed, bn_ed, ed_notes = build_editorial_story(ed_item, day_iso, ed_ca)
    stories_en.append(en_ed)
    stories_bn[ed_ca] = bn_ed
    story_notes[ed_ca] = ed_notes

    # --- vocab: verbatim, except the phrase-example repair ------------
    words = vocab.get("words", [])
    phrases = vocab.get("phrases", [])
    revision = vocab.get("revision_words", [])
    items_bodies = {it["id"]: it.get("body_text", "") for it in
                    items_by_id.values()
                    if isinstance(it, dict) and "id" in it}
    for p in phrases:
        if not clean(p.get("Original example 2", "")):
            filled = ""
            if items_bodies:
                pre = re.compile(r"\b" + re.escape(p.get("Phrase", "").lower())
                                 + r"s?\b", re.IGNORECASE)
                for body in items_bodies.values():
                    for sent in re.split(r"(?<=[.!?])\s+", body or ""):
                        if pre.search(sent) and sent.strip() != clean(p.get("Original example 1", "")):
                            filled = sent.strip()
                            break
                    if filled:
                        break
            if filled:
                p["Original example 2"] = filled
                report["repairs"].append(
                    f"phrase '{p.get('Phrase')}': empty Original example 2 "
                    f"filled from a body sentence (items file)")
            else:
                p["Original example 2"] = p.get("Original example 1", "")
                report["repairs"].append(
                    f"phrase '{p.get('Phrase')}': empty Original example 2 "
                    f"copied from Original example 1 (no second sentence "
                    f"exists in the v2 outputs; no items file for 15 Nov) "
                    f"-- the validator requires the complement word in "
                    f"both examples")
    log(f"vocab: {len(words)} words, {len(phrases)} phrases, "
        f"{len(revision)} revision (verbatim from v2)")

    # --- learning modules (v2, opt-in ONLY) ---------------------------
    # Default OFF: the live daily path never passes --learning-modules,
    # so the live conversion is byte-identical to before. When the flag
    # IS passed (dry-runs only, until the format is proven), every
    # story gets learning_module.py's 11-section module and the data
    # file declares renovation_format "learning-module-v2". The gate
    # (publish_v2.py check 15) validates the shape + answer traces.
    lm_notes = {}
    lm_gk_used = []
    if learning_modules:
        gk_entries = learning_module.load_gk_entries()
        if not learning_module.GK_PATH.exists():
            raise SystemExit(
                "learning modules requested but the GK knowledge file "
                f"is missing: {learning_module.GK_PATH} -- refusing to "
                "emit GK sections without their sourced entries")
        enrichment = learning_module.load_enrichment()
        base_ctx = {
            "questions": questions,
            "vocab_words": words,
            "enrichment": enrichment,
            "gk_entries": gk_entries,
            "page_items": news_items,
            "articles": articles,
            "edition_stories": stories_en,
            "date": day_iso,
        }
        for i, item in enumerate(news_items):
            ca = f"CA{i + 1:02d}"
            ctx = dict(base_ctx)
            ctx["ca_id"] = ca
            module, notes = learning_module.build_module(
                stories_en[i], stories_bn[ca], item, ctx)
            stories_en[i]["learning_module"] = module
            lm_notes[ca] = notes
            if any("GK entry '" in n for n in notes):
                lm_gk_used.append(ca)
        ed_ctx = dict(base_ctx)
        ed_ctx["ca_id"] = ed_ca
        ed_ctx["is_editorial"] = True
        module, notes = learning_module.build_module(
            stories_en[-1], stories_bn[ed_ca], ed_item, ed_ctx)
        stories_en[-1]["learning_module"] = module
        lm_notes[ed_ca] = notes
        log(f"learning modules: 15 stories, GK entry used on "
            f"{lm_gk_used or 'none'}; vocabulary matched "
            f"{sum(len(s.get('learning_module', {}).get('vocabulary', [])) for s in stories_en)} "
            f"edition words in total")

    # --- MCQs ------------------------------------------------------------
    seed = int(date_str.replace("-", ""))
    rng = random.Random(seed)
    letters = (["A"] * 6 + ["B"] * 6 + ["C"] * 6 + ["D"] * 7)
    rng.shuffle(letters)
    mcqs = []
    # 1-10 Vocabulary (first 10 words, deterministic).
    word_pool = [{"key": w.get("Headword / phrase", ""),
                  "text": w.get("English definition", ""), "rec": w}
                 for w in words]
    used_option_texts = set()
    for i, w in enumerate(words[:N_VOCAB_MCQ]):
        distract = pick_distractors(w.get("English definition", ""), word_pool,
                                    used_option_texts)
        used_option_texts.add(norm(w.get("English definition", "")))
        for d in distract:
            used_option_texts.add(norm(d["text"]))
        src = best_source_story(w.get("Article headline", ""),
                                w.get("Original example", ""), news_items)
        mcqs.append(build_vocab_mcq(
            i + 1, w, [d["rec"] for d in distract], letters[i],
            ca_of.get(src["id"], "CA01") if src else "CA01"))
    # 11-12 Phrases (first 2 phrases).
    phrase_pool = [{"key": p.get("Phrase", ""),
                    "text": p.get("English explanation", ""), "rec": p}
                   for p in phrases]
    for j, p in enumerate(phrases[:N_PHRASE_MCQ]):
        distract = pick_distractors(p.get("English explanation", ""), phrase_pool,
                                    used_option_texts)
        used_option_texts.add(norm(p.get("English explanation", "")))
        for d in distract:
            used_option_texts.add(norm(d["text"]))
        src = best_source_story(p.get("Article headline", ""),
                                p.get("Original example 1", ""), news_items)
        mcqs.append(build_phrase_mcq(
            10 + j + 1, p, [d["rec"] for d in distract], letters[10 + j],
            ca_of.get(src["id"], "CA01") if src else "CA01"))
    # 13-25 Current Affairs.
    selected, dropped, per_story = select_ca_mcqs(news_items, questions, articles)
    log(f"CA MCQ pool: {len(selected)} selected, {len(dropped)} dropped")
    for k, (sid, m) in enumerate(selected):
        mcqs.append(build_ca_mcq(12 + k + 1, ca_of[sid], m, letters[12 + k]))
    if len(selected) < N_CA_MCQ:
        raise SystemExit(f"only {len(selected)} usable CA MCQs -- need "
                         f"{N_CA_MCQ}; see dropped list in report")
    report["notes"].append(
        "Vocab/phrase MCQ sources are best-token-overlap page stories, "
        "not exact traces: v2 vocab words trace to the 60 final items, "
        "mostly non-page articles (0 of the first 10 words' article "
        "headlines match a page story exactly). The source field is "
        "therefore best-effort provenance to satisfy the validator's "
        "'source is a story id' rule; the MCQ itself tests the word, "
        "not the story.")
    letter_counts = {L: sum(1 for m in mcqs if m["correct"] == L) for L in "ABCD"}
    longest_n = sum(1 for m in mcqs if longest_letter(m) == m["correct"])
    longest_list = [m["no"] for m in mcqs if longest_letter(m) == m["correct"]]
    report["mcq"] = {
        "method": ("Vocabulary 1-10: first 10 vocab words, 'What does X "
                   "mean?', correct = English definition, distractors = "
                   "3 other words' definitions (longer-than-correct "
                   "preferred). Phrases 11-12: first 2 phrases, same "
                   "pattern with English explanations. Current Affairs "
                   "13-25: v2 MCQs filtered (HTML/quote-trace/shared-"
                   "quote/other-headline/dupes) then round-robin, one "
                   "per story in CA order. Correct letters: seeded "
                   f"shuffle (seed {seed}), target A6/B6/C6/D7."),
        "letters": letter_counts,
        "longest_correct": longest_n,
        "longest_correct_nos": longest_list,
        "ca_selected": [{"no": m["no"], "v2_id": m.get("_v2_id"),
                         "story": m["source"]} for m in mcqs[12:]],
        "ca_dropped": dropped,
        "ca_per_story": per_story,
        "vocab_sources": [{"no": m["no"], "source": m["source"]}
                          for m in mcqs[:12]],
    }
    log(f"MCQ letters {letter_counts}, longest-correct {longest_n}/25 "
        f"(nos {longest_list})")

    # --- sources ---------------------------------------------------------
    sources = []
    seen_urls = set()
    for i, s in enumerate(stories_en):
        src = s["sources"][0]
        url = src.get("url", "")
        if url in seen_urls:
            report["notes"].append(f"duplicate source URL skipped for "
                                   f"{s['id']}: {url}")
            continue
        seen_urls.add(url)
        sources.append({
            "Source ID": f"S{i + 1:02d}",
            "Publication / organisation": src.get("publication", ""),
            "Headline / report": s["headline"],
            "Publication date": s["article_date"],
            "Direct URL": url,
        })

    # --- assemble data file ----------------------------------------------
    counts = {"stories": len(stories_en), "words": len(words),
              "phrases": len(phrases), "mcqs": len(mcqs),
              "revision_words": len(revision)}
    coverage = coverage_label(day)
    data = {
        "edition_date": day_iso,
        "edition_day": day.strftime("%A"),
        "coverage": coverage,
        "status": "published",
        "counts": counts,
        "stories": stories_en,
        "words": words,
        "revision_words": revision,
        "phrases": phrases,
        "mcqs": [{k: v for k, v in m.items() if not k.startswith("_")}
                 for m in mcqs],
        "sources": sources,
        "approved_by": "dry-run -- not approved",
        "approval_notes": ("Dry-run conversion of the v2 engine outputs for "
                           f"{day_iso}. NOT published, NOT approved under "
                           "Rudro's rule. Status is 'published' only "
                           "because the edition validators hard-code that "
                           "value; these files live in staging only "
                           "(runs/<date>/app-format/) and were never copied "
                           "to editions/."),
    }
    if learning_modules:
        # Learning-module v2 edition: the app renders the 11-section
        # module per story; the gate validates its shape (check 15).
        data["renovation_format"] = learning_module.RENOVATION_FORMAT
        data["renovation_date"] = day_iso
    # counts.sources is not a v1 counts key; index carries sources count.
    bn = {
        "edition_date": day_iso,
        "status": "published",
        "language": "bn",
        # Renovated-archive contract: the repo validator
        # (tools/validate_renovated_editions.py) requires this flag to
        # be exactly False -- English fallback is disabled for the BN
        # overlay. The live v1 editions already carry it.
        "english_fallback_allowed": False,
        "note": ("Bengali overlay rendered from the v2 engine's Bangla "
                 "fact lines (fact_lines) and sanitised v2 questions. "
                 "Figures, dates, names and money are rendered in "
                 "authentic Bengali: Bangla digits, Bangla month names, "
                 "Taka as টাকা/কোটি/লাখ, and Bengali transliterations of "
                 "proper nouns. Source publication names stay as in "
                 "English. English fallback is disabled for this overlay "
                 "(english_fallback_allowed is false)."),
        "stories": stories_bn,
        "mcqs": {str(m["no"]): m["_bn"] for m in mcqs},
    }
    # --- staging index: copy the live index, append the new entry ------
    live_index = load_json(EDITIONS_DIR / "index.json")
    index = copy.deepcopy(live_index)
    index["editions"].append({
        "edition_date": day_iso,
        "file": f"data-{day_iso}.json",
        "status": "published",
        "review": ("DRY RUN (staging only -- not published, not approved): "
                   f"v2->app conversion of the {day.strftime('%d %b %Y')} v2 dry run. "
                   "15 stories: 14 news in page order + editorial CA15. "
                   f"Rank-15 page item {dropped_story['id']} "
                   f"({dropped_story['headline'][:60]}) not carried -- 15-story "
                   "ceiling. EN prose is rendered from facts_en quotes; BN from "
                   f"fact_lines. See conversion-report-{day_iso}.md."
                   + (" Learning modules (v2, 11 sections) attached to all "
                      "15 stories; GK entry used on "
                      f"{', '.join(lm_gk_used) if lm_gk_used else 'no story'}."
                      if learning_modules else "")),
        "stories": counts["stories"],
        "words": counts["words"],
        "phrases": counts["phrases"],
        "mcqs": counts["mcqs"],
        "revision_words": counts["revision_words"],
        "sources": len(sources),
        "coverage": coverage,
    })

    # --- self-checks -------------------------------------------------------
    checks = []
    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        log(("PASS " if ok else "FAIL ") + name + (f" -- {detail}" if detail else ""))
    check("counts", counts["stories"] == 15 and counts["words"] == 20 and
          counts["phrases"] == 10 and counts["mcqs"] == 25 and
          counts["revision_words"] == 5,
          str(counts))
    check("mcq letters 5-8 each", all(5 <= v <= 8 for v in letter_counts.values()),
          str(letter_counts))
    check("no '[example]'",
          "[example]" not in json.dumps(data, ensure_ascii=False) and
          "[example]" not in json.dumps(bn, ensure_ascii=False))
    check("no 'rice, wheat,'",
          "rice, wheat," not in json.dumps(data, ensure_ascii=False))
    # word / phrase validator rules (validate_editions.py replicas).
    bad_words = [w.get("Headword / phrase") for w in words + revision
                 if (w.get("Headword / phrase") or "").strip().lower()
                 not in (w.get("Original example") or "").lower()]
    check("word examples contain headword", not bad_words, str(bad_words))
    bad_phrases = []
    for p in phrases:
        ph = p.get("Phrase", "")
        ws = [w for w in re.findall(r"[a-z']+", ph.lower()) if len(w) >= 3]
        for key in ("Original example 1", "Original example 2"):
            ex = (p.get(key) or "").lower()
            for w in ws[1:]:
                if w not in ex and w[:4] not in ex:
                    bad_phrases.append((ph, key, w))
    check("phrase examples contain complement", not bad_phrases, str(bad_phrases[:5]))
    # BN summary numbers preserved (check_data.py #4 replica).
    missing_nums = []
    for s in stories_en:
        bn_sum = stories_bn[s["id"]]["summary"]
        missing_nums += [(s["id"], t) for t in
                         bn_summary_numbers_ok(s["summary"], bn_sum)]
    check("BN summary numbers preserved", not missing_nums, str(missing_nums[:5]))
    # BN overlay: no validator violations (python replica of the Dart
    # detectors) in any scanned BN string.
    def _walk(node, path=""):
        if isinstance(node, str):
            yield path, node
        elif isinstance(node, dict):
            for k, v in node.items():
                yield from _walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from _walk(v, f"{path}[{i}]")
    bn_viol = []
    for path, val in _walk(bn):
        if path in ("note", "edition_date", "language"):
            continue
        # image_url is a publisher URL, not Bengali prose: its Latin
        # digits (e.g. /2026/11/17/ in a TBS image path) are not a
        # hygiene violation. The gate validates it separately as a
        # URL (check 15); the prose scan must not see it.
        if path.endswith(".image_url"):
            continue
        for kind, match in bn_violations(val):
            bn_viol.append((path, kind, match))
    check("BN overlay: no Bangla violations (python replica)",
          not bn_viol, str(bn_viol[:5]))
    # BN key_fact 'original' rule (validate_editions.py).
    bad_orig = []
    for sid, bs in stories_bn.items():
        for kf in bs.get("key_facts", []):
            o = kf.get("original") or ""
            if (re.search(r"[0-9]", o) or "Tk" in o or
                    re.search(r"\b(?:January|February|March|April|May|June|"
                              r"July|August|September|October|November|"
                              r"December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|"
                              r"Sept|Oct|Nov|Dec)\b", o)):
                bad_orig.append((sid, o[:60]))
    check("BN key_fact originals clean", not bad_orig, str(bad_orig[:3]))
    # Story ids / MCQ sources / dup URLs.
    check("story ids CA01..CA15",
          [s["id"] for s in stories_en] == [f"CA{i + 1:02d}" for i in range(15)])
    sids = {s["id"] for s in stories_en}
    check("MCQ sources are story ids",
          all(m["source"] in sids for m in mcqs))
    urls = [x.get("Direct URL") for x in sources]
    check("no dup top-level source URLs", len(urls) == len(set(urls)))
    check("BN story ids == EN", set(stories_bn) == sids)
    check("BN MCQ numbers == EN 1..25",
          set(bn["mcqs"]) == {str(m["no"]) for m in mcqs})
    check("BN story fields non-empty",
          all(bool(bs.get(k)) for bs in stories_bn.values()
              for k in ("headline", "summary", "why_it_matters",
                        "exam_facts", "figures")),
          "all stories carry headline/summary/why/exam_facts/figures")
    # Renovated-archive standard (repo validator
    # tools/validate_renovated_editions.py): exactly 2 EN + 2 BN
    # short Q&A per story, BN english_fallback_allowed False. The
    # converter enforces this at build time; this self-check fails
    # the conversion (exit 1) if a story ever yields fewer than 2
    # usable Q&A, instead of letting the gate auto-publish a file
    # the repo validator then fails (run #17 lesson, 2026-11-17).
    check("renovated standard: exactly 2 EN exam_qa per story",
          all(len(s.get("exam_qa", [])) == 2 for s in stories_en),
          str([(s["id"], len(s.get("exam_qa", []))) for s in stories_en
               if len(s.get("exam_qa", [])) != 2]))
    check("renovated standard: exactly 2 BN exam_qa per story",
          all(len(bs.get("exam_qa", [])) == 2 for bs in stories_bn.values()),
          str([(sid, len(bs.get("exam_qa", [])))
               for sid, bs in stories_bn.items()
               if len(bs.get("exam_qa", [])) != 2]))
    check("renovated standard: BN english_fallback_allowed is False",
          bn.get("english_fallback_allowed") is False)
    check("EN one_liners <= 20 words",
          all(len(s["one_liner"].split()) <= 20 for s in stories_en))
    check("key_facts 1-4 per story",
          all(1 <= len(s["key_facts"]) <= 4 for s in stories_en))
    check("EN summaries <= 90 words",
          all(len(s["summary"].split()) <= 90 for s in stories_en),
          str([(s["id"], len(s["summary"].split())) for s in stories_en
               if len(s["summary"].split()) > 90]))
    check("every story has >=1 http source",
          all(s["sources"] and str(s["sources"][0].get("url", "")).startswith("http")
              for s in stories_en))
    # Story banner image (Phase 0, ws5): the key is always present,
    # a string, "" or a valid http(s) URL — never null, never a
    # local path, never a data: URI, never a downloaded file.
    def _img_ok(v):
        return (isinstance(v, str)
                and (v == "" or v.startswith(("http://", "https://"))))
    bad_img = [(s["id"], s.get("image_url")) for s in stories_en
               if not _img_ok(s.get("image_url"))]
    bad_img += [(sid, bs.get("image_url")) for sid, bs in stories_bn.items()
                if not _img_ok(bs.get("image_url"))]
    check("every story carries image_url ('' or http(s) URL, never null/local/data:)",
          not bad_img, str(bad_img))
    # Learning-module v2 shape (opt-in only): the same validator the
    # gate runs (publish_v2.py check 15) — 11 keys in order, 4 MCQs
    # with traced answers + explanations, no unmarked empty GK.
    if learning_modules:
        lm_problems = []
        edition_headwords = [w.get("Headword / phrase", "")
                             for w in words]
        for s in stories_en:
            probs = learning_module.validate_module(
                s.get("learning_module"), s, edition_headwords,
                is_editorial=(s["id"] == ed_ca))
            lm_problems += [f"{s['id']}: {p}" for p in probs]
        check("learning_module v2 shape (11 keys, 4 MCQs, traced "
              "answers, no unmarked empty GK)",
              not lm_problems, str(lm_problems[:5]))
    report["self_checks"] = checks
    report["notes"].extend(
        f"{ca}: {'; '.join(n for n in story_notes[ca])}" for ca in story_notes
        if story_notes[ca])
    if learning_modules:
        report["notes"].append(
            "learning-module v2: GK entry used on "
            f"{', '.join(lm_gk_used) if lm_gk_used else 'no story'}; "
            "every other story carries the per-section marker for "
            "topic_gk/institutions/extra_knowledge (no GK entry in "
            "rules/gk_knowledge.json for its topic — never guessed). "
            f"Vocabulary matched "
            f"{sum(len(s.get('learning_module', {}).get('vocabulary', [])) for s in stories_en)} "
            "edition Step 10 words in total across 15 stories (most "
            "stories match 0 by headline — the list is left short, "
            "never padded). Written-prep analytical questions are the "
            "Step 8 analytical where one exists for the story, else a "
            "generic template question whose outline is the story's "
            "own facts.")
        report["notes"].extend(
            f"{ca} [learning-module]: {'; '.join(ns)}"
            for ca, ns in sorted(lm_notes.items()) if ns)
    report["empty_fields"] = [
        {"field": "key_people (EN + BN, all stories)",
         "why": "v2 carries no key_people anywhere (no Step 4/5/6 field, "
                "no items-file field). Left empty; neither validator "
                "requires it."},
        {"field": "recall_cards for the editorial story (CA15)",
         "why": "the v2 editorial slot has no numeric facts to blank; "
                "the list is left empty (shape-only checks). Its exam_qa "
                "is NOT empty: 2 mechanical Q&A derived from the summary "
                "sentence + source (renovated-archive standard)."},
        {"field": "Synonyms / Antonyms / Word family / Collocations / IPA / "
                  "Bangla phonetic on today's 20 words",
         "why": "v2 Step 10 enriches only words that appeared in an "
                "earlier v1 edition; none of today's 20 words (or 10 "
                "phrases) ever appeared as a v1 headword (checked: 305 "
                "v1 headwords, 0 overlap). No honest source exists in "
                "the repo -- see 'unmeetable'."},
        {"field": "EN why_it_matters (all stories)",
         "why": "v2's why_important line is Bangla ([পটভূমি] ...), so "
                "there is no English why-line to carry. EN why is a "
                "templated frame around the first verified fact quote "
                "(no new facts). BN why uses the real Bangla line where "
                "it exists (score-3 items)."},
        {"field": "EN summary/detail/exam_facts for Bangla-article stories",
         "why": "facts_en for Bangla articles is untranslated Bangla "
                "(render_facts_en did not translate the a784 article). "
                "The 15 Nov page's only Bangla-article story is a784, "
                "kept as CA07, so its EN summary/detail/exam_facts ARE "
                "Bangla text in the staged file. Validators pass (the BN "
                "overlay covers those EN fields, so they are not scanned "
                "as Bengali text), but an English-mode user sees Bangla "
                "for CA07. Its BN overlay is correct Bangla. The gap "
                "belongs in render_facts_en (Step 4), not the converter."},
    ]
    report["unmeetable"] = [
        {"requirement": "check_data.py #7/#8: synonym pool >= 15/20, "
                        "antonym pool >= 10/20, collocation field >= 15/20, "
                        "synonym/antonym distractor pools >= 4",
         "why": "Today's 20 v2 words carry no synonyms/antonyms/"
                "collocations (see empty_fields). The converter cannot "
                "invent them, and no synonym source exists in the repo "
                "(vocab bank has Bangla meaning + English definition "
                "only). check_data.py WILL fail on #7/#8 for this edition. "
                "Fix belongs in Step 10 (a synonym/antonym source) or in "
                "the bank -- not in the converter."},
        {"requirement": "publish.py checklist #13 (every summary AND "
                        "figures carry a digit) and #16 (exam_facts adds "
                        ">= 5 new tokens) for the editorial story CA15",
         "why": "The editorial slot is one summary sentence with no "
                "numbers and no further facts. Its figures fall back to "
                "the publication date (has a digit) but its summary "
                "cannot honestly carry a digit, and its exam_facts "
                "cannot add new facts beyond the one sentence. The two "
                "required validators do not have these checks."},
        {"requirement": "BN key_fact labels in Bangla (15 Nov run only)",
         "why": "No Bangla structured facts were persisted for 15 Nov "
                "(no items file). BN labels are sanitised English 'what' "
                "text. From the next run, run_v2.py persists items-"
                "<date>.json and the converter can use Bangla fact text."},
    ]
    report["mapping"] = [
        ["edition_date", "run date (page date)"],
        ["edition_day", "weekday derived from the date"],
        ["coverage", "v1 formula, copied: previous day 07:47 Dhaka -> date 07:47 Dhaka"],
        ["counts", "len() of each list; sources = deduped story sources"],
        ["story.id", "CA01..CA15 in at_a_glance (ranked) order; editorial last"],
        ["story.headline", "v2 page headline, verbatim"],
        ["story.image_url", "v2 page item image_url (Step 1 og:image, the URL only, never downloaded); '' when the article has none; editorial always '' (editorial articles are never fetched)"],
        ["story.category", "v2 topic_primary mapped to the 7 fixed v1 categories (ENV->Bangladesh, SCI->Technology, SPORT/PEOPLE->Bangladesh if headline names Bangladesh else World)"],
        ["story.event_date / article_date", "articles file 'published' parsed to ISO; fallback edition date"],
        ["story.summary (EN)", "first 2 facts_en QUOTES (verbatim article sentences) whose numbers survive into the BN summary; <=90 words"],
        ["story.why_it_matters (EN)", "templated frame around the first verified quote (v2 why line is Bangla, no English source)"],
        ["story.exam_facts (EN)", "remaining facts_en quotes (3rd-5th)"],
        ["story.exam_relevance", "fixed template per v2 topic (no facts)"],
        ["story.key_people", "EMPTY -- v2 has no key_people anywhere"],
        ["story.figures (EN)", "value+unit per fact, else first number in the quote; fallback publication date"],
        ["story.sources", "v2 page item sources (name+url), headline = story headline"],
        ["story.one_liner (EN)", "first fact quote truncated to 20 words"],
        ["story.key_facts (EN)", "facts_en: label = 'what' (<=12 words), value = value+unit or fact date or first number, original = verbatim quote"],
        ["story.what_happened (EN)", "one bullet per facts_en quote"],
        ["story.exam_qa (EN)", "filtered v2 Q&A for the story (HTML dropped, why-QA excluded, exactly 2 -- renovated-archive standard)"],
        ["story.recall_cards (EN)", "first 2 facts with values: value blanked in its quote"],
        ["story.learning_module (opt-in --learning-modules only)",
         "11-section v2 module (learning_module.py): hero/news_summary/verified_facts from the story's own facts; topic_gk/institutions/extra_knowledge from rules/gk_knowledge.json (sourced entries) or the per-section marker; mcq_practice 4/story (usable Step 8 MCQs first, then synthesised from the story's own facts; editorial: 4 mechanical MCQs from the edition file itself); written_prep from the Step 8 analytical where one exists, else a templated question with the story's own facts as outline; vocabulary = matched edition Step 10 words only (headline or source URL); revision from the story's own Q&A/recall cards; deep_prep from the GK entry or a category-templated title list"],
        ["renovation_format / renovation_date (opt-in only)",
         "\"learning-module-v2\" + the edition date, when --learning-modules was passed"],
        ["story.keywords", "headline content words (len>=4, stopwords removed, max 5)"],
        ["story.detail (EN)", "all facts_en quotes joined"],
        ["BN story.headline", "v2 headline, bn_sanitised (digits/months/Tk) -- NOT translated"],
        ["BN story.summary / exam_facts", "v2 fact_lines joined"],
        ["BN story.why_it_matters", "score-3: real [পটভূমি] line minus marker; else 'মনে রাখার তথ্য: <first fact line>'"],
        ["BN story.figures", "bn_sanitised EN figures"],
        ["BN story.key_facts", "label/value = bn_sanitised EN key_fact; original = Bangla fact line"],
        ["BN story.what_happened", "v2 fact_lines"],
        ["BN story.exam_qa", "sanitised v2 Q&A incl. the Bangla why-QA as one of exactly 2 (renovated-archive standard)"],
        ["BN english_fallback_allowed", "False -- renovated-archive contract, repo validator requires it"],
        ["BN story.recall_cards", "first 2 fact lines: first Bangla number blanked"],
        ["BN story.detail", "focus_paragraph (score-3) sanitised, else fact_lines joined"],
        ["words / phrases / revision_words", "verbatim from vocab-<date>.json (phrase ex2 repaired when empty -- see repairs)"],
        ["mcqs 1-10 Vocabulary", "generated from vocab: 'What does X mean?', correct = English definition, distractors = 3 other definitions (longer preferred)"],
        ["mcqs 11-12 Phrases", "generated from phrases: 'What does the phrase X mean?', correct = English explanation, distractors = 3 other explanations"],
        ["mcqs 13-25 Current Affairs", "v2 MCQs filtered + round-robin one per story (see mcq section)"],
        ["mcq.explanation (EN)", "CA: 'Correct answer: <key>. Source: <source quote, <=300 chars>'; vocab/phrase: definition + verbatim example"],
        ["mcq BN overlay", "CA: sanitised stem/options/why_wrong[key]; vocab/phrase: Bangla question + Bangla meanings as options"],
        ["sources[]", "one per story: S01.., publication, headline, article_date, URL"],
        ["index entry", "live index.json copied, entry appended (stories 15, sources 15, DRY RUN review text)"],
    ]
    report["bn"] = {
        "headline": "v2 headline as-is, bn_sanitised only (digits->Bangla, months->Bangla, Tk->টাকা, hyphen-suffix fixed). NOT translated: an English headline stays English in the BN overlay.",
        "exam_qa_recall": "BN exam_qa/recall_cards are derived from the v2 Bangla fact lines and the (mixed-language) v2 Q&A, sanitised. English words remain where v2 has no Bangla text; the validators only forbid Latin digits, English months, Tk and hyphen-suffixes, which the sanitiser removes.",
        "consequence": "In Bengali mode the user sees genuine Bangla for summary/exam_facts/figures/what_happened/detail, but exam_qa answers and key_fact labels may still read English where v2 never produced Bangla text. The items file (next run) narrows this to key_fact labels only.",
    }

    # --- write staging files ----------------------------------------------
    staging_dir.mkdir(parents=True, exist_ok=True)
    save_json(staging_dir / f"data-{day_iso}.json", data)
    save_json(staging_dir / f"bn-{day_iso}.json", bn)
    save_json(staging_dir / f"index-{day_iso}.json", index)
    save_json(staging_dir / f"conversion-report-{day_iso}.json", report)
    md = render_report_md(report, data, stories_en, story_notes)
    (staging_dir / f"conversion-report-{day_iso}.md").write_text(
        md, encoding="utf-8")
    log(f"wrote {staging_dir}/data-{day_iso}.json, bn-{day_iso}.json, "
        f"index-{day_iso}.json, conversion-report-{day_iso}.json/.md")
    failed = [c for c in checks if not c["ok"]]
    log(f"self-checks: {len(checks) - len(failed)}/{len(checks)} passed"
        + (f"; FAILING: {[c['check'] for c in failed]}" if failed else ""))
    return report, data, bn, index


def render_report_md(report, data, stories_en, story_notes):
    lines = [f"# Conversion report — v2 -> app, {report['date']}",
             "",
             "Staging only. Nothing published, synced or switched live.",
             "",
             "## Editorial decision",
             "",
             f"- **{report['editorial']['decision']}**",
             f"- Why: {report['editorial']['why']}",
             f"- Dropped news item: {report['editorial']['dropped_news_item']['id']} "
             f"— “{report['editorial']['dropped_news_item']['headline']}” "
             f"({report['editorial']['dropped_news_item']['reason']}).",
             f"- Editorial carried as {data['stories'][-1]['id']}: "
             f"“{report['editorial']['editorial_headline']}” "
             f"({report['editorial']['editorial_source']}).",
             "",
             "## MCQ selection",
             "",
             f"- Letters: {report['mcq']['letters']} (target A6/B6/C6/D7, "
             f"seeded shuffle).",
             f"- Longest-correct: {report['mcq']['longest_correct']}/25 "
             f"(MCQs {report['mcq']['longest_correct_nos']}).",
             f"- Current Affairs: {len(report['mcq']['ca_selected'])} selected, "
             f"{len(report['mcq']['ca_dropped'])} dropped by the filters.",
             "- Dropped CA MCQs:",
             ]
    for d in report["mcq"]["ca_dropped"]:
        lines.append(f"  - {d['id']} ({d['story']}): {d['reason']}")
    lines += ["",
              "## EN summary rendering — examples (rendered from facts_en quotes)",
              ""]
    for s in stories_en[:3]:
        lines.append(f"### {s['id']}: {s['headline']}")
        lines.append("")
        lines.append(f"Summary: {s['summary']}")
        lines.append("")
        lines.append(f"Exam facts: {s['exam_facts'][:400]}")
        lines.append("")
    lines += ["## Fields left empty",
              ""]
    for e in report["empty_fields"]:
        lines.append(f"- **{e['field']}** — {e['why']}")
    lines += ["",
              "## Repairs made by the converter",
              ""]
    for r in report["repairs"]:
        lines.append(f"- {r}")
    if not report["repairs"]:
        lines.append("- (none)")
    lines += ["",
              "## What the converter CANNOT meet honestly",
              ""]
    for u in report["unmeetable"]:
        lines.append(f"- **{u['requirement']}** — {u['why']}")
    lines += ["",
              "## Self-checks",
              ""]
    for c in report["self_checks"]:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'} {c['check']}"
                     + (f" — {c['detail']}" if c['detail'] else ""))
    lines += ["",
              "## Per-story notes",
              ""]
    for ca in sorted(story_notes):
        if story_notes[ca]:
            lines.append(f"- {ca}: {'; '.join(story_notes[ca])}")
    lines += ["",
              "## Mapping table (v1 field <- v2 source)",
              ""]
    for row in report["mapping"]:
        lines.append(f"- **{row[0]}** <- {row[1]}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert a v2 run to app-format edition files (staging only).")
    ap.add_argument("--date", required=True, help="edition date YYYY-MM-DD")
    ap.add_argument("--run-dir", default="",
                    help="v2 run dir (default runs/<date>)")
    ap.add_argument("--staging", default="",
                    help="staging dir (default runs/<date>/app-format)")
    ap.add_argument("--learning-modules", action="store_true",
                    help="opt-in ONLY: attach the 11-section learning_module "
                         "(v2) to every story and set renovation_format "
                         "'learning-module-v2'. Default OFF -- the live "
                         "daily path never passes this flag.")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir) if args.run_dir else HERE / "runs" / args.date
    staging = Path(args.staging) if args.staging else run_dir / "app-format"
    report, _data, _bn, _index = convert(args.date, run_dir, staging,
                                         learning_modules=args.learning_modules)
    failed = [c for c in report["self_checks"] if not c["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
