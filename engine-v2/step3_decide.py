#!/usr/bin/env python3
"""Step 3 — Decide (Sarangsho Plus engine v2).

Deterministic decider: no LLM, no API, stdlib only. Reads the rubric,
topics and lexicon from rules/RULES.md at runtime via rules_loader.py —
no hardcoded topic lists in this file. (The small pattern lists below —
approval verbs, crime/statement phrasing, the rubric's minor-story
concepts — are the RUBRIC's own patterns from RULES.md, not topic lists.)

Input:  one article dict (Step 1 shape): id, title, url, section,
        published, summary, ...
        The decider reads title + summary only, truncated to the first
        200 words. Full article text is NOT fetched before this step.
Output: {"id", "decision", "topic_primary", "topic_secondary",
         "evidence_quote", "reason", "score"}
        decision: keep (score 2/3) | maybe (score 1) | reject (score 0).
        topic_primary is "" for reject and for maybe (score 1, no named
        topic). evidence_quote is "" only for reject; every keep/maybe
        carries a quote that is a verbatim substring of the input text.

Rubric (RULES.md):
  3 = Strong-term hit in the HEADLINE matching a score-3 pattern:
      new law/ordinance/commission, treaty, appointment to a
      constitutional or major economic body, official statistic,
      development involving a named international organisation.
  2 = Strong- or Support-term hit that clearly supports a named topic.
  1 = same broad area, no named topic.
  0 = nothing (or an edge rule rejects it).
Tie-breaks, in order: (1) topic of the headline's main subject,
(2) more specific topic (Strong hit beats Support-only), (3) earlier
topic in RULES.md.

Edge rules (RULES.md): crime/accident kept ONLY if it produced a law,
ordinance, commission, court directive or policy (then keep 2, BD-GOV,
reason notes "instrument only"); awards/world indexes/rankings are
maybe UNLESS a Bangladeshi institution/person is involved (keep 2);
opinion columns reject; bank robbery / single branch event / single
market price reject; minister statement with no number and no decision
rejects; minor stories touching an established institution/treaty/
concept (NATO, BRICS, UN, IMF, WTO, Green Climate Fund, hydrogen,
space missions) keep 2 on that topic; published > 36 months ago
rejects with reason "too old" (no date -> no age rejection).
Two guards (2026-11-15 mislabels): a bare court term does not count
as BD-GOV when the headline names a foreign leader/country and
nothing in the article anchors it to Bangladesh; "record" counts as
SPORT only when the article carries a sports anchor.

Robustness: decide() never raises. On any failure of the main pass it
retries once with a simpler keyword pass; if that also fails it returns
maybe/1 with reason "decider fallback". Malformed input (missing
title) -> maybe/1, never a crash.

Usage:
  python3 step3_decide.py runs/<date>/articles-<date>.json
      -> writes decisions-<date>.json beside the input file.
  from step3_decide import decide, decide_batch
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from rules_loader import load_rules
except Exception:  # pragma: no cover - loader missing entirely
    load_rules = None

# ---------------------------------------------------------------- rules
_RULES = load_rules() if load_rules else {"topics": {}, "topic_order": []}
TOPICS = _RULES.get("topics", {}) or {}
TOPIC_ORDER = _RULES.get("topic_order", []) or list(TOPICS)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36 SarangshoPlus/2.0"

# --- Rubric patterns (wording from RULES.md's RUBRIC / EDGE RULES) -------
# Approval / decision verbs that turn a Strong headline hit into score 3.
_APPROVAL_VERBS = [
    "approves", "approved", "approve", "passes", "passed", "pass",
    "adopts", "adopted", "adopt", "signs", "signed", "sign",
    "ratifies", "ratified", "ratify", "promulgates", "promulgated",
    "promulgate", "enacts", "enacted", "enact", "forms", "formed",
    "form", "establishes", "established", "establish", "appoints",
    "appointed", "appoint", "elects", "elected", "grants", "granted",
    "grant", "releases", "released", "release",
]
# Verbs that make a Support-only hit concrete enough for score 2.
_ACTION_VERBS = _APPROVAL_VERBS + [
    "announces", "announced", "announce", "launches", "launched",
    "launch", "unveils", "unveiled", "unveil", "issues", "issued",
    "issue", "declares", "declared", "declare", "orders", "ordered",
    "order", "directs", "directed", "direct", "sets", "set", "raises",
    "raised", "raise", "cuts", "cut", "hikes", "hiked", "inaugurates",
    "inaugurated", "inaugurate", "introduces", "introduced",
    "introduce", "proposes", "proposed", "propose", "submits",
    "submitted", "submit", "begins", "begin", "starts", "start",
    "opens", "opened", "open", "wins", "won", "win",
]
# Statement-only verbs: a minister saying something, with no number
# and no decision, is reject (RULES.md edge rule).
_STATEMENT_VERBS = [
    "says", "said", "say", "claims", "claimed", "claim", "hopes",
    "hoped", "hope", "expects", "expected", "expect", "believes",
    "believed", "believe", "thinks", "think", "vows", "vowed", "vow",
    "assures", "assured", "assure",
]
# Decision nouns: presence of one means the statement is not empty.
_DECISION_NOUNS = [
    "decision", "directive", "ordinance", "policy", "bill", "budget",
    "plan", "programme", "program", "agreement", "treaty",
    "announcement", "approval", "law", "commission", "reform",
    "election", "appointment", "directives", "আদালতের নির্দেশ",
    "অধ্যাদেশ", "আইন", "নীতি", "বাজেট", "চুক্তি",
]
# Crime / accident vocabulary (Step 2 deprioritise terms + "crime").
# Bangla case/crime terms added 2026-11-15: the PA Bangla sitemap
# surfaced crime stories (a951: a case against an MP's father for
# vandalism/assault/looting/land-grab; a720: a compensation suit over
# a boat collision) that the English-heavy feed never put on the
# page. "মামলা" is the catch-all: a case filing is a crime story
# unless an instrument rescues it. "জমি দখল" (not bare "দখল") so
# forest/water-body encroachment stories are not caught by accident.
_CRIME_TERMS = [
    "murder", "হত্যা", "robbery", "ডাকাতি", "rape", "ধর্ষণ",
    "accident", "দুর্ঘটনা", "crash", "সংঘর্ষ", "suicide", "আত্মহত্যা",
    "arrested", "গ্রেপ্তার", "crime", "theft", "burglary", "stabbed",
    "stabbing", "shot dead", "shooting", "kidnapped", "kidnap",
    "arson", "mugging",
    "মামলা", "ভাঙচুর", "মারধর", "লুট", "জমি দখল", "অপহরণ",
    "চাঁদাবাজি", "খুন",
]
# Disaster vocabulary for the crime-rule carve-out (below): a story
# about a named disaster is ENV/SCI, not crime, even if it carries a
# crime word ("accident", "crash"). This must be a NARROW list — the
# old carve-out fired on ANY ENV/SCI Strong match, so a compensation
# suit (ENV Strong on "ক্ষতিপূরণ", climate loss-and-damage) escaped
# the crime rule (a720, 2026-11-15).
_DISASTER_TERMS = [
    "flood", "বন্যা", "cyclone", "ঘূর্ণিঝড়", "earthquake", "ভূমিকম্প",
    "drought", "খরা", "landslide", "ভূমিধস", "storm", "ঝড়",
    "tidal surge", "জলোচ্ছ্বাস", "tsunami", "সুনামি", "wildfire",
    "দাবানল", "heatwave", "তাপপ্রবাহ", "dengue", "ডেঙ্গু",
    "outbreak", "প্রাদুর্ভাব", "epidemic", "মহামারি", "pandemic",
]
# Instruments that rescue a crime/accident story (edge rule): the story
# is then kept for the instrument only, never for the incident.
_INSTRUMENT_TERMS = [
    "ordinance", "অধ্যাদেশ", "commission", "কমিশন", "directive",
    "নির্দেশনা", "আদালতের নির্দেশ", "policy", "নীতি", "law", "আইন",
    "court directive",
]
# Awards / rankings / indexes (maybe unless a Bangladeshi institution
# or person is involved -> keep 2).
_AWARD_TERMS = [
    "award", "পুরস্কার", "ranked", "ranking", "ranks", "rank",
    "index", "named among", "shortlisted", "wins award", "won an award",
]
_BD_MARKERS = ["bangladesh", "বাংলাদেশ", "dhaka", "ঢাকা", "bangladeshi"]
# Bare court terms are BD-GOV Strong terms (Bangladesh Supreme Court),
# but the same words name foreign courts too ("At the Supreme Court,
# Trump aims to cut the power of judges again" — US story, kept 2 as
# BD-GOV on 2026-11-15, a349). FOREIGN-COURT GUARD: a bare court term
# does NOT count as BD-GOV when the headline names a foreign leader
# or country and nothing in the article anchors it to Bangladesh.
# Headline-only on purpose: a genuine Bangladesh court story often
# mentions a foreign country in passing in its summary, but the
# headline's main subject is what the rubric scores (tie-break 1).
_COURT_TERMS = [
    "supreme court", "সুপ্রিম কোর্ট", "high court", "হাইকোর্ট",
    "chief justice", "প্রধান বিচারপতি", "attorney general",
    "অ্যাটর্নি জেনারেল", "tribunal", "ট্রাইব্যুনাল",
]
_FOREIGN_ANCHORS = [
    "trump", "biden", "putin", "modi", "netanyahu", "xi jinping",
    "erdogan", "starmer", "macron", "united states", "u.s.", "usa",
    "america", "american", "india", "indian", "pakistan", "pakistani",
    "china", "chinese", "russia", "russian", "britain", "british",
    "united kingdom", "france", "french", "germany", "german",
    "israel", "israeli", "australia", "australian", "canada",
    "canadian", "japan", "japanese", "turkey", "turkiye", "turkish",
    "iran", "iranian", "saudi arabia", "south africa",
    "যুক্তরাষ্ট্র", "মার্কিন", "আমেরিকা", "ভারত", "পাকিস্তান", "চীন",
    "রাশিয়া", "ব্রিটেন", "যুক্তরাজ্য", "ফ্রান্স", "জার্মানি",
    "ইসরায়েল", "তুরস্ক",
]
# "Record" is a SPORT Strong term, but a record is not always sport:
# "Bangladesh registers record 361 delegates at COP31" was kept 2 as
# SPORT on 2026-11-15 (a282) although it is climate diplomacy.
# SPORTS-RECORD GUARD: "record"/"রেকর্ড" counts as SPORT only when
# the article carries a sports anchor — another SPORT lexicon term,
# or one of these unambiguous sport words. A record delegation, a
# record deal or a record loss has no anchor and is not sport.
_RECORD_TERMS = ["record", "রেকর্ড"]
_SPORT_ANCHORS = [
    "century", "wicket", "innings", "goal", "league", "championship",
    "medal", "athlete", "tennis", "badminton", "chess", "archery",
    "t20", "odi", "hat-trick", "hat trick", "penalty", "shootout",
    "সেঞ্চুরি", "উইকেট", "গোল", "লিগ", "পদক",
]
# First / record achievement signals (Proposal 1, syllabus): a first
# or record in the headline, with a number and a date, is a score-3
# signal. "Ranking" is NOT in this list — rankings are handled by the
# awards/rankings block below (Proposal 2): a ranking scores 3 only
# when it states Bangladesh's position.
_FIRST_TERMS = [
    "first-ever", "first ever", "first time", "প্রথম", "প্রথমবার",
    "record", "রেকর্ড", "milestone", "মাইলফলক",
]
# Headline phrases where "first" is a schedule, not an achievement
# ("first phase of the metro opens") — not a Proposal 1 first.
_FIRST_EXCLUSIONS = [
    "first phase", "প্রথম ধাপ", "first day", "প্রথম দিন",
    "first round", "প্রথম রাউন্ড",
]
# Ranking/index terms (Proposal 2): a ranking story keeps only when
# it states Bangladesh's rank/position.
_RANK_TERMS = [
    "rank", "ranked", "ranking", "ranks", "index", "সূচক",
]
_EN_MONTHS = ("january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november",
              "december", "jan", "feb", "mar", "apr", "jun", "jul",
              "aug", "sep", "sept", "oct", "nov", "dec")
_BN_MONTHS = ("জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে",
              "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর",
              "নভেম্বর", "ডিসেম্বর")
# Minor-story concepts from the RUBRIC (established institution /
# treaty / concept). Terms already in the RULES lexicon are found via
# the loader; Green Climate Fund is not a lexicon term, so it is
# mapped here to the topic the rubric points at (environment).
_MINOR_CONCEPTS = {"green climate fund": "ENV"}
# Phrases where a lexicon term means something else ("land records"
# is not a sports record). The word immediately before the match is
# checked; if it is in the list, that occurrence does not count.
_TERM_EXCLUSIONS = {
    "record": ["land", "court", "public", "track", "health"],
}
_ORDINANCE_TERMS = ["ordinance", "অধ্যাদেশ", "bill passed", "আইন পাস",
                    "reform commission", "সংস্কার কমিশন",
                    "ordinance promulgated", "অধ্যাদেশ জারি"]
_TREATY_TERMS = ["treaty", "peace deal", "শান্তি চুক্তি", "চুক্তি"]
_APPOINT_VERBS = ["appointed", "appoints", "appoint", "named as", "names"]
_APPOINT_BODIES = [
    "chief justice", "প্রধান বিচারপতি", "election commission",
    "নির্বাচন কমিশন", "bangladesh bank", "বাংলাদেশ ব্যাংক",
    "supreme court", "সুপ্রিম কোর্ট", "attorney general",
    "অ্যাটর্নি জেনারেল", "high court", "হাইকোর্ট", "governor",
    "ambassador", "chairman", "commissioner", "chief adviser",
    "প্রধান উপদেষ্টা",
]
# Official-statistic topics: a Strong eco term + a number in the headline.
_STAT_TOPICS = {"BD-ECO"}

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_TERM_RE = {}


# ---------------------------------------------------------------- helpers
def _norm(text):
    """NFC + Bangla digits -> English + lowercase (matches loader terms)."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text)).translate(_BN_DIGITS).lower()


def _term_re(term):
    rx = _TERM_RE.get(term)
    if rx is None:
        # Word-boundary on both ends (Bangla letters count as word chars).
        # A trailing plural is allowed for longer terms ("export" also
        # matches "exports", "directive" also "directives", "policy"
        # also "policies") so real headlines are not missed on plurals.
        core = term
        suffix = ""
        if len(term) >= 4 and not term.endswith("s"):
            if len(term) >= 2 and term.endswith("y") \
                    and term[-2] not in "aeiou":
                core, suffix = term[:-1], r"(?:y|ies)"
            else:
                suffix = r"s?"
        rx = re.compile(r"(?<![0-9a-z\u0980-\u09ff])" + re.escape(core) +
                        suffix + r"\d*" +
                        r"(?![0-9a-z\u0980-\u09ff])")
        _TERM_RE[term] = rx
    return rx


def _iter_matches(text_norm, term):
    """Match spans for `term`, skipping _TERM_EXCLUSIONS phrases."""
    for m in _term_re(term).finditer(text_norm):
        excluded = _TERM_EXCLUSIONS.get(term)
        if excluded:
            before = text_norm[:m.start()].rstrip()
            prev = before.split()[-1] if before.split() else ""
            if prev in excluded:
                continue
        yield m


def _contains(text_norm, term):
    return _term_re(term).search(text_norm) is not None


def _find(text_norm, term):
    for m in _iter_matches(text_norm, term):
        return m.start()
    return -1


def _has_digit(text_norm):
    return re.search(r"\d", text_norm) is not None


def _stat_digits(head_norm):
    """Digits in the headline that are NOT part of a date.

    A date is not a statistic: "begins on 14 November 2026" carries
    no figure, so the year and the month-day are stripped before the
    digit check (Proposal 1's number+date test uses _has_digit and
    _has_date separately and is unaffected).
    """
    h = re.sub(r"\b(?:19|20)\d{2}\b", " ", head_norm)
    h = re.sub(r"\b\d{1,2}\s+(?:" + "|".join(_EN_MONTHS) + r")\b", " ", h)
    h = re.sub(r"\b(?:" + "|".join(_EN_MONTHS) + r")\s+\d{1,2}\b", " ", h)
    h = re.sub(r"\b\d{1,2}\s+(?:" + "|".join(_BN_MONTHS) + r")\b", " ", h)
    return _has_digit(h)


def _has_date(text_norm):
    """A date in the text: a year, or a month name (English/Bangla).

    English months need a word boundary ("may" must not match
    "maybe"); Bangla months are matched as substrings.
    """
    if re.search(r"\b(?:19|20)\d{2}\b", text_norm):
        return True
    if re.search(r"\b(?:" + "|".join(_EN_MONTHS) + r")\b", text_norm):
        return True
    return any(m in text_norm for m in _BN_MONTHS)


def _has_first_signal(head_norm):
    """A first/record achievement signal in the headline (Proposal 1).

    Exclusion-aware: "land record" etc. do not count (see
    _TERM_EXCLUSIONS), and schedule phrases ("first phase",
    "প্রথম ধাপ") are not achievements.
    """
    if any(p in head_norm for p in _FIRST_EXCLUSIONS):
        return False
    return any(_find(head_norm, t) >= 0 for t in _FIRST_TERMS)


def _bd_rank_stated(text_norm):
    """Does the text state Bangladesh's rank/position (Proposal 2)?

    A direct phrase ("Bangladesh ranks ...", "বাংলাদেশের অবস্থান ..."),
    or a sentence carrying both a Bangladesh marker and a rank/position
    word. Substring matching on purpose: "তম" lives inside "৮৮তম"
    (a digit is a Bangla word char, so the word-boundary term match
    would miss it).
    """
    direct = (
        "bangladesh ranks", "bangladesh ranked", "bangladesh's rank",
        "rank of bangladesh", "bangladesh's position",
        "position of bangladesh", "বাংলাদেশের অবস্থান",
        "বাংলাদেশের স্থান", "বাংলাদেশের র‌্যাংক",
    )
    if any(p in text_norm for p in direct):
        return True
    rank_words = ("rank", "position", "তম", "অবস্থান")
    bd_words = ("bangladesh", "বাংলাদেশ", "bangladeshi", "dhaka", "ঢাকা")
    for start, end in _sentences(text_norm):
        seg = text_norm[start:end]
        if any(b in seg for b in bd_words) and \
                any(r in seg for r in rank_words):
            return True
    return False


# Keyword -> topic for a ranking/index story that matched no lexicon
# term at all (Proposal 2): the ranking itself is the topic signal,
# and the index's subject picks the topic. Default PEOPLE — the
# rubric's generic home for awards/rankings.
_RANKING_TOPICS = [
    (("hunger", "food security", "poverty", "nutrition"), "BD-ECO"),
    (("corruption", "transparency"), "BD-GOV"),
    (("passport", "visa"), "INT-REL"),
    (("development", "human development"), "BD-NATL"),
    (("innovation", "competitiveness"), "BD-ECO"),
    (("press freedom", "media freedom"), "BD-NATL"),
]


def _ranking_topic(text_norm):
    for terms, tid in _RANKING_TOPICS:
        if _has_any(text_norm, list(terms)):
            return tid
    return "PEOPLE"


def _has_any(text_norm, terms):
    return any(_contains(text_norm, t) for t in terms)


def _court_term_guarded(head_norm, text_norm):
    """Foreign-court guard: True when a bare court term must NOT count
    as BD-GOV. Fires only when the headline names a foreign leader or
    country AND nothing in the article anchors it to Bangladesh
    (no Bangladesh/Dhaka marker anywhere in title + summary).
    Bare "US" is a pronoun elsewhere, so it only counts directly in
    front of a court term ("US Supreme Court")."""
    if _has_any(text_norm, _BD_MARKERS):
        return False
    if _has_any(head_norm, _FOREIGN_ANCHORS):
        return True
    return re.search(
        r"\bus\s+(?:supreme court|high court|chief justice|"
        r"attorney general|tribunal)\b", head_norm) is not None


def _has_sport_anchor(text_norm, sport_topic):
    """Sports-record guard: True when "record" may count as SPORT —
    some other SPORT lexicon term (Strong or Support, other than
    "record" itself) or an unambiguous sport word appears in the text."""
    terms = ([t for t in sport_topic.get("strong", [])
              if t not in _RECORD_TERMS]
             + [t for t in sport_topic.get("support", [])
                if t not in _RECORD_TERMS]
             + _SPORT_ANCHORS)
    return _has_any(text_norm, terms)


def _input_text(article):
    """Title + summary, first 200 words. Returns (text, title, summary)."""
    title = (article.get("title") or "").strip()
    summary = (article.get("summary") or "").strip()
    full = (title + " " + summary).strip()
    words = full.split()
    return " ".join(words[:200]), title, summary


def _parse_date(raw):
    if not raw:
        return None
    try:
        s = str(raw).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(str(raw))
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _months_ago(months, now):
    """Datetime `months` months before `now` (calendar months)."""
    year = now.year
    month = now.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(now.day, 28)
    try:
        return now.replace(year=year, month=month, day=day)
    except ValueError:
        return now.replace(year=year, month=month, day=28)


def _sentences(text):
    """Sentence spans of `text` (kept as slices, so quotes stay verbatim)."""
    spans = []
    for m in re.finditer(r"[^.!?\n।]+(?:[.!?।]+|$)", text):
        s = m.group(0)
        if s.strip():
            spans.append((m.start(), m.end()))
    if not spans and text.strip():
        spans = [(0, len(text))]
    return spans


def _pick_quote(text, text_norm, terms_by_strength, title=""):
    """Sentence/phrase containing the strongest matched term.

    Scores each sentence: +3 per distinct Strong term, +1 per Support
    term, +2 for a score-3 approval verb, +1 for a digit; ties go to
    the longest sentence (so a summary sentence beats a headline that
    says the same thing in fewer words). The title is its own segment
    (it has no closing punctuation, so it must not merge with the
    first summary sentence). Returns "" if no term hits.
    `terms_by_strength` is a list of (term, is_strong).
    """
    if not terms_by_strength:
        return ""
    spans = _sentences(text)
    if title:
        tlen = len(title)
        if text.startswith(title):
            rest = [(s + tlen + 1, e + tlen + 1)
                    for (s, e) in _sentences(text[tlen + 1:])
                    if s + tlen + 1 < len(text)]
            spans = [(0, tlen)] + rest
    best, best_score, best_len = "", -1, -1
    for start, end in spans:
        seg = text[start:end]
        seg_norm = _norm(seg)
        score = 0
        for term, is_strong in terms_by_strength:
            if _contains(seg_norm, term):
                score += 3 if is_strong else 1
        if _has_any(seg_norm, _APPROVAL_VERBS):
            score += 2
        if _has_digit(seg_norm):
            score += 1
        if score > best_score or (score == best_score and
                                  len(seg) > best_len and score > 0):
            best, best_score, best_len = seg.strip(), score, len(seg)
    return best if best_score > 0 else ""


def _match_topics(head_norm, text_norm):
    """Per-topic matches: {tid: {strong_head, strong, support_head,
    support, head_pos, terms}} — terms = [(term, is_strong)]."""
    out = {}
    for tid in TOPIC_ORDER:
        t = TOPICS[tid]
        strong_head, strong, support_head, support = [], [], [], []
        head_pos = None
        terms = []
        for term in t.get("strong", []):
            # Foreign-court guard: a bare court term naming a foreign
            # court does not count as BD-GOV (2026-11-15 a349).
            if tid == "BD-GOV" and term in _COURT_TERMS \
                    and _court_term_guarded(head_norm, text_norm):
                continue
            # Sports-record guard: "record" counts as SPORT only with
            # a sports anchor in the article (2026-11-15 a282).
            if tid == "SPORT" and term in _RECORD_TERMS \
                    and not _has_sport_anchor(text_norm, t):
                continue
            pos_h = _find(head_norm, term)
            pos_t = _find(text_norm, term)
            if pos_h >= 0:
                strong_head.append(term)
                head_pos = pos_h if head_pos is None else min(head_pos, pos_h)
            if pos_t >= 0:
                strong.append(term)
            if pos_h >= 0 or pos_t >= 0:
                terms.append((term, True))
        for term in t.get("support", []):
            pos_h = _find(head_norm, term)
            pos_t = _find(text_norm, term)
            if pos_h >= 0:
                support_head.append(term)
                head_pos = pos_h if head_pos is None else min(head_pos, pos_h)
            if pos_t >= 0:
                support.append(term)
            if pos_h >= 0 or pos_t >= 0:
                terms.append((term, False))
        # Minor-story concepts that are not lexicon terms (Green Climate
        # Fund -> ENV, per the rubric).
        for concept, ctid in _MINOR_CONCEPTS.items():
            if ctid == tid and _contains(text_norm, concept):
                terms.append((concept, True))
                strong.append(concept)
                if _contains(head_norm, concept):
                    strong_head.append(concept)
                    p = _find(head_norm, concept)
                    head_pos = p if head_pos is None else min(head_pos, p)
        if terms:
            out[tid] = {
                "strong_head": strong_head, "strong": strong,
                "support_head": support_head, "support": support,
                "head_pos": head_pos if head_pos is not None else 10 ** 9,
                "terms": terms,
            }
    return out


def _primary_topic(matches):
    """Tie-breaks: (1) headline main subject = Strong headline hit,
    then earliest headline term; (2) more specific (Strong > Support,
    then more matched terms); (3) earlier in RULES.md order."""
    def key(item):
        tid, m = item
        return (
            0 if m["strong_head"] else 1,          # Strong in headline
            m["head_pos"],                          # headline subject
            0 if m["strong"] else 1,                # Strong anywhere
            -len(m["terms"]),                       # more terms = specific
            TOPIC_ORDER.index(tid),                 # earlier in RULES.md
        )
    return min(matches.items(), key=key)[0]


def _secondary_topic(matches, primary):
    """A second topic that clearly applies: Strong hit in the headline
    (else a Strong hit anywhere), earliest in RULES.md order."""
    others = [(tid, m) for tid, m in matches.items() if tid != primary]
    head = [tid for tid, m in others if m["strong_head"]]
    if head:
        return min(head, key=lambda t: TOPIC_ORDER.index(t))
    any_strong = [tid for tid, m in others if m["strong"]]
    if any_strong:
        return min(any_strong, key=lambda t: TOPIC_ORDER.index(t))
    return ""


def _score3(head_norm, text_norm, matches):
    """Score-3 pattern on a Strong headline hit. Returns (topic, why)."""
    head_strong = {tid: m["strong_head"] for tid, m in matches.items()
                   if m["strong_head"]}
    if not head_strong:
        return None
    # 1. Named international organisation + approval/action verb.
    if "INT-ORG" in head_strong and _has_any(head_norm, _APPROVAL_VERBS):
        return ("INT-ORG", "named international organisation development")
    # 2. New law / ordinance / commission + approval verb.
    if _has_any(head_norm, _ORDINANCE_TERMS) and (
            _has_any(head_norm, _APPROVAL_VERBS) or
            _contains(head_norm, "draft")):
        for tid, terms in head_strong.items():
            if any(t in _ORDINANCE_TERMS or "commission" in t
                   for t in terms):
                return (tid, "new law/ordinance/commission")
        return ("BD-GOV", "new law/ordinance/commission")
    # 3. Treaty + signed/approved/ratified.
    if _has_any(head_norm, _TREATY_TERMS) and _has_any(
            head_norm, ["signed", "signs", "sign", "approved", "approves",
                        "ratified", "ratifies", "ratify", "reached",
                        "sealed", "concluded"]):
        for tid in ("INT-REL", "INT-ORG"):
            if tid in head_strong:
                return (tid, "treaty signed/approved")
        for tid, terms in head_strong.items():
            if any(t in _TREATY_TERMS for t in terms):
                return (tid, "treaty signed/approved")
    # 4. Appointment to a constitutional / major economic body.
    if _has_any(head_norm, _APPOINT_VERBS):
        for body in _APPOINT_BODIES:
            # Foreign-court guard: "Trump appoints a Supreme Court
            # justice" is not a Bangladeshi appointment — a guarded
            # court body must not fall through to the BD-GOV default.
            if body in _COURT_TERMS \
                    and _court_term_guarded(head_norm, text_norm):
                continue
            if _contains(head_norm, body):
                for tid, m in matches.items():
                    if body in m["strong"] or body in m["support"]:
                        return (tid, "appointment to a constitutional or "
                                     "major economic body")
                return ("BD-GOV", "appointment to a constitutional or "
                                   "major economic body")
    # 5. Official statistic: Strong eco term + a (non-date) number in
    # the headline.
    if _stat_digits(head_norm):
        for tid in _STAT_TOPICS:
            if tid in head_strong:
                return (tid, "official statistic")
    # 6. First / record with a number and a date (Proposal 1, syllabus):
    # a first or record in the headline, with a number and a date in
    # the article, is directly on a topic AND likely to be asked.
    # (Rankings are handled by the awards/rankings block in
    # _decide_main — a ranking scores 3 only when it states
    # Bangladesh's position.)
    if _has_first_signal(head_norm) and _has_digit(text_norm) \
            and _has_date(text_norm):
        return (_primary_topic(matches),
                "first/record with number and date")
    return None


# ---------------------------------------------------------------- main pass
def _decide_main(article, allow_opinion=False):
    if not isinstance(article, dict):
        raise ValueError("article is not a dict")
    aid = article.get("id") or ""
    title = (article.get("title") or "").strip()
    if not title:
        raise ValueError("missing title")
    if not TOPICS:
        raise RuntimeError("no topics loaded from RULES.md")

    text, _, _ = _input_text(article)
    text_norm = _norm(text)
    head_norm = _norm(title)
    url = (article.get("url") or "").lower()
    section = (article.get("section") or "").strip().lower()

    def reject(reason):
        return {"id": aid, "decision": "reject", "score": 0,
                "topic_primary": "", "topic_secondary": "",
                "evidence_quote": "", "reason": reason}

    # --- Time window: older than 36 months -> reject, reason "too old".
    pub = _parse_date(article.get("published"))
    if pub is not None:
        if pub < _months_ago(36, datetime.now(timezone.utc)):
            return reject("too old")

    # --- Opinion columns: reject (unless allow_opinion, which the
    # মতামত editorial slot uses to score opinion pieces separately
    # from the news rubric — see RULES.md Step 7 item 7).
    if not allow_opinion and (section in ("editorial", "opinion") or "/opinion/" in url \
            or "/editorial/" in url or title.lower().startswith(
                ("opinion:", "editorial:"))):
        return reject("opinion")

    crime = _has_any(text_norm, _CRIME_TERMS)
    instrument = _has_any(text_norm, _INSTRUMENT_TERMS)
    # A crime/accident story is kept ONLY if it produced an instrument.
    # Disaster carve-out: a named disaster is ENV/SCI, not crime, even
    # if it carries a crime word. Narrow list (see _DISASTER_TERMS):
    # the old "any ENV/SCI Strong match" version rescued a compensation
    # suit (ENV Strong on ক্ষতিপূরণ) — a720, 2026-11-15.
    has_disaster_strong = _has_any(text_norm, _DISASTER_TERMS)
    matches_early = _match_topics(head_norm, text_norm)

    # --- Bank robbery / single branch / single market price: reject.
    if _contains(text_norm, "robbery") or _contains(text_norm, "ডাকাতি"):
        if not instrument:
            return reject("bank robbery — not BD-BANK")
    if "branch" in head_norm.split() or _contains(head_norm, "branch"):
        if not matches_early.get("BD-BANK", {}).get("strong"):
            return reject("single branch event — not BD-BANK")
    if _contains(head_norm, "price") and (
            _contains(head_norm, "market") or _contains(head_norm, "bazaar")
            or "per kg" in head_norm or "per litre" in head_norm
            or "per liter" in head_norm):
        if not any(m["strong"] for m in matches_early.values()):
            return reject("single market price — not BD-ECO")

    # --- Crime / accident with no instrument: reject.
    if crime and not instrument and not has_disaster_strong:
        return reject("crime/accident story with no law, ordinance, "
                      "commission, directive or policy")

    # --- Minister statement with no number and no decision: reject.
    if _has_any(head_norm, _STATEMENT_VERBS) and not _has_digit(text_norm) \
            and not _has_any(text_norm, _DECISION_NOUNS) \
            and not _has_any(head_norm, _APPROVAL_VERBS):
        return reject("statement without decision or figure")

    matches = matches_early
    if not matches:
        # Rankings/indexes with no lexicon hit at all (Proposal 2):
        # the ranking itself is the topic signal. A ranking that
        # states Bangladesh's rank/position keeps (score 2, or 3 with
        # a number and a date); one with no Bangladesh position is
        # broad area only -> maybe 1.
        if (_has_any(head_norm, _AWARD_TERMS)
                or _has_any(text_norm, _AWARD_TERMS)) and (
                _has_any(head_norm, _RANK_TERMS)
                or _has_any(text_norm, _RANK_TERMS)):
            if _bd_rank_stated(text_norm):
                topic = _ranking_topic(text_norm)
                quote = _pick_quote(
                    text, text_norm,
                    [(t, True) for t in _RANK_TERMS
                     if _contains(text_norm, t)],
                    title=title) or text.split(".")[0].strip()
                if _has_digit(text_norm) and _has_date(text_norm):
                    return {"id": aid, "decision": "keep", "score": 3,
                            "topic_primary": topic, "topic_secondary": "",
                            "evidence_quote": quote,
                            "reason": "ranking stating Bangladesh's "
                                      "position, with number and date"}
                return {"id": aid, "decision": "keep", "score": 2,
                        "topic_primary": topic, "topic_secondary": "",
                        "evidence_quote": quote,
                        "reason": "ranking stating Bangladesh's position"}
            return {"id": aid, "decision": "maybe", "score": 1,
                    "topic_primary": "", "topic_secondary": "",
                    "evidence_quote": _pick_quote(
                        text, text_norm,
                        [(t, True) for t in _RANK_TERMS
                         if _contains(text_norm, t)],
                        title=title) or text.split(".")[0].strip(),
                    "reason": "ranking/index with no Bangladesh position"}
        return reject("no named topic supported")

    # --- Awards / world indexes / rankings: maybe by default.
    # Awards keep (score 2) when a Bangladeshi institution or person
    # is involved. Rankings/indexes keep (score 2) only when the
    # article states Bangladesh's rank/position (Proposal 2); with a
    # number and a date as well, they score 3 (Proposal 1).
    if _has_any(head_norm, _AWARD_TERMS) or _has_any(text_norm, _AWARD_TERMS):
        # A Strong SPORT record (world record etc.) is not an award story.
        is_record = any("record" in t for m in matches.values()
                        for t in m["strong"])
        # A story with a Strong topic hit AND a number is decided on
        # its own merits, not by the awards/rankings rule — the rule
        # is for stories ABOUT an award/ranking, not for substantive
        # stories that merely cite one (e.g. an index's findings with
        # concrete figures, like a climate-debt estimate).
        strong_substance = (any(m["strong"] for m in matches.values())
                            and _has_digit(text_norm))
        if not is_record and not strong_substance:
            is_ranking = _has_any(head_norm, _RANK_TERMS) or \
                _has_any(text_norm, _RANK_TERMS)
            if is_ranking:
                if _bd_rank_stated(text_norm):
                    primary = _primary_topic(matches)
                    quote = _pick_quote(
                        text, text_norm,
                        [t for m in matches.values() for t in m["terms"]],
                        title=title)
                    if not quote:
                        return reject("no evidence quote")
                    if _has_digit(text_norm) and _has_date(text_norm):
                        return {"id": aid, "decision": "keep", "score": 3,
                                "topic_primary": primary,
                                "topic_secondary": _secondary_topic(matches, primary),
                                "evidence_quote": quote,
                                "reason": "ranking stating Bangladesh's "
                                          "position, with number and date"}
                    return {"id": aid, "decision": "keep", "score": 2,
                            "topic_primary": primary,
                            "topic_secondary": _secondary_topic(matches, primary),
                            "evidence_quote": quote,
                            "reason": "ranking stating Bangladesh's position"}
                return {"id": aid, "decision": "maybe", "score": 1,
                        "topic_primary": "", "topic_secondary": "",
                        "evidence_quote": _pick_quote(
                            text, text_norm,
                            [t for m in matches.values() for t in m["terms"]],
                            title=title)
                        or text.split(".")[0].strip(),
                        "reason": "ranking/index with no Bangladesh position"}
            if _has_any(text_norm, _BD_MARKERS):
                primary = _primary_topic(matches)
                quote = _pick_quote(
                    text, text_norm,
                    [t for m in matches.values() for t in m["terms"]],
                    title=title)
                if not quote:
                    return reject("no evidence quote")
                return {"id": aid, "decision": "keep", "score": 2,
                        "topic_primary": primary,
                        "topic_secondary": _secondary_topic(matches, primary),
                        "evidence_quote": quote,
                        "reason": "award/ranking involving a Bangladeshi "
                                  "institution or person"}
            return {"id": aid, "decision": "maybe", "score": 1,
                    "topic_primary": "", "topic_secondary": "",
                    "evidence_quote": _pick_quote(
                        text, text_norm,
                        [t for m in matches.values() for t in m["terms"]],
                        title=title)
                    or text.split(".")[0].strip(),
                    "reason": "award/ranking with no Bangladeshi "
                              "institution or person"}

    # --- Ordinary sport result (one bilateral match): maybe 1.
    sport = matches.get("SPORT")
    if sport and not sport["strong"]:
        if _contains(head_norm, "match") or _contains(head_norm, "series") \
                or _contains(text_norm, "match"):
            quote = _pick_quote(text, text_norm, sport["terms"], title=title)
            return {"id": aid, "decision": "maybe", "score": 1,
                    "topic_primary": "", "topic_secondary": "",
                    "evidence_quote": quote or text.split(".")[0].strip(),
                    "reason": "ordinary bilateral match result"}

    # --- Score 3: Strong headline hit + score-3 pattern.
    s3 = _score3(head_norm, text_norm, matches)
    if s3:
        topic3, why = s3
        quote = _pick_quote(text, text_norm, matches[topic3]["terms"], title=title)
        if not quote:
            return reject("no evidence quote")
        reason = why
        if crime and instrument:
            reason += "; instrument only"
        return {"id": aid, "decision": "keep", "score": 3,
                "topic_primary": topic3,
                "topic_secondary": _secondary_topic(matches, topic3),
                "evidence_quote": quote, "reason": reason}

    # --- Score 2 / 1.
    primary = _primary_topic(matches)
    m = matches[primary]
    terms_all = [t for mm in matches.values() for t in mm["terms"]]
    quote = _pick_quote(text, text_norm, terms_all, title=title)
    if not quote:
        return reject("no evidence quote")

    strong_any = bool(m["strong"])
    # Support-only hit is score 2 only if it is concrete: a number, a
    # decision/action verb, two or more terms from the same topic, or a
    # Strong term in the summary. Otherwise it is broad area only -> 1.
    # Support-only cap (RULES.md): a Support-only hit (no Strong term
    # matched in ANY topic) is broad area only, score 1, for ALL topics
    # — it caps at maybe/1 no matter how concrete it looks (a bare
    # number in the summary does not rescue it; that was the
    # US-flight-delay miss of 14 Nov). The one exemption is a
    # crime/accident story rescued by an instrument (law/ordinance/
    # commission/directive/policy): it keeps whatever score its
    # concrete signals give it.
    strong_anywhere = any(mm["strong"] for mm in matches.values())
    support_only = not strong_any and not strong_anywhere
    digit_concrete = _has_digit(text_norm) and not support_only
    concrete = (
        digit_concrete
        or _has_any(head_norm, _ACTION_VERBS)
        or len(m["support"]) + len(m["strong"]) >= 2
        or bool(m["strong"])
        or strong_anywhere
    )
    if support_only and not (crime and instrument):
        concrete = False
    if strong_any or concrete:
        if m["strong"]:
            reason = ("strong match: %s (%s)"
                      % (", ".join(m["strong"]), primary))
        else:
            reason = ("support match: %s (%s)"
                      % (", ".join(m["support"][:2]), primary))
        if crime and instrument:
            reason = "instrument only: " + reason
        return {"id": aid, "decision": "keep", "score": 2,
                "topic_primary": primary,
                "topic_secondary": _secondary_topic(matches, primary),
                "evidence_quote": quote, "reason": reason}

    return {"id": aid, "decision": "maybe", "score": 1,
            "topic_primary": "", "topic_secondary": "",
            "evidence_quote": quote,
            "reason": "same broad area, no named topic"}


def score_editorial(article):
    """Score one opinion/editorial article for the মতামত slot
    (RULES.md Step 7 item 7): the same rubric as decide(), except
    the opinion-reject does not apply. Returns the decision dict.
    The slot takes the best-scoring editorial of the day, and only
    if it scores 2 or higher; anything below that leaves the slot
    empty. Never raises."""
    return decide(article, allow_opinion=True)


def decide(article, allow_opinion=False):
    """Decide one article. Never raises.

    allow_opinion=True skips the opinion-column reject (used only by
    the মতামত editorial slot via score_editorial); the news path
    always uses False.
    """
    try:
        return _decide_main(article, allow_opinion=allow_opinion)
    except Exception:
        pass
    try:
        return _decide_simple(article)
    except Exception:
        return _fallback(article)


def decide_batch(articles, allow_opinion=False):
    """Decide a list of articles. Never raises (per-article fallback)."""
    out = []
    for a in articles or []:
        try:
            out.append(decide(a, allow_opinion=allow_opinion))
        except Exception:
            out.append(_fallback(a))
    return out


def _decide_simple(article):
    """Simpler keyword pass (retry): plain Strong/Support substring
    scan, no edge rules. Score 2 for a Strong hit, 1 for Support, else 0."""
    aid = article.get("id") or "" if isinstance(article, dict) else ""
    title = (article.get("title") or "").strip() if isinstance(article, dict) else ""
    if not title:
        raise ValueError("missing title")
    text, title, _ = _input_text(article)
    text_norm = _norm(text)
    head_norm = _norm(title)
    best = None
    for tid in TOPIC_ORDER:
        t = TOPICS[tid]
        for term in t.get("strong", []):
            # Same guards as the main pass: a foreign court is not
            # BD-GOV, and "record" without a sports anchor is not SPORT.
            if tid == "BD-GOV" and term in _COURT_TERMS \
                    and _court_term_guarded(head_norm, text_norm):
                continue
            if tid == "SPORT" and term in _RECORD_TERMS \
                    and not _has_sport_anchor(text_norm, t):
                continue
            if _contains(text_norm, term):
                best = (tid, term, True)
                break
        if best:
            break
    if best is None:
        for tid in TOPIC_ORDER:
            t = TOPICS[tid]
            for term in t.get("support", []):
                if _contains(text_norm, term):
                    best = (tid, term, False)
                    break
            if best:
                break
    if best is None:
        return {"id": aid, "decision": "reject", "score": 0,
                "topic_primary": "", "topic_secondary": "",
                "evidence_quote": "", "reason": "no named topic supported"}
    tid, term, is_strong = best
    quote = _pick_quote(text, text_norm, [(term, is_strong)], title=title)
    if not quote:
        return {"id": aid, "decision": "reject", "score": 0,
                "topic_primary": "", "topic_secondary": "",
                "evidence_quote": "", "reason": "no evidence quote"}
    if is_strong:
        return {"id": aid, "decision": "keep", "score": 2,
                "topic_primary": tid, "topic_secondary": "",
                "evidence_quote": quote,
                "reason": "strong match (simple pass): %s" % term}
    return {"id": aid, "decision": "maybe", "score": 1,
            "topic_primary": "", "topic_secondary": "",
            "evidence_quote": quote,
            "reason": "support match only (simple pass)"}


def _fallback(article):
    aid = ""
    try:
        if isinstance(article, dict):
            aid = article.get("id") or ""
    except Exception:
        pass
    return {"id": aid, "decision": "maybe", "score": 1,
            "topic_primary": "", "topic_secondary": "",
            "evidence_quote": "", "reason": "decider fallback"}


# ---------------------------------------------------------------- __main__
def main(argv=None):
    ap = argparse.ArgumentParser(description="Step 3 decider (engine v2)")
    ap.add_argument("input", help="articles JSON file "
                    "({date, articles:[...]} or a bare list)")
    ap.add_argument("--out", help="output path (default: "
                    "decisions-<date>.json beside the input file)")
    args = ap.parse_args(argv)

    in_path = Path(args.input)
    data = json.loads(in_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        date = data.get("date") or ""
        articles = data.get("articles") or []
    else:
        date, articles = "", data
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    decisions = decide_batch(articles)
    out_path = Path(args.out) if args.out else \
        in_path.parent / ("decisions-%s.json" % date)
    payload = {"date": date, "decided": len(decisions),
               "decisions": decisions}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    counts = {"keep": 0, "maybe": 0, "reject": 0}
    for d in decisions:
        counts[d["decision"]] = counts.get(d["decision"], 0) + 1
    print("decided %d articles -> %s" % (len(decisions), out_path))
    print("keep=%d maybe=%d reject=%d" % (counts["keep"], counts["maybe"],
                                          counts["reject"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
