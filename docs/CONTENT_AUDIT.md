# Existing content audit

**Repository:** `Amiroudro/Sngs-plus`  
**Branch inspected:** `main`  
**Audit date:** 15 November 2026

## Executive finding

The current repository does **not** contain a back catalogue of newspaper articles or previously generated study notes. It contains a foundation website, three demonstration cards, an editorial policy, a basic SQLite schema and an API endpoint that explicitly returns an empty story list. The three homepage cards are product demonstrations, not real reporting.

That means there is no factual news archive to rewrite yet. Treating demonstration text as real articles or manufacturing replacement headlines would create false content. This renovation improves the content that actually exists and establishes the standard for the real article library.

## Inventory

| Area | What exists on `main` | Finding |
|---|---|---|
| Homepage | `frontend/src/pages/index.astro` | Three generic demo cards and a partial English/Bangla switch |
| Styling | `frontend/src/styles/global.css` | Basic responsive visual system |
| Editorial policy | `docs/EDITORIAL_POLICY.md` | Good source-integrity principles, but limited operational detail |
| API | `backend/app/main.py` | Health route and demo briefing endpoint; story list is empty |
| Database | `database/schema.sql` | Sources, articles, events, event links, summaries and facts |
| Source rows | Four starter publishers | All four are disabled; no feed URL is configured |
| Article archive | None found in the inspected schema/repository content | No existing article summaries to renovate |
| Exam content | No vocabulary or question bank found | Needs a defined content model and production pipeline |

## Changes in this renovation branch

1. Replaced the generic demo-story cards with three transparent coverage desks: Bangladesh/public affairs, economy/banking, and world affairs.
2. Expanded the language switch so all homepage content has English and Bangla text, with the selected language remembered locally when browser storage is available.
3. Added clear foundation/live-data status labels so a visitor cannot mistake the preview for current reporting.
4. Added the intended exam tracks and learning components, each marked as planned rather than falsely shown as operational.
5. Strengthened the editorial workflow on the page: responsible collection, fact checking, bilingual explanation and source-linked practice.
6. Added `docs/CONTENT_STANDARD.md` as the production specification for summaries, facts, relevance scoring, vocabulary, questions, revisions and quality control.

## Existing data that must be preserved

- Source names and homepage URLs already recorded in `database/schema.sql`
- Original source metadata and article URLs once collection begins
- The distinction between article, event and individual source contribution
- The existing editorial policy's rules against paywall bypassing, fabricated facts and unsupported corroboration

## Not yet done

- No live feeds have been configured or verified.
- No newspaper articles have been collected into the database.
- No existing article summaries, vocabulary entries or MCQs could be rewritten because none were present.
- No claim is made that the site is deployed, the collector is running, or the editorial pipeline is automated.
- The separate draft pull request for RSS metadata collection remains a separate change and must be reviewed/tested before merge.

## Next content milestone

Once the collection pipeline stores real source items, run a batch audit by article ID: deduplicate, inspect the accessible source material, assign relevance, verify material facts, create bilingual notes, derive vocabulary and questions, and retain a trace from each generated item back to its supporting source. Start with a small reviewable batch before processing the full source pool.
