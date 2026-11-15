# Engine v2 integration status

**Branch:** `feature/engine-v2-runtime-import`  
**Source:** `Amiroudro/Engine` root-level v2 snapshot  
**Target:** `Amiroudro/Sngs-plus`

## Imported

- Engine v2 plan and data contracts
- Canonical editorial rules at `engine-v2/rules/RULES.md`
- Vocabulary bank at `engine-v2/rules/vocab_bank.json`
- Shared helpers, runtime orchestrators, converter, exporter and publisher
- Steps 1–10
- Test modules and cron instructions

## Structural repair

The standalone Engine repository stores `RULES.md` and `vocab_bank.json`
at its root, while the runtime expects them under `rules/`. This integration
places them at the expected paths. Python modules are placed under
`engine-v2/`, and tests under `engine-v2/tests/`, matching the contracts.

## Not yet connected

- No API endpoint reads generated editions.
- No database ingestion for engine events, source contributions, facts,
  vocabulary or questions.
- No frontend Today/Topics/Exam Desk data binding.
- No scheduler or GitHub Actions workflow runs the live collector.
- No 50-publisher source registry or verified direct-feed coverage.
- No production publish validator in `tools/`.

## Required next milestones

1. Run deterministic and live-collection tests in the target repository.
2. Repair English rendering for Bangla-origin articles and enrich vocabulary.
3. Reconcile the 0–3 engine score with the 0–10 app score and expand topics.
4. Add event/article/fact/question/vocabulary database models and an importer.
5. Expose read-only edition APIs and connect the frontend.
6. Add source health and coverage reporting.
7. Enable scheduled collection only after the test and human-review gates pass.

The import does not publish or activate any article.
