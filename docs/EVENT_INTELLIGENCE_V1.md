# Event Intelligence v1: shared data contract

Status: schema foundation implemented on `feat/event-intelligence-foundation`.
This is a development contract, not a publication or deployment approval.

## Scope

The first three product features share one event identity and one evidence graph:

1. Three-level summaries: Quick, Standard and Deep.
2. Story timelines: source-backed chronological entries attached to an event.
3. Multiple newspaper perspectives: one reviewed perspective per publication article, linked to shared fact records.

The existing `events`, `articles`, `event_articles`, `facts`, `fact_evidence` and `summaries` tables remain intact. Migration 004 adds versioned feature tables and indexes. Existing `summaries.short_summary` remains readable for older consumers.

## Canonical relationships

- An `event` is the persistent identity for one real-world developing story.
- An `article` is one publication's report, with its canonical URL and source identity.
- `event_articles` links reports to the event without copying article text.
- `facts` stores individual claims attached to an event.
- `fact_evidence` records which article supports, partly supports, contradicts or contextualises a fact.
- `event_summary_versions` stores each language, level and version independently.
- `event_timeline_entries` stores dated or undated developments, each with a required source article.
- `event_article_perspectives` stores a reviewed framing/emphasis note for one article/event pair.
- `perspective_fact_links` links that publication's treatment to shared facts.

## Summary levels

| Level | Reader need | Required behaviour |
|---|---|---|
| `quick` | Understand the essential update quickly | Lead with what changed, who/where, and the key verified fact |
| `standard` | Understand the full report | Explain context, important facts, source attribution and consequences |
| `deep` | Understand the wider issue | Add background, competing evidence, implications, uncertainty and open questions |

Each record is keyed by event, language, level and version. A new revision creates a higher version; it does not silently overwrite a previously approved version. Every generated record begins as `needs_review`. Only reviewed records may be exposed as reader-ready content.

The database does not invent numeric confidence. Verification labels describe evidence state, not mathematical probability.

## Timeline rules

- `occurred_at` means when the event happened, if known.
- `reported_at` means when the source reported it.
- `chronology_precision` records whether the event time is exact, date-only, approximate or unknown.
- A missing event date stays unknown. The app must never substitute publication time and present it as event time.
- Each entry must cite a stored source article.
- Single-source reporting must remain labelled as such; it cannot be promoted to corroborated without independent evidence.
- Corrections are new entries with `entry_type='correction'`; approved history is not silently edited.

## Multiple-perspective rules

- Compare reports about the same event, not unrelated headlines grouped by keyword alone.
- Preserve publication identity and article URL.
- Describe observable framing and emphasis in neutral language.
- Do not infer political affiliation, motive, bias or intent from one article.
- Do not treat different emphasis as factual contradiction.
- A contradiction exists only when two source-backed claims are materially incompatible.
- Link each comparison to shared fact records and their evidence trail.
- Missing coverage is not proof of deliberate omission.
- Each perspective remains `needs_review` until editorially approved.

## Publication and compatibility rules

- Existing published edition JSON and its index remain the authoritative historical record.
- New event-intelligence tables are additive and do not rewrite published editions.
- Existing clients continue reading their current edition payload.
- The current FastAPI service reads the published-edition repository and does not yet open the SQLite study database. Do not add live endpoints until the database path, migration lifecycle, backup/restore and deployment ownership are explicitly wired and tested.
- Proposed read endpoints, once persistence is operational:
  - `GET /api/v1/events/{event_id}`
  - `GET /api/v1/events/{event_id}/summaries?language=bn&level=quick`
  - `GET /api/v1/events/{event_id}/timeline`
  - `GET /api/v1/events/{event_id}/perspectives`
- These endpoints must return only approved records by default. Draft/review records require an authenticated editorial interface, which is outside this public read API.

## Free-first implementation sequence

1. Apply migration 004 in isolated test databases and verify constraints.
2. Build deterministic event/article linking and duplicate detection.
3. Add source-backed timeline extraction with conservative date handling.
4. Add fact-to-evidence linking and publication perspective records.
5. Produce Quick/Standard/Deep drafts from the same fact set; keep all generated content in review.
6. Add read-only APIs after the SQLite database is deployed with backups.
7. Add Flutter screens behind feature flags and retain graceful fallback to existing story pages.
8. Populate historical events only from source material already lawfully available; do not rewrite published editions.

## Acceptance gates

- Every summary version has a language, level, version, status and traceable event.
- No draft summary is served as approved.
- Every timeline item has a source article and distinguishes event time from report time.
- Every perspective points to a distinct article and can link to shared facts.
- Approved records cannot be silently edited.
- Legacy edition and API tests remain unchanged and pass.
- No write path touches the published-editions repository.
