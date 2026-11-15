#!/usr/bin/env python3
"""Module 6 — Publish + human review gate (ENGINE_DESIGN §5/§9).

The gate: a draft NEVER becomes published by the engine alone.
  1. --check   runs the review checklist on runs/<date>/draft-<date>.json
               and writes runs/<date>/review-<date>.json.
  2. A human (Rudro) reads the draft + checklist and, if it is correct,
     marks it approved by writing runs/<date>/approval-<date>.json:
       {"approved": true, "reviewer": "Rudro", "date": "...", "notes": "..."}
     (or {"approved": false, "corrections": [...]})
  3. --publish  only runs when approval-<date>.json says approved=true.
     It copies the draft to editions/data-<date>.json with
     status "published" and exports the XLSX + PDF.
Exports reuse the 7 Nov format: 6-sheet XLSX (Vocabulary, Phrases,
Current Affairs, MCQs, Answer Key, Sources) and an A4 PDF.

Usage:
  python3 publish.py --date 2026-11-08 --check
  python3 publish.py --date 2026-11-08 --publish
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (load_json, save_json, today, ROOT, EDITIONS_DIR,
                    new_fact_tokens, has_attribution, OPINION_URL_MARKERS)

TARGET = {"stories": 15, "words": 20, "phrases": 10, "mcqs": 25, "revision_words": 5}
# Thin day stays thin (video rule 6): 15 stories is the CEILING, not
# the floor. An edition with 12 good stories is a correct edition;
# the old check (stories == 15 exactly) failed every thin-day draft.
MIN_STORIES = 12


def checklist(day, draft, events=None):
    checks = []
    def add(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
    c = draft.get("counts", {})
    n_stories = c.get("stories", 0)
    add("counts: stories", MIN_STORIES <= n_stories <= TARGET["stories"],
        f"{n_stories} stories (12-15 ok — 15 is the ceiling, not the floor)")
    add("counts: words", c.get("words") == TARGET["words"],
        f"{c.get('words')} of {TARGET['words']}")
    add("counts: phrases", c.get("phrases") == TARGET["phrases"],
        f"{c.get('phrases')} of {TARGET['phrases']}")
    add("counts: mcqs", c.get("mcqs") == TARGET["mcqs"],
        f"{c.get('mcqs')} of {TARGET['mcqs']}")
    add("counts: revision", c.get("revision_words") == TARGET["revision_words"],
        f"{c.get('revision_words')} of {TARGET['revision_words']}")
    bad_urls = [s["id"] for s in draft.get("stories", [])
                for src in s.get("sources", [])
                if not str(src.get("url", "")).startswith("http")]
    add("every story has >=1 real http source URL", not bad_urls,
        f"stories with bad urls: {bad_urls}" if bad_urls else "all ok")
    no_src = [s["id"] for s in draft.get("stories", []) if not s.get("sources")]
    add("no story without sources", not no_src, str(no_src))
    story_ids = {s["id"] for s in draft.get("stories", [])}
    untraced = [m["no"] for m in draft.get("mcqs", [])
                if m.get("source") not in story_ids]
    add("every MCQ traces to a story in this edition", not untraced,
        f"untraced MCQs: {untraced}" if untraced else "all ok")
    key_mismatch = []
    for m in draft.get("mcqs", []):
        opts = m.get("options", {})
        if m.get("correct") not in opts or len(opts) != 4:
            key_mismatch.append(m.get("no"))
    add("MCQ answer key valid (correct option exists, 4 options)", not key_mismatch,
        f"bad MCQs: {key_mismatch}" if key_mismatch else "all ok")
    long_summ = [s["id"] for s in draft.get("stories", [])
                 if len((s.get("summary") or "").split()) > 90]
    add("summaries ~60 words (<=90)", not long_summ, f"long: {long_summ}")
    heads = [w.get("Headword / phrase", "").lower()
             for w in draft.get("words", [])]
    add("no duplicate words inside the edition", len(heads) == len(set(heads)),
        f"{len(heads) - len(set(heads))} duplicates")
    figures = [s["id"] for s in draft.get("stories", [])
               if not (s.get("figures") or "").strip()]
    add("every story has figures / exam facts recorded", not figures,
        f"missing figures: {figures}" if figures else "all ok")
    # --- Checks 13-17 (audit Fix 4): content, not just form. ---
    # 13. Lead figure present. Automated proxy only: the summary and
    # the figures field must each carry at least one digit. A proxy
    # cannot tell whether the LEAD figure is the one carried — the
    # human MUST spot-check 5 stories by opening the source (see
    # detail + runbook). A 12/12 that passes with a summary missing
    # its lead figure is a broken gate.
    no_digit = [s["id"] for s in draft.get("stories", [])
                if not re.search(r"\d", s.get("summary") or "")
                or not re.search(r"\d", s.get("figures") or "")]
    add("13. every summary carries a figure (lead-figure proxy)",
        not no_digit,
        (f"stories with no figure in summary/figures: {no_digit}"
         if no_digit else "all ok — MANUAL: spot-check 5 stories by "
         "opening the source; does the summary carry the article's "
         "LEAD figure (e.g. the 119%, not a side number)?"))
    # 14. Direct, openable source; no Google-News-only story.
    gn_only = [s["id"] for s in draft.get("stories", [])
               if s.get("sources") and
               all("news.google.com" in str(x.get("url", ""))
                   for x in s["sources"])]
    add("14. no Google-News-only story (every story has a direct source)",
        not gn_only,
        f"Google-News-only stories: {gn_only}" if gn_only else "all ok")
    # 15. Editorial & Opinion story present — OR the slot was empty
    # by design (no editorial scored >=60 and exam-answerable that
    # day; the ranker records that in events-<day>.json). An empty
    # slot on a thin day is correct, not a failure.
    has_ed = any(s.get("category") == "Editorial & Opinion"
                 for s in draft.get("stories", []))
    slot = (events or {}).get("editorial_slot") or {}
    if has_ed:
        add("15. >=1 Editorial & Opinion story in the edition", True,
            "present")
    elif slot.get("title") is None and slot.get("reason"):
        add("15. >=1 Editorial & Opinion story in the edition", True,
            f"slot empty by design: {slot['reason']}")
    elif slot.get("title"):
        add("15. >=1 Editorial & Opinion story in the edition", False,
            f"ranker reserved the slot for {slot['title'][:60]!r} but the "
            "draft has no Editorial & Opinion story from that event")
    else:
        add("15. >=1 Editorial & Opinion story in the edition", False,
            "no Editorial & Opinion story and no events file to show "
            "why the slot stayed empty — check events-<day>.json")
    # 16. exam_facts add >=2 new facts (same rule as the importer).
    thin_facts = [s["id"] for s in draft.get("stories", [])
                  if new_fact_tokens(s.get("summary") or "",
                                     s.get("exam_facts") or "") < 5]
    add("16. exam_facts add >=2 new facts beyond the summary",
        not thin_facts,
        f"stories whose exam_facts restate the summary: {thin_facts}"
        if thin_facts else "all ok")
    # 17. No opinion claim presented as fact. Automated proxy: an
    # opinion-sourced story must carry an attribution marker. Plus
    # a manual spot-check (see detail).
    unattributed = []
    for s in draft.get("stories", []):
        if any(any(m in str(x.get("url", "")).lower()
                   for m in OPINION_URL_MARKERS)
               for x in s.get("sources", [])):
            text = (s.get("summary") or "") + " " + (s.get("exam_facts") or "")
            if not has_attribution(text):
                unattributed.append(s["id"])
    add("17. no opinion claim presented as fact",
        not unattributed,
        (f"opinion-sourced stories without attribution: {unattributed}"
         if unattributed else "all ok — MANUAL: spot-check any story "
         "whose sources include an /opinion/ or /editorial/ URL; a "
         "columnist's calculation must never read as a reported fact."))
    return checks


def export_xlsx(draft, path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vocabulary"
    wkeys = ["Headword / phrase", "IPA", "Bangla phonetic", "Part of speech / type",
             "Difficulty", "Bangla meaning", "English definition", "Synonyms",
             "Antonyms", "Word family / derivatives", "Collocations / patterns",
             "Original example", "Newspaper context note", "Source publication",
             "Article headline", "Publication date", "Direct source URL",
             "BCS / Bank relevance", "Priority"]
    ws.append(wkeys)
    for w in draft.get("words", []) + draft.get("revision_words", []):
        ws.append([w.get(k, "") for k in wkeys])
    ws = wb.create_sheet("Phrases")
    pkeys = ["Phrase", "Type", "Bangla meaning", "English explanation",
             "Usage / register", "Original example 1", "Original example 2",
             "Common collocations / grammar pattern", "Source publication",
             "Article headline", "Publication date", "Direct source URL", "Exam value"]
    ws.append(pkeys)
    for p in draft.get("phrases", []):
        ws.append([p.get(k, "") for k in pkeys])
    ws = wb.create_sheet("Current Affairs")
    ws.append(["ID", "Headline", "Category", "Summary", "Why it matters",
               "Exam facts", "Key people", "Figures"])
    for s in draft.get("stories", []):
        ws.append([s.get("id"), s.get("headline"), s.get("category"),
                   s.get("summary"), s.get("why_it_matters"),
                   s.get("exam_facts"), s.get("key_people"), s.get("figures")])
    ws = wb.create_sheet("MCQs")
    ws.append(["No", "Section", "Question", "A", "B", "C", "D", "Source story"])
    for m in draft.get("mcqs", []):
        o = m.get("options", {})
        ws.append([m.get("no"), m.get("section"), m.get("question"),
                   o.get("A"), o.get("B"), o.get("C"), o.get("D"), m.get("source")])
    ws = wb.create_sheet("Answer Key")
    ws.append(["No", "Correct", "Explanation"])
    for m in draft.get("mcqs", []):
        ws.append([m.get("no"), m.get("correct"), m.get("explanation")])
    ws = wb.create_sheet("Sources")
    ws.append(["Source ID", "Publication", "Headline", "Date", "URL"])
    for s in draft.get("sources", []):
        ws.append([s.get("Source ID"), s.get("Publication / organisation"),
                   s.get("Headline / report"), s.get("Publication date"),
                   s.get("Direct URL")])
    wb.save(path)
    return path


def export_pdf(draft, path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT
    styles = getSampleStyleSheet()
    h1, h2, body = styles["Heading1"], styles["Heading2"], styles["BodyText"]
    body.alignment = TA_LEFT
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"Sarangsho Plus — {draft['edition_date']}")
    story = [Paragraph(f"Sarangsho Plus — Daily Edition {draft['edition_date']}", h1),
             Paragraph(f"Coverage: {draft.get('coverage', '')}", body),
             Paragraph(f"Stories: {draft['counts'].get('stories')} | Words: "
                       f"{draft['counts'].get('words')} | Phrases: "
                       f"{draft['counts'].get('phrases')} | MCQs: "
                       f"{draft['counts'].get('mcqs')}", body), Spacer(1, 12)]
    for s in draft.get("stories", []):
        story.append(Paragraph(f"{s.get('id', '')} — {s.get('headline', '')}", h2))
        story.append(Paragraph(s.get("summary", ""), body))
        story.append(Paragraph(f"<b>Why it matters:</b> {s.get('why_it_matters', '')}", body))
        story.append(Paragraph(f"<b>Exam facts:</b> {s.get('exam_facts', '')}", body))
        srcs = "; ".join(f"{x.get('publication', '')} ({x.get('url', '')})"
                         for x in s.get("sources", []))
        story.append(Paragraph(f"<b>Sources:</b> {srcs}", body))
        story.append(Spacer(1, 8))
    story.append(PageBreak())
    story.append(Paragraph("Vocabulary", h1))
    for w in draft.get("words", []):
        story.append(Paragraph(
            f"<b>{w.get('Headword / phrase', '')}</b> — {w.get('Bangla meaning', '')}. "
            f"{w.get('English definition', '')} <i>{w.get('Original example', '')}</i>", body))
    story.append(Paragraph("MCQs (answers on the last page)", h1))
    for m in draft.get("mcqs", []):
        o = m.get("options", {})
        story.append(Paragraph(
            f"{m.get('no')}. {m.get('question', '')}<br/>"
            f"A. {o.get('A', '')} &nbsp; B. {o.get('B', '')}<br/>"
            f"C. {o.get('C', '')} &nbsp; D. {o.get('D', '')}", body))
    story.append(PageBreak())
    story.append(Paragraph("Answer Key", h1))
    for m in draft.get("mcqs", []):
        story.append(Paragraph(
            f"{m.get('no')}. {m.get('correct')} — {m.get('explanation', '')}", body))
    doc.build(story)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today())
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--in", dest="indir", default=None)
    args = ap.parse_args()
    day = args.date
    indir = Path(args.indir) if args.indir else Path(__file__).resolve().parent / "runs" / day
    draft = load_json(indir / f"draft-{day}.json")
    if args.check:
        ev_path = indir / f"events-{day}.json"
        events = load_json(ev_path) if ev_path.exists() else None
        checks = checklist(day, draft, events=events)
        save_json(indir / f"review-{day}.json",
                  {"date": day, "status": draft.get("status", "draft"),
                   "checks": checks,
                   "passed": sum(1 for c in checks if c["ok"]),
                   "total": len(checks),
                   "manual_spot_checks": [
                       "13: open the source of 5 stories; does each summary "
                       "carry the article's LEAD figure?",
                       "17: open any story whose sources include an /opinion/ "
                       "or /editorial/ URL; is every claim from it attributed?"],
                   "checklist_version": "17 checks (audit Fix 4, 2026-11-11)"})
        for c in checks:
            print(f"  [{'PASS' if c['ok'] else 'FAIL'}] {c['check']} — {c['detail']}")
        failed = [c for c in checks if not c["ok"]]
        print(f"[publish] review: {len(checks) - len(failed)}/{len(checks)} passed")
        if failed:
            print("[publish] DRAFT NOT READY — fix the failures, then re-check.")
            print("[publish] To approve anyway, the reviewer must write "
                  f"runs/{day}/approval-{day}.json with approved=true and notes.")
        return 0 if not failed else 2
    if args.publish:
        appr_path = indir / f"approval-{day}.json"
        if not appr_path.exists():
            print(f"[publish] BLOCKED: no {appr_path.name} — a human must approve first.")
            return 1
        appr = load_json(appr_path)
        if not appr.get("approved"):
            print(f"[publish] BLOCKED: approval file says approved=false. "
                  f"Corrections requested: {appr.get('corrections')}")
            return 1
        draft["status"] = "published"
        draft["approved_by"] = appr.get("reviewer", "Rudro")
        draft["approval_notes"] = appr.get("notes", "")
        # Fix (2026-11-15): the importer writes edition_day "Draft" as a
        # placeholder; publish must set the real weekday, otherwise the
        # validator's "weekday matches date" check fails on the new edition.
        from datetime import datetime as _dt
        draft["edition_day"] = _dt.strptime(day, "%Y-%m-%d").strftime("%A")
        EDITIONS_DIR.mkdir(parents=True, exist_ok=True)
        save_json(EDITIONS_DIR / f"data-{day}.json", draft)
        save_json(indir / f"published-{day}.json", draft)
        # Fix (2026-11-15): --publish must also flip the review file's status,
        # otherwise db.py --record reads review-<date>.json and records a
        # published edition as 'draft' (this hid Edition 8's publish in tracker.db).
        rev_path = indir / f"review-{day}.json"
        if rev_path.exists():
            rev = load_json(rev_path)
            rev["status"] = "published"
            save_json(rev_path, rev)
        xlsx = export_xlsx(draft, indir / f"edition-{day}.xlsx")
        pdf = export_pdf(draft, indir / f"edition-{day}.pdf")
        print(f"[publish] PUBLISHED {day} -> editions/data-{day}.json")
        print(f"[publish] exports: {xlsx} ; {pdf}")
        return 0
    ap.error("need --check or --publish")


if __name__ == "__main__":
    raise SystemExit(main())
