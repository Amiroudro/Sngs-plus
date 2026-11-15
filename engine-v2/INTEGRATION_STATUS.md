# Engine v2 integration status

**Branch:** feature/engine-v2-runtime-import  
**Source:** Amiroudro/Engine root-level v2 snapshot  
**Target:** Amiroudro/Sngs-plus

## Imported

- Engine v2 plan and data contracts
- Canonical editorial rules at engine-v2/rules/RULES.md
- Vocabulary bank at engine-v2/rules/vocab_bank.json
- Shared helpers, runtime orchestrators, converter, exporter and publisher
- Steps 1–10, test modules and cron instructions

## Connected in this branch

- Read-only API for editions explicitly marked published in both the index and edition file.
- English/Bangla briefing endpoint and bilingual Today page.
- Bangla converter overlays are marked needs_review. The API now uses Bangla fields only when every story in the edition has explicit translation_status=approved; otherwise it falls back to English.
- SQLite migrations for source health, fact evidence, questions/options, vocabulary occurrences, review progress, editorial corrections, publisher rights reviews, article localizations and separate exam relevance assessments.
- Independent 0–10 exam score, topic tags and exam tracks are stored separately from the engine's 0–3 processing score.
- Candidate source directory for 50 publishers plus BSS and UNB; candidates are not automatically considered verified or active.
- First-pass public-route and publisher-terms audit for eight candidates.
- Collector retains sports, entertainment and lifestyle articles for editorial scoring rather than discarding them at URL-filter time.

## Known limitations

- No source is marked active or cleared for article-body processing. Rights and technical checks remain separate gates.
- Prothom Alo's terms restrict derivative works and reuse; The Daily Star and BSS require further rights-scope review before body processing or app redistribution.
- The 50-publisher candidate directory is not a verified direct-feed registry.
- The current Bangla renderer uses deterministic templates and sanitisation, not fluent translation. Its output must remain unapproved until human review or a properly tested translation workflow is introduced.
- The expanded study taxonomy is specified in docs/EXAM_TAXONOMY_V1.md but not yet wired to an automated classifier or frontend filters.
- The separate 0–10 assessment schema exists, but no calibrated scoring model or importer currently populates it.
- Engine events, facts, vocabulary and questions are not yet ingested into the new database tables.
- Topics and Exam Desk are not yet connected to the new data layer.
- The publisher gate still references a legacy validator that is not present in this repository.
- No live collector schedule or automatic app publishing is enabled.

## Required next milestones

1. Complete a rights and access review for each candidate before enabling collection.
2. Implement a verified source registry with feed freshness, robots/terms evidence and source health.
3. Replace telegraphic Bangla rendering with source-grounded fluent translation and explicit review.
4. Implement multi-label study-topic assignment and validate it against a hand-labelled test set.
5. Calibrate the 0–10 exam relevance score separately for BCS, Bank and government tracks.
6. Import only approved, rights-cleared article/event/fact/question/vocabulary records into the database.
7. Connect Topics and Exam Desk to approved records.
8. Complete the human publish validator and only then consider scheduled collection.

The import does not publish or activate any article.
