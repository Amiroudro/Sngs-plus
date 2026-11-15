# Engine v2 integration status

**Branch:** feature/engine-v2-runtime-import  
**Source:** Amiroudro/Engine  
**Target:** Amiroudro/Sngs-plus  
**Status:** Draft integration; not merged and not live.

## Imported

- Engine v2 steps 1–10, orchestration scripts, converter, exporter, publisher, rules, vocabulary bank and tests.
- Canonical rules and vocabulary under engine-v2/rules/.
- Shared helpers and fail-closed robots policy.

## Connected in this branch

- Read-only API for editions explicitly marked published in both the index and edition file.
- English/Bangla briefing endpoint and bilingual Today page.
- Bangla converter overlays are marked needs_review. The API serves Bangla fields only when every story has explicit translation_status=approved; otherwise it falls back to English.
- SQLite migrations for source health, fact evidence, questions/options, vocabulary occurrences, review progress, editorial corrections, publisher rights reviews, article localizations and separate exam relevance assessments.
- Database triggers block source activation in the application database unless a current documented licence covers the existing article-body collector.
- Independent 0–10 exam score, topic tags and exam tracks are stored separately from the engine's 0–3 processing score.
- Candidate source directory for 50 publishers plus BSS and UNB. It is not a list of active integrations.
- 16 Nov 2026 source audit: 49 of 50 candidate publishers have a domain lead; Sonali Sangbad remains unresolved. The operational JSON registry contains 54 host records including aliases, separate Prothom Alo language hosts, BSS and UNB. Third-party Inkline feed claims are recorded separately from direct verification.
- Operational collector rights gate in engine-v2/rights_registry.py and engine-v2/state/source_rights.json:
  - Direct publisher feeds/sitemaps require approved metadata scope, evidence, a current dated review and separate automated-processing approval with its own scope/evidence.
  - Bing/Google News are discovery-only. Each publisher URL is checked separately before it enters the article collection.
  - Unknown or unmapped publisher URLs are denied.
  - Article-page headline extraction requires separate page-metadata scope/evidence plus automated-processing approval, or a body licence covering page processing.
  - Article-body fetching requires a current body licence and separate automated-processing scope/evidence.
  - Robots policy is enforced independently; robots.txt fetch failures are fail-closed.
- Regression tests cover metadata vs page/body permissions, unknown domains, malformed URLs, expired licences, overdue reviews, direct feed blocking, title-page fetch blocking, body fetch blocking and robots behaviour.
- Collector retains sports, entertainment and lifestyle articles for editorial scoring rather than discarding them at URL-filter time.

## Important distinction between rights stores

The JSON rights registry is the operational policy source read by Engine v2. The SQLite source_rights_reviews table is an application audit store with database activation triggers. They are not automatically synchronised yet. Do not approve a publisher in one store and assume the other has changed. A reviewed activation workflow must update and validate both stores before any source is enabled.

## Current rights and collection state

- Every publisher's metadata and page-metadata status remains pending. Automated-processing status is pending or restricted for flagged sources.
- Every publisher's article-body status remains not_permitted.
- No publisher is enabled for collection.
- No live collection schedule is enabled.
- No articles have been published or synced to the app.
- Third-party feed-registry verification is a discovery signal, not a reuse licence.
- Prothom Alo terms restrict derivative works and reuse; The Daily Star, BSS and UNB require rights-scope review before reuse. The Daily Sangbad terms require prior written consent for republication/reproduction.
- Daily Inqilab and Risingbd are set to automated_processing_status=restricted because a third-party registry reports AI-crawler blocks; they must be rechecked against current publisher-controlled robots files and terms before any automated processing.

## Known limitations

- The 50-publisher directory is not yet 50 direct feed integrations. Exact official route, current item timestamps, robots response and deployment-region reachability still need direct verification.
- The current Bangla renderer uses deterministic templates and sanitisation, not fluent translation. Its output must remain unapproved until human review or a properly tested translation workflow is introduced.
- The expanded study taxonomy is specified in docs/EXAM_TAXONOMY_V1.md but is not yet wired to an automated classifier or frontend filters.
- The separate 0–10 assessment schema exists, but no calibrated scoring model or importer currently populates it.
- Engine events, facts, vocabulary and questions are not yet ingested into the new database tables.
- Topics and Exam Desk are not yet connected to the new data layer.
- The publisher gate still references a legacy validator that is not present in this repository.
- The DB-to-JSON sync is manual and dry-run-first; a reviewed admin interface and scheduled export are not yet implemented.

## Required next milestones

1. Verify exact feed/sitemap URLs and current robots/terms evidence for each candidate from publisher-controlled sites and the deployment environment.
2. Build a reviewed rights workflow that synchronises the JSON operational registry and SQLite rights records.
3. Obtain permission where intended metadata, automated processing, page extraction, article-body analysis or app display is not already allowed.
4. Replace telegraphic Bangla rendering with source-grounded fluent translation and explicit review.
5. Implement multi-label study-topic assignment and validate it against a hand-labelled test set.
6. Calibrate the 0–10 exam relevance score separately for BCS, Bank and government tracks.
7. Import only approved, rights-cleared article/event/fact/question/vocabulary records into the database.
8. Connect Topics and Exam Desk to approved records.
9. Complete the human publish validator before considering scheduled collection.

The integration does not publish or activate any article. PR #4 must remain unmerged until the user approves it.
