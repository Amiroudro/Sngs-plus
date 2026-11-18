# System B Audit — Final Report (Phase 0, workstream 4)

**Scope:** ChatGPT's scaffold in the PRIVATE repo `Amiroudro/Sngs-plus`, at main HEAD `cb5d4e12` (16 Nov 2026 21:54 UTC). READ-ONLY audit — nothing merged, pushed, or edited.
**Method:** Recovered raw material in `/tmp/auditB/` re-read in full; gaps filled with the GitHub connector read tools (`get_file_contents`, `list_commits`, `search_code`) plus local files under `~/workspace/sarangsho-plus/`. Web search used once (Flutter 3.50.0 existence) and `browser.open` once (Pages 404 check).

## 0. What the previous auditor got wrong, and what failed to fetch

- **Recovered and usable:** all f0–f9 files, rights/taxonomy/integ/pkg, `prs.json` (17 PRs).
- **Failed fetches (all errors, re-attempted by me):** `pr6.json`, `pr7.json`, `pr8.json`, `pr17files.json`, `pr17status.json` — every one reads `Error: GitHub MCP server does not currently advertise tool 'get_pull_request_files' / 'get_pull_request_status'`. I re-ran all four tool names directly: `get_pull_request`, `get_pull_request_files`, `get_pull_request_status` are **not advertised by the live MCP server**, even though the connector doc lists them as reviewed read tools. `pull_request_read` exists in the live catalog but is **not in Muse's reviewed read-only set**, so I did not use it. Consequence: **no PR file list and no PR check status is obtainable through the approved read tools.** Worked around by fetching files at the PR branch ref (`ci.yml` at `fix/flutter-android-ci-toolchain`) and by reading full PR bodies from `prs.json`.
- **`search_code` is effectively unusable for this repo:** with `owner/repo/query` args it silently searches all of GitHub (returned results from `ag2ai/fastagency` etc.); with `repo:Amiroudro/Sngs-plus …` in the query it returns `total_count: 0, incomplete_results: true`. Private-repo code search returns nothing. All "does X exist in the repo" answers below come from direct `get_file_contents` fetches, not search.
- **Workflow run history is not reachable** via the approved read tools (no runs API in the reviewed set). Any claim about a specific scheduled run's outcome is therefore reasoning from the workflow file + known validator state, not observation. Stated explicitly wherever it matters (§3).
- **Coordinator-context correction #1:** "zero `CREATE TABLE` in the repo (no SQLite schemas exist anywhere)" is **wrong**. `database/schema.sql` has 6 `CREATE TABLE`s and the three migration files add 11 more tables plus 8 triggers (§6).

---

## 1. Workflows (f0–f3) — ADAPT

### 1a. `automatic-edition-sync.yml` (f0) — the important one

**What it really does.** Triggers: `push` (only when its own file changes), `workflow_dispatch`, and **schedule `cron: "0 2,12 * * *"`** — i.e. 08:00 and 18:00 Asia/Dhaka, as the comment says. Steps: checkout `Sngs-plus` main; checkout public `Amiroudro/sarangsho-plus-editions` into `source-editions/`; run `python source-editions/tools/validate_renovated_editions.py`; copy every `status: published` edition into `editions/` (EN) and `app/assets/editions/` (EN byte-identical + BN overlay, stamping `translation_status: "automated_checks_passed"` only where headline/summary/why_it_matters are non-empty — the file itself comments "This is a structural gate, not a claim of human or factual verification"); set up Python 3.11, install `backend/requirements.txt`, run backend unit tests; commit as `github-actions[bot]` with `git push origin HEAD:main` (default `GITHUB_TOKEN`).

**The earlier claim is wrong.** The previous auditor's claim that "no scheduled workflow exists" is refuted by the file itself (`schedule:` + `cron: "0 2,12 * * *"`). The schedule is real, and it has run: main HEAD is itself a sync commit, `cb5d4e12 "chore: sync automatically validated editions"` (16 Nov 21:54 UTC), preceded by `66b81623` (16 Nov 09:24 UTC) with the same message. Two successful scheduled syncs on 16 Nov prove the workflow works when the validator passes.

**Edition 11 / 17 Nov question.** The validator is fail-closed by construction: `if errors: … return 1`, and `if __name__ == "__main__": raise SystemExit(main())` — any issue count > 0 exits non-zero and the GitHub Actions step fails, stopping the job before any copy or commit. It validates the **whole archive** (every edition in the source index), so one bad edition blocks sync of all of them. Edition 11 was published 09:06 Dhaka (03:06 UTC) on 17 Nov, i.e. **after** the 08:00 Dhaka (02:00 UTC) run and **before** the 18:00 Dhaka (12:00 UTC) run. Therefore: the 08:00 run could not have seen Edition 11; the 18:00 run would have run the validator against an archive containing Edition 11's 86 issues and **failed at "Validate source archive before syncing", syncing nothing**. Caveat (unverifiable): I could not check workflow run history or the exact time the 86-issue state entered the editions repo, so this is deduction from the workflow file + the known validator failure, not an observed run. The "Validate renovated editions" run #20 failure (86 issues: ~19 words + ~9 phrases with empty enrichment fields, duplicate headword `postpone`) is taken from the coordinator's verified record.

**The GITHUB_TOKEN chain break (the workflow's real defect).** PR #9's body claims the sync commit works by "triggering the existing CI workflow". That is false under GitHub's rule: events triggered by `GITHUB_TOKEN` — except `workflow_dispatch` and `repository_dispatch` — do **not** create a new workflow run. A sync commit therefore triggers **neither** `ci.yml` **nor** `deploy-pages.yml` (whose push trigger covers `editions/**` and `app/assets/editions/**`). Consequence: even a perfectly successful sync never redeploys the Pages site. Deployment only happens on a direct human push touching `frontend/**`, `editions/**`, `app/assets/editions/**`, or the deploy workflow file itself, or by manual dispatch. PR #10 correctly notes "edition commits do not retrigger this workflow" (its push trigger is path-limited to its own file) but nobody noticed the same token rule also silences the deploy chain.

### 1b. `ci.yml` (f1, "Foundation checks")

Four jobs on push/PR to main: `api-check` (backend compile + backend tests + `database/tests`), `web-build` (Node 22, `npm install`, Astro build), `flutter-app` (Java 17, **Flutter `3.50.0`** — the version PR #17 fixes — then `flutter pub get`, `tools/check_data.py`, `flutter analyze`, `flutter test`, release APK build, artifact upload), `engine-v2` (compile + rules load + 11 named test files). Gaps in coverage: the engine-v2 job runs only a named subset — it does **not** run `test_exam_learning_sidecar.py`, `test_step1.py`, `test_step456.py`, `test_step789.py`, or the metadata-archive tests. A test can exist in the repo and never execute in CI.

### 1c. `deploy-pages.yml` (f2)

Push trigger on `frontend/**`, `editions/**`, `app/assets/editions/**`, its own file + dispatch. Copies `editions/index.json`, `editions/data-*.json`, `app/assets/editions/bn-*.json` into `frontend/public/editions/`, builds Astro, verifies `dist/index.html`, `dist/today/index.html`, `dist/editions/index.json`, and — hardcoded — `dist/editions/bn-2026-11-15.json` (brittle: verifies a fixed date, not the latest edition). Publishes with `peaceiris/actions-gh-pages@v4`, `personal_token: ${{ secrets.PAGES_DEPLOY_TOKEN }}`, to `Amiroudro/sarangsho-plus-editions` `gh-pages`, `force_orphan: true`. Depends on a secret whose existence cannot be checked via read tools. **The site is not live: `https://amiroudro.github.io/sarangsho-plus-editions/` returns HTTP 404 (verified by direct fetch during this audit).**

### 1d. `engine-v2-smoke.yml` (f3)

PR/push on `engine-v2/**` + dispatch. Compiles engine modules, loads rules/vocab, runs 8 named tests (`test_collection_policy`, `test_robots_policy`, `test_source_routes`, `test_rights_registry`, `test_rights_sync`, `test_step2`, `test_step3`, `test_translation_approval_gate`). Also does **not** run the sidecar test — contradicting PR #7's claim ("Run the new test in the Engine v2 smoke workflow").

**Verdict: ADAPT** — the sync workflow is real and proven when the validator passes, but fix the token-trigger break (use a PAT or `workflow_dispatch` chaining for deploy) and add the sidecar test to a workflow that actually runs it. The schedule claim in the earlier audit was wrong; the workflow file is the evidence.

---

## 2. Rights registry — ADAPT (as policy; DROP as an operating control unless wired in)

**What it really does.** `engine-v2/rights_registry.py` (7,316 bytes) is a fail-closed policy gate. `load_registry()` requires `version == 1` and a `publishers` dict, else raises (callers must stop). `_review_current()` requires a valid `reviewed_at` and a `review_due_at` that is not past and not before the review date, plus an unexpired `expires_at` if set. Three decisions, all requiring `source_enabled is True` plus current scope + evidence + dated review:
- `metadata_decision`: `metadata_status == "approved"` + metadata scope/evidence + `automated_processing_status == "approved"` with its own scope/evidence.
- `page_metadata_decision`: page-metadata approval + scope/evidence, or a body licence.
- `body_decision`: `body_status == "licensed"` + body scope/evidence + automated processing.
`filter_metadata_items()` strips RSS descriptions ("RSS descriptions are article excerpts, not basic bibliographic metadata… do not retain or process them"). Discovery hosts allowed: `bing.com`, `www.bing.com`, `news.google.com`. Unknown/unmapped domains are denied; robots policy is enforced independently and fail-closed.

**State (verified by parsing `engine-v2/state/source_rights.json`, 55 publishers):** `source_enabled: false` for **55/55**. `metadata_status: pending` 55/55. `page_metadata_status: pending` 55/55. `body_status: not_permitted` 55/55. `automated_processing_status: pending` 53, `restricted` 2 (Daily Inqilab, Risingbd — third-party registry reports AI-crawler blocks). `reviewed_at` and `review_due_at` are **empty for all 55**; **zero records carry any scope or evidence string at all**. The only populated "evidence" fields are third-party directory labels, e.g. `third_party_feed_registry_status: "listed_as_feed_verified_2026-10-17"` pointing at `https://inklinenews.com/feeds/bangladesh/` — discovery signal, explicitly not permission.

**How a publisher becomes approved/enabled.** Nothing in the repo does it automatically. The documented path (`INTEGRATION_STATUS.md`): record the review in the SQLite ledger table `source_rights_reviews`, then run `engine-v2/sync_rights_registry.py --write` (dry-run by default; manual, one-way, human-reviewed) to export into `state/source_rights.json` and `state/source_routes.json`. There is no admin UI, no schedule, no live process. Approval requires: metadata scope + evidence, automated-processing scope + evidence, a dated review with a future due date, and `source_enabled: true`.

**What depends on it, and what zero-enabled means.** In System B's design, everything: Step 1 collection is gated by `metadata_decision`; page extraction and body fetching each need their own approval. With zero enabled, a wired-in gate would collect **nothing**. In practice the gate is not wired into anything that produces editions: **the local working engine-v2 has no `rights_registry.py` at all** and collects via Google News/Bing discovery plus direct RSS/sitemaps with no rights gate. So the registry is currently a policy document plus passing unit tests, not an operating control. Its value is the fail-closed design and the honest ledger (55 hosts, 8 third-party leads, 19 historical routes, 0 verified, 0 enabled — all consistent with `INTEGRATION_STATUS.md`).

**Verdict: ADAPT** — keep the fail-closed design and the ledger as the Phase 1 rights workflow, but only if Phase 1 actually wires it into collection; as it stands it gates nothing. Do not present "55 publishers in the registry" as 55 sources — it is 55 disabled rows.

---

## 3. Auto-sync chain (PRs #9–12) — ADAPT

Covered in §1a, summarised: PR #9 (twice-daily sync + Bangla structural validation; GITHUB_TOKEN commit; wrong claim about triggering CI), PR #10 (one-time trigger via workflow-file push), PR #11 (fixed JSON newline serialisation + backend-deps install order after the first real run failed because FastAPI was not installed), PR #12 (added the renovated-archive validator gate before copying). **Proven working** when the validator passes (two sync commits 16 Nov). **Broken in two places:** (1) whole-archive validation means one bad edition (Edition 11, 86 issues) blocks all syncing — by design, but with no alerting and no partial sync; (2) the GITHUB_TOKEN commit never triggers `deploy-pages.yml`, so synced editions never reach the live site automatically. The sync workflow also runs backend tests *after* copying but *before* committing, which is the right order.

**Verdict: ADAPT** — keep, but fix the deploy trigger (PAT or dispatch) and consider per-edition validation so one bad edition cannot hold the other 15 hostage.

---

## 4. Exam-learning sidecar (PRs #6–8) — DROP in current form; ADAPT the spec

**What it is supposed to add.** Per `engine-v2/EXAM_LEARNING_SIDECAR.md` and `docs/EXAM_LEARNING_SCHEMA.md`: an optional, editor-researched `exam-learning-YYYY-MM-DD.json` placed in the run directory, keyed by original v2 story ID, with separate `en`/`bn` layers of up to 10 sections (`concepts`, `institutions`, `processes`, `distinctions`, `exam_notes`, `mcqs`, `short_questions`, `analytical_questions`, `vocabulary`, `revision`), each material fact carrying `source_refs` (`title, publisher, url, published_date, accessed_date, source_type`). The converter "only validates the sidecar's outer structure and attaches the supplied objects. It does not fetch URLs, fact-check claims, translate text or approve publication." Missing sidecar = valid no-enrichment run; invalid date/structure = conversion stops. Bangla notes display only when the story overlay has `translation_status: "approved"`. PR #6 renders the sections on the Today page with Bangla-first gating; PR #7 wires the sidecar into conversion; PR #8 renders source citations.

**What is actually broken — the central finding of this audit.** The functions the sidecar depends on **do not exist**:
- `grep -c "learning"` on the repo's `engine-v2/convert_to_app.py` at HEAD `cb5d4e12` = **0**. Its `def` list contains no `validate_exam_learning_sidecar` and no `attach_exam_learning`.
- The local working converter (`~/workspace/sarangsho-plus/engine-v2/convert_to_app.py`, 76,205 bytes) also contains neither function.
- Yet `engine-v2/tests/test_exam_learning_sidecar.py` (2,678 bytes, merged in PR #7) imports `convert_to_app as converter` and calls `converter.validate_exam_learning_sidecar(...)` and `converter.attach_exam_learning(...)` — **that test cannot pass as written** (the names don't exist to import/call).
- And no workflow runs it anyway: neither `ci.yml`'s engine-v2 job nor `engine-v2-smoke.yml` lists `test_exam_learning_sidecar.py`, contradicting PR #7's "Run the new test in the Engine v2 smoke workflow".

So the attach path is unproven and, as the code stands, non-functional: nothing in the converter reads a sidecar file at all (zero "learning" matches in the whole file).

**Who consumes it.** The Astro Today page *does* render `story.exam_learning || story.learning` (EN mode; Bangla mode explicitly `delete merged.exam_learning` so English learning text never leaks into Bangla). But **no shipped data contains the key**: `grep -rl "exam_learning"` over `~/workspace/sarangsho-plus/renovated-editions/` and `~/workspace/sarangsho-plus/app/assets/editions/` returns **nothing**. The Flutter app does not read `exam_learning` either — it reads the renovation's `learning_module` object with `topic_gk` / `exam_notes` (`app/lib/models.dart:616,676,687,853`). The local engine-v2 has no sidecar doc, no test, no functions. The sidecar is therefore a spec + two docs + a failing test + a frontend renderer with **no data supply on either side**. Note also the format split nobody reconciled: System B's `exam_learning_en/bn` and the renovation's `learning_module` are two different, incompatible learning shapes for the same stories.

**Verdict: DROP in current form** — do not carry the sidecar code forward as if it works. **ADAPT the spec**: the schema doc (10 sections, source_refs, MCQ rules) is sound and worth keeping as the target contract for the 2.0 learning-module format, but it must be re-implemented against the converter that actually ships, with its test added to a workflow that runs it, and reconciled with `learning_module` (one shape, not two).

---

## 5. Astro frontend (f4, f8, f9 + package.json) — ADAPT (Today page) / DROP (homepage as a live product claim)

**What it is.** `frontend/astro.config.mjs`: `site: 'https://amiroudro.github.io'`, `base: '/sarangsho-plus-editions'`, `output: 'static'`. `frontend/package.json`: `sarangsho-plus-web` 0.1.0, Astro `^5.7.0`, `@astrojs/check`, TypeScript; scripts `dev/build/preview/check`. Only two pages exist: `src/pages/index.astro` (192 lines) and `src/pages/today.astro` (633 lines). `frontend/public/` contains only `.nojekyll` and `manifest.webmanifest`.

**Homepage (`index.astro`): static marketing only.** Hero, coverage desks, method, footer. No `fetch`, no edition data. Its own copy admits it: "These are the coverage desks the platform is being built around, not live articles or current headlines." Small but telling inconsistency: the status pill's `data-en` says `PUBLISHED EDITIONS · AUTOMATIC SYNC ENABLED` while the visible default text says `FOUNDATION PREVIEW · LIVE FEEDS NOT CONNECTED` (and `data-bn` says `প্রকাশিত সংস্করণ · স্বয়ংক্রিয় সমন্বয় চালু`) — the English toggle string claims something the visible text contradicts. PR #14 ("Refresh homepage status") evidently left the three strings disagreeing.

**Today page (`today.astro`): a real renderer, with real data paths.** It fetches `BASE_URL + 'editions/index.json'`, picks the latest `status: published` edition, loads `data-<date>.json` and `bn-<date>.json` from the bundled static files copied in by the deploy workflow. Bangla mode requires each story's `translation_status === 'automated_checks_passed'` plus headline/summary/why_it_matters, else the story is dropped and the page falls back to "No approved edition yet" / translation-pending. It renders story fields, key facts, sources, and the exam-learning sections with citations. The API path (`PUBLIC_API_BASE_URL + '/api/v1/briefing'`, `/api/v1/archive`) is used **only if** `PUBLIC_API_BASE_URL` is set; otherwise it uses the static path, and archive search is explicitly unavailable in the static build ("Archive search is unavailable in the static edition"). **No placeholder or sample data** — it renders real bundled JSON or an empty state. Two honest limits: (1) the exam-learning renderer has no data to render (see §4); (2) PR #15 records that "`astro check` reports a large set of pre-existing TypeScript diagnostics in the inline Today-page script" — the deploy workflow was changed to skip `astro check` and only run the production build, i.e. the diagnostics were worked around, not fixed.

**Deployment status.** The site has never deployed to a live URL: `https://amiroudro.github.io/sarangsho-plus-editions/` returns **HTTP 404** (verified by direct fetch in this audit). This contradicts PR #16's claim that "The successful deployment exposed malformed concatenated paths" — either Pages is not enabled from `gh-pages` in the editions repo, or no deploy ever actually succeeded, or `PAGES_DEPLOY_TOKEN` was never added (PR #13 says deployment "will remain pending until the repository owner adds `PAGES_DEPLOY_TOKEN` and enables Pages from `gh-pages`"). Which of these is true cannot be checked via the approved read tools (no secrets access, no run history) — it needs a look at the editions repo's Pages settings and the Actions run log.

**Verdict: ADAPT** — the Today page is genuine, working renderer code worth keeping; the homepage is a static brochure that over-claims in its toggle strings. Neither has ever been seen live.

---

## 6. INTEGRATION_STATUS.md + EXAM_TAXONOMY_V1.md

### 6a. `engine-v2/INTEGRATION_STATUS.md` — ADOPT with corrections (it is unusually honest, but stale)

**What it claims.** Branch `feature/engine-v2-runtime-import`, source `Amiroudro/Engine`, target `Amiroudro/Sngs-plus`, "Status: Draft integration; not merged and not live." Imported engine v2 steps 1–10, converter, publisher, rules, vocab, tests. Read-only published-edition API, bilingual Today page, metadata-only archive API, SQLite migrations, fail-closed rights gate, 50-publisher candidate directory (55 host records), 8 third-party feed leads, 19 historical collector routes, 0 verified routes, 0 enabled sources. Known limitations it admits itself: the 50-publisher directory "is not yet 50 direct feed integrations"; Bangla renderer is deterministic templates, not fluent translation; taxonomy specified but not wired; 0–10 assessment schema exists but "no calibrated scoring model or importer currently populates it"; "Engine events, facts, vocabulary and questions are not yet ingested into the new database tables"; "Topics and Exam Desk are not yet connected to the new data layer"; "The publisher gate still references a legacy validator that is not present in this repository"; "No articles have been published or synced to the app."

**What is stale or misleading.**
- **"Draft integration; not merged and not live" + "PR #4 must remain unmerged until the user approves it"** — stale. PR #4 merged `2026-11-15T19:50:54Z`. The doc was never updated after its own merge.
- **"No articles have been published or synced to the app"** — stale. Two sync commits on 16 Nov copied 15 published editions into `editions/` and `app/assets/editions/`; the app ships them.
- **"No live collection schedule is enabled"** — true for *collection*, but the *edition-sync* schedule (08:00/18:00 Dhaka) is live, and the sentence as written invites misreading it as "nothing runs on a schedule".
- **What checks out (verified):** the DB claims. `database/schema.sql` (6 tables: `sources, articles, events, event_articles, summaries, facts`) plus migrations `001_study_and_verification_layer.sql` (8 tables: `source_checks, fact_evidence, questions, question_options, vocabulary_entries, vocabulary_occurrences, review_progress, editorial_corrections`), `002_rights_translation_exam_assessment.sql` (3 tables: `source_rights_reviews, article_localizations, article_exam_assessments`; 2 triggers), `003_operational_rights_registry_sync.sql` (6 triggers, including `trg_sources_enable_requires_metadata_and_processing`, `trg_sources_body_mode_requires_license`, `trg_source_rights_reviews_no_update/no_delete`). The trigger-based least-privilege activation the doc describes exists in SQL. What does **not** exist is any runtime that applies these migrations or opens the database — the backend API reads JSON editions, CI only runs `database/tests` unit tests, and no deployment runs SQLite. The DB is a schema with no ingestion path and no operator.
- **Correction to the coordinator's brief:** the brief said "zero `CREATE TABLE` in the repo (no SQLite schemas exist anywhere)". That is wrong: 17 `CREATE TABLE` statements exist across `database/schema.sql` + migrations 001/002 (verified by direct fetch and count). What is true is that the *local working engine-v2* has no SQLite and no rights registry — the schemas live only in System B's `database/` + `backend/` layer.

**Verdict: ADOPT with corrections** — update the header (merged 15 Nov), the sync sentence, and the schedule sentence; keep the limitations section, which is accurate. It is the most honest document in System B.

### 6b. `docs/EXAM_TAXONOMY_V1.md` — ADOPT as spec, DROP as a claim of function

**What it claims.** "App-facing taxonomy specification. The Engine v2 primary topic IDs remain unchanged until a separately tested classifier upgrade is implemented." 18 reader-facing study tags (`BD-GOVERNANCE` … `PEOPLE-AWARDS`), 6 exam tracks (`bcs_preliminary`, `bcs_written`, `bangladesh_bank`, `bank_recruitment`, `government_recruitment`, `general_knowledge`), a multi-label mapping from the 10 engine topics, quality tiers by 0–10 score (8–10 full note, 5–7 concise, 2–4 short note, 0–1 archive only), and a 5-step implementation sequence ending in "Expose filters in the app only after tag assignments are validated."

**What is stale/misleading.** Nothing in it is false — but nothing in it is implemented either. No classifier exists; no code assigns `topic_tags_json`/`exam_tracks_json`; the `article_exam_assessments` table exists in migration 002 but, per `INTEGRATION_STATUS.md` itself, "no calibrated scoring model or importer currently populates it". Step 1 of its own sequence ("Store … in article_exam_assessments") has not happened. It also cites `docs/EDITORIAL_SCORING_CONTRACT.md` as authoritative — I did not verify that file's existence or contents (not fetched; listed under "could not verify").

**Verdict: ADOPT as spec** — the taxonomy design is sound and matches the 2.0 learning-platform direction; **DROP any implication that tagging works today**. It is a design doc, not a feature.

---

## 7. PR #17 — "Fix Android CI Flutter/Gradle toolchain mismatch" — ADOPT (the pin), merge only after a green run

**State.** Open draft, head branch `fix/flutter-android-ci-toolchain`, base `main`, created 16 Nov 08:55 UTC, 2 commits on base `e9ec62af`: `3b9ad2e8 "ci: pin Flutter to compatible Android toolchain"` and `ff9ec62 "Install required Android CMake version in CI"`. Check status **could not be verified**: `get_pull_request_status` / `get_pull_request_files` / `get_pull_request` are not advertised by the live MCP server (re-attempted directly), and `pull_request_read` is not in Muse's reviewed read-only set, so no CI run result for this branch is obtainable through approved read tools.

**What the PR actually changes (verified by fetching `.github/workflows/ci.yml` at the branch ref).** Exactly two changes against main: `flutter-version: '3.50.0'` → `'3.35.7'` in the `flutter-app` job, and a new step "Install Android CMake 3.31.6" (via `sdkmanager`) before `flutter pub get`. Everything else unchanged: Gradle wrapper 8.11.1, AGP 8.9.2, Kotlin plugin, app identity, signing, data.

**Is the pin correct? Judged against the local working app — yes, exactly right.**
- Local `app/android/settings.gradle`: `com.android.application version "8.9.2"`, `org.jetbrains.kotlin.android version "2.1.0"`. Local wrapper: Gradle **8.11.1**. Local `app/android/app/build.gradle`: CMake `version "3.31.6"` (comment: "AGP's default CMake is 3.22.1, whose Linux package Google no longer hosts; use the installed 3.31.6 instead"). Local `app/pubspec.yaml`: `flutter: ">=3.22.0"` (no pin), version `1.3.0+2014`. The task brief confirms the working app builds locally with Flutter **3.35.7** stable, AGP 8.9.2, Gradle 8.11.1, and its release build works.
- The repo's `app/` files are byte-identical to local on every checked file (settings, build.gradle, pubspec content except version) — so the pin matches the toolchain the app demonstrably ships with.
- Flutter 3.50.0 is real (stable, released 11 Nov 2026 with Dart 3.14 — verified by web search), so CI's `3.50.0` was not a typo; it was the brand-new stable, and the PR body's account (resolution/analysis/tests pass, release APK build fails because 3.50.0 wants a newer Gradle generation than the repo's AGP 8.9.2 setup) is plausible. The PR body's own compatibility note checks out: AGP 8.9's minimum Gradle is 8.11.1, which is what the wrapper has.
- One flag: the repo's `app/pubspec.yaml` is version **1.2.1+2013** while the local shipped app is **1.3.0+2014** — the repo lags the shipped app by one release. Merging the pin fixes CI's toolchain, but CI would then build and test the older 2013 app, not the 2014 one Rudro ships. That lag should be closed separately (sync the app, or it will keep confusing "CI green" with "the shipped app is green").
- The PR body's own safety note is the right call and still stands: "the PR must remain unmerged until its actual GitHub Actions run verifies the release build." That verification has not been observed by this audit.

**Verdict: ADOPT** — the 3.35.7 pin + CMake 3.31.6 install are the correct, minimal, conservative fix and match the proven local toolchain exactly. Merge only after a green Actions run on the branch is actually seen.

---

## 8. Overall judgment: how much of System B is real?

**Roughly a third is real working infrastructure; a third is honest spec and ledger; a third is scaffold that claims more than it does.**

| Piece | Real? |
|---|---|
| Auto-sync workflow (f0) | **Real and proven** — ran twice successfully 16 Nov; schedule is genuine. Broken downstream (validator blocks on any bad edition; GITHUB_TOKEN never triggers deploy). |
| `ci.yml` / smoke workflow | **Real, partial** — runs, but covers a named subset of tests; Flutter job was pinned to a broken-new 3.50.0 until PR #17. |
| Rights registry code + state | **Real code, honest ledger, zero effect** — fail-closed design is sound, 55/55 disabled is truthful, but it gates nothing because the engine that produces editions doesn't load it. |
| SQLite schema + migrations + triggers | **Real SQL, no runtime** — 17 tables + 8 triggers exist and match the doc; nothing applies them, populates them, or reads them in production. |
| Backend API (`backend/`, `database/tests`) | **Real code, no host** — unit-tested in CI, never deployed; the Astro site defaults to static JSON. |
| Astro Today page | **Real renderer, no audience** — correctly renders real bundled editions with Bangla gating; never deployed (site 404s). |
| Astro homepage | **Static brochure** with self-contradictory status strings. |
| Exam-learning sidecar | **Scaffold that doesn't run** — spec + docs are good, the converter functions don't exist, its test can't pass, no workflow runs it, no data carries the key, the Flutter app reads a different shape. |
| Taxonomy | **Spec only** — sound design, zero implementation. |
| `INTEGRATION_STATUS.md` | **Honest but stale** — the limitations section is accurate; the header and two status sentences are out of date since PR #4 merged. |
| PR #17 | **Correct fix, unverified** — the pin matches the proven toolchain; its required green CI run has not been observed. |

**The single most important structural fact:** System B and the working product (System A) are two parallel stacks that barely touch. The working engine-v2 has no rights registry, no SQLite, no sidecar; the working app reads `learning_module`, not `exam_learning`; the working editions live in the public editions repo and reach the phone through the app's own update banner. System B's sync workflow is the one real bridge — it copies editions into the repo — and even that bridge ends at a commit that triggers no deployment. Everything else in System B (API, DB, rights gate, taxonomy, sidecar, Astro site) is a second, unconnected system built around the same data. Phase 1 should therefore pick, per piece, ADOPT vs ADAPT vs DROP as above — and should not assume that because a file exists in System B, the capability exists in the product.

## 9. What I could not verify (and how to check)

1. **PR #17 check status / CI run result on `fix/flutter-android-ci-toolchain`.** `get_pull_request_status`, `get_pull_request_files`, `get_pull_request` are not advertised by the live GitHub MCP server; `pull_request_read` is not in Muse's reviewed read-only set. Check: open the PR on github.com (or use a browser agent) and read the Checks tab / the Actions run for the branch.
2. **Whether the 18:00 Dhaka 17 Nov scheduled sync actually failed** (and which run failed first). No workflow-run history API in the approved read tools. Check: `Amiroudro/Sngs-plus` → Actions → "Automatic edition sync" run list for 17 Nov.
3. **Whether `PAGES_DEPLOY_TOKEN` exists and whether any deploy-pages run ever succeeded** (PR #16 claims a successful deployment; the site 404s). No secrets/run access via read tools. Check: repo Settings → Secrets + Actions → "Build and deploy Sarangsho Plus to GitHub Pages" runs; and the editions repo's Settings → Pages (is Pages enabled from `gh-pages`?).
4. **Whether any sidecar file (`exam-learning-*.json`) was ever created.** Nothing in the repo or local workspace references one; a sidecar in a run directory would not be in the repo. Check: local run directories / whoever would have authored one (ChatGPT).
5. **`docs/EDITORIAL_SCORING_CONTRACT.md`** (cited as authoritative by the taxonomy) — existence/contents not fetched.
6. **The 86-issue Edition 11 validator failure itself** (run #20) — taken from the coordinator's verified record, not re-observed; the validator code path (any error → exit 1) was verified by direct fetch from the editions repo.
