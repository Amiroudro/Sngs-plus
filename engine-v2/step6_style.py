#!/usr/bin/env python3
"""Step 6 — Bangla style (engine v2).

Deterministic, stdlib-only. No LLM, no v1 imports.

render_bangla(facts, topic_primary, lang="bn", english_first=True)
    -> {"bangla_lines": [1-5 fact lines in cholito Bangla],
        "why_important_bn": "..."}

Rules (RULES.md, STEP 6):
- Standard cholito news Bangla, not sadhu; no word-for-word
  translation — lines are rendered FROM the fact list with short
  templates ("<what>: <value> <unit> (<date>)।").
- Glossary terms from RULES.md (via rules_loader) are used exactly;
  first mention of a foreign name/organisation gets the English in
  brackets, e.g. বিশ্বব্যাংক (World Bank), আইএমএফ (IMF).
- Bengali digits in Bangla text; amounts exactly as printed — never
  converted, rounded or written "প্রায়".

English-first note: for English-language papers the facts are
extracted in English first (the fact list is language-neutral) and the
Bangla lines are written from it. ``english_first=True`` (default)
means the fact list is English: common English words are rendered
through the glossary + a small fixed word map, and English proper
nouns are kept on first mention in brackets where a Bangla form
exists. ``english_first=False`` means the fact list is already Bangla:
the words are used as printed (glossary terms already in place) and
only the template, digits and date formatting are applied. Proper
nouns with no Bangla form in the glossary are kept in their printed
(Latin) form rather than guessed at — Step 5's name check still passes
because the name is unchanged.
"""
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from step4_facts import to_bangla_digits, WHY_TEMPLATES, WHY_DEFAULT
except Exception:  # pragma: no cover - fallback if step4 unavailable
    _EN_TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    WHY_TEMPLATES, WHY_DEFAULT = {}, "[পটভূমি] এই খবরটি পরীক্ষার সাধারণ জ্ঞান ও সাম্প্রতিক ঘটনা অংশের জন্য প্রাসঙ্গিক।"

    def to_bangla_digits(text):
        return str(text).translate(_EN_TO_BN)

try:
    from rules_loader import load_rules
except Exception:
    load_rules = None


# ---------------------------------------------------------------------------
# Glossary (RULES.md at runtime): Bangla -> English, and its reverse
# ---------------------------------------------------------------------------
def _glossary():
    """(bangla->english, english-lower->bangla) from RULES.md.

    rules_loader.parse_glossary() returns one entry per *line*, but
    RULES.md packs several "bangla = english;" pairs on one line, so a
    returned value looks like "ministry; অধ্যাদেশ = ordinance; ...".
    The pairs are recovered here (rules_loader itself is untouched):
    the text before the first ";" is the English of the line's Bangla
    term; every later ";"-chunk is itself a "bangla = english" pair.
    """
    if load_rules is None:
        return {}, {}
    try:
        raw = load_rules().get("glossary", {})
    except Exception:
        return {}, {}
    pairs = {}
    for bn, eng_full in raw.items():
        chunks = [c.strip() for c in str(eng_full).split(";") if c.strip()]
        if not chunks:
            continue
        pairs[bn.strip()] = chunks[0]
        for chunk in chunks[1:]:
            if "=" in chunk:
                b2, e2 = chunk.split("=", 1)
                if b2.strip() and e2.strip():
                    pairs[b2.strip()] = e2.strip()
    reverse = {}
    for bn, eng in pairs.items():
        # "agreement / treaty" -> both alternatives map back to the Bangla.
        for alt in re.split(r"[/;]", eng):
            alt = alt.strip().lower()
            if alt:
                reverse.setdefault(alt, bn)
    return pairs, reverse


BN_MONTHS = ["", "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে",
             "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর",
             "নভেম্বর", "ডিসেম্বর"]

# English verbs that must NOT be translated word-by-word into a Bangla
# label: a slot line ("আইএমএফ বোর্ড কিস্তি বাংলাদেশ: ৪৪২ মিলিয়ন …")
# needs no verb, and translating one in English word order produces
# word salad. These words are dropped from the label instead; the
# number + unit + date carry the fact. (The magazine's own digest lines
# are telegraphic in exactly this way.)
VERB_DROP = {
    "approves", "approved", "announces", "announced", "says", "said",
    "expects", "expected", "rises", "rose", "falls", "fell",
    "increases", "increased", "decreases", "decreased",
    "launches", "launched", "signs", "signed", "stands", "stood",
    "outlined", "speaking", "raised", "mobilised", "mobilized",
    "spent", "delivered", "jumped", "recorded", "directed",
    "finalise", "finalize", "working", "remove", "introduce",
    "posted", "reported", "remained", "risen", "might", "could",
    "citing", "held", "reduce", "minimise", "minimize", "withdraw",
    "despite", "unilaterally",
}

# Fixed English -> Bangla word map for the common words that appear in
# English fact lists. NOUN phrases and modifiers only — verbs live in
# VERB_DROP above and are removed, never translated. Proper nouns are
# NOT in this map — they are kept (see module docstring). Longest
# phrases first at apply time.
WORD_MAP = {
    "prime minister": "প্রধানমন্ত্রী",
    "chief adviser": "প্রধান উপদেষ্টা",
    "foreign minister": "পররাষ্ট্রমন্ত্রী",
    "finance minister": "অর্থমন্ত্রী",
    "central bank": "কেন্দ্রীয় ব্যাংক",
    "supreme court": "সুপ্রিম কোর্ট",
    "high court": "হাইকোর্ট",
    "election commission": "নির্বাচন কমিশন",
    "foreign exchange": "বৈদেশিক মুদ্রা",
    "interest rate": "সুদের হার",
    "policy rate": "নীতি সুদহার",
    "monetary policy": "মুদ্রানীতি",
    "economic growth": "অর্থনৈতিক প্রবৃদ্ধি",
    "per capita income": "মাথাপিছু আয়",
    "trade deficit": "বাণিজ্য ঘাটতি",
    "climate change": "জলবায়ু পরিবর্তন",
    "renewable energy": "নবায়নযোগ্য জ্বালানি",
    "artificial intelligence": "কৃত্রিম বুদ্ধিমত্তা",
    "nobel prize": "নোবেল পুরস্কার",
    "world bank": "বিশ্বব্যাংক",
    "united nations": "জাতিসংঘ",
    "security council": "নিরাপত্তা পরিষদ",
    "government": "সরকার",
    "parliament": "সংসদ",
    "constitution": "সংবিধান",
    "cabinet": "মন্ত্রিসভা",
    "gazette": "গেজেট",
    "ministry": "মন্ত্রণালয়",
    "minister": "মন্ত্রী",
    "adviser": "উপদেষ্টা",
    "president": "রাষ্ট্রপতি",
    "court": "আদালত",
    "reserves": "রিজার্ভ",
    "reserve": "রিজার্ভ",
    "budget": "বাজেট",
    "inflation": "মূল্যস্ফীতি",
    "remittance": "রেমিট্যান্স",
    "exports": "রপ্তানি",
    "export": "রপ্তানি",
    "imports": "আমদানি",
    "import": "আমদানি",
    "economy": "অর্থনীতি",
    "growth": "প্রবৃদ্ধি",
    "tranche": "কিস্তি",
    "loan": "ঋণ",
    "board": "বোর্ড",
    "approval": "অনুমোদন",
    "meeting": "বৈঠক",
    "decision": "সিদ্ধান্ত",
    "review": "পর্যালোচনা",
    "programme": "কর্মসূচি",
    "program": "কর্মসূচি",
    "bangladesh": "বাংলাদেশ",
    "country": "দেশ",
    "month": "মাস",
    "year": "বছর",
    "economic": "অর্থনৈতিক",
    "fiscal year": "অর্থবছর",
    "fiscal": "অর্থবছর",
    "crore": "কোটি",
    "next": "পরবর্তী",
    "under": "অধীনে",
    "after": "পরে",
    "before": "আগে",
    "governor": "গভর্নর",
    "summit": "সম্মেলন",
    "fifth": "পঞ্চম",
    "organised": "আয়োজিত",
    "organized": "আয়োজিত",
    "plans": "পরিকল্পনা",
    "plan": "পরিকল্পনা",
    "ceiling": "সীমা",
    "types": "ধরনের",
    "three": "তিন",
    "neighbouring": "প্রতিবেশী",
    "countries": "দেশগুলো",
    "similar": "একই ধরনের",
    "accounts": "হিসাব",
    "within": "মধ্যে",
    "months": "মাস",
    "pressure": "চাপ",
    "public": "সরকারি",
    "finances": "অর্থ",
    "significant": "উল্লেখযোগ্য",
    "domestic": "দেশীয়",
    "resources": "সম্পদ",
    "dependence": "নির্ভরতা",
    "imported": "আমদানিকৃত",
    "fuels": "জ্বালানি",
    "modern": "আধুনিক",
    "technologies": "প্রযুক্তি",
    "damage": "ক্ষতি",
    "agricultural": "কৃষি",
    "land": "জমি",
    "broader": "বৃহত্তর",
    "outlook": "চিত্র",
    "examples": "উদাহরণ",
    "through": "মাধ্যমে",
    "target": "লক্ষ্য",
    "bank": "ব্যাংক",
    "banks": "ব্যাংকগুলো",
    "largest": "বৃহত্তম",
    "listed": "তালিকাভুক্ত",
    "drug": "ওষুধ",
    "maker": "প্রস্তুতকারক",
    "reporting": "",
    "consolidated": "সমন্বিত",
    "fastest": "দ্রুততম",
    "major": "বড়",
    "players": "কোম্পানিগুলো",
    "turnover": "বিক্রি",
    "rise": "বৃদ্ধি",
    "profit": "মুনাফা",
    "revenue": "আয়",
    "existing": "বিদ্যমান",
    "power": "বিদ্যুৎ",
    "purchase": "ক্রয়",
    "agreements": "চুক্তি",
    "agreement": "চুক্তি",
    "discussions": "আলোচনা",
    "other": "অন্যান্য",
    "indian": "ভারতীয়",
    "suppliers": "সরবরাহকারী",
    "teams": "দলগুলো",
    "officials": "কর্মকর্তা",
    "roadmap": "রোডম্যাপ",
    "coal": "কয়লা",
    "extraction": "উত্তোলন",
    "maturity": "মেয়াদ",
    "bond": "বন্ড",
    "bonds": "বন্ড",
    "retail": "খুচরা",
    "sme": "এসএমই",
    "expatriate": "প্রবাসী",
    "expat": "প্রবাসী",
    "quarter": "প্রান্তিক",
    "mining": "খনন",
    "subsidy": "ভর্তুকি",
    "subsidies": "ভর্তুকি",
    "energy": "জ্বালানি",
    "fuel": "জ্বালানি",
    "foreign": "বিদেশি",
    "record": "রেকর্ড",
    "level": "স্তর",
    "rate": "হার",
    "rates": "হার",
    "market": "বাজার",
    "price": "দাম",
    "prices": "দাম",
    "share": "শেয়ার",
    "shares": "শেয়ার",
    "company": "কোম্পানি",
    "companies": "কোম্পানিগুলো",
    "trade": "বাণিজ্য",
    "deficit": "ঘাটতি",
    "surplus": "উদ্বৃত্ত",
    "crisis": "সংকট",
    "reform": "সংস্কার",
    "reforms": "সংস্কার",
    "election": "নির্বাচন",
    "vote": "ভোট",
    "deal": "চুক্তি",
    "agreement": "চুক্তি",
    "treaty": "চুক্তি",
    "summit": "সম্মেলন",
}

UNIT_MAP = {
    "USD": "মার্কিন ডলার", "US dollar": "মার্কিন ডলার",
    "US dollars": "মার্কিন ডলার", "dollars": "ডলার", "dollar": "ডলার",
    "million": "মিলিয়ন", "billion": "বিলিয়ন", "trillion": "ট্রিলিয়ন",
    "crore": "কোটি", "lakh": "লাখ", "taka": "টাকা",
    "percent": "শতাংশ", "per cent": "শতাংশ",
    "megawatt": "মেগাওয়াট", "MW": "মেগাওয়াট", "GW": "গিগাওয়াট",
    "kilometres": "কিলোমিটার", "km": "কিলোমিটার",
    "tonnes": "টন", "tonne": "টন", "tons": "টন", "ton": "টন",
}


def format_date_bn(iso_date):
    """'2026-11-14' -> '১৪ নভেম্বর ২০২৬'; 'উল্লেখ নেই' stays."""
    if not iso_date or iso_date == "উল্লেখ নেই":
        return "উল্লেখ নেই"
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", str(iso_date).strip())
    if not m:
        return to_bangla_digits(str(iso_date))
    y, mo, d = (int(x) for x in m.groups())
    if not 1 <= mo <= 12:
        return to_bangla_digits(str(iso_date))
    return "%s %s %s" % (to_bangla_digits(str(d)), BN_MONTHS[mo],
                         to_bangla_digits(str(y)))


def _is_name_like(eng):
    """Is this English glossary term a name/organisation (bracket-worthy)?
    Acronyms (IMF, ADB, WTO, GDP) and organisation names (World Bank,
    Election Commission, Supreme Court) get "(English)" on first
    mention; common nouns (reserves, budget, inflation) render plainly.
    """
    eng = eng.strip()
    if re.fullmatch(r"[A-Z]{2,6}", eng.upper()):
        return True
    return any(t in eng.lower().split() for t in
               ("bank", "court", "commission", "union", "nations",
                "fund", "council", "organisation", "organization",
                "justice", "parliament"))


def _apply_phrases(text, mapping, seen, bracket):
    """Replace phrases in ``mapping`` (longest first, case-insensitive).

    On first mention, if ``bracket`` is set, render "বাংলা (English)".
    ``seen`` tracks already-bracketed English forms across lines.
    Text already inside parentheses (e.g. an earlier "(IMF)") is never
    rewritten, so a later map cannot clobber the bracketed English.
    """
    for eng in sorted(mapping, key=len, reverse=True):
        bn = mapping[eng]
        pattern = re.compile(r"\b" + re.escape(eng) + r"\b", re.I)

        def _sub(m, eng=eng, bn=bn):
            if bracket and _is_name_like(eng) and eng.lower() not in seen:
                seen.add(eng.lower())
                return "%s (%s)" % (bn, m.group(0))
            return bn

        parts = re.split(r"(\([^)]*\))", text)
        parts = [pattern.sub(_sub, p) if not p.startswith("(") else p
                 for p in parts]
        text = "".join(parts)
    return text


def _render_what(what, reverse_glossary, seen, english_first):
    """Render one fact's 'what' into a cholito Bangla slot label.

    Slot format, not sentence translation: verbs are dropped (see
    VERB_DROP) and only noun phrases are mapped, so the line reads like
    the magazine's own telegraphic digest lines
    ("আইএমএফ বোর্ড কিস্তি বাংলাদেশ: ৪৪২ মিলিয়ন (১৩ নভেম্বর ২০২৬)।")
    instead of a word-salad sentence.
    """
    text = (what or "").strip()
    if not english_first:
        return to_bangla_digits(text)
    # Drop English verbs first: they must never reach the word map.
    if VERB_DROP:
        pat = re.compile(r"\b(?:" + "|".join(sorted(VERB_DROP)) + r")\b",
                         re.I)
        text = pat.sub(" ", text)
    # Glossary first (fixed terms, exactly as in RULES.md), then the
    # small common-word map. Both bracket the English on first mention
    # for glossary terms; the word map renders plainly.
    text = _apply_phrases(text, reverse_glossary, seen, bracket=True)
    text = _apply_phrases(text, WORD_MAP, seen, bracket=False)
    # "Tk1,260" -> "টাকা ১,২৬০" (digits converted below); a Bangla
    # word's English possessive ("দেশ's") -> "দেশের".
    text = re.sub(r"\bTk(?=\d)", "টাকা ", text)
    text = re.sub(r"([\u0980-\u09FF])'s\b", r"\1ের", text)
    # Drop English filler words the template does not need.
    text = re.sub(r"\b(for|of|the|a|an|its|is|are|was|were|has|have|had|"
                  r"under|by|with|from|as|per|in|on|at|to|and|also|around|"
                  r"while|allowing|within|this|he|she|it|they|among|been|"
                  r"requiring)\b", " ",
                  text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,;:")
    return to_bangla_digits(text)


def _render_unit(unit, english_first):
    if not unit:
        return ""
    if not english_first:
        return unit
    return UNIT_MAP.get(unit, UNIT_MAP.get(unit.lower(), unit))


def _render_value(value):
    """Value exactly as printed, digits in Bengali for Bangla text."""
    if value in (None, ""):
        return ""
    return to_bangla_digits(str(value))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_bangla(facts, topic_primary="", lang="bn", english_first=True):
    """Render fact lines in Bangla (or English when lang != 'bn').

    ``facts``: list of Step 4 fact dicts. Returns
    {"bangla_lines": [...], "why_important_bn": "..."}.
    """
    _glossary_bn, reverse = _glossary()
    seen = set()  # English forms already given "(English)" once
    lines = []
    for fact in (facts or [])[:5]:
        what = fact.get("what") or ""
        value = _render_value(fact.get("value") or "")
        unit = _render_unit(fact.get("unit") or "", english_first)
        date = fact.get("date") or "উল্লেখ নেই"
        if lang == "bn":
            what_bn = _render_what(what, reverse, seen, english_first)
            date_bn = format_date_bn(date)
            parts = [what_bn]
            if value:
                parts.append(": " + value + (" " + unit if unit else ""))
            if date_bn != "উল্লেখ নেই":
                parts.append(" (" + date_bn + ")")
            line = "".join(parts).strip()
            if not line.endswith("।"):
                line += "।"
            lines.append(line)
        else:
            parts = [what]
            if value:
                parts.append(": " + str(fact.get("value") or "")
                            + (" " + (fact.get("unit") or "") if fact.get("unit") else ""))
            if date != "উল্লেখ নেই":
                parts.append(" (" + str(date) + ")")
            lines.append("".join(parts).strip() + ".")

    why = WHY_TEMPLATES.get(topic_primary or "", WHY_DEFAULT)
    return {"bangla_lines": lines, "why_important_bn": why}


if __name__ == "__main__":
    import json
    facts = [{
        "what": "IMF board approves tranche for Bangladesh",
        "value": "442", "unit": "million",
        "date": "2026-11-13", "status": "happened",
        "quote": "The International Monetary Fund board has approved a "
                 "$442 million tranche for Bangladesh under its loan programme."}]
    print(json.dumps(render_bangla(facts, "INT-ORG"),
                     ensure_ascii=False, indent=2))
