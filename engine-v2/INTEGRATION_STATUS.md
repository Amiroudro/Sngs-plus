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
- Searchable metadata-only archive API (`/api/v1/archive`) and bilingual Today-page search. It exposes only whitelisted headline/source/URL/date/status fields from human-published editions; it never returns article bodies or generated study notes.
- Bangla converter overlays are marked needs_review. The API serves Bangla fields only when every story has explicit translation_status=approved; otherwise it falls back to English.
- SQLite migrations for source health, fact evidence, questions/options, vocabulary occurrences, review progress, editorial corrections, publisher rights reviews, article localizations and separate exam relevance assessments.
- Database triggers allow least-privilege `metadata_only` activation only with current metadata and separate automated-processing scope/evidence; `article_body` mode additionally requires a current body licence. Article-page extraction has its own approval gate.
- Independent 0–10 exam score, topic tags and exam tracks are stored separately from the engine's 0–3 processing score.
- Candidate source directory for 50 publishers plus BSS and UNB. It is not a list of active integrations.
- 16 Nov 2026 source audit: all 50 candidate publishers have a domain lead. Sonali Sangbad's homepage is active, but its feed parser/robots checks remain unverified. The machine-readable route matrix contains 55 hosts, eight feed-route leads, zero directly verified routes and zero enabled sources. CI checks exact host/status parity between source_routes.json and source_rights.json. Third-party feed claims are discovery evidence only.
- Route evidence is split into eight third-party feed leads and 19 collector routes noted in the original Engine development VM on 15 Nov 2026. The latter are historical/configured route observations only, not deployment verification; all 19 carry explicit `deployment_environment_verified=false`, `rights_approved=false` and `source_enabled=false`. The collector documentation now states this distinction.
- Operational collector rights gate in engine-v2/rights_registry.py and engine-v2/state/source_rights.json:
  - Direct publisher feeds/sitemaps require the DB source to be explicitly enabled, approved metadata scope/evidence, a current dated review and separate automated-processing approval with its own scope/evidence.
  - Bing/Google News are discovery-only. Each publisher URL is checked separately before it enters the article collection.
  - Unknown or unmapped publisher URLs are denied.
  - Article-page headline extraction requires separate page-metadata scope/evidence plus automated-processing approval, or a body licence covering page processing.
  - Article-body fetching requires a current body licence and separate automated-processing scope/evidence.
  - Robots policy is enforced independently; robots.txt fetch failures are fail-closed.
- Regression tests cover metadata vs page/body/automated-processing permissions, unknown domains, malformed URLs, expired licences, overdue reviews, direct feed blocking, title-page fetch blocking, body fetch blocking, SQLite-to-JSON sync, conflicting source records and robots behaviour.
- Collector retains sports, entertainment and lifestyle articles for editorial scoring rather than discarding them at URL-filter time.
- Kept stories whose body cannot be fetched are written to a separate metadata-only archive with headline/source/URL/date and a reason. RSS excerpts are stripped by default; no article body, facts, translation or questions are generated for these records.
- The app converter stages `metadata-only-<date>.json` separately from the 15-story study edition. The publish script requires and validates this file, then copies it only after the human approval file and 15/15 gate pass. The API additionally requires the matching edition to be marked published in the index.

## Rights ledger and operational registry sync

The SQLite source_rights_reviews table is the review ledger. The Engine reads a JSON policy snapshot. The new sync_rights_registry.py exports the latest reviewed DB rows into both source_rights.json and source_routes.json, matches publisher_domain to known registry hosts, rejects conflicting DB rows for the same registry domain, and is dry-run by default. It writes only with --write after a human reviews the report. This is a manual, one-way sync, not a scheduled process or admin UI. Record approvals in the DB ledger and do not edit approved JSON entries independently.

## Current rights and collection state

- Every publisher's metadata and page-metadata status remains pending. Automated-processing status is pending or restricted for flagged sources. No source is currently eligible for metadata-only activation.
- Every publisher's article-body status remains not_permitted.
- No publisher is enabled for collection.
- No live collection schedule is enabled.
- No articles have been published or synced to the app.
- Third-party feed-registry verification is a discovery signal, not a reuse licence.
- Prothom Alo terms restrict derivative works and reuse; The Daily Star, BSS and UNB require rights-scope review before reuse. The Daily Sangbad terms require prior written consent for republication/reproduction.
- Daily Inqilab and Risingbd are set to automated_processing_status=restricted because a third-party registry reports AI-crawler blocks; they must be rechecked against current publisher-controlled robots files and terms before any automated processing.

## Known limitations

- The 50-publisher directory is not yet 50 direct feed integrations. Exact official route, current item timestamps, robots response and deployment-region reachability still need direct verification. The metadata-only archive reader and UI are now wired, but will remain empty until a rights-cleared source is collected and a human-approved edition containing its archive file is published.
- The current Bangla renderer uses deterministic templates and sanitisation, not fluent translation. Its output must remain unapproved until human review or a properly tested translation workflow is introduced.
- The expanded study taxonomy is specified in docs/EXAM_TAXONOMY_V1.md but is not yet wired to an automated classifier or frontend filters.
- The separate 0–10 assessment schema exists, but no calibrated scoring model or importer currently populates it.
- Engine events, facts, vocabulary and questions are not yet ingested into the new database tables.
- Topics and Exam Desk are not yet connected to the new data layer.
- The publisher gate still references a legacy validator that is not present in this repository.
- The DB-to-JSON sync is manual and dry-run-first; a reviewed admin interface and scheduled export are not yet implemented.

## Metadata-only archive API

`GET /api/v1/archive?q=<text>&source=<publisher>&limit=30` searches metadata-only records associated with human-published editions. It returns a maximum of 100 records per request and explicitly marks `record_type=metadata_only` and `study_notes_available=false`. The reader whitelists fields and rejects any record without a recognised archive status and `study_note_status=not_generated`. It will not return RSS excerpts, article bodies, facts, translations or questions. The Today page provides English/Bangla search labels and opens the publisher URL in a new tab.

The converter stages the archive separately; `publish_v2.py` refuses to publish if the archive file is missing, malformed, contains unapproved status values, or includes body/study fields. It is copied to `editions/metadata-only-<date>.json` only after the existing approval and 15/15 checks pass. No existing live edition or source has been changed by this integration.

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


## Source route ledger update (16 Nov 2026)

- Added `state/source_routes.json`, a machine-readable route audit ledger for all 55 operational host records (50 candidate publishers plus separate language hosts and BSS/UNB records).
- Eight candidate feed URLs are recorded as discovery leads only; zero are marked directly verified by this ledger. The Sonali Sangbad route is recorded as an RSS-content-type observation with an unparsed payload.
- All 55 hosts remain disabled; article-body status remains `not_permitted` throughout.
- Added `tests/test_source_routes.py` to enforce host-count consistency, lead counts, default-deny status and honest verification labels. The Engine smoke workflow now runs this test.
- Corrected a stale collector diagnostic that described robots fetch failures as fail-open; the runtime policy and regression tests are fail-closed.

This ledger is an audit tracker, not a live probe result. Direct fetch, parse, freshness, robots and rights evidence must be populated from the actual deployment environment before any source can be reviewed for activation.


## Rights and route ledger synchronisation

The SQLite-to-JSON rights export now updates both `state/source_rights.json` and the adjacent `state/source_routes.json` ledger when the latter exists. The route ledger mirrors the current metadata, page-metadata, automated-processing, body-rights and enabled states for mapped hosts, and recalculates its enabled count. Dry-run remains the default; `--write` is still required to change either file. The sync regression test verifies dry-run immutability, metadata-only grants, later body/page grants, and restrictive-review revocation across both ledgers.


## Metadata-only archive preservation

The v2 run now writes `metadata-only-<date>.json` and includes `metadata_only_items` in the run edition when a Step-3-kept story has no accessible body text. Each record preserves headline, publisher, canonical URL, publication timestamp and the publisher-provided feed summary (capped at 600 characters), with an explicit reason such as missing body licence, robots disallow, non-direct URL or fetch failure. It contains no extracted facts, generated translation or study questions, and its study-note status is `not_generated`. This prevents kept metadata from disappearing from the engine run; the separate metadata-only archive is not yet surfaced in the app UI.
