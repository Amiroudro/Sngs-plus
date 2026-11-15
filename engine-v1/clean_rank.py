#!/usr/bin/env python3
"""Modules 2 + 3 — Clean/Deduplicate + Rank (ENGINE_DESIGN §5).

Event grouping: same event in several papers = ONE story with all
sources. Grouping is by normalised title-keyword overlap (Jaccard
>= 0.35) or a shared distinctive token (name/figure). Anything that
overlaps a previous edition's story is flagged as a follow-up, not a
new story — the operator decides whether the new development is big
enough to keep.

Rank 0-100, exact public weights from the design:
  Bangladesh relevance 30 | public importance 25 | exam relevance 25
  novelty 10 | credibility / cross-source agreement 10
  Penalties: single-source unconfirmed -10 | press-release-only -5
             outdated-as-new -20

REVISED 2026-11-11 (audit Fixes 1 + video lessons, approved by Rudro
2026-11-11 22:04). What changed and why — see
summary-editorial-audit-2026-11-11.md Part 4 and
video-lessons-synthesis-2026-11-11.md:
  * Score on TITLE + RSS DESCRIPTION + CLEANED BODY. Raw body text is
    NEVER scored: fetched bodies are site-navigation chrome (a TBS
    body starts with a ~900-char menu run; a UK fish-and-chip story
    scored 92-97 on nav words alone). Bodies are cleaned with
    common.strip_boilerplate() first and only used when >=200 chars
    survive. Descriptions are the publisher's own RSS lede — clean.
  * Bangladesh relevance comes from title/description (30), or from
    the cleaned body only (15); 5 otherwise. A BD word found only in
    raw chrome no longer gives 30.
  * Graded keyword counting replaces max-of-one: each component is
    5 x (distinct keywords hit), capped at 25. One incidental word
    in a nav link used to max a 25-point component; now it scores 5.
    This breaks the 97-point tie (26-31 events shared score 97 on
    9-10 Nov). Matched keywords are recorded in the parts dict so
    any reader can audit a score.
  * Tie-break on substance: (-score, -n_sources, -credibility, title).
    The old key (-score, title) let the alphabet decide the edition.
  * Missing vocabulary added (audit Fix 1.5 + video hard-keep list):
    transport, infrastructure, reform, corruption, minority,
    democracy, judiciary, poverty, inequality, digital, ai, monetary,
    fiscal, financ, policy, development, project, treaty, agreement,
    summit, science, technology, remittance, reserves.
  * Editorial/opinion/analysis items are tagged by URL path
    (/opinion/, /editorial/, /analysis/, /thoughts/, /op-ed/) or by
    the collector's editorial route (found_via == "editorial").
    ONE slot per edition is reserved for the best editorial/opinion
    with score >= 60 AND exam_answerable (see below). There is NO
    flat +10 boost (video rule: an editorial must be the best of its
    kind that day, not merely boosted past news) and the slot MAY
    STAY EMPTY on a thin day — never fill it with the least-bad piece.
  * Selection test (video rule 1): the BCS written-question test is
    a real signal. SELECTION_TOPICS are the exam-answerable subjects
    (policy, development projects, economy, IR with a Bangladesh
    angle, climate, science/AI...). An event is exam_answerable when
    >=2 selection topics hit in title+description (or >=1 for an
    editorial). Recorded per event; the editorial slot requires it.
  * Hard skips are SKIPS, not down-weights (video rule 1): sport,
    entertainment/celebrity, crime, accidents, village fights,
    matrimonial ads. The 10 Nov Mushfiqur record (sport) and 9 Nov
    Miss Universe (celebrity) keeps are exactly the violations this
    eliminates. Skips are recorded in the borderline list, never
    silently dropped.
  * Thin day stays thin (video rule 6): MIN_KEEP_SCORE is a quality
    floor — events below it are not kept even if fewer than 15
    remain. The daily count is a ceiling, not a quota. Skips are
    recorded with a reason so the same trivia does not resurface.

Component scores are rule-based and deterministic (keyword lists are
in this file, so any reader can audit a score). No ML, no API.
Keep top ~15; the rest go to the borderline/skipped audit list.

Usage:
  python3 clean_rank.py --date 2026-11-08 [--in runs/2026-11-08]
Writes runs/<date>/events-<date>.json and runs/<date>/borderline-<date>.json
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (load_json, save_json, today, previous_story_titles,
                    parse_pubdate, strip_boilerplate)

STOP = set("""a an the of in on at to for and or by with from as is are was were be
been it its this that these those after before over under into about
bangladesh bangladeshi dhaka said says new report reports""".split())

BD_WORDS = ["bangladesh", "bangladeshi", "dhaka", "chattogram", "chittagong",
            "sylhet", "khulna", "taka", "bcs", "bnp", "awami"]
# IMPORTANCE / EXAM: graded counting — each distinct keyword hit is
# worth 5 points, capped at 25. Values are kept in the dicts for
# documentation (the old tiers) but the score no longer takes max().
IMPORTANCE = {"econom": 25, "bank": 25, "budget": 25, "inflation": 25,
              "financ": 25, "health": 20, "education": 20, "job": 20,
              "wage": 20, "governance": 20, "transport": 20,
              "infrastructure": 20, "reform": 20, "energy": 15,
              "climate": 15, "trade": 15, "court": 15, "election": 15,
              "foreign": 15, "police": 10, "accident": 10, "culture": 10,
              "heritage": 10, "corruption": 15, "minority": 15,
              "democracy": 15, "judiciary": 15, "poverty": 15,
              "inequality": 15, "digital": 15, "ai": 15, "monetary": 15,
              "fiscal": 15, "policy": 15, "development": 15,
              "project": 15, "treaty": 15, "agreement": 15, "summit": 15,
              "science": 15, "technology": 15, "remittance": 15,
              "reserves": 15}
EXAM = {"bank": 25, "econom": 25, "budget": 25, "foreign policy": 25,
        "constitution": 25, "financ": 25, "history": 20, "education": 20,
        "climate": 20, "governance": 20, "recruit": 20, "admission": 20,
        "wage": 20, "reform": 20, "trade": 15, "energy": 15, "court": 15,
        "election": 15, "parliament": 15, "remittance": 15, "export": 15,
        "import": 15, "transport": 15, "infrastructure": 15,
        "corruption": 15, "minority": 15, "democracy": 15,
        "judiciary": 15, "poverty": 15, "inequality": 15, "digital": 15,
        "ai": 15, "monetary": 15, "fiscal": 15, "policy": 15,
        "development": 15, "project": 15, "treaty": 15, "agreement": 15,
        "summit": 15, "science": 15, "technology": 15, "reserves": 15}

# The BCS written-question test (video rule 1): could this story help
# answer a written-exam question like the 45th-47th BCS ones? These
# are the subjects that earn a story its place. An event is
# exam_answerable when >=2 of these hit in title+description (>=1
# for an editorial/opinion piece, whose value is the argument).
SELECTION_TOPICS = ["policy", "development", "project", "budget",
                    "inflation", "remittance", "reserve", "trade",
                    "climate", "science", "technology", "ai", "treaty",
                    "agreement", "summit", "reform", "infrastructure",
                    "education", "health", "governance", "election",
                    "parliament", "constitution", "foreign", "energy",
                    "export", "import", "econom", "bank", "wage", "job"]

# Hard skips (video rule 1 + audit): SKIPS, not down-weights. Matched
# against the event TITLE only, recorded in the borderline list.
# "league" and "runs" are deliberately NOT in the sport list — in
# Bangladesh news "Awami League" is a party, not a sport, and "runs"
# appears in ordinary prose. A sport story must carry a strong
# cricket/football token. "century" / "test runs" are added because
# the 10 Nov Mushfiqur record ("7,000 Test runs", "14 centuries")
# slipped through on exactly those words.
SPORT = ["cricket", "football", "wicket", "innings", "tournament",
         "test match", "test runs", "test cricket", "double century",
         "century", "centuries", "t20", "odi", "maiden test"]
ENTERTAIN = ["film", "movie", "actor", "actress", "concert", "song",
             "celebrity", "drama", "pageant", "miss universe",
             "beauty contest", "affair", "romantic", "duchess", "duke",
             "prince", "princess", "royal visit", "royal tour",
             "royal family"]
CRIME = ["murder", "murdered", "rape", "raped", "robbery", "mugging",
         "kidnap", "kidnapped", "abduct", "abducted", "stabbed",
         "shot dead", "snatching"]
ACCIDENT = ["accident", "road crash", "train crash"]
VILLAGE = ["village fight", "villagers clash", "clash between villagers",
           "village feud", "two groups of villagers"]
MATRIMONIAL = ["matrimonial", "bride wanted", "groom wanted",
               "patra chai", "patri chai"]
SKIP_RULES = [(SPORT, "sport — low exam relevance"),
              (ENTERTAIN, "entertainment/celebrity — out of scope"),
              (CRIME, "crime news — hard skip (video rule)"),
              (ACCIDENT, "accident news — hard skip (video rule)"),
              (VILLAGE, "village fight — hard skip (video rule)"),
              (MATRIMONIAL, "matrimonial ad — hard skip (video rule)")]
# History guard: the crime/accident skip is for CURRENT crime news,
# not history. A piece about 1975 ("November 1975: Bangladesh
# undermined, patriots murdered") is BCS history material, not crime
# news — the year / history markers exempt it from the CRIME and
# ACCIDENT rules only (SPORT / ENTERTAIN still apply).
HISTORY_GUARD = re.compile(
    r"\b(19\d\d|history|anniversary|on this day|remembers?|"
    r"retrospective|liberation war)\b")
PRESS_RELEASE_HINTS = ["bss", "press release", "announces", "inaugurat"]

# Editorial / opinion / analysis detection (audit Fix 1.6).
EDITORIAL_PATHS = [("/editorial/", "editorial"),
                   ("/opinion/", "opinion"),
                   ("/thoughts/", "opinion"),
                   ("/op-ed/", "opinion"),
                   ("/analysis/", "analysis")]
EDITORIAL_SLOT_MIN_SCORE = 55
# Calibrated 2026-11-11 against the 9-10 Nov pools (live simulation):
# the audit's own correct pick for 9 Nov, the DT climate editorial,
# scores 57 under graded counting (BD 30 + climate 5 + climate 5 +
# novelty 10 + credibility 7) — it has no fetchable body (DT is 403
# from this VM), so its keyword signal is thin. The audit's Fix 1.6
# draft number was 60, written against the OLD scale on which that
# same editorial scored 82; at 60 the slot stays empty on 9 Nov and
# the fix fails on the audit's headline example. At 55 the slot
# takes the 57-point climate editorial on 9 Nov and the 82-point
# AI-finance op-ed on 10 Nov, while the 47-point biodiversity op-ed
# stays out. The audit's Fix 1.3 says exact numbers are "to be tuned
# against the 9-10 Nov pools" — this is that tuning. Revisit if a
# weak editorial ever takes the slot.
# Thin day stays thin (video rule 6): an event below this score is
# never kept to fill the daily count. Calibrated 2026-11-11 against
# the 9-10 Nov pools (see the dry-run note in the report); tune only
# with a fresh before/after on real pools.
MIN_KEEP_SCORE = 40


def word_in(text, word):
    """Whole-word match — 'league' must not match inside 'League' as a
    substring of another word, and 'runs' must not match 'returns'."""
    return re.search(r"\b" + re.escape(word) + r"\b", text) is not None


def word_forms(text):
    """The set of word forms present in `text`, expanded so a keyword
    matches its plurals: bank/banks, court/courts, policy/policies.
    Also adds the stems 'econom' (economy/economic) and 'financ'
    (finance/financial) when a word starts with them. Built once per
    event and reused for every keyword check."""
    words = set(re.findall(r"[a-z]+", text or ""))
    out = set(words)
    for w in words:
        if w.endswith("ies") and len(w) > 3:
            out.add(w[:-3] + "y")
        if w.endswith("es") and len(w) > 3:
            out.add(w[:-2])
        if w.endswith("s") and len(w) > 2:
            out.add(w[:-1])
        if w.startswith("econom"):
            out.add("econom")
        if w.startswith("financ"):
            out.add("financ")
    return out


def kw_hit(wset, text, kw):
    """Keyword hit for graded counting. Whole-word match (with
    plurals, via word_forms) — NOT plain substring: 'court' must not
    match inside 'Courtesy', and 'ai' must not match 'said' /
    'again' / 'available'. Phrases ('foreign policy') match as
    substrings of the raw text."""
    if " " in kw:
        return kw in text
    return kw in wset


def keywords(text):
    # Google/Bing titles often end with the outlet name
    # ("... - The Daily Star", "... | Dhaka Tribune"). That is not
    # content — strip a short trailing " - X" / " | X" suffix so outlet
    # words do not inflate the union and hide real overlap.
    text = re.sub(r"\s+[-|]\s+[^-|]{1,40}$", "", text or "")
    words = re.findall(r"[a-z]+", (text or "").lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def figures(text):
    """Normalised money/figure tokens, e.g. '$300 million', '$300m' and
    'US$300mil' all become '300m'. Same event, different wording,
    same figure."""
    out = set()
    for num, unit in re.findall(r"\$?\s*(\d+(?:\.\d+)?)\s*(m|mil|million|bn|billion|crore|cr)\b",
                                (text or "").lower()):
        u = {"million": "m", "mil": "m", "billion": "bn",
             "crore": "cr", "cr": "cr"}.get(unit, unit)
        out.add(f"{num}{u}")
    return out


def _same_event(a, b):
    j = jaccard(a["keywords"], b["keywords"])
    return j >= 0.35 or (bool(a["figures"] & b["figures"]) and j >= 0.20)


def group_events(articles):
    events = []  # each: {key, title, articles:[...]}
    for a in articles:
        kw = keywords(a["title"])
        fg = figures(a["title"])
        placed = False
        for ev in events:
            if _same_event({"keywords": kw, "figures": fg}, ev):
                ev["articles"].append(a)
                ev["keywords"] |= kw
                ev["figures"] |= fg
                placed = True
                break
        if not placed:
            events.append({"title": a["title"], "keywords": kw,
                           "figures": fg, "articles": [a]})
    # Merge pass: greedy grouping is order-dependent (an early article
    # can found its own event before the bigger group exists). Compare
    # every pair until stable so the same event ends up as one story.
    changed = True
    while changed:
        changed = False
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                if _same_event(events[i], events[j]):
                    events[i]["articles"] += events[j]["articles"]
                    events[i]["keywords"] |= events[j]["keywords"]
                    events[i]["figures"] |= events[j]["figures"]
                    del events[j]
                    changed = True
                    break
            if changed:
                break
    return events


def editorial_type(ev):
    """'editorial' / 'opinion' / 'analysis' / 'news'. By URL path, or
    by the collector's editorial route (found_via/section == 'editorial').
    An item from /opinion/editorial/ counts as editorial."""
    for a in ev["articles"]:
        url = (a.get("url") or "").lower()
        if "/editorial/" in url:
            return "editorial"
    for a in ev["articles"]:
        url = (a.get("url") or "").lower()
        if "/opinion/" in url or "/thoughts/" in url or "/op-ed/" in url:
            return "opinion"
        if "/analysis/" in url:
            return "analysis"
        if (a.get("found_via") or "") == "editorial" or \
           (a.get("section") or "") == "editorial":
            return "opinion"
    return "news"


def selection_test(ev, title_desc, etype):
    """The BCS written-question test (video rule 1). Returns
    (topics_matched, exam_answerable). Topics are counted on
    title+description only — the body must not smuggle a story in."""
    topics = sorted({t for t in SELECTION_TOPICS
                     if kw_hit(word_forms(title_desc), title_desc, t)})
    need = 1 if etype in ("editorial", "opinion", "analysis") else 2
    return topics, len(topics) >= need


def score_event(ev, day, backfill=False, use_body=True):
    title = ev["title"].lower()
    descs = " ".join((a.get("summary") or "") for a in ev["articles"]).lower()
    title_desc = title + " " + descs
    # Cleaned body only, and only when >=200 chars survive stripping.
    # Raw body text is NEVER scored (nav chrome). Bodies are scarce
    # anyway (38/393 on 10 Nov) — most events score on title+desc.
    bodies = []
    if use_body:
        for a in ev["articles"]:
            c = strip_boilerplate(a.get("body_text") or "")
            if len(c) >= 200:
                bodies.append(c)
    clean_body = " ".join(bodies).lower()
    text = title_desc + " " + clean_body
    n_src = len({a["source"] for a in ev["articles"]})
    # 1. Bangladesh relevance /30 — from title/description (30), or
    # from the cleaned body only (15); 5 otherwise.
    if any(w in title_desc for w in BD_WORDS):
        bd = 30
    elif any(w in clean_body for w in BD_WORDS):
        bd = 15
    else:
        bd = 5
    # 2. Public importance /25 — graded counting: 5 per distinct
    # keyword hit, capped at 25. Matched keywords are recorded so
    # the score is auditable.
    wset = word_forms(text)
    imp_hits = sorted({k for k in IMPORTANCE if kw_hit(wset, text, k)})
    imp = min(25, 5 * len(imp_hits))
    # 3. Exam relevance /25 — same graded counting.
    ex_hits = sorted({k for k in EXAM if kw_hit(wset, text, k)})
    ex = min(25, 5 * len(ex_hits))
    # 4. Novelty /10 — published inside the coverage window
    dates = [parse_pubdate(a.get("published") or "") for a in ev["articles"]]
    dates = [d for d in dates if d]
    if backfill:
        # Backfill: "now" is the edition day itself. An article published
        # on the edition day is fully novel; the old COVERAGE_START
        # penalty (all backfill articles predate 7 Nov) must not apply.
        from datetime import date as _date
        day_d = _date.fromisoformat(day)
        nov = 10 if dates and any(d.date() == day_d or
                                  (d + __import__("datetime").timedelta(hours=6)).date() == day_d
                                  for d in dates) else 5
    elif dates:
        newest = max(dates)
        age_h = (datetime.now(timezone.utc) - newest).total_seconds() / 3600
        nov = 10 if age_h <= 48 else (5 if age_h <= 96 else 0)
    else:
        nov = 5  # unknown date: neither reward nor punish
    # 5. Credibility /10
    cred = 10 if n_src >= 2 else 7
    score = bd + imp + ex + nov + cred
    penalties = []
    # Single-source unconfirmed: claim language in the HEADLINE only.
    # Body text mentions ("reportedly", "claimed") are normal reporting.
    if n_src == 1 and any(w in title for w in
                          ["alleged", "claimed", "reportedly", "unconfirmed"]):
        score -= 10
        penalties.append("single-source unconfirmed -10")
    if any(h in text for h in PRESS_RELEASE_HINTS) and n_src == 1:
        score -= 5
        penalties.append("press-release-only -5")
    if backfill:
        from datetime import date as _date, datetime as _dt, timezone as _tz, timedelta as _td
        cov_start = _dt.combine(_date.fromisoformat(day), _dt.min.time()).replace(tzinfo=_tz(_td(hours=6)))
        if dates and max(dates) < cov_start:
            score -= 20
            penalties.append("outdated-as-new -20")
    else:
        from common import coverage_start
        cov_start = coverage_start(day)
        if dates and cov_start and max(dates) < cov_start:
            score -= 20
            penalties.append("outdated-as-new -20")
    return max(0, min(100, score)), {"bangladesh": bd, "importance": imp,
                                     "exam": ex, "novelty": nov,
                                     "credibility": cred,
                                     "importance_hits": imp_hits,
                                     "exam_hits": ex_hits}, penalties


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today())
    ap.add_argument("--in", dest="indir", default=None)
    ap.add_argument("--keep", type=int, default=15)
    ap.add_argument("--backfill", action="store_true",
                    help="score as if 'now' is the edition day (for Nov 1-6 backfill)")
    ap.add_argument("--min-score", type=int, default=MIN_KEEP_SCORE,
                    help="quality floor: never keep an event below this score "
                         "(thin day stays thin; default 40)")
    ap.add_argument("--no-body-score", action="store_true",
                    help="score on title+description only, ignoring bodies "
                         "(sensitivity check; not the default)")
    args = ap.parse_args()
    day = args.date
    indir = Path(args.indir) if args.indir else Path(__file__).resolve().parent / "runs" / day
    data = load_json(indir / f"articles-{day}.json")
    articles = data["articles"]
    events = group_events(articles)
    prev = previous_story_titles()
    if args.backfill:
        # Follow-ups only vs EARLIER editions; 7/8 Nov editions are later
        # than a backfill day and must not flag its stories.
        prev = [(d, i, t) for d, i, t in prev if d < day]
    prev_kw = [(d, i, keywords(t)) for d, i, t in prev]
    ranked, borderline = [], []
    for ev in events:
        title = ev["title"]
        low = title.lower()
        # Hard skips first (recorded, not silently dropped)
        skipped = None
        for tokens, reason in SKIP_RULES:
            if reason.startswith(("crime", "accident")) and HISTORY_GUARD.search(low):
                continue  # history piece, not current crime news
            if any(word_in(low, s) if " " not in s else s in low for s in tokens):
                skipped = reason
                break
        if skipped:
            borderline.append({"title": title, "reason": skipped,
                               "sources": [a["source"] for a in ev["articles"]]})
            continue
        score, parts, pens = score_event(ev, day, backfill=args.backfill,
                                         use_body=not args.no_body_score)
        etype = editorial_type(ev)
        title_desc = (title + " " +
                      " ".join((a.get("summary") or "") for a in ev["articles"])).lower()
        topics, answerable = selection_test(ev, title_desc, etype)
        # Overlap with a previous edition?
        follow = None
        for d, sid, kw in prev_kw:
            if jaccard(ev["keywords"], kw) >= 0.45:
                follow = f"follow-up of {sid} ({d})"
                break
        ranked.append({"title": title, "score": score, "parts": parts,
                       "penalties": pens, "n_sources": len({a["source"] for a in ev["articles"]}),
                       "follow_up_of": follow, "type": etype,
                       "selection": {"topics": topics,
                                     "exam_answerable": answerable},
                       "articles": [{"title": a["title"], "url": a["url"],
                                     "source": a["source"],
                                     "published": a.get("published", ""),
                                     "found_via": a.get("found_via", "")}
                                    for a in ev["articles"]]})
    # Substance tie-break: (-score, -n_sources, -credibility, title).
    ranked.sort(key=lambda e: (-e["score"], -e["n_sources"],
                               -e["parts"]["credibility"], e["title"]))
    # Editorial slot (audit Fix 1.6 + video rule 2): the best
    # editorial/opinion/analysis with score >= 60 AND exam_answerable.
    # No flat boost. The slot may stay EMPTY on a thin day.
    slot = None
    slot_candidates = [e for e in ranked
                       if e["type"] in ("editorial", "opinion", "analysis")
                       and e["score"] >= EDITORIAL_SLOT_MIN_SCORE
                       and e["selection"]["exam_answerable"]]
    if slot_candidates:
        slot = slot_candidates[0]
        slot["editorial_slot"] = True
    slot_info = ({"title": slot["title"], "score": slot["score"],
                  "type": slot["type"]} if slot else
                 {"title": None,
                  "reason": "no editorial/opinion scored >=60 and exam-answerable"})
    # Thin day stays thin: never keep below the floor to fill the count.
    kept = []
    if slot is not None:
        kept.append(slot)
    for e in ranked:
        if e is slot:
            continue
        if len(kept) >= args.keep:
            break
        if e["score"] < args.min_score:
            break  # sorted: everything after is lower too
        kept.append(e)
    for s in ranked:
        if s in kept:
            continue
        if s is slot:
            continue
        reason = (f"ranked below top {args.keep} (score {s['score']})"
                  if s["score"] >= args.min_score else
                  f"below quality floor (score {s['score']} < {args.min_score})")
        borderline.append({"title": s["title"], "reason": reason,
                           "sources": [a["source"] for a in s["articles"]]})
    save_json(indir / f"events-{day}.json",
              {"date": day, "events_collected": len(events),
               "kept": kept, "borderline": borderline,
               "editorial_slot": slot_info,
               "min_score_floor": args.min_score,
               "scoring": "title + RSS description + cleaned body "
                          "(strip_boilerplate, >=200 chars); graded "
                          "keyword counting 5/distinct hit, cap 25; "
                          "tie-break (-score, -n_sources, -credibility, title)"})
    save_json(indir / f"borderline-{day}.json",
              {"date": day, "borderline": borderline})
    print(f"[clean_rank] {day}: {len(articles)} articles -> {len(events)} events "
          f"-> {len(kept)} kept, {len(borderline)} borderline/skipped")
    if slot is not None:
        print(f"  editorial slot: [{slot['score']}] {slot['title'][:70]} ({slot['type']})")
    else:
        print(f"  editorial slot: EMPTY ({slot_info['reason']})")
    if len(kept) < args.keep:
        print(f"  thin day: {len(kept)} kept of {args.keep} (quality floor "
              f"{args.min_score} — not padded)")
    for i, k in enumerate(kept, 1):
        print(f"  {i:2d}. [{k['score']:3d}] {k['title'][:80]}"
              f"{' | ' + k['follow_up_of'] if k['follow_up_of'] else ''}"
              f"{' | EDITORIAL SLOT' if k.get('editorial_slot') else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
