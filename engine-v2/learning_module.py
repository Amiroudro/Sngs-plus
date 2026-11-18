#!/usr/bin/env python3
"""Deterministic learning-module (v2) builder — Sarangsho Plus engine v2.

Builds the per-story ``learning_module`` in the 11-section model of
``renovation/LEARNING_MODULE_MODEL_V2.md`` (confirmed by Rudro
2026-11-18 02:00; ``exam_notes`` dropped, ``news_summary.source`` an
explicit object). Edition key: ``renovation_format`` =
``"learning-module-v2"``.

Sections, in order: hero, news_summary, verified_facts, topic_gk,
institutions, extra_knowledge, mcq_practice, written_prep, vocabulary,
revision, deep_prep.

Honesty rules (the engine NEVER invents):
  * News facts come only from the story's own pipeline data
    (``facts_en`` / ``key_facts`` / ``exam_qa`` / ``recall_cards`` /
    Step 8 MCQs / Step 10 words). Nothing else is added as news.
  * GK (``topic_gk`` / ``institutions`` / ``extra_knowledge``) comes
    only from the curated, sourced knowledge file
    ``engine-v2/rules/gk_knowledge.json``. A story whose topic has no
    entry there gets the per-section marker string
    ``"যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"`` — never a guess.
  * ``mcq_practice`` is exactly 4 per story, built in tiers (first
    tier that fills wins per slot): (1) usable Step 8 MCQs (same
    filters as ``convert_to_app.mcq_filters``, replicated here so
    this module stays importable without the converter); (2)
    synthesised from the story's own numeric fact values (correct
    = a verified fact value; distractors = other values from the
    same story, or computed +/- perturbations of the correct
    value); (3a) cloze on extra numbers inside a verified quote
    (the number blanked, never a year / a number glued to a name
    like COP31 / Dinajpur-2 / FY26, never a number that occurs
    twice in its quote); (3b) the story's own Step 8 Q&A, whose
    source quote must still trace to the story (sidebar
    boilerplate the converter dropped is excluded), distractors
    from other stories' Q&A answers; (3c) the story's own recall
    cards; (3d) metadata questions (publication / article date /
    section / headline), every correct answer copied verbatim from
    the edition file itself; the date question's wrong options are
    other stories' dates first, then neighbouring calendar dates
    when the edition has too few distinct dates (distractors are
    wrong answers by design, like the +/- perturbations in Tier 2).
    The editorial story uses the mechanical
    set (main argument + publication + date + section).
    Every candidate, from every tier, is rejected when the
    question gives the answer away (the answer inside the
    question, its number inside the question, or question and
    answer near-duplicates) — a story whose only questions are
    of that shape falls through to the honest metadata floor
    instead of a fake quiz. Every emitted MCQ is re-verified by
    the gate: its correct answer must trace to the story's own
    text.
  * ``vocabulary`` reuses the edition's Step 10 words only, matched
    by the word's ``Article headline`` (exact match on the story
    headline) or by its ``Direct source URL`` (== the story's source
    URL). Most page stories match 0 words — the list is then short
    or empty, never padded with invented words. Synonyms/antonyms
    come from ``engine-v2/rules/enrichment.json`` when the headword
    is in it, else empty lists.
  * ``written_prep`` / ``revision`` / ``deep_prep`` reuse the story's
    own Q&A, analytical questions (Step 8), fact lines and category;
    questions that have no story-specific source use a labelled
    generic template whose OUTLINE is always the story's own facts.
    Every template use is recorded in the build notes the converter
    writes into its report.

Stdlib only. No import of the converter (avoids a cycle: the
converter imports this module) and no import of v1 (frozen).
"""
import copy
import json
import random
import re
import unicodedata
from datetime import date as _date, timedelta as _timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GK_PATH = HERE / "rules" / "gk_knowledge.json"
ENRICHMENT_PATH = HERE / "rules" / "enrichment.json"

MARKER = "যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"
RENOVATION_FORMAT = "learning-module-v2"
SECTION_KEYS = ("hero", "news_summary", "verified_facts", "topic_gk",
                "institutions", "extra_knowledge", "mcq_practice",
                "written_prep", "vocabulary", "revision", "deep_prep")

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
LATIN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
BN_MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
             "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
_ZERO_WIDTH = ("\u200b", "\u200c", "\u200d", "\ufeff")
STOPWORDS = set("""a an the of in on at to for and or by with from as is are was were
be been it its this that these those after before over under into about has
have had will would can could should may might not no nor but if then than
so such only own same too very just also more most other some any each when
while who whom which what how why always never""".split())
_FORBIDDEN_OPTIONS = ("সবগুলো", "কোনোটিই নয়", "কোনোটিই না", "সবগুলোই")
_NEG_STEM_RE = re.compile(r"\b(not|never|except|incorrect)\b", re.IGNORECASE)
_NEG_STEM_BN_RE = re.compile(r"(^|\s)নয়(\s|\?|$)")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_UNIT_WORDS = ("crore", "lakh", "thousand", "million", "billion",
               "percent", "%", "taka", "tk")
_BN_UNIT = {"crore": "কোটি", "lakh": "লাখ", "thousand": "হাজার",
            "million": "মিলিয়ন", "billion": "বিলিয়ন", "percent": "%",
            "%": "%", "taka": "টাকা", "tk": "টাকা"}

# Generic related-topic titles, by app category (titles only, no
# factual claims — used only when the story has no GK entry with its
# own deep_prep list). Curated by hand, 2026-11-18.
DEEP_PREP_BY_CATEGORY = {
    "Economy & Banking": ["বাংলাদেশের বাজেট প্রক্রিয়া",
                          "বাংলাদেশ ব্যাংক ও মুদ্রানীতি",
                          "মুদ্রাস্ফীতি: কারণ ও প্রতিকার",
                          "বৈদেশিক বাণিজ্য ও রপ্তানি",
                          "রাজস্ব নীতি ও কর ব্যবস্থা",
                          "উন্নয়ন প্রকল্প ও এডিপি"],
    "Bangladesh": ["বাংলাদেশের সংবিধান ও রাষ্ট্রব্যবস্থা",
                   "বাংলাদেশের ভূগোল ও নদ-নদী",
                   "বাংলাদেশের অর্থনীতি এক নজরে",
                   "বাংলাদেশের ইতিহাস: মুক্তিযুদ্ধ",
                   "স্থানীয় সরকার ব্যবস্থা",
                   "বাংলাদেশের শিক্ষা ব্যবস্থা"],
    "Jobs & Education": ["বিসিএস পরীক্ষার সিলেবাস",
                         "ব্যাংক নিয়োগ পরীক্ষার প্রস্তুতি",
                         "বাংলাদেশের শিক্ষা ব্যবস্থা",
                         "চাকরির পরীক্ষায় সাম্প্রতিক ঘটনা",
                         "ইংরেজি ভোকাবুলারি: পরীক্ষার শব্দ",
                         "সাধারণ জ্ঞান: বাংলাদেশ বিষয়াবলি"],
    "World": ["জাতিসংঘ ও আন্তর্জাতিক সংস্থা",
              "বিশ্ব অর্থনীতি ও বাণিজ্য",
              "জলবায়ু পরিবর্তন ও পরিবেশ",
              "আন্তর্জাতিক সম্পর্কের মূল ধারণা",
              "বিশ্বের গুরুত্বপূর্ণ চুক্তি ও সম্মেলন",
              "দক্ষিণ এশিয়ার রাজনীতি"],
    "Politics": ["বাংলাদেশের সংবিধান",
                 "নির্বাচন ব্যবস্থা ও গণতন্ত্র",
                 "রাজনৈতিক দল ও আন্দোলন",
                 "স্থানীয় সরকার ও প্রশাসন",
                 "আন্তর্জাতিক সম্পর্কের মূল ধারণা",
                 "মানবাধিকার ও সুশাসন"],
    "Technology": ["তথ্যপ্রযুক্তি ও ডিজিটাল বাংলাদেশ",
                   "কৃত্রিম বুদ্ধিমত্তা: প্রাথমিক ধারণা",
                   "সাইবার নিরাপত্তা",
                   "বিজ্ঞান ও প্রযুক্তির সাম্প্রতিক অগ্রগতি",
                   "মোবাইল ব্যাংকিং ও ফিনটেক",
                   "পরিবেশবান্ধব প্রযুক্তি"],
    "Editorial & Opinion": ["মতামত ও সম্পাদকীয় লেখার কৌশল",
                            "ফোকাস রাইটিং: যুক্তি ও পাল্টা যুক্তি",
                            "বাংলাদেশের ইতিহাস: মুক্তিযুদ্ধ",
                            "সমসাময়িক বাংলাদেশ: আলোচিত বিষয়",
                            "রচনা ও প্রবন্ধ লেখার নিয়ম",
                            "বিতর্ক ও যুক্তিবিদ্যা"],
}


def log(msg):
    print(f"[learning-module] {msg}")


def clean(text):
    """Strip zero-width chars, collapse whitespace. No content change."""
    t = unicodedata.normalize("NFC", str(text or ""))
    for ch in _ZERO_WIDTH:
        t = t.replace(ch, "")
    return re.sub(r"\s+", " ", t).strip()


def norm(text):
    """Normalised text for comparisons: NFC, Bangla->Latin digits."""
    return re.sub(r"\s+", " ", clean(text).translate(LATIN_DIGITS)).strip().lower()


def to_bn_digits(text):
    return clean(text).translate(BN_DIGITS)


def bn_date(iso):
    """ISO date -> Bangla date ('2026-11-15' -> '১৫ নভেম্বর ২০২৬')."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", clean(iso or ""))
    if not m:
        return ""
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        _date(y, mo, d)
    except ValueError:
        return ""
    return (f"{str(d).translate(BN_DIGITS)} {BN_MONTHS[mo - 1]} "
            f"{str(y).translate(BN_DIGITS)}")


def content_words(text):
    toks = re.findall(r"[a-z0-9'\u0980-\u09FF]+", clean(text).lower())
    out = []
    for t in toks:
        t = t.strip("'")
        if len(t) >= 4 and t not in STOPWORDS:
            out.append(t)
    return out


def _num_of(text):
    """First number token in text, as float + its raw string, or None."""
    m = _NUM_RE.search(clean(text or ""))
    if not m:
        return None
    raw = m.group(0).rstrip(",.")
    try:
        return float(raw.replace(",", "")), raw
    except ValueError:
        return None


def bn_value(value, unit="", quote=""):
    """A story value rendered in Bangla: digits -> Bangla digits,
    unit word -> Bangla unit, currency from the quote context
    ('Tk' -> টাকা, '$' -> ডলার). ``value`` may already carry its
    unit ('20,160 crore'); ``unit`` is the separate facts_en unit
    when the caller has it. Returns '' when there is no number."""
    text = clean(value or "")
    m = _NUM_RE.search(text)
    if not m:
        return to_bn_digits(text)
    raw = m.group(0).rstrip(",.")
    rest = clean(text[m.end():]).lower()
    unit_word = (clean(unit or "").lower() or
                 (rest.split()[0] if rest.split() else ""))
    unit_word = unit_word.rstrip(".,")
    bn_unit = _BN_UNIT.get(unit_word, "")
    out = raw.translate(BN_DIGITS)
    if bn_unit:
        out += " " + bn_unit
    q = clean(quote or "")
    # Currency only when the value is money (a unit is present or the
    # quote carries a currency marker next to this number).
    if bn_unit or unit_word:
        if re.search(r"\bTk(?![A-Za-z])", q):
            out += " টাকা"
        elif "$" in q or "US$" in q:
            out += " ডলার"
    return out


def _split_sentences(text):
    """Split Bangla/English prose into sentences on । . ! ? boundaries."""
    parts = re.split(r"(?<=[।.!?])\s+", clean(text))
    return [p for p in parts if p]


def _clean_fact_line(line):
    """Minimal cleanup of a v2 Bangla fact line (Step 6 telegraphic
    output): drop the stray '(:' artefact and collapse spaces.
    No words are added, removed or reordered here."""
    t = clean(line)
    t = t.replace("(:", "").replace(" :", "")
    t = re.sub(r"\s+([।,])", r"\1", t)
    return clean(t)


# ---------------------------------------------------------------------------
# Curated knowledge + enrichment
# ---------------------------------------------------------------------------

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_gk_entries(path=GK_PATH):
    """GK knowledge entries (list). Missing file -> no entries (every
    GK section then gets the marker); a corrupt file is an error."""
    p = Path(path)
    if not p.exists():
        return []
    doc = load_json(p)
    if isinstance(doc, dict):
        return doc.get("entries", []) or []
    return doc or []


def load_enrichment(path=ENRICHMENT_PATH):
    """Step 10 enrichment bank: {'words': {headword: {...}},
    'phrases': {...}}. Missing file -> empty bank."""
    p = Path(path)
    if not p.exists():
        return {"words": {}, "phrases": {}}
    doc = load_json(p)
    if isinstance(doc, dict):
        return {"words": doc.get("words", {}) or {},
                "phrases": doc.get("phrases", {}) or {}}
    return {"words": {}, "phrases": {}}


def find_gk_entry(headline, topic, entries):
    """First entry whose headline keywords all appear (case-insensitive
    substring) in the headline. No entry -> None (marker)."""
    hl = clean(headline or "").lower()
    for e in entries or []:
        match = (e or {}).get("match", {}) or {}
        kws = [str(k).lower() for k in match.get("headline_keywords", [])]
        if kws and all(k in hl for k in kws):
            return e
    return None


def _enrichment_words(entry, headword):
    """Synonyms/antonyms lists for a headword from the enrichment
    bank. 'No direct antonym' / empty -> []."""
    if not isinstance(entry, dict):
        return [], []
    def _split(raw):
        if not raw:
            return []
        parts = [p.strip() for p in re.split(r"[;,]", str(raw)) if p.strip()]
        return [p for p in parts
                if p.lower() not in ("no direct antonym", "none", "-")]
    return (_split(entry.get("synonyms")),
            _split(entry.get("antonyms")))


# ---------------------------------------------------------------------------
# Step 8 MCQs (usable subset) — replica of convert_to_app.mcq_filters
# ---------------------------------------------------------------------------

def _stem_core(stem):
    core = re.sub(r"\s*\([^)]*অনুযায়ী\)\s*\??\s*$", "", clean(stem))
    core = re.sub(r"\s*(কত|কী|কবে|কোনটি)\s*\??\s*$", "", core).strip()
    return core


def _usable_step8_mcqs(item_id, questions, page_items, articles):
    """Usable Step 8 MCQs for one page item, in Step 8 order.
    Replica of convert_to_app.mcq_filters + the per-story dedupe in
    select_ca_mcqs (kept here so this module stays importable without
    the converter; the gate re-verifies every emitted MCQ traces to
    its story, so a drift here would fail the gate, not ship)."""
    by_id = {it.get("id"): it for it in page_items or []}
    story = by_id.get(item_id)
    if story is None:
        return []
    pool = [m for m in (questions or {}).get("mcq", [])
            if str(m.get("id", "")).rsplit("-mcq", 1)[0] == item_id]
    story_quotes = [norm(f.get("quote", ""))
                    for f in story.get("facts_en", [])]
    usable, seen_stem, seen_opts = [], set(), set()
    for m in pool:
        stem = clean(m.get("stem", ""))
        if "<" in stem or ">" in stem:
            continue
        if not stem.endswith("?") or len(stem) < 12:
            continue
        opts = m.get("options", {}) or {}
        vals = [clean(opts.get(k, "")) for k in ("ক", "খ", "গ", "ঘ")]
        if not vals[0] or len({norm(v) for v in vals}) != 4:
            continue
        if any(any(f in v for f in _FORBIDDEN_OPTIONS) for v in vals):
            continue
        quote = clean(m.get("source_quote", ""))
        if not quote:
            continue
        qn = norm(quote)
        if not any(qn and (qn in q or q in qn) for q in story_quotes):
            continue
        shared = False
        for other in page_items or []:
            if other.get("id") == item_id:
                continue
            oq = [norm(f.get("quote", ""))
                  for f in other.get("facts_en", [])]
            if any(qn and (qn in q or q in qn) for q in oq):
                shared = True
                break
        if shared:
            continue
        core = _stem_core(stem)
        core_toks = set(content_words(core))
        if len(core_toks) >= 5:
            hit = False
            for art in articles or []:
                if art.get("id") == item_id:
                    continue
                title_toks = set(content_words(art.get("title", "")))
                if title_toks and len(core_toks & title_toks) / len(core_toks) >= 0.7:
                    hit = True
                    break
            if hit:
                continue
        stem_n = norm(stem)
        opts_key = tuple(norm(opts.get(k, "")) for k in ("ক", "খ", "গ", "ঘ"))
        if stem_n in seen_stem or opts_key in seen_opts:
            continue
        seen_stem.add(stem_n)
        seen_opts.add(opts_key)
        usable.append(m)
    return usable


def _other_story_values(facts):
    """All (number, unit) pairs in a story's facts_en, in order."""
    out = []
    for f in facts or []:
        v = _num_of(f.get("value", ""))
        if v is None:
            continue
        unit = clean(f.get("unit", ""))
        out.append((v[0], v[1], unit, clean(f.get("quote", ""))))
    return out


def _perturb_options(number, raw, unit, quote):
    """Computed wrong answers: -10%, +10%, +20% of the correct number.
    Percents keep 2 decimals; whole money keeps integers. These are
    arithmetic distractors, not facts — they are wrong by
    construction, which is what an MCQ option must be."""
    out = []
    for factor in (0.9, 1.1, 1.2):
        val = number * factor
        if "%" in (unit or "") or (unit or "").lower() == "percent":
            txt = f"{val:.2f}"
        elif abs(val - round(val)) < 0.005:
            txt = f"{int(round(val)):,}"
        else:
            txt = f"{val:,.2f}".rstrip("0").rstrip(".")
        out.append(bn_value(txt, unit, quote))
    return out


def _to_v2_mcq(question, options_bn, correct_idx, explanation):
    return {"question": clean(question), "options": options_bn,
            "correct": int(correct_idx),
            "explanation": clean(explanation)}


def _synthesise_mcq(fact, story_values):
    """One MCQ from a facts_en entry: stem = the fact's 'what' clause
    + ' কত (date অনুযায়ী)?' (the same cloze pattern Step 8 itself
    uses); correct = the fact's value in Bangla; distractors = other
    same-unit values from the same story first, else computed
    perturbations. Returns None when the fact cannot yield 4
    distinct options."""
    what = clean(fact.get("what", ""))
    quote = clean(fact.get("quote", ""))
    value = clean(fact.get("value", ""))
    unit = clean(fact.get("unit", ""))
    fdate = clean(fact.get("date", ""))
    parsed = _num_of(value)
    if not what or not quote or parsed is None:
        return None
    number, _raw = parsed
    correct_bn = bn_value(value, unit, quote)
    if not correct_bn:
        return None
    # Same-unit distractors from the story's own facts.
    distract = []
    for (n2, _r2, u2, _q2) in story_values:
        if n2 == number:
            continue
        if clean(u2).lower() != clean(unit).lower():
            continue
        cand = bn_value(_r2, u2, _q2)
        if cand and cand != correct_bn and cand not in distract:
            distract.append(cand)
        if len(distract) >= 3:
            break
    if len(distract) < 3:
        for cand in _perturb_options(number, _raw, unit, quote):
            if cand != correct_bn and cand not in distract:
                distract.append(cand)
            if len(distract) >= 3:
                break
    if len(distract) < 3:
        return None
    stem = what
    if not stem.endswith("?"):
        stem = stem.rstrip("…").rstrip(".")
        stem = f"{stem} কত"
        if _ISO_RE.match(fdate or ""):
            stem += f" ({bn_date(fdate)} অনুযায়ী)?"
        else:
            stem += "?"
    explanation = (f"সঠিক উত্তর: {correct_bn}। "
                   f"উৎসের উদ্ধৃতি: {quote[:200]}")
    return _to_v2_mcq(stem, [correct_bn] + distract[:3], 0, explanation)


def _quote_numbers(quote):
    """Numbers inside one verified quote, as (float, raw, unit,
    num_start, num_end) on the cleaned quote. Only standalone
    numbers: a number glued to letters or a hyphen (COP31,
    Dinajpur-2, FY26, 2025-26, Tk358-cr) is part of a name or a
    date, not a fact. Years (1900-2100) and 0/1 are skipped.
    Bangla digits are normalised to Latin first (positions are
    unchanged: the translation is 1 digit -> 1 digit)."""
    text = clean(quote).translate(LATIN_DIGITS)
    out = []
    for m in re.finditer(
            r"(?<![A-Za-z0-9\u0980-\u09FF-])"
            r"(\d[\d,]*(?:\.\d+)?)"
            r"(?![A-Za-z0-9\u0980-\u09FF-])"
            r"\s*(crore|lakh|thousand|million|billion|percent|%)?",
            text):
        raw = m.group(1).rstrip(",.")
        try:
            number = float(raw.replace(",", ""))
        except ValueError:
            continue
        if number in (0, 1):
            continue
        if re.fullmatch(r"\d{4}", raw) and 1900 <= int(raw) <= 2100:
            continue
        unit = (m.group(2) or "").lower()
        out.append((number, raw, unit, m.start(1), m.end(1)))
    return out


def _synthesise_cloze(fact, story_values, quote_numbers):
    """Tier 3a: one MCQ per extra number inside a verified quote.
    The quote is the question, with the number blanked:
    '<quote with ______> — শূন্যস্থানে কত বসবে?' Correct = the
    number in Bangla; distractors = other same-unit numbers from
    the story, else computed perturbations. Skipped when the number
    occurs twice in its quote (the blank would give itself away),
    or the quote carries a negative-stem word."""
    quote = clean(fact.get("quote", ""))
    if not quote:
        return None
    if _NEG_STEM_RE.search(quote) or _NEG_STEM_BN_RE.search(quote):
        return None
    for (number, raw, unit, start, end) in quote_numbers:
        if clean(quote).translate(LATIN_DIGITS).count(raw) != 1:
            continue
        correct_bn = bn_value(raw, unit, quote)
        if not correct_bn:
            continue
        distract = []
        for (n2, _r2, u2, _q2) in story_values:
            if n2 == number or clean(u2).lower() != unit:
                continue
            cand = bn_value(_r2, u2, _q2)
            if cand and cand != correct_bn and cand not in distract:
                distract.append(cand)
            if len(distract) >= 3:
                break
        if len(distract) < 3:
            for (n2, r2, u2, _s2, _e2) in quote_numbers:
                if n2 == number or u2 != unit:
                    continue
                cand = bn_value(r2, u2, quote)
                if cand and cand != correct_bn and cand not in distract:
                    distract.append(cand)
                if len(distract) >= 3:
                    break
        if len(distract) < 3:
            for cand in _perturb_options(number, raw, unit, quote):
                if cand != correct_bn and cand not in distract:
                    distract.append(cand)
                if len(distract) >= 3:
                    break
        if len(distract) < 3:
            continue
        blanked = (clean(quote)[:start] + "______" +
                   clean(quote)[end:])
        question = blanked + " — শূন্যস্থানে কত বসবে?"
        explanation = (f"সঠিক উত্তর: {correct_bn}। "
                       f"উৎসের উদ্ধৃতি: {quote[:200]}")
        return _to_v2_mcq(question, [correct_bn] + distract[:3], 0,
                          explanation)
    return None


def _qa_is_junk(question, answer):
    """Junk filter for QA-based MCQs: UI text, markup, or an answer
    too short to be a question's answer."""
    text = (question or "") + " " + (answer or "")
    if "//" in text or "<" in text or ">" in text:
        return True
    if len(clean(answer or "")) < 10:
        return True
    if "[পটভূমি]" in (answer or ""):
        return True
    return False


def _qa_mcqs(item, en_story, ctx, used_values, seen_questions):
    """Tier 3b: MCQs from the story's own Step 8 Q&A (non-why).
    A record qualifies only when its source quote still traces to
    this story's (decontaminated) facts — sidebar boilerplate the
    converter dropped is excluded by that. Distractors are other
    stories' Q&A answers (same edition), preferring the same shape
    (numeric vs non-numeric)."""
    questions = ctx.get("questions") or {}
    page_items = ctx.get("page_items") or []
    item_id = item.get("id", "")
    story = next((it for it in page_items if it.get("id") == item_id), None)
    if story is None:
        return []
    story_quotes = [norm(f.get("quote", ""))
                    for f in story.get("facts_en", [])]
    other_quotes = []
    for other in page_items:
        if other.get("id") == item_id:
            continue
        other_quotes += [norm(f.get("quote", ""))
                         for f in other.get("facts_en", [])]
    own_qa = [q for q in questions.get("qa", [])
              if str(q.get("id", "")).rsplit("-qa", 1)[0] == item_id
              and clean(q.get("question", "")) !=
              "এই খবরটি কেন গুরুত্বপূর্ণ?"]
    pool = []
    for q in questions.get("qa", []):
        if str(q.get("id", "")).rsplit("-qa", 1)[0] == item_id:
            continue
        if clean(q.get("question", "")) == "এই খবরটি কেন গুরুত্বপূর্ণ?":
            continue
        ans = clean(q.get("answer", ""))
        if _qa_is_junk(q.get("question", ""), ans):
            continue
        pool.append(ans)
    out = []
    for q in own_qa:
        question = clean(q.get("question", ""))
        answer = clean(q.get("answer", ""))
        if not question.endswith("?") or _qa_is_junk(question, answer):
            continue
        if norm(question) in seen_questions:
            continue
        quote = clean(q.get("source_quote", ""))
        qn = norm(quote)
        if not quote or not any(
                qn and (qn in sq or sq in qn) for sq in story_quotes):
            continue
        if any(qn and (qn in sq or sq in qn) for sq in other_quotes):
            continue
        numeric = _num_of(answer) is not None
        # The correct answer is NEVER truncated: the gate requires it
        # to trace verbatim to the story text. (Distractors below may
        # be truncated — they only need to be recognisably wrong.)
        correct = bn_value(answer, "", quote) if numeric else answer
        if norm(correct) in used_values:
            continue
        distract = []
        for cand in pool:
            if norm(cand) in used_values or norm(cand) == norm(correct):
                continue
            cand_num = _num_of(cand) is not None
            if cand_num != numeric:
                continue
            disp = bn_value(cand, "", "") if cand_num else cand
            if len(disp) > 150:
                disp = disp[:150].rstrip() + "…"
            if disp not in distract and disp != correct:
                distract.append(disp)
            if len(distract) >= 3:
                break
        if len(distract) < 3:
            for cand in pool:
                if norm(cand) in used_values or norm(cand) == norm(correct):
                    continue
                disp = (bn_value(cand, "", "") if _num_of(cand) is not None
                        else cand)
                if len(disp) > 150:
                    disp = disp[:150].rstrip() + "…"
                if disp not in distract and disp != correct:
                    distract.append(disp)
                if len(distract) >= 3:
                    break
        if len(distract) < 3:
            continue
        explanation = f"সঠিক উত্তর: {correct}।"
        if quote:
            explanation += f" উৎস: {quote[:200]}"
        out.append(_to_v2_mcq(question, [correct] + distract[:3], 0,
                              explanation))
    return out


def _recall_mcqs(en_story):
    """Tier 3c: MCQs from the story's own recall cards (cloze with
    the answer blanked). Distractors are computed perturbations of
    the answer — the recall card itself establishes the answer."""
    out = []
    for rc in en_story.get("recall_cards", []) or []:
        cloze = clean(rc.get("cloze", ""))
        ans = clean(rc.get("answer", ""))
        if not cloze or "______" not in cloze or not ans:
            continue
        parsed = _num_of(ans)
        if parsed is None:
            continue
        number, _raw = parsed
        correct = bn_value(ans, "", cloze)
        distract = _perturb_options(number, _raw, "", cloze)
        distract = [d for d in distract if d != correct][:3]
        if len(distract) < 3:
            continue
        question = cloze + " — শূন্যস্থানে কত বসবে?"
        out.append(_to_v2_mcq(
            question, [correct] + distract, 0,
            f"সঠিক উত্তর: {correct}।"))
    return out


def _metadata_mcqs(en_story, edition_stories):
    """Tier 3d / editorial set: MCQs about the story's own metadata
    — publication, article date, section, headline. Every correct
    answer and every distractor is copied verbatim from the edition
    file itself, so nothing is invented. Last resort only."""
    src = (en_story.get("sources") or [{}])[0]
    pub = clean(src.get("publication", ""))
    headline = clean(en_story.get("headline", ""))
    category = clean(en_story.get("category", ""))
    art_date = bn_date(en_story.get("article_date", ""))
    others = [s for s in edition_stories or []
              if s.get("id") != en_story.get("id")]
    other_pubs = []
    for s in others:
        p = clean((s.get("sources") or [{}])[0].get("publication", ""))
        if p and p != pub and p not in other_pubs:
            other_pubs.append(p)
    other_dates = []
    for s in others:
        d = bn_date(s.get("article_date", ""))
        if d and d != art_date and d not in other_dates:
            other_dates.append(d)
    other_cats = []
    for s in others:
        c = clean(s.get("category", ""))
        if c and c != category and c not in other_cats:
            other_cats.append(c)
    other_headlines = [clean(s.get("headline", "")) for s in others]
    other_headlines = [t for t in other_headlines if t and t != headline]
    mcqs = []
    if pub and len(other_pubs) >= 3:
        mcqs.append(_to_v2_mcq(
            "এই খবরটি কোন প্রকাশনায় ছাপা হয়েছে?",
            [pub] + other_pubs[:3], 0, f"সঠিক উত্তর: {pub}।"))
    if art_date and len(other_dates) >= 3:
        mcqs.append(_to_v2_mcq(
            "এই খবরটি কোন তারিখে প্রকাশিত হয়েছে?",
            [art_date] + other_dates[:3], 0,
            f"সঠিক উত্তর: {art_date}।"))
    elif art_date:
        # Too few distinct other dates in this edition (most stories
        # share one publication date): fill the wrong options with
        # neighbouring calendar dates. Distractors are wrong answers
        # by design, like the +/- perturbations in Tier 2; the
        # correct answer stays verbatim from the edition file.
        distract_dates = list(other_dates)
        iso = clean(en_story.get("article_date", ""))
        if _ISO_RE.match(iso or ""):
            try:
                base = _date.fromisoformat(iso)
            except ValueError:
                base = None
            if base is not None:
                for delta in (1, -1, 2, -2):
                    d = bn_date((base + _timedelta(days=delta))
                                .isoformat())
                    if d and d != art_date and d not in distract_dates:
                        distract_dates.append(d)
                    if len(distract_dates) >= 3:
                        break
        if len(distract_dates) >= 3:
            mcqs.append(_to_v2_mcq(
                "এই খবরটি কোন তারিখে প্রকাশিত হয়েছে?",
                [art_date] + distract_dates[:3], 0,
                f"সঠিক উত্তর: {art_date}।"))
    if category and len(other_cats) >= 3:
        mcqs.append(_to_v2_mcq(
            "এই খবরটি কোন বিভাগের?",
            [category] + other_cats[:3], 0,
            f"সঠিক উত্তর: {category}।"))
    if headline and len(other_headlines) >= 3:
        mcqs.append(_to_v2_mcq(
            "এই খবরের শিরোনাম কী?",
            [headline] + other_headlines[:3], 0,
            f"সঠিক উত্তর: {headline}।"))
    return mcqs


def _editorial_mcqs(en_story, edition_stories):
    """The editorial slot's 4 mechanical MCQs: main argument (from
    its own summary), publication, headline, section — all copied
    verbatim from the edition file itself."""
    summary = clean(en_story.get("summary", "")).removeprefix("Opinion: ").strip()
    if not summary:
        summary = clean(en_story.get("headline", ""))
    others = [s for s in edition_stories or []
              if s.get("id") != en_story.get("id")]
    other_summaries = [clean(s.get("one_liner", "") or s.get("summary", ""))
                       for s in others]
    other_summaries = [t for t in other_summaries if t and t != summary]
    mcqs = []
    if summary and len(other_summaries) >= 3:
        mcqs.append(_to_v2_mcq(
            "এই সম্পাদকীয়ের মূল বক্তব্য কী?",
            [summary] + other_summaries[:3], 0,
            f"সঠিক উত্তর: {summary[:200]}"))
    mcqs.extend(_metadata_mcqs(en_story, edition_stories))
    return mcqs[:4]


def _is_degenerate(question, correct):
    """True when the question gives the answer away, so the MCQ
    tests nothing. Three shapes, all seen in real Step 8 output:
    (1) the correct answer appears inside the question stem
    (a Q&A answer that IS the headline the question quotes;
    a recall answer '31' when the question says 'COP31');
    (2) the answer's number appears in the stem even when the
    full answer does not (Bangla '২০,১৬০ কোটি টাকা' vs an
    English stem holding '20,160'); (3) question stem and answer
    are near-duplicates — one is a prefix of the other, or they
    share a >= 30-char common prefix (a Q&A answer that is the
    question minus its last word). Single-digit answers are
    exempt from the number check: '5' inside '5.43%' is a
    different number, not a leak."""
    q = clean(question or "").translate(LATIN_DIGITS)
    a = clean(correct or "").translate(LATIN_DIGITS)
    if len(a) < 2:
        return False
    # Strip the trailing "কী (date অনুযায়ী)?" tail before comparing.
    stem = re.sub(r"\s*কী\s*(\([^)]*\))?\s*\??\s*$", "", q)
    stem = re.sub(r"\s*কত\s*(\([^)]*\))?\s*\??\s*$", "", stem)
    if not stem:
        return False
    if a in stem:
        return True
    parsed = _num_of(a)
    if parsed is not None:
        raw = parsed[1]
        if len(raw) >= 2 and raw in stem:
            return True
    if stem.startswith(a) or a.startswith(stem):
        return True
    n = 0
    for x, y in zip(stem, a):
        if x == y:
            n += 1
        else:
            break
    return n >= 30


def _build_mcq_practice(en_story, item, ctx):
    """Exactly 4 MCQs, in tiers (first tier that fills wins per slot):
    1. usable Step 8 MCQs; 2. synthesised from the story's own fact
    values; 3a. cloze on extra numbers inside a verified quote;
    3b. the story's own Q&A (quote must still trace to the story);
    3c. the story's own recall cards; 3d. metadata questions
    (publication / date / section / headline). Correct positions
    are a seeded shuffle of 0-3, so no position is used more than
    once."""
    notes = []
    if ctx.get("is_editorial"):
        mcqs = _editorial_mcqs(en_story, ctx.get("edition_stories"))
        notes.append(f"editorial mcq_practice: {len(mcqs)} mechanical "
                     "(argument/publication/headline/section)")
        if len(mcqs) != 4:
            notes.append("WARNING: editorial mcq_practice is short "
                         f"({len(mcqs)}/4) — fewer than 3 other stories "
                         "carry distinct summaries/publications")
        return _place_correct(mcqs, ctx), notes
    questions = ctx.get("questions") or {}
    page_items = ctx.get("page_items") or []
    articles = ctx.get("articles") or []
    item_id = item.get("id", "")
    usable = _usable_step8_mcqs(item_id, questions, page_items, articles)
    facts = item.get("facts_en", []) or []
    story_values = _other_story_values(facts)
    used_fact_ids = set()
    mcqs = []
    used_values = set()
    seen_questions = set()
    degenerate_rejected = [0]

    def _accept(cand):
        if cand is None:
            return False
        if norm(cand["options"][cand["correct"]]) in used_values:
            return False
        if norm(cand["question"]) in seen_questions:
            return False
        if _is_degenerate(cand["question"],
                           cand["options"][cand["correct"]]):
            degenerate_rejected[0] += 1
            return False
        used_values.add(norm(cand["options"][cand["correct"]]))
        seen_questions.add(norm(cand["question"]))
        mcqs.append(cand)
        return True

    for m in usable:
        if len(mcqs) >= 4:
            break
        key = clean(m.get("key", "ক"))
        key_idx = {"ক": 0, "খ": 1, "গ": 2, "ঘ": 3}.get(key, 0)
        opts_v2 = m.get("options", {}) or {}
        quote = clean(m.get("source_quote", ""))
        vals = [clean(opts_v2.get(k, "")) for k in ("ক", "খ", "গ", "ঘ")]
        options_bn = [bn_value(v, "", quote) or v for v in vals]
        if len({norm(o) for o in options_bn}) != 4:
            continue
        why = (m.get("why_wrong", {}) or {}).get(key, "") or ""
        if "\ufffd" in why or not clean(why):
            why = f"সঠিক উত্তর: {options_bn[key_idx]}।"
        cand = _to_v2_mcq(m.get("stem", ""), options_bn, key_idx, why)
        if _accept(cand):
            used_fact_ids.add(clean(m.get("fact_id", "")))
    n_reused = len(mcqs)
    notes.append(f"mcq_practice: {n_reused} reused Step 8 MCQs")

    # Tier 2: fact values.
    for f in facts:
        if len(mcqs) >= 4:
            break
        fid = clean(f.get("fact_id", "")) or None
        if fid and fid in used_fact_ids:
            continue
        _accept(_synthesise_mcq(f, story_values))
        if fid:
            used_fact_ids.add(fid)
    # Tier 3a: extra numbers inside verified quotes.
    if len(mcqs) < 4:
        for f in facts:
            if len(mcqs) >= 4:
                break
            quote = clean(f.get("quote", ""))
            if not quote:
                continue
            cand = _synthesise_cloze(f, story_values,
                                      _quote_numbers(quote))
            _accept(cand)
    # Tier 3b: the story's own Q&A.
    if len(mcqs) < 4:
        for cand in _qa_mcqs(item, en_story, ctx, used_values,
                             seen_questions):
            if len(mcqs) >= 4:
                break
            _accept(cand)
    # Tier 3c: recall cards.
    if len(mcqs) < 4:
        for cand in _recall_mcqs(en_story):
            if len(mcqs) >= 4:
                break
            _accept(cand)
    # Tier 3d: metadata (publication / date / section / headline).
    if len(mcqs) < 4:
        for cand in _metadata_mcqs(en_story, ctx.get("edition_stories")):
            if len(mcqs) >= 4:
                break
            _accept(cand)
    notes.append(f"mcq_practice: {len(mcqs)}/4 after synthesis tiers "
                 f"(reused {n_reused})")
    if degenerate_rejected[0]:
        notes.append(f"mcq_practice: {degenerate_rejected[0]} candidate(s) "
                     "rejected — the question gave the answer away "
                     "(answer inside the question, or near-duplicate)")
    return _place_correct(mcqs, ctx), notes


def _place_correct(mcqs, ctx):
    """Assign correct positions by a seeded shuffle of 0..3 so no
    position is used more than once across the 4. Returns the MCQs
    in order with options reordered to match."""
    seed = f"{ctx.get('date', '')}-{ctx.get('ca_id', '')}"
    rng = random.Random(seed)
    positions = list(range(min(4, len(mcqs))))
    while len(positions) < 4:
        positions.append(len(positions))
    rng.shuffle(positions)
    out = []
    for i, m in enumerate(mcqs):
        if i >= 4:
            break
        opts = list(m["options"])
        correct_text = opts[m["correct"]]
        rest = [o for j, o in enumerate(opts) if j != m["correct"]]
        pos = positions[i]
        new_opts = rest[:pos] + [correct_text] + rest[pos:]
        new_opts = new_opts[:4]
        out.append({"question": m["question"], "options": new_opts,
                    "correct": pos, "explanation": m["explanation"]})
    return out


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_hero(en_story, item, ctx):
    headline = clean(en_story.get("headline", ""))
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*%", headline)
    if m:
        figure = m.group(1).translate(BN_DIGITS) + "%"
        label = headline[:m.start()] + headline[m.end():]
        label = clean(label)
        label = re.sub(r"\s(of|at|to|for|on)\s+(in|on|at|to|for)\b",
                       r" \2", label)
        label = clean(label).strip(" ,—-")
        return {"figure": figure, "label": label or headline}
    for kf in en_story.get("key_facts", []) or []:
        val = clean(kf.get("value", ""))
        if _num_of(val) is None:
            continue
        quote = clean(kf.get("original", ""))
        figure = bn_value(val, "", quote)
        label = clean(kf.get("label", "")).rstrip("…").strip()
        label = " ".join(label.split()[:10])
        return {"figure": figure, "label": label or headline}
    if ctx.get("is_editorial"):
        return {"figure": "মতামত", "label": headline}
    return {"figure": to_bn_digits(en_story.get("article_date", "")),
            "label": headline}


def _build_news_summary(en_story, bn_story, item, ctx):
    if ctx.get("is_editorial"):
        text = clean(bn_story.get("summary", "") or
                     en_story.get("summary", ""))
    else:
        lines = [_clean_fact_line(ln)
                 for ln in (item.get("fact_lines", []) or [])]
        lines = [ln for ln in lines if ln]
        hero_fig = ""
        hero = ctx.get("_hero") or {}
        if hero.get("figure"):
            hero_fig = clean(hero["figure"]).translate(LATIN_DIGITS)
            hero_fig = hero_fig.replace(" ", "")
        if hero_fig:
            lines.sort(key=lambda ln: 0 if hero_fig in
                       clean(ln).translate(LATIN_DIGITS).replace(" ", "")
                       else 1)
        text = " ".join(lines[:4])
        if not text:
            text = clean(en_story.get("summary", ""))
    src = (en_story.get("sources") or [{}])[0]
    url = clean(src.get("url", ""))
    if url and not url.startswith(("http://", "https://")):
        url = ""
    return {"text": text,
            "source": {"publication": clean(src.get("publication", "")),
                       "date": clean(en_story.get("article_date", "")),
                       "url": url}}


def _build_verified_facts(en_story, item, ctx):
    src = (en_story.get("sources") or [{}])[0]
    pub = clean(src.get("publication", ""))
    if ctx.get("is_editorial"):
        return [{"label": "মতামত", "value": pub or "মতামত",
                 "date": bn_date(en_story.get("article_date", "")),
                 "source": pub}]
    facts_by_value = {}
    for f in item.get("facts_en", []) or []:
        facts_by_value.setdefault(norm(f.get("value", "")), f)
    out = []
    for kf in en_story.get("key_facts", []) or []:
        val = clean(kf.get("value", ""))
        if not val:
            continue
        f = facts_by_value.get(norm(val.split()[0] if val.split() else val))
        quote = clean(kf.get("original", ""))
        unit = ""
        fdate = ""
        if f is not None:
            unit = clean(f.get("unit", ""))
            fdate = clean(f.get("date", ""))
            quote = clean(f.get("quote", "")) or quote
        value_bn = bn_value(val, unit, quote)
        if not value_bn:
            continue
        out.append({"label": clean(kf.get("label", "")).rstrip("…").strip()
                    or "তথ্য",
                    "value": value_bn,
                    "date": bn_date(fdate) or
                    bn_date(en_story.get("article_date", "")),
                    "source": pub})
    return out


def _build_gk_sections(en_story, ctx):
    entry = find_gk_entry(en_story.get("headline", ""),
                          en_story.get("category", ""),
                          ctx.get("gk_entries"))
    if entry is None:
        return MARKER, MARKER, MARKER, None
    return (copy.deepcopy(entry.get("topic_gk")),
            copy.deepcopy(entry.get("institutions")),
            copy.deepcopy(entry.get("extra_knowledge")),
            entry)


def _build_written_prep(en_story, bn_story, item, ctx):
    notes = []
    if ctx.get("is_editorial"):
        summary = clean(en_story.get("summary", "")).removeprefix("Opinion: ").strip()
        pub = clean((en_story.get("sources") or [{}])[0].get("publication", ""))
        short = {"question": "এই সম্পাদকীয়ের মূল বক্তব্য সংক্ষেপে লেখো।",
                 "outline": ([summary] if summary else []) +
                 ([f"প্রকাশনা: {pub}"] if pub else [])}
        analytical = {"question":
                      "এই মতামতের সঙ্গে আপনি কতটা একমত? যুক্তিসহ লেখো।",
                      "outline": ([summary] if summary else []) +
                      ([f"লেখাটি প্রকাশ করেছে: {pub}"] if pub else [])}
        return {"short": short, "analytical": analytical}, notes
    fact_lines = [_clean_fact_line(ln)
                  for ln in (item.get("fact_lines", []) or [])]
    fact_lines = [ln for ln in fact_lines if ln]
    short_outline = fact_lines[:3]
    if len(short_outline) < 2:
        short_outline = [clean(en_story.get("summary", ""))]
    short = {"question": "এই খবরের মূল তথ্যগুলো সংক্ষেপে লেখো।",
             "outline": short_outline}
    analytical = None
    for a in (ctx.get("questions") or {}).get("analytical", []) or []:
        if str(a.get("fact_id", "")).rsplit("-f", 1)[0] != item.get("id", ""):
            continue
        if str(a.get("id", "")).rsplit("-aq", 1)[0] != item.get("id", ""):
            continue
        answer = clean(a.get("answer", ""))
        answer = re.sub(r"^\[পটভূমি\]\s*", "", answer)
        answer = re.sub(r"^বিশ্লেষণ \(তথ্যের ভিত্তিতে, নতুন তথ্য নয়\):\s*",
                        "", answer)
        sents = [s for s in _split_sentences(answer) if s]
        sents = [re.sub(r"^\[পটভূমি\]\s*", "", s) for s in sents]
        sents = [s for s in sents if s]
        if a.get("question") and sents:
            analytical = {"question": clean(a.get("question")),
                          "outline": sents[:4]}
        break
    if analytical is None:
        why = clean(item.get("why_important", ""))
        why = re.sub(r"^\[পটভূমি\]\s*", "", why)
        outline = ([why] if why else []) + fact_lines[:2]
        outline = outline[:3]
        if len(outline) < 2:
            outline = fact_lines[:2] or [clean(en_story.get("summary", ""))]
        analytical = {"question": "এই খবরের প্রভাব ও তাৎপর্য বিশ্লেষণ করো।",
                      "outline": outline}
        notes.append("written_prep analytical: generic template question; "
                     "outline is the story's own facts")
    else:
        notes.append("written_prep analytical: Step 8 analytical question")
    return {"short": short, "analytical": analytical}, notes


def _build_vocabulary(en_story, ctx):
    notes = []
    words = ctx.get("vocab_words") or []
    src_url = clean((en_story.get("sources") or [{}])[0].get("url", ""))
    headline = clean(en_story.get("headline", ""))
    exact, by_url = [], []
    seen = set()
    for w in words:
        hw = clean(w.get("Headword / phrase", ""))
        if not hw or hw.lower() in seen:
            continue
        if clean(w.get("Article headline", "")) == headline:
            exact.append(w)
            seen.add(hw.lower())
        elif src_url and clean(w.get("Direct source URL", "")) == src_url:
            by_url.append(w)
            seen.add(hw.lower())
    matched = (exact + by_url)[:5]
    enrichment = (ctx.get("enrichment") or {}).get("words", {}) or {}
    out = []
    for w in matched:
        hw = clean(w.get("Headword / phrase", ""))
        example = clean(w.get("Original example", ""))
        if hw.lower() not in example.lower():
            notes.append(f"vocabulary: skipped '{hw}' — its example "
                         "does not contain the headword")
            continue
        syn, ant = _enrichment_words(enrichment.get(hw.lower()), hw)
        out.append({"word": hw,
                    "meaning_bn": clean(w.get("Bangla meaning", "")),
                    "example": example,
                    "synonyms": syn,
                    "antonyms": ant})
    notes.append(f"vocabulary: {len(out)} matched edition word(s) "
                 f"({len(exact)} by headline, {len(by_url)} by URL)")
    return out, notes


def _build_revision(en_story, bn_story, item, ctx, written_prep):
    notes = []
    flashcards = []
    seen_q = set()
    if ctx.get("is_editorial"):
        # The editorial slot has no Step 8 Q&A: its flashcards are its
        # own mechanical exam_qa (main argument / publication).
        for qa in en_story.get("exam_qa", []) or []:
            qq, aa = clean(qa.get("q", "")), clean(qa.get("a", ""))
            if qq and aa and norm(qq) not in seen_q:
                flashcards.append({"q": qq, "a": aa})
                seen_q.add(norm(qq))
    else:
        qa_all = [q for q in (ctx.get("questions") or {}).get("qa", [])
                  if str(q.get("id", "")).rsplit("-qa", 1)[0] == item.get("id", "")]
        qa_all = [q for q in qa_all
                  if clean(q.get("question", "")) != "এই খবরটি কেন গুরুত্বপূর্ণ?"]
        for q in qa_all[:4]:
            qq = clean(q.get("question", ""))
            aa = clean(q.get("answer", ""))
            if not qq or not aa or norm(qq) in seen_q:
                continue
            quote = clean(q.get("source_quote", ""))
            flashcards.append({"q": qq, "a": bn_value(aa, "", quote) or aa})
            seen_q.add(norm(qq))
            if len(flashcards) >= 4:
                break
    if len(flashcards) < 3:
        for rc in en_story.get("recall_cards", []) or []:
            if len(flashcards) >= 3:
                break
            cloze = clean(rc.get("cloze", ""))
            ans = clean(rc.get("answer", ""))
            if not cloze or "______" not in cloze or not ans:
                continue
            qq = cloze.replace("______", "কত", 1)
            if not qq.endswith("?"):
                qq += "?"
            if norm(qq) in seen_q:
                continue
            flashcards.append({"q": qq, "a": bn_value(ans, "", cloze) or ans})
            seen_q.add(norm(qq))
    if ctx.get("is_editorial") and len(flashcards) < 3:
        headline = clean(en_story.get("headline", ""))
        flashcards.append({"q": "এই সম্পাদকীয়ের শিরোনাম কী?",
                           "a": headline})
    next_rev = []
    if not ctx.get("is_editorial"):
        qa_all = [q for q in (ctx.get("questions") or {}).get("qa", [])
                  if str(q.get("id", "")).rsplit("-qa", 1)[0] == item.get("id", "")]
        qa_all = [q for q in qa_all
                  if clean(q.get("question", "")) != "এই খবরটি কেন গুরুত্বপূর্ণ?"]
        for q in qa_all[4:]:
            qq = clean(q.get("question", ""))
            if qq and norm(qq) not in seen_q:
                next_rev.append(qq)
            if len(next_rev) >= 2:
                break
    if len(next_rev) < 2:
        next_rev.append(written_prep["short"]["question"])
    if len(next_rev) < 2:
        next_rev.append(written_prep["analytical"]["question"])
    next_rev = next_rev[:2]
    notes.append(f"revision: {len(flashcards)} flashcards from the "
                 "story's own Q&A/recall cards")
    return {"flashcards": flashcards, "next_revision": next_rev}, notes


def _build_deep_prep(en_story, entry):
    if entry is not None and entry.get("deep_prep"):
        return list(entry["deep_prep"])[:6]
    bank = DEEP_PREP_BY_CATEGORY.get(clean(en_story.get("category", "")))
    if not bank:
        bank = DEEP_PREP_BY_CATEGORY["Bangladesh"]
    return list(bank)[:5]


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_module(en_story, bn_story, item, ctx):
    """Build the 11-section learning_module for one converted story.

    ``en_story`` / ``bn_story``: the converter's story dicts.
    ``item``: the v2 page item (facts_en / fact_lines / why_important)
    or, for the editorial slot, the editorial item dict with
    ``is_editorial`` set in ``ctx``.
    ``ctx``: {"questions", "vocab_words", "enrichment", "gk_entries",
    "page_items", "articles", "edition_stories", "date", "ca_id",
    "is_editorial"}.
    Returns (module_dict, notes_list)."""
    ctx = dict(ctx or {})
    notes = []
    hero = _build_hero(en_story, item, ctx)
    ctx["_hero"] = hero
    news_summary = _build_news_summary(en_story, bn_story, item, ctx)
    verified_facts = _build_verified_facts(en_story, item, ctx)
    topic_gk, institutions, extra_knowledge, entry = _build_gk_sections(
        en_story, ctx)
    if entry is None:
        notes.append("topic_gk/institutions/extra_knowledge: no GK entry "
                     "— per-section marker")
    else:
        notes.append(f"topic_gk/institutions/extra_knowledge: GK entry "
                     f"'{entry.get('id')}' (sourced)")
    mcqs, mcq_notes = _build_mcq_practice(en_story, item, ctx)
    notes.extend(mcq_notes)
    written_prep, wp_notes = _build_written_prep(en_story, bn_story, item, ctx)
    notes.extend(wp_notes)
    vocabulary, vocab_notes = _build_vocabulary(en_story, ctx)
    notes.extend(vocab_notes)
    revision, rev_notes = _build_revision(en_story, bn_story, item, ctx,
                                          written_prep)
    notes.extend(rev_notes)
    deep_prep = _build_deep_prep(en_story, entry)
    if entry is None:
        notes.append("deep_prep: category-templated titles (no GK entry)")
    module = {
        "hero": hero,
        "news_summary": news_summary,
        "verified_facts": verified_facts,
        "topic_gk": topic_gk,
        "institutions": institutions,
        "extra_knowledge": extra_knowledge,
        "mcq_practice": mcqs,
        "written_prep": written_prep,
        "vocabulary": vocabulary,
        "revision": revision,
        "deep_prep": deep_prep,
    }
    return module, notes


# ---------------------------------------------------------------------------
# Validation (single implementation: converter self-check + gate check 15
# + tests all call this)
# ---------------------------------------------------------------------------

def _nonempty_str(v):
    return isinstance(v, str) and bool(clean(v))


def _story_trace_text(en_story):
    """Everything a mcq_practice correct answer must trace to: the
    story's own figures, key facts, Q&A answers, summaries and
    sources (plus its dates, so a metadata date question traces).
    Digits are normalised to Latin for comparison."""
    parts = [en_story.get("headline", ""), en_story.get("summary", ""),
             en_story.get("exam_facts", ""), en_story.get("figures", ""),
             en_story.get("detail", ""), en_story.get("category", ""),
             en_story.get("event_date", ""),
             en_story.get("article_date", "")]
    for kf in en_story.get("key_facts", []) or []:
        parts += [kf.get("label", ""), kf.get("value", ""),
                  kf.get("original", "")]
    for qa in en_story.get("exam_qa", []) or []:
        parts += [qa.get("q", ""), qa.get("a", "")]
    for rc in en_story.get("recall_cards", []) or []:
        parts += [rc.get("cloze", ""), rc.get("answer", "")]
    for s in en_story.get("sources", []) or []:
        parts += [s.get("publication", ""), s.get("headline", "")]
    return norm(" ".join(parts))


def _traces_to_story(correct, en_story):
    """A correct option traces to the story when its number (if it
    carries one) appears among the story's numbers, or — for a
    number-free option — its normalised text appears in the story
    text (editorial mechanical MCQs: argument / publication /
    headline / section)."""
    text = _story_trace_text(en_story)
    c = norm(correct)
    nums = _NUM_RE.findall(c)
    if nums:
        story_nums = set(_NUM_RE.findall(text))
        return any(n.rstrip(",.") in story_nums for n in nums)
    return bool(c) and c in text


def validate_module(module, en_story, edition_word_headwords,
                    is_editorial=False):
    """Validate one learning_module against the v2 shape + trace rules.
    Returns a list of problem strings (empty == valid)."""
    problems = []
    if not isinstance(module, dict):
        return ["learning_module is not an object"]
    keys = list(module.keys())
    if keys != list(SECTION_KEYS):
        problems.append(
            f"section keys {keys} != the 11 v2 keys in order "
            f"{list(SECTION_KEYS)}")
    if "[example]" in json.dumps(module, ensure_ascii=False):
        problems.append("module contains '[example]'")
    hero = module.get("hero")
    if not isinstance(hero, dict):
        problems.append("hero is not an object")
    else:
        if not _nonempty_str(hero.get("figure")):
            problems.append("hero.figure empty")
        elif not is_editorial and not re.search(r"[০-৯]", hero["figure"]):
            problems.append("hero.figure has no Bangla digit "
                            f"({hero.get('figure')!r})")
        if not _nonempty_str(hero.get("label")):
            problems.append("hero.label empty")
    ns = module.get("news_summary")
    if not isinstance(ns, dict):
        problems.append("news_summary is not an object")
    else:
        if not _nonempty_str(ns.get("text")):
            problems.append("news_summary.text empty")
        src = ns.get("source")
        if not isinstance(src, dict):
            problems.append("news_summary.source is not an object")
        else:
            if not _nonempty_str(src.get("publication")):
                problems.append("news_summary.source.publication empty")
            if not _ISO_RE.match(clean(src.get("date", "")) or ""):
                problems.append("news_summary.source.date is not ISO "
                                f"({src.get('date')!r})")
            url = src.get("url", "")
            if not isinstance(url, str) or (
                    url and not url.startswith(("http://", "https://"))):
                problems.append("news_summary.source.url is not '' or "
                                f"http(s) ({str(url)[:60]!r})")
    vf = module.get("verified_facts")
    if not isinstance(vf, list) or not vf:
        problems.append("verified_facts is not a non-empty list")
    else:
        for i, f in enumerate(vf):
            if not isinstance(f, dict):
                problems.append(f"verified_facts[{i}] is not an object")
                continue
            if not _nonempty_str(f.get("label")):
                problems.append(f"verified_facts[{i}].label empty")
            if not _nonempty_str(f.get("value")):
                problems.append(f"verified_facts[{i}].value empty")
            if not _nonempty_str(f.get("source")):
                problems.append(f"verified_facts[{i}].source empty")
            d = f.get("date", "")
            if d and not (re.search(r"[০-৯]", str(d)) or
                          _ISO_RE.match(clean(d))):
                problems.append(f"verified_facts[{i}].date is neither "
                                f"Bangla nor ISO ({d!r})")
    for section in ("topic_gk", "institutions", "extra_knowledge"):
        problems.extend(_validate_gk_section(section,
                                             module.get(section)))
    mcqs = module.get("mcq_practice")
    if not isinstance(mcqs, list) or len(mcqs) != 4:
        problems.append(f"mcq_practice has "
                        f"{len(mcqs) if isinstance(mcqs, list) else 'non-list'} "
                        "items, need exactly 4")
    else:
        correct_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for i, m in enumerate(mcqs):
            if not isinstance(m, dict):
                problems.append(f"mcq_practice[{i}] is not an object")
                continue
            q = clean(m.get("question", ""))
            if not q:
                problems.append(f"mcq_practice[{i}].question empty")
            elif not q.endswith("?"):
                problems.append(f"mcq_practice[{i}].question does not "
                                f"end with '?' ({q[:60]!r})")
            if _NEG_STEM_RE.search(q) or _NEG_STEM_BN_RE.search(q):
                problems.append(f"mcq_practice[{i}] has a negative stem")
            opts = m.get("options")
            if not isinstance(opts, list) or len(opts) != 4:
                problems.append(f"mcq_practice[{i}].options is not a "
                                "list of 4")
                continue
            if any(not _nonempty_str(o) for o in opts):
                problems.append(f"mcq_practice[{i}] has an empty option")
            if len({norm(o) for o in opts}) != 4:
                problems.append(f"mcq_practice[{i}] has duplicate options")
            if any(any(f in str(o) for f in _FORBIDDEN_OPTIONS)
                   for o in opts):
                problems.append(f"mcq_practice[{i}] has a forbidden option")
            correct = m.get("correct")
            if not isinstance(correct, int) or correct not in (0, 1, 2, 3):
                problems.append(f"mcq_practice[{i}].correct is not an "
                                f"index 0-3 ({correct!r})")
                continue
            correct_counts[correct] += 1
            if not _nonempty_str(m.get("explanation")):
                problems.append(f"mcq_practice[{i}].explanation empty")
            if not _traces_to_story(opts[correct], en_story):
                problems.append(
                    f"mcq_practice[{i}] correct answer "
                    f"{opts[correct][:60]!r} does not trace to the story")
        for idx, n in correct_counts.items():
            if n > 2:
                problems.append(f"mcq_practice correct index {idx} used "
                                f"{n}x (max 2)")
    wp = module.get("written_prep")
    if not isinstance(wp, dict):
        problems.append("written_prep is not an object")
    else:
        for part in ("short", "analytical"):
            item = wp.get(part)
            if not isinstance(item, dict):
                problems.append(f"written_prep.{part} is not an object")
                continue
            if not _nonempty_str(item.get("question")):
                problems.append(f"written_prep.{part}.question empty")
            outline = item.get("outline")
            if not isinstance(outline, list) or not (2 <= len(outline) <= 4):
                problems.append(
                    f"written_prep.{part}.outline has "
                    f"{len(outline) if isinstance(outline, list) else 'non-list'} "
                    "bullets, need 2-4")
            elif any(not _nonempty_str(b) for b in outline):
                problems.append(f"written_prep.{part}.outline has an "
                                "empty bullet")
    vocab = module.get("vocabulary")
    if not isinstance(vocab, list) or len(vocab) > 5:
        problems.append("vocabulary is not a list of 0-5")
    else:
        headwords = {clean(h).lower()
                     for h in (edition_word_headwords or [])}
        for i, w in enumerate(vocab):
            if not isinstance(w, dict):
                problems.append(f"vocabulary[{i}] is not an object")
                continue
            hw = clean(w.get("word", ""))
            if not hw:
                problems.append(f"vocabulary[{i}].word empty")
            elif hw.lower() not in headwords:
                problems.append(f"vocabulary[{i}] word {hw!r} is not one "
                                "of the edition's Step 10 words")
            if not _nonempty_str(w.get("meaning_bn")):
                problems.append(f"vocabulary[{i}].meaning_bn empty")
            ex = clean(w.get("example", ""))
            if not ex:
                problems.append(f"vocabulary[{i}].example empty")
            elif hw.lower() not in ex.lower():
                problems.append(f"vocabulary[{i}].example does not "
                                "contain the headword")
            for key in ("synonyms", "antonyms"):
                if not isinstance(w.get(key), list):
                    problems.append(f"vocabulary[{i}].{key} is not a list")
                elif any(not _nonempty_str(s) for s in w.get(key) or []):
                    problems.append(f"vocabulary[{i}].{key} has an empty "
                                    "entry")
    rev = module.get("revision")
    if not isinstance(rev, dict):
        problems.append("revision is not an object")
    else:
        cards = rev.get("flashcards")
        if not isinstance(cards, list) or not (3 <= len(cards) <= 5):
            problems.append(
                f"revision.flashcards has "
                f"{len(cards) if isinstance(cards, list) else 'non-list'} "
                "cards, need 3-5")
        else:
            for i, c in enumerate(cards):
                if not isinstance(c, dict) or not _nonempty_str(c.get("q")) \
                        or not _nonempty_str(c.get("a")):
                    problems.append(f"revision.flashcards[{i}] has an "
                                    "empty q/a")
        nxt = rev.get("next_revision")
        if not isinstance(nxt, list) or len(nxt) != 2:
            problems.append(
                f"revision.next_revision has "
                f"{len(nxt) if isinstance(nxt, list) else 'non-list'} "
                "items, need exactly 2")
        elif any(not _nonempty_str(s) for s in nxt):
            problems.append("revision.next_revision has an empty item")
    deep = module.get("deep_prep")
    if not isinstance(deep, list) or not (4 <= len(deep) <= 6):
        problems.append(
            f"deep_prep has "
            f"{len(deep) if isinstance(deep, list) else 'non-list'} items, "
            "need 4-6")
    elif any(not _nonempty_str(s) for s in deep):
        problems.append("deep_prep has an empty item")
    return problems


def _validate_gk_section(section, value):
    """One GK section: either the exact marker string, or content in
    its v2 shape with named sources and no empty strings. An empty
    string, or any other string, fails: unverified GK must carry the
    marker, never a blank or a guess."""
    problems = []
    if isinstance(value, str):
        if value != MARKER:
            problems.append(
                f"{section} is a non-marker string "
                f"({value[:60]!r}) — unverified GK must carry the exact "
                "marker, never a blank or a guess")
        return problems
    if section == "topic_gk":
        if not isinstance(value, dict):
            return [f"{section} is neither the marker nor an object"]
        if not _nonempty_str(value.get("intro")) and \
                not value.get("tables"):
            problems.append("topic_gk has no intro and no tables")
        sources = value.get("sources")
        if not isinstance(sources, list) or not sources:
            problems.append("topic_gk.sources is empty — every GK block "
                            "carries its source name + URL")
        else:
            for i, s in enumerate(sources):
                if not isinstance(s, dict) or not _nonempty_str(s.get("name")):
                    problems.append(f"topic_gk.sources[{i}] has no name")
                url = s.get("url", "")
                if url and not str(url).startswith(("http://", "https://")):
                    problems.append(f"topic_gk.sources[{i}].url is not "
                                    f"http(s) ({str(url)[:60]!r})")
        for i, t in enumerate(value.get("tables", []) or []):
            if not isinstance(t, dict) or not t.get("rows"):
                problems.append(f"topic_gk.tables[{i}] has no rows")
                continue
            for j, r in enumerate(t["rows"]):
                if not isinstance(r, dict) or \
                        not _nonempty_str(r.get("label")) or \
                        not _nonempty_str(r.get("value")):
                    problems.append(f"topic_gk.tables[{i}].rows[{j}] has "
                                    "an empty label/value")
        for i, d in enumerate(value.get("distinctions", []) or []):
            if not isinstance(d, dict):
                problems.append(f"topic_gk.distinctions[{i}] is not an "
                                "object")
                continue
            if d.get("a") and d.get("b"):
                if not d.get("points"):
                    problems.append(
                        f"topic_gk.distinctions[{i}] has no points")
            elif not _nonempty_str(d.get("text")) and \
                    not _nonempty_str(d.get("title")):
                problems.append(f"topic_gk.distinctions[{i}] is empty")
        return problems
    if section == "institutions":
        if not isinstance(value, list) or not value:
            return [f"{section} is neither the marker nor a non-empty "
                    "list"]
        for i, inst in enumerate(value):
            if not isinstance(inst, dict):
                problems.append(f"institutions[{i}] is not an object")
                continue
            if not _nonempty_str(inst.get("name")):
                problems.append(f"institutions[{i}].name empty")
            if not _nonempty_str(inst.get("role")):
                problems.append(f"institutions[{i}].role empty")
            if not _nonempty_str(inst.get("source")):
                problems.append(f"institutions[{i}].source empty")
        return problems
    if section == "extra_knowledge":
        if not isinstance(value, list) or not value:
            return [f"{section} is neither the marker nor a non-empty "
                    "list"]
        for i, term in enumerate(value):
            if not isinstance(term, dict):
                problems.append(f"extra_knowledge[{i}] is not an object")
                continue
            if not _nonempty_str(term.get("term")):
                problems.append(f"extra_knowledge[{i}].term empty")
            if not _nonempty_str(term.get("meaning")):
                problems.append(f"extra_knowledge[{i}].meaning empty")
            if not _nonempty_str(term.get("source")):
                problems.append(f"extra_knowledge[{i}].source empty")
        return problems
    return problems
