# Renovation spec — existing editions → 8-part learning-module format

Date: 2026-11-17. Ordered by Rudro 01:13: "first change the existing days contents like this now".
Source format: the ADP sample Rudro pasted (ChatGPT's renovated article, "ADP implementation falls to 6.53%", TBS 15 Nov 2026).

## Scope

- ALL 16 live editions: `editions/data-2026-11-01.json` … `data-2026-11-16.json`.
- 225 stories total (backfills 1–6 Nov: 90; daily 7–16 Nov: 135).
- Source of truth = the LOCAL files in `~/workspace/sarangsho-plus/editions/`.
  Do NOT use the live-site files (they carry ChatGPT's earlier renovation bits;
  the new format supersedes them). Note divergences in the run log; do not block on them.

## The 8-part format (per story)

1. **সংবাদ (News):** short, clear Bangla summary (2–4 sentences, lead with the key
   number — NOT a restatement of the headline) + hero figure (the single most
   exam-askable number, big, with a label, e.g. ৬.৫৩% / ADP implementation rate) +
   source line (publication, date, link from the story's `sources`).
2. **যাচাইকৃত তথ্য (Verified facts):** table of facts — date, numbers, people,
   institutions, source. EVERY fact must come from the existing story data
   (`summary` / `exam_facts` / `key_facts` / `figures` / `sources`). Never add a
   news fact that is not in the existing data. Bangla digits in Bangla text.
3. **বিষয়ভিত্তিক সাধারণ জ্ঞান (Topic GK):** the lesson on the story's topic —
   what the thing is, a facts table, key distinctions (e.g. ADP vs RADP).
   Grounded ONLY in authoritative sources (Banglapedia, official govt sites —
   plancomm.gov.bd, bbs.gov.bd, bangladeshbank.org.bd, ministry sites — or the
   source newspaper's own explainer). Record source name + URL for every GK block.
   If a GK fact cannot be verified from an authoritative source, OMIT it.
4. **BCS/Bank Exam Notes:** definitions, differences, institutions and their roles
   (e.g. Planning Commission, NEC, ECNEC, IMED). Same sourcing rule as (3).
5. **MCQ Practice:** 4 MCQs per story — GK-based where the topic allows, news-based
   where the story's numbers allow — each with correct answer + one-line explanation.
   Correct letters balanced across the 4 (no letter more than twice). No
   "সবগুলো"/"কোনোটিই নয়" options, no negative stems. Existing edition MCQs stay
   untouched in the file.
6. **লিখিত পরীক্ষার প্রস্তুতি (Written prep):** 1 short question + 1 analytical
   question per story, each with a model-answer outline (2–4 bullets, not an essay).
7. **Vocabulary:** 5 English words per story — Bangla meaning, usage example (from
   the story where possible), synonym + antonym. Words must appear in the story
   or be standard topic vocabulary. Prefer the edition's existing word list where a
   word belongs to this story (match by the word's `Article headline`).
8. **Revision:** flashcards — 3–5 Q/A pairs from the story's verified facts + GK —
   plus 2 "next revision" questions.
   Plus per story: **আরও গভীর প্রস্তুতি** — a list of 4–6 related topics for separate
   lessons (titles only, no content).

## Editorial rule (mandatory, Rudro's rule)

News facts and GK facts are in SEPARATE sections with SEPARATE source labels.
A reader must be able to tell what came from the news vs what is extra teaching.
Every GK block carries its source name + URL.

## Rudro's cut (15 Nov, stands)

NO মূল সারাংশ / Comprehensive Summary section ("প্রতিবেদনে বলা হয়েছে...").
Part 1 is the short clear summary, not a headline restatement.

## Output schema (backward-compatible — the current app must keep working)

- Keep EVERY existing field in the file byte-identical in value. Do not edit existing
  story fields, `mcqs`, `words`, `phrases`, `revision_words`, `sources`, `counts`.
- ADD per story a new key `learning_module` with the 8 parts:
  `hero`, `news_summary`, `verified_facts`, `topic_gk`, `exam_notes`,
  `mcq_practice`, `written_prep`, `vocabulary`, `revision`, `deep_prep`.
  Each GK block carries `sources: [{name, url}]`.
- ADD per edition top-level keys: `renovation_format: "learning-module-v1"`,
  `renovation_date: "2026-11-17"`.
- If a story's topic GK cannot be verified: include parts 1, 2, 5 (news MCQs), 6, 7, 8
  and set `topic_gk` / `exam_notes` to `"যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"`.
  NEVER fill with guesses. Record it in the edition report.

## Language

Bangla-first, cholito (not sadhu). Bangla digits in Bangla text. English proper
nouns/acronyms in brackets on first mention. Same style as `engine-v2/rules/RULES.md`
Step 6.

## Staging (do NOT publish)

- Write renovated files to `~/workspace/sarangsho-plus/renovated-editions/data-YYYY-MM-DD.json`.
- Write a per-edition report `~/workspace/sarangsho-plus/renovated-editions/report-YYYY-MM-DD.md`:
  stories done, GK sources used, any story skipped (with reason), any fact that
  could not be verified, MCQ letter counts per story.
- Do NOT touch `editions/`, `app/`, the live site, GitHub, `index.json`, `MEMORY.md`,
  or any engine code. Staging only. CAT verifies and syncs.

## Self-check (per edition, before reporting done)

- Every news fact traceable to the existing data file (quote the source field).
- Every GK fact has a named source + URL.
- Every MCQ answer verified against the facts in the module; letters balanced.
- JSON valid; all 8 parts present per story (or the explicit "যাচাই করা যায়নি" marker).
- Story count, words, phrases, mcqs unchanged vs the source file.
