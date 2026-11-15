#!/usr/bin/env python3
"""Modules 4 + 5 — Summarise + Exam-Generate (ENGINE_DESIGN §5).

Two modes, because the AI brain is Rudro's Claude Project (free),
not a paid API — there is no API key in this repo and none is needed:

(a) --prompt : from the ranked events + collected articles, generate a
    ready-to-paste Claude Project prompt + a pack template
    (runs/<date>/claude-prompt-<date>.md). Rudro pastes it into his
    Claude Project with the articles, Claude returns a reviewed pack
    as JSON, and mode (b) imports it. The prompt carries the design's
    rules verbatim: ~60-word summaries, sources named+linked, no
    invented facts/figures/Bangla, IMPORTANCE_RULES for words, MCQ
    counts 10 vocab + 2 phrases + 13 current affairs, answers separate.

(b) --import-pack reviewed-pack-<date>.json : validate + assemble a
    DRAFT edition JSON in the exact Edition 1 contract shape
    (~/workspace/sarangsho-plus/data-2026-11-07.json). Checks:
    - every story has >=1 real http source URL, and every source URL
      appears in the collected articles (or the paste file);
    - words screened against all previous editions (no duplicates,
      case-insensitive) — duplicates are moved to borderline, not
      silently kept;
    - revision words picked by SRS from previous editions (due today:
      first-seen + 1/3/7/14/30/60 days), 5 prompts;
    - MCQ count and split, every MCQ's `source` traces to a story id
      in the same edition.
    The draft is written with status "draft". It is NOT published —
    publish.py + a human approval do that.

Pack JSON shape (what Claude / the operator returns):
  {"stories":[{...same fields as edition stories...}],
   "words":[{...same fields as edition words...}],
   "phrases":[...], "mcqs":[...]}
Revision words are computed here from previous editions, not by Claude.

Usage:
  python3 summarise_exam.py --date 2026-11-08 --prompt
  python3 summarise_exam.py --date 2026-11-08 --import-pack runs/2026-11-08/reviewed-pack-2026-11-08.json
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (load_json, save_json, today, previous_editions,
                    previous_headwords, EDITION_1, strip_boilerplate,
                    new_fact_tokens, has_attribution, OPINION_URL_MARKERS,
                    coverage_label)

SRS_GAPS = [1, 3, 7, 14, 30, 60]
TARGET = {"stories": 15, "words": 20, "phrases": 10, "mcqs": 25,
          "mcq_vocab": 10, "mcq_phrases": 2, "mcq_ca": 13, "revision": 5}

RULES = """RULES (from the approved engine design — do not break them).
REVISED 2026-11-11 (audit Fix 3 + video lessons, approved by Rudro
2026-11-11 22:04). The old Rule 2 ("Summary ~60 words") is replaced
by Rules 2-12 below — the audit found summaries were not wrong but
shallow: they paraphrased the opening paragraphs and dropped the
lead figure, the cause, and the second half, where the exam detail
lives. A summary that reports a trend without its cause, or a figure
without the comparison that makes it meaningful, is incomplete.
1. NEVER invent a story, figure, date, name, quote or source URL. If a
   fact is not in the articles below, leave it out and say so.
2. INPUT: every story below carries its RSS description and, where one
   was fetched, the cleaned article body (up to ~6,000 chars; site
   navigation has been stripped — ignore any menu text that remains).
   If a story has NO description and NO body, DO NOT summarise it
   from the title alone — drop the story and say so. No body, no
   summary. (Audit: 8 of the 15 kept events on 9 Nov had no body at
   all and were written from the title alone.)
3. STRUCTURE (mandatory, in order) — write the summary the way an
   exam answer would be written:
   (a) the LEAD — who did what, WITH the article's headline number
       (the one figure the article exists to report; e.g. graduate
       unemployment up 119% in 8 years, 405,000 → 885,000);
   (b) the CAUSE or context — WHY it happened, not just THAT it
       happened (e.g. merchants used Bangla QR as a free
       cash-withdrawal channel, so Bangladesh Bank announced
       account closures on 30 September);
   (c) the NUMBERS that make it exam-askable, then the CONSEQUENCE,
       then the EXAM HOOK (which paper/topic/question type it feeds).
   A summary with no number is not finished. Where the article has
   them, carry: the infographic's numbers, the history that explains
   the story, a comparison with both sides and the numbers (e.g.
   tax-to-GDP 6.6% vs Vietnam ~15%), and the constitutional/legal
   anchor (article, treaty, law — e.g. Article 15 for a benefit
   payment). Lift phrases from the real article; never shorten the
   article into a retelling.
4. exam_facts must add >=2 facts that are NOT in the summary.
   Lists, usage data, named actors, second-half figures — the
   material a student would be tested on. If the article has no such
   facts, the story is too thin to keep. Never restate the summary.
5. ATTRIBUTION: if a source is opinion, editorial or analysis,
   attribute every claim from it — "columnist X argues...",
   "the editorial says...", "the analysis estimates...". A
   columnist's calculation is NEVER a reported fact and NEVER an
   exam_fact without the attribution attached. (Audit: a Prothom Alo
   column's "fair wage at least Tk 17,500" was published as fact.)
6. DATE RULE: state the event date and the publication date
   separately (fields event_date and article_date). Never infer a
   date from "yesterday"/"today" without saying so. Never attach
   the publication date to the event.
7. why_it_matters: ONE sentence naming the SPECIFIC exam hook AND
   the compounding background — the fact that lets the reader
   understand the NEXT story on the same topic without re-studying
   it (e.g. ~20% of daily oil trade passes through Hormuz, and
   Bangladesh's LNG comes through it). Ban bare template phrases
   ("core topic", "recurring topic", "increasingly relevant",
   "directly askable") unless followed by the specific hook.
8. SOURCE RULE: every story needs >=1 direct, openable publisher
   URL. A Google News RSS link (news.google.com) may NOT be the
   only source of a story — it is an unopenable redirect. (Audit:
   two published stories had only Google News sources and no figure
   in them could be verified.)
9. Summary ~60 words per story, in English. Key facts with units.
   Why it matters + likely exam facts. Sources named with direct URLs.
10. Bangla ONLY for word/phrase meanings (verified). NEVER invent a
    Bangla translation of a full story.
11. Words: 20 NEW words only — none may repeat any headword from
    Edition 1 (7 Nov 2026) or any earlier edition. Screen with
    IMPORTANCE_RULES: keep only if it meets >=2 of: past BCS/Bank
    questions (word/family/synonym/antonym), syllabus fit, repeats in
    important news, exam-level difficulty, reusable in writing, live
    current-affairs term. Give IPA, Bangla phonetic, Bangla meaning,
    definition, synonyms, antonyms, word family, collocations, an
    original example, newspaper context, source publication + URL,
    BCS/Bank relevance and priority for EVERY word. Word and phrase
    examples must come from the article's own sentences (the headword
    in the example) — never invent an example.
12. Phrases: 10 idioms / phrasal verbs / collocations from the articles.
13. MCQs: 25 total — 10 vocabulary, 2 phrases, 13 current affairs.
    Every MCQ must trace to a story in THIS edition (field "source":
    the story id, e.g. "CA01"). 4 options, exactly one correct, with
    an explanation. Answers must match the key — check them twice.
14. Proposals are proposals, allegations are allegations, press-release
    claims are claims. Flag any figure that differs between sources
    instead of silently picking one.
15. If a kept event is marked EDITORIAL SLOT, its story's category
    MUST be "Editorial & Opinion" and Rule 5 (attribution) applies
    to the whole story.
16. Return ONLY the JSON pack (no prose outside the code block).
"""


def make_prompt(day, events, articles):
    kept = events["kept"]
    slot = (events.get("editorial_slot") or {}).get("title")
    lines = [f"# Sarangsho Plus — Edition {day} — Claude pack\n",
             f"Coverage: from {coverage_label(day)}.\n",
             f"Kept events: {len(kept)} (ranked; fewer than 15 on a thin day "
             f"is correct — never pad with a weak story). Produce the pack "
             f"for exactly these events.\n",
             RULES,
             "\n## Ranked events (with sources)\n"]
    for i, ev in enumerate(kept, 1):
        lines.append(f"### CA{i:02d} — score {ev['score']} — {ev['title']}")
        if ev.get("type") in ("editorial", "opinion", "analysis"):
            lines.append(f"TYPE: {ev['type']} — Rule 5 attribution applies to "
                         f"the whole story.")
        if ev.get("editorial_slot"):
            lines.append("EDITORIAL SLOT — this story's category MUST be "
                         "\"Editorial & Opinion\".")
        if ev.get("selection"):
            lines.append(f"Selection test: exam_answerable="
                         f"{ev['selection'].get('exam_answerable')} "
                         f"(topics: {', '.join(ev['selection'].get('topics', [])) or 'none'})")
        if ev.get("follow_up_of"):
            lines.append(f"NOTE: {ev['follow_up_of']} — only include if this is a genuinely new development.")
        readable = False
        google_only = True
        for a in ev["articles"]:
            full = next((x for x in articles if x["url"] == a["url"]), None)
            desc = (full or {}).get("summary", "") or ""
            raw_body = (full or {}).get("body_text", "") or ""
            body = strip_boilerplate(raw_body)
            if desc.strip() or len(body) >= 200:
                readable = True
            if "news.google.com" not in a["url"]:
                google_only = False
            lines.append(f"- {a['source']}: {a['title']} — {a['url']}")
            if desc.strip():
                lines.append(f"  Description (RSS lede): {desc[:600]}")
            if body:
                lines.append(f"  Article text (cleaned, navigation stripped): {body[:6000]}")
            elif raw_body:
                lines.append("  Article text: fetched but only navigation survived cleaning — "
                             "use the description and the other sources.")
            else:
                lines.append("  Article text: NOT FETCHED (no direct body available).")
        if not readable:
            lines.append("  ⚠ NO READABLE TEXT — no description and no body for any "
                         "source. Rule 2: DO NOT summarise this story from the "
                         "title alone. DROP IT and say so.")
        if google_only:
            lines.append("  ⚠ GOOGLE-NEWS-ONLY — every source is a news.google.com "
                         "redirect. Rule 8: find a direct publisher URL or DROP "
                         "the story.")
        lines.append("")
    lines.append("## Output — return this JSON shape (same as Edition 1):\n"
                 '{"stories": [{"id": "CA01", "headline": "...", "category": "...", '
                 '"event_date": "...", "article_date": "...", "summary": "...", '
                 '"why_it_matters": "...", "exam_facts": "...", "exam_relevance": "...", '
                 '"key_people": "...", "figures": "...", '
                 '"sources": [{"publication": "...", "headline": "...", "date": "...", "url": "..."}]}], '
                 '"words": [{"Headword / phrase": "...", "IPA": "...", "Bangla phonetic": "...", '
                 '"Part of speech / type": "...", "Difficulty": "...", "Bangla meaning": "...", '
                 '"English definition": "...", "Synonyms": "...", "Antonyms": "...", '
                 '"Word family / derivatives": "...", "Collocations / patterns": "...", '
                 '"Original example": "...", "Newspaper context note": "...", '
                 '"Source publication": "...", "Article headline": "...", "Publication date": "...", '
                 '"Direct source URL": "...", "BCS / Bank relevance": "...", "Priority": "..."}], '
                 '"phrases": [{"Phrase": "...", "Type": "...", "Bangla meaning": "...", '
                 '"English explanation": "...", "Usage / register": "...", '
                 '"Original example 1": "...", "Original example 2": "...", '
                 '"Common collocations / grammar pattern": "...", "Source publication": "...", '
                 '"Article headline": "...", "Publication date": "...", "Direct source URL": "...", '
                 '"Exam value": "..."}], '
                 '"mcqs": [{"no": 1, "section": "Vocabulary|Phrases|Current Affairs", '
                 '"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
                 '"correct": "A", "explanation": "...", "source": "CA01"}]}\n')
    return "\n".join(lines)


def srs_revision(day):
    """5 words due today from previous editions (SRS 1-3-7-14-30-60)."""
    due = []
    day_d = date.fromisoformat(day)
    for ed in previous_editions():
        first = ed.get("edition_date")
        if not first:
            continue
        first_d = date.fromisoformat(first)
        for w in ed.get("words", []):
            for gap in SRS_GAPS:
                if first_d + timedelta(days=gap) == day_d:
                    due.append(w)
                    break
    # Deterministic order: earliest edition first, then headword.
    return due[:5]


def import_pack(day, pack_path, indir, author="unknown"):
    pack = load_json(pack_path)
    events = load_json(indir / f"events-{day}.json")
    articles = load_json(indir / f"articles-{day}.json")["articles"]
    known_urls = {a["url"] for a in articles}
    by_url = {a["url"]: a for a in articles}
    problems, borderline = [], []
    stories = pack.get("stories", [])
    words = pack.get("words", [])
    phrases = pack.get("phrases", [])
    mcqs = pack.get("mcqs", [])
    # 1. Stories: source URLs must be real and collected.
    story_ids = set()
    for s in stories:
        story_ids.add(s.get("id", ""))
        srcs = s.get("sources", [])
        if not srcs:
            problems.append(f"{s.get('id')}: no sources")
        for src in srcs:
            u = src.get("url", "")
            if not u.startswith("http"):
                problems.append(f"{s.get('id')}: source URL not http: {u!r}")
            elif u not in known_urls:
                problems.append(f"{s.get('id')}: source URL was NOT collected: {u}")
        if len((s.get("summary") or "").split()) > 90:
            problems.append(f"{s.get('id')}: summary over 90 words "
                            f"({len(s['summary'].split())})")
        # 1b. Source rule (audit Fix 3.8): a Google News redirect may
        # not be the ONLY source of a story.
        if srcs and all("news.google.com" in (x.get("url", "") or "")
                        for x in srcs):
            problems.append(f"{s.get('id')}: Google-News-only sources — "
                            "no direct, openable publisher URL")
        # 1c. No body, no summary (audit Fix 3.2): the story must have
        # readable source text — a description or a fetched body —
        # for at least one of its sources. Title-only is not a story.
        readable = False
        for src in srcs:
            a = by_url.get(src.get("url", ""), {})
            if (a.get("summary") or "").strip():
                readable = True
            if len(strip_boilerplate(a.get("body_text") or "")) >= 200:
                readable = True
        if srcs and not readable:
            problems.append(f"{s.get('id')}: no readable source text "
                            "(no description, no body) — summarised "
                            "from the title alone")
        # 1d. Attribution (audit Fix 3.4): a story sourced from
        # opinion/editorial/analysis must attribute its claims.
        if any(any(m in (x.get("url", "") or "").lower()
                   for m in OPINION_URL_MARKERS) for x in srcs):
            text = (s.get("summary") or "") + " " + (s.get("exam_facts") or "")
            if not has_attribution(text):
                problems.append(f"{s.get('id')}: opinion-sourced story "
                                "with no attribution (no 'argues'/'says'/"
                                "'according to'/...) — opinion laundered "
                                "as fact")
        # 1e. exam_facts must add >=2 new facts (audit Fix 3.3):
        # at least 5 new content words / number tokens beyond the
        # summary (common.new_fact_tokens — same rule as review 16).
        if (s.get("exam_facts") or "").strip():
            n_new = new_fact_tokens(s.get("summary") or "",
                                    s.get("exam_facts") or "")
            if n_new < 5:
                problems.append(f"{s.get('id')}: exam_facts add only "
                                f"{n_new} new facts beyond the summary "
                                "(want >=5) — restates the summary")
    # 1f. Editorial slot (audit Fix 1.6): if the ranker reserved the
    # slot, the edition must carry that story as "Editorial & Opinion".
    slot = (events.get("editorial_slot") or {}).get("title")
    if slot:
        slot_urls = set()
        for ev in events.get("kept", []):
            if ev.get("title") == slot:
                slot_urls = {a["url"] for a in ev.get("articles", [])}
        slot_covered = any(
            s.get("category") == "Editorial & Opinion" and
            any((x.get("url") or "") in slot_urls
                for x in s.get("sources", []))
            for s in stories)
        if not slot_covered:
            problems.append("editorial slot: ranker reserved the slot for "
                            f"{slot[:60]!r} but no story has category "
                            "'Editorial & Opinion' from that event")
    # 2. Words: de-duplicate against all previous editions.
    seen_prev = previous_headwords()
    kept_words = []
    for w in words:
        hw = (w.get("Headword / phrase") or "").strip()
        if hw.lower() in seen_prev:
            borderline.append({"headword": hw,
                               "reason": "duplicate of an earlier edition"})
        else:
            kept_words.append(w)
            seen_prev.add(hw.lower())
    # 3. MCQs: count, split, traceability, answer validity.
    counts = {"Vocabulary": 0, "Phrases": 0, "Current Affairs": 0}
    for m in mcqs:
        counts[m.get("section", "?")] = counts.get(m.get("section", "?"), 0) + 1
        if m.get("source") not in story_ids:
            problems.append(f"MCQ {m.get('no')}: source {m.get('source')!r} "
                            "is not a story in this edition")
        if m.get("correct") not in ("A", "B", "C", "D"):
            problems.append(f"MCQ {m.get('no')}: bad correct option {m.get('correct')!r}")
        if len(m.get("options", {})) != 4:
            problems.append(f"MCQ {m.get('no')}: not 4 options")
    if counts.get("Vocabulary", 0) != TARGET["mcq_vocab"]:
        problems.append(f"MCQ split: {counts.get('Vocabulary', 0)} vocabulary, "
                        f"want {TARGET['mcq_vocab']}")
    if counts.get("Phrases", 0) != TARGET["mcq_phrases"]:
        problems.append(f"MCQ split: {counts.get('Phrases', 0)} phrases, want {TARGET['mcq_phrases']}")
    if counts.get("Current Affairs", 0) != TARGET["mcq_ca"]:
        problems.append(f"MCQ split: {counts.get('Current Affairs', 0)} current affairs, "
                        f"want {TARGET['mcq_ca']}")
    revision = srs_revision(day)
    # BACKFILL fallback (Nov 2026 backfill only): if no SRS-due words exist
    # and there is NO earlier edition at all (the first edition in the
    # archive, 1 Nov), the revision slot is filled from the earliest
    # existing edition's words so the app's Revision tab still works.
    # Recorded in the import report; never silently invented.
    if len(revision) < 5:
        eds = sorted(previous_editions(), key=lambda e: e.get("edition_date", ""))
        earlier = [e for e in eds if e.get("edition_date", "") < day]
        if not earlier and eds:
            revision = list(eds[0].get("words", []))[:5]
            print(f"[summarise_exam] BACKFILL: no earlier edition; revision "
                  f"filled from earliest edition {eds[0].get('edition_date')}")
    edition = {
        "edition_date": day,
        "edition_day": "Draft",
        "coverage": coverage_label(day),
        "status": "draft",
        "counts": {"stories": len(stories), "words": len(kept_words),
                   "phrases": len(phrases), "mcqs": len(mcqs),
                   "revision_words": len(revision)},
        "stories": stories, "words": kept_words,
        "revision_words": revision, "phrases": phrases, "mcqs": mcqs,
        "sources": [{"Source ID": f"S{i+1:02d}",
                     "Publication / organisation": s.get("publication", ""),
                     "Headline / report": s.get("headline", ""),
                     "Publication date": s.get("date", ""),
                     "Direct URL": s.get("url", "")}
                    for st in stories for i, s in enumerate(st.get("sources", []))],
    }
    save_json(indir / f"draft-{day}.json", edition)
    save_json(indir / f"import-report-{day}.json",
              {"date": day, "problems": problems, "borderline_words": borderline,
               "counts": edition["counts"], "target": TARGET,
               "pack_author": author,
               "revision_due": [w.get("Headword / phrase") for w in revision]})
    print(f"[summarise_exam] draft: {edition['counts']} (target {TARGET})")
    print(f"[summarise_exam] problems: {len(problems)} | duplicate words dropped: {len(borderline)}")
    for p in problems:
        print("  PROBLEM:", p)
    return 0 if not problems else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today())
    ap.add_argument("--prompt", action="store_true")
    ap.add_argument("--import-pack", default=None)
    ap.add_argument("--author", default="unknown",
                    choices=["agent", "claude", "unknown"],
                    help="who wrote the reviewed pack (audit Fix 5): "
                         "'claude' = the Claude Project as designed, "
                         "'agent' = the operator acting as the Claude "
                         "Project, 'unknown' = not recorded. Recorded in "
                         "the import report; the RUN_REPORT must say the "
                         "same. Pass it every time — do not leave it unknown.")
    ap.add_argument("--in", dest="indir", default=None)
    args = ap.parse_args()
    day = args.date
    indir = Path(args.indir) if args.indir else Path(__file__).resolve().parent / "runs" / day
    if args.prompt:
        events = load_json(indir / f"events-{day}.json")
        articles = load_json(indir / f"articles-{day}.json")["articles"]
        text = make_prompt(day, events, articles)
        out = indir / f"claude-prompt-{day}.md"
        out.write_text(text, encoding="utf-8")
        print(f"[summarise_exam] wrote {out} ({len(text)} chars)")
        print("[summarise_exam] Paste it + the articles into the Claude Project.")
        print("[summarise_exam] Save Claude's JSON reply as "
              f"runs/{day}/reviewed-pack-{day}.json, then run --import-pack.")
        return 0
    if args.import_pack:
        return import_pack(day, Path(args.import_pack), indir,
                           author=args.author)
    ap.error("need --prompt or --import-pack")


if __name__ == "__main__":
    raise SystemExit(main())
