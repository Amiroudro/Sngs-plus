# Engine v2 inside Sarangsho Plus

This directory contains the source modules imported from the standalone
Amiroudro/Engine repository. The canonical editorial rules and vocabulary
bank are stored in rules/, matching the paths expected by the code.

## Status

This is an integration branch, not a live publishing deployment. The
published-edition API and Astro Today page are connected, but Engine output
is not yet imported into the application database or automatically scheduled.
The imported 15 November 2026 run is a historical dry-run, not a live feed.

## Runtime

Requires Python 3.11+ and uses the Python standard library.

From the repository root:

```bash
python3 engine-v2/rules_loader.py
python3 engine-v2/run_v2.py --help
python3 engine-v2/run_v2_daily.py --help
python3 engine-v2/tests/test_robots_policy.py
python3 engine-v2/tests/test_rights_registry.py
```

The orchestrator writes generated material under engine-v2/runs/<date>/.
Conversion writes to a staging directory. Publishing is a separate,
human-approved action; browser/GitHub sync is separate again.

## Publisher rights registry

The operational collector policy is in:

- rights_registry.py
- state/source_rights.json

The registry denies unknown publishers by default. Direct publisher feed and
sitemap routes require approved metadata scope, permission evidence, a
current dated review and separate automated-processing permission. Bing and Google News may be used only as discovery
inputs; each resulting publisher URL is checked against the registry.
Article-page headline extraction requires separate page-metadata permission
and automated-processing approval. Article-body fetching requires a current
licence with explicit scope/evidence and automated-processing approval. Robots rules are enforced independently, and robots.txt fetch
failures are fail-closed.

The 16 November 2026 source audit records 49 domain leads for the 50 candidate
publishers; Sonali Sangbad remains unresolved. The registry includes aliases
and BSS/UNB. Third-party feed-verification claims are discovery leads, not
publisher permission. All metadata and page-metadata statuses remain pending. Automated-processing status is pending or restricted for flagged sources; article-body processing remains not permitted.
No publisher is enabled.

SQLite source_rights_reviews is the review ledger. Run sync_rights_registry.py
with --db to preview the latest DB-to-JSON changes; add --write only after
reviewing the report. This is a manual, one-way sync, not a scheduled process.
Record approvals in the DB ledger and do not edit approved JSON entries by hand.

## Important limitations before production

- The source collector has a small set of hard-coded publisher routes and
  aggregator discovery queries. It does not provide 50 direct publisher feeds.
- Some sites are blocked or inaccessible from the test environment. Do not
  bypass robots.txt, paywalls, logins or technical access controls.
- Public RSS availability does not itself grant a right to reuse article
  bodies, generate derivative summaries or redistribute content.
- The current relevance rubric is 0–3. The app editorial standard requires
  0–10; the separate schema exists but is not yet calibrated or populated.
- Bangla-origin articles need genuine English translation before they can be
  shown in English mode. The current glossary-based rendering is insufficient.
- Vocabulary enrichment is incomplete for new headwords.
- Step 5 checks traceability to the article; this is not independent
  corroboration. Important claims need a separate primary-source check.
- The publishing gate references the legacy edition validator under tools/,
  which has not yet been imported into this repository.
- No live sources are enabled in the app database. No output is auto-published.

Do not mark an edition live until the editorial fixes, integration tests,
validator, rights review and human approval are complete.
