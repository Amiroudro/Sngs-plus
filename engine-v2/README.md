# Engine v2 inside Sarangsho Plus

This directory contains the source modules imported from the standalone
`Amiroudro/Engine` repository. The canonical editorial rules and vocabulary
bank are stored in `rules/`, matching the paths expected by the code.

## Status

This is an integration branch, not a live publishing deployment. The engine
has not yet been connected to the FastAPI briefing endpoint or the Astro UI.
The imported 15 November 2026 run is a historical dry-run, not a live feed.

## Runtime

Requires Python 3.11+ and uses the Python standard library.

From the repository root:

```bash
python3 engine-v2/rules_loader.py
python3 engine-v2/run_v2.py --help
python3 engine-v2/run_v2_daily.py --help
```

The orchestrator writes generated material under `engine-v2/runs/<date>/`.
Conversion writes to a staging directory. Publishing is a separate,
human-approved action; browser/GitHub sync is separate again.

## Important limitations before production

- The source collector has a small, mixed-access set of publisher routes and
  aggregator discovery queries. It does not provide 50 direct publisher feeds.
- Some sites are blocked or inaccessible from the test environment. Do not
  bypass robots.txt, paywalls, logins or technical access controls.
- The current relevance rubric is 0–3. The app editorial standard requires
  0–10; a documented mapping and wider topic taxonomy are still required.
- Bangla-origin articles need genuine English translation before they can be
  shown in English mode. The current glossary-based rendering is insufficient.
- Vocabulary enrichment is incomplete for new headwords.
- Step 5 checks traceability to the article; this is not independent
  corroboration. Important claims need a separate primary-source check.
- The publishing gate references the legacy edition validator under
  `tools/`, which has not yet been imported into this repository.
- No live sources are enabled in the app database. No output is auto-published.

Do not mark an edition live until the editorial fixes, integration tests,
validator, and human review are complete.
