# Sarangsho Plus — AI Guide

**For an outside AI (ChatGPT, Claude, or any collaborator) handed this repo.**
Read this first. It is the map: what the project is, where everything lives,
how to build, test and release it, and the rules that keep it honest.
Current as of **18 November 2026** (app 1.4.0, build 2015).
If this guide and `README.md` disagree, this guide wins — `README.md` is
stale in places (it still says app 1.2.1 and that engine v2 is not live).

## 1. What this is

Sarangsho Plus is a **Bengali-first daily newspaper + BCS/Bank exam-prep
platform** for job candidates in Bangladesh, built by the owner (Rudro)
to compete with the Sarangsho app. It has three parts that live in this repo:

- **`app/`** — the Flutter app (Android). Bengali-first: daily editions,
  story learning modules, vocabulary cards, MCQ quizzes, SRS revision,
  self-update from GitHub. Free, offline-first, no login, no ads.
- **`engine-v2/`** — the Python daily engine (standard library only).
  Collects the day's news, ranks it, writes the edition, and gates it
  through a 15-check publish gate. This is the **live, working engine**.
- **`engine-v1/`** — the FROZEN v1 engine. It produced Editions 1–10
  and the 7/7 proof. Read it for history only. **Do not run it.**
  (Its tracker is `engine-v1/tracker.md`, final state: 9 correct v1
  editions, run closed.)

The **live editions feed** (what the app downloads, plus `app/version.json`
and the app Releases) lives in a **separate public repo**,
`Amiroudro/sarangsho-plus-editions`, served by GitHub Pages. It is **not**
in this repo. Do not touch it from here — syncs to it go through the
GitHub web UI as Amiroudro and are currently HELD (see §7).

**Owner:** Rudro (GitHub `Amiroudro`). He decides what goes live.
CAT (his main agent) verifies, runs the engine, builds and ships.
You write and propose; Rudro/CAT verify and release.

**Free-only, always.** No paid APIs, services, hosting or subscriptions.
No card on file anywhere. If a task seems to need something paid, stop
and say so — do not sign up for anything.

## 2. Where things live

```
Sngs-plus/
├── README.md                    # Repo map (STALE in places — see note above)
├── docs/
│   └── AI_GUIDE.md              # This file — the authoritative handover doc
├── app/                         # Flutter app, package com.sarangsho.plus
│   ├── lib/                     # main.dart, models.dart, data/, screens/,
│   │                            # services/, state/, utils/, widgets/
│   ├── test/                    # Dart tests + golden tests (PNG masters
│   │                            # live in test/goldens/ — see §3)
│   ├── tools/                   # build_release.sh (release gate), validators
│   ├── android/                 # Gradle config, manifest, launcher icons
│   ├── assets/editions/         # Bundled edition JSONs (EN data-*.json)
│   │                            # + Bangla overlays (bn-*.json) + index.json
│   ├── assets/fonts/            # Hind Siliguri + Noto Serif Bengali (TTF)
│   ├── assets/engine-rules/     # rules.md mirrored from engine-v2
│   ├── pubspec.yaml             # version 1.4.0+2015
│   └── app-version.json         # Update channel: latest version + APK URL
├── engine-v2/                   # The live daily engine (Python stdlib only)
│   ├── step1_collect.py … step10_vocab.py   # The pipeline, one file per step
│   ├── run_v2.py / run_v2_daily.py          # Orchestrator (daily run)
│   ├── convert_to_app.py        # v2 edition → app-format JSON
│   ├── publish_v2.py            # 15-check gate + publish
│   ├── learning_module.py       # 11-section learning-module builder
│   ├── common.py                # Shared helpers (incl. clean_body_text)
│   ├── rules/                   # RULES.md, vocab_bank.json,
│   │                            # enrichment.json, gk_knowledge.json
│   ├── tests/                   # pytest-style suites, one per step
│   ├── tools/check_routes.py    # Weekly source-route health check
│   ├── SOURCES.md               # Source registry (11/15 papers wired)
│   ├── CONTRACTS.md             # Edition format + gate contract
│   ├── CRON_INSTRUCTIONS_V2.md  # Exact daily-run instructions
│   └── state/sources.json       # Source state (not run data)
├── engine-v1/                   # FROZEN v1 engine + runbook + tracker
├── design-system/               # Design tokens + system spec (2.0)
│   └── sarangsho-plus/MASTER.md, tokens.json (DTCG), RECONCILIATION.md
├── renovation/                  # Renovation + v2-conversion tooling & specs
│   ├── RENOVATION_SPEC.md, LEARNING_MODULE_MODEL_V2.md
│   ├── CONVERSION_RULES_V2.md, convert_v1_to_v2.py, conversion-verify.py
│   └── conversion-summary.json (audit trail)
├── tools/
│   └── validate_editions.py + validate_editions_allowlist.json
│                            # Edition validator (used by the release gate)
├── phase0-audit-system-b.md     # Audit of the scaffold parts (see §6)
├── frontend/ backend/ database/ # Astro web scaffold — NOT the live product
├── docs/                        # Scaffold docs (taxonomy, integration status)
└── .github/workflows/           # Auto-sync, CI, Pages deploy, smoke
```

**Not in this repo, by design:** the release keystore +
`keystore.properties` (§3), build outputs (`app/build/`, `.dart_tool/`),
`__pycache__`, daily run data (`engine-v2/runs/`, `engine/runs/` — run
outputs stay local, only code + rules + docs are synced here), and the
`reverse-engineering/` directory (never in any repo).

**Repo-only scaffold files** (not part of the working product, left
untouched by the working tree — see `phase0-audit-system-b.md` for the
verdict on each): `frontend/`, `backend/`, `database/schema.sql`
(6 tables, no runtime applies or reads them), `docs/EXAM_TAXONOMY_V1.md`,
`docs/INTEGRATION_STATUS.md`, `engine-v2/rights_registry.py`,
`engine-v2/INTEGRATION_STATUS.md`. Do not mistake them for the live system.

## 3. The app (Flutter)

- **Stack:** Flutter **3.35.7** stable (Dart 3.9.2), Android only.
  On CAT's machine it lives at `~/tools/flutter/bin`; on another machine
  install Flutter 3.35.7 + **JDK 17** (`openjdk-17-jdk-headless`).
  Gradle wrapper 8.11.1, AGP 8.9.2. The Gradle daemon needs IPv4
  loopback (`-Djava.net.preferIPv4Stack=true` — the release script sets it).
- **Dependencies — deliberately light, no heavy packages:**
  `shared_preferences`, `url_launcher`, `path_provider` (+
  `path_provider_android` pinned **exactly** to 2.2.17 — 2.2.20 needs
  AGP 8.12.1, which is not cached). No `http` package (uses
  `dart:io` HttpClient). No new fonts or assets without Rudro's say-so.
  Report the APK size with every release.
- **Current version: 1.4.0+2015.** `pubspec.yaml` `version` and
  `lib/services/app_update_service.dart` `currentVersionCode` must match
  — the release gate checks this. The 1.4.0 APK is 52,219,478 bytes,
  SHA-256 `366e9c54cc25abf62a534020e0b7ed602d05a0025628bc02443c1bb0832c7fff`.
- **Self-update:** the app polls `app/version.json` (in the editions-feed
  repo) and shows an update banner when `latest_version_code` is newer.
  It downloads the APK from the GitHub Release asset URL in that file.
  Never deliver APKs in chat — the update goes through this channel.
- **Release keystore — READ THIS:** `app/sarangsho-plus-release.keystore`
  (alias `sarangsho-plus`, valid until 2054) + `app/keystore.properties`
  live **only** on the owner's machine, mode 600. **NEVER put them in
  this repo, any handover, any chat message, or any screenshot.**
  Losing them means no Play Store updates ever — only a new listing.
  Release signing stays with Rudro/CAT. If you build an APK, it will be
  unsigned/debug. The release certificate SHA-256 is
  `b8d0d003dc79ec7e28f86d8b61b9a4802c4dce573260f8fbace1239c537e1db7`
  — verify any release APK against it with `apksigner`.
- **Build / test / release:**
  ```
  flutter analyze
  flutter test            # 187 tests at 1.4.0; golden tests included
  app/tools/build_release.sh   # THE release gate — run this, not bare flutter build
  ```
  The gate runs, in order: the edition validator
  (`tools/validate_editions.py`, run from the repo root), the Bengali
  validator (`dart tools/validate_bangla.dart`), the version-sync check,
  `flutter analyze`, `flutter test`, then
  `flutter build apk --release --split-per-abi` (plus the universal APK
  built separately — `--split-per-abi` does not rebuild it).
  A failing validator stops the build. A missing validator file fails
  closed. A bad edition can never ship through this gate.
  `android/app/build.gradle` also has a `validateEditions` Gradle task
  hooked to `preReleaseBuild` as a backstop.
- **Screens:** Home, Story (the 11-section learning module), Words,
  Quiz, Profile, plus Current Affairs, Editorial, English, Flashcards,
  Library, Search, Word Detail. Story rendering lives in
  `lib/screens/story_detail_screen.dart` +
  `lib/screens/learning_module_section.dart`; the model in `lib/models.dart`.
- **Design system (2.0):** palette Forest Green `#1E3A2B` (primary/deep),
  Oat `#EEE6D6` (light surfaces), Flamingo Pink `#FF7AB8` (restrained
  accent only — never large pink surfaces or pink body text).
  Tokens + components in `lib/widgets/app_theme.dart`
  (`AppColors`/`AppType`/`AppRadii`/`AppShadows`/`AppMotion`) and the
  hidden centralized shape system (`AppShapes` + `ShapeRole` — one
  token layer for every box/corner/button; no per-screen hardcoding).
  Full spec: `design-system/sarangsho-plus/MASTER.md`, `tokens.json`.
  Light + dark must both be correct; check contrast (≥ 4.5:1 for text).
  **Taste and Hallmark design rules must never be mixed on one screen**
  — pick one visual direction per screen.
- **Story banner images:** the source article's `og:image`, **hotlinked**
  from the publisher's server with attribution + tap-to-open-original.
  Never downloaded, copied or hosted. Typographic hero banner
  (hero number + headline) is the fallback when there is no image.
- **Golden tests:** `app/test/goldens/` holds the master PNGs
  (stage3 screens + story screens). They are binary files; if you clone
  this repo and the golden tests fail with missing masters, that is why
  — the PNGs travel separately. The 4 Home goldens are known to flip
  nondeterministically (a test-harness font-measurement quirk, confined
  to the offline-row tail) — if they flip, check the diff is confined
  to that row before regenerating only those 4. Do not pin the greeting.
- **Language rule:** the app is Bengali-first. UI, navigation, summaries,
  quiz questions and explanations are Bangla. Only English headwords stay
  English. See `app/README.md` for the full language rule.

## 4. The engine (v2, live)

Python standard library only — no third-party packages, no paid APIs.
Entry points: `engine-v2/run_v2_daily.py` (daily orchestrator),
`engine-v2/run_v2.py` (single run), `engine-v2/publish_v2.py`
(15-check gate + publish), `engine-v2/convert_to_app.py` (app format).

**Pipeline (one file per step, see `engine-v2/PLAN.md`):**
collect (RSS → sitemap → section links; robots.txt respected;
Google News RSS is OUT) → prefilter → decide (keep/maybe/reject, rubric
0–3, every keep needs a topic ID + an exact quote) → facts (what/value/
unit/date/status/exact quote; numbers copied exactly, never converted or
rounded; conflicting numbers shown separately, marked "বিতর্কিত", kept
out of quizzes) → check (quote/number/name must appear in the article)
→ Bangla style (cholito) → daily page (max 15 full items + 1 editorial
slot, best-of-day-or-empty, labelled মতামত) → questions (MCQ stem +
ক খ গ ঘ + key + quoted source sentence + why each wrong option fails)
→ study features (SRS 1→3→7→14) → vocabulary (Step 10).

**10 topics only:** BD-GOV, BD-ECO, BD-BANK, BD-NATL, INT-ORG, INT-REL,
ENV, SCI, SPORT, PEOPLE. There is no BD-EDU topic — Rudro removed it.
Do not re-add it.

**Sources (Level 1, see `engine-v2/SOURCES.md`):** 11 of 15 papers wired
(Prothom Alo Bangla/English, bdnews24, Jugantor, TBS, Daily Star,
Financial Express, Daily Tribune, Ittefaq, Bangla Tribune, Jago News 24,
UNB, BSS, New Age — direct RSS/sitemaps + Bing News `site:` discovery).
**Blocked (4):** Bangladesh Pratidin, Kaler Kantho, Samakal, Bonik Barta.
Weekly route-health check runs Sundays ~10:44 Asia/Dhaka
(`engine-v2/tools/check_routes.py`).

**The gate (`publish_v2.py`, 15 checks):** counts (≤15 stories, exactly
20 words / 10 phrases / 5 revision words / 25 MCQs), longest-correct
option ≤10/25, the renovated standard (exactly 2 EN + 2 BN exam Q&A per
story), `image_url` present-or-empty (never null), and — when the
edition declares the learning-module format — the 11-section shape
check. **The checks verify form, not content against sources.**
An edition can pass 15/15 with a wrong exam answer (that happened to
Edition 7). Say so in any run report.

**Auto-publish rules (Rudro's):**
- v2: gate 15/15 → auto-publish, reviewer `auto-15/15 (Rudro's rule
  2026-11-15)`. Below 15/15 or a short draft → stop, report, no publish.
- v1 fallback: allowed only if the v2 run fails before 10:00 Dhaka;
  needs 17/17 + longest-correct ≤10/25, reviewer
  `auto-17/17 (Rudro's rule 2026-11-13)`. A v1 fallback does **not**
  advance the v2 proof count.
- Full daily-run instructions: `engine-v2/CRON_INSTRUCTIONS_V2.md`.
  The cron itself (`sarangsho-plus-daily-engine`, daily 08:00
  Asia/Dhaka) lives outside this repo — do not try to run or move it
  from here.

**Vocabulary (Step 10):** `engine-v2/rules/vocab_bank.json` — 281 words
+ 68 phrases. `engine-v2/rules/enrichment.json` — the same 281 words +
68 phrases with IPA (Free Dictionary API), synonyms/antonyms (Datamuse),
Bangla phonetics (transliterations) and collocations traced to each
word's example sentence. Enrichment is never guessed: a field the
sources do not support stays empty (with the `যাচাই করা যায়নি` marker
where the format requires it), never invented.
**Known shortfall (18 Nov):** only 9 fresh phrases were available
against 10 required, so v2 stopped at convert. Growing the bank by
~10–15 curated entries (candidates: `death toll`, `artificial
intelligence`, `health services`, `press release`, `big tech`) is the
fix — each entry needs a checked Bangla meaning + English explanation.

**Learning-module format (`learning_module.py`, `--learning-modules`
flag on `convert_to_app.py`):** the 11-section model, in order —
`hero`, `news_summary` (source as an explicit object: name + link),
`verified_facts`, `topic_gk`, `institutions`, `extra_knowledge`,
`mcq_practice` (4 MCQs/story, answers + explanations required),
`written_prep`, `vocabulary`, `revision`, `deep_prep`.
`exam_notes` is dropped — its content is split into `institutions` and
`extra_knowledge`. Editions carrying it declare
`renovation_format: "learning-module-v2"`. The 16 renovated editions
(1–16 Nov, 225 stories) were converted to this model on 18 Nov 2026
(tooling + audit trail in `renovation/`). `engine-v2/rules/
gk_knowledge.json` holds the verified topic-GK entries (currently one:
`adp` — ADP vs RADP table, 5 institutions, 4 extra-knowledge terms).
Stories without a verified GK entry carry the `যাচাই করা যায়নি` marker.

**Bugs fixed in this tree (do not reintroduce):**
- TBS sidebar leak (18 Nov): every TBS page ends with a comments
  disclaimer followed by a sidebar of bare headlines; Step 4 mined the
  MJL warehouse headline as a fact in 34 stories. `common.py:
  clean_body_text()` now cuts the body at the line containing
  `while most comments will be posted` (backups: `tbs news of the day`,
  `tbs stories`), once a real paragraph has been seen.
- `publish_v2.py` tracker tests, the `meeting` validator allowlist
  entry (base noun, Bangla সভা), the converter's BN hygiene scan
  excluding `.image_url` paths.

## 5. Data formats

- **Edition JSON** (`data-YYYY-MM-DD.json`): `stories[]` (id, headline,
  category, summary, one_liner, key_facts, sources[], exam_qa, MCQs…),
  `words[]` (20), `phrases[]` (10), `mcqs[]` (25), `revision_words[]` (5).
  Canonical EN editions live in the feed repo; the app bundles copies in
  `app/assets/editions/` plus Bangla overlays (`bn-YYYY-MM-DD.json`).
- **Index (`editions/index.json` in the feed repo; `app/assets/editions/
  index.json` bundled):** one entry per edition + top-level
  `correct_consecutive_editions` (the v2 proof count) + `correct_rule` +
  `renovation_summary`. The v2 run reset to 0 at Edition 11 (17 Nov);
  local index says 1, live index says 0 — see §7, do not resolve this
  yourself.
- **Renovation:** the 16 editions 1–16 Nov carry `renovation_format:
  "learning-module-v2"`, `renovation_date: "2026-11-18"`. Spec:
  `renovation/RENOVATION_SPEC.md`. News facts come ONLY from existing
  story data; GK ONLY from authoritative sources with name + URL recorded;
  unverifiable GK is left blank with the marker, never guessed.

## 6. What is real vs scaffold (read before believing a file)

`phase0-audit-system-b.md` is the audit (18 Nov 2026). Short version:
~⅓ of this repo is the working product (app + engine-v2 + frozen
engine-v1), ~⅓ is honest spec/ledger, ~⅓ is scaffold that claims more
than it does. In particular:

- The **Astro website** (`frontend/`) was never deployed — the Pages
  site returns 404. The Today page is a real renderer; the homepage is
  static marketing.
- The **auto-sync workflows** (`.github/workflows/`) work when the
  validator passes, but whole-archive validation lets one bad edition
  block everything, and `GITHUB_TOKEN` commits never trigger a deploy.
- The **rights registry** (`engine-v2/rights_registry.py`) is sound
  fail-closed code with **0/55 publishers enabled** — and the working
  engine does not use it. Treat it as policy, not an operating control,
  until it is wired in.
- **`database/schema.sql`** has 6 CREATE TABLEs and no runtime applies,
  populates or reads them.
- **`docs/EXAM_TAXONOMY_V1.md`** is a sound spec with zero implementation.
- **PR #17** ("Fix Android CI Flutter/Gradle toolchain mismatch", pins
  Flutter CI 3.35.7): the pin is correct; merge only after a green run.
- **ChatGPT's earlier app copies** in this repo (`app/assets/editions/
  bn-*.json` + `index.json`) are its renovated copies — story text
  differs from the shipped overlays. **Do NOT overwrite them with the
  shipped overlays without Rudro's word.**

## 7. Current state — watch out (18 Nov 2026)

- **App 1.4.0 (build 2015) is live** — GitHub Release v1.4.0 on the
  editions-feed repo, `app/version.json` 2015/1.4.0. The update banner
  shows on Rudro's phone.
- **Edition 12 (18 Nov) published LOCALLY as a v1 fallback** (12 stories,
  17/17, longest-correct 4/25). **Live sync is HELD.** Do not sync it
  until Rudro decides §7's 17 Nov question.
- **The 17 Nov question (OPEN, do not resolve unilaterally):** the LIVE
  index's 17 Nov entry is a 5-story replacement ("Five-study-item
  replacement; official/institutional sources only; v2 engine not run",
  tracker 0). The local tree's 17 Nov entry is the 15-story v2
  Edition 11 (gate 15/15, tracker 1). Someone replaced the live edition
  after its 17 Nov 09:06 publish; who/why is unknown. A backup of the
  live replacement is kept locally (`live-17nov-replacement-backup-
  2026-11-18/`). The next daily run builds on the LOCAL index — if it
  publishes, it will re-assert the local state over the live one.
  Rudro decides: keep the replacement (tracker 0) or restore Edition 11
  (tracker 1).
- **Edition 11's file still carries 86 validator flags** (empty
  word/phrase enrichment fields + duplicate headword `postpone`).
  The enrichment root fix is in for Edition 12 onward. Whether to
  backfill Edition 11 is Rudro's call — open.
- **Edition 11 has NO learning_module** (old v2 format, never converted).
  Edition 12 (v1 fallback) has none either. The 11-section model covers
  1–16 Nov only, in the app bundle.
- **App vs sample mismatch (OPEN, 18 Nov):** Rudro says the app does not
  match his news-description sample — "far more differences between my
  sample and your app's, and many more throughout the app". Known gaps:
  the ADP story (Edition 11) has no learning_module in the app, and
  `topic_gk` has **0 tables** across all 225 converted stories (the
  sample's ADP vs RADP table exists nowhere in the data). The build was
  verified structurally (11 keys, 4 MCQs, sources) but never compared
  against his sample side by side before shipping. Fix path: Rudro
  sends screenshots / names the story; fix each difference starting
  with the ADP story as the golden example. **Do not claim the app
  matches the sample.**
- **Phrase bank is 1 phrase short for Edition 13** (19 Nov 08:00) — see §4.
- **Open decisions awaiting Rudro (do not nag, do not decide):** Bhola
  cyclone hero figure (news "১০ লাখের বেশি" vs record ৩–৫ লাখ);
  Investopedia as a GK source; Edition 11 backfill; keystore backup
  confirmation; 72 Phase 4 uncertain Bengali sentences
  (`phase4-uncertain-sentences.md`, in the local workspace, not this repo).
- **Known v2 gaps:** Step 6 Bangla is still telegraphic; some MCQ stems
  are cloze fragments; some EN fields on Bangla-article stories are
  Bangla text; the GK bank has 1 entry; vocabulary is empty on most
  dry-run stories (Step 10 matches by headline — the edition's 20 words
  are shared). Longest-option-correct is still over target in the
  published 8 Nov (16/25) and 10 Nov (14/25) editions — do not rewrite
  published editions unprompted.
- **Syllabus facts the engine is built on:** BCS prelim 200, written
  900; Bank prelim 100, written 200 — Focus Writing is 65–70 of the
  bank written 200, the engine's biggest direct relevance. (The
  "50th BCS syllabus" PDF in circulation is a LiveMCQ reprint, NOT
  official BPSC. BCS viva is 100 marks, SRO 412-I/2024.)

## 8. Rules for working here

1. **Free-only.** No paid services, no card, no sign-ups that cost money.
2. **Never the keystore.** No `*.keystore`, no `keystore.properties`, no
   passwords, no secrets — not in the repo, not in a PR, not in chat,
   not in a screenshot. If you see one, stop and say so.
3. **Never invent data.** News facts only from story data; GK only from
   authoritative sources with name + URL; numbers copied exactly, never
   rounded, converted or approximated; conflicts shown separately and
   kept out of quizzes. Unverifiable → blank with the marker.
4. **Verify by re-running.** Run the tests yourself and recount any
   number you report from the source files. Never repeat a builder's
   counts on trust. A negative claim ("X is not in the repo") must be
   checked against the files before you state it.
5. **Check live before syncing.** Fetch the live/shared copy first,
   compare field by field, pull live-only fixes into local before
   syncing. Never overwrite a live file you have not read.
6. **The checks verify form, not content.** A green gate is not a
   human review. Say so when an edition auto-publishes.
7. **Bengali-first.** See §3. Do not translate English headwords.
   Do not add English UI where Bangla belongs.
8. **Small, honest commits.** One change per commit, message says what
   and why. Prefer a branch + PR for review; never merge your own PR,
   never force-push `main`. If a change touches the daily engine, say
   so explicitly — it affects the 08:00 run.
9. **Do not touch the editions-feed repo** (`sarangsho-plus-editions`)
   from here, and do not run, move or duplicate the daily cron.
   Trading is paper-only and lives elsewhere; this repo has nothing
   to do with it.
10. **When in doubt, ask Rudro — once, plainly, with the options
    spelled out.** Never refer to a decision by number alone.
    Silence is not approval.

### UI rules (shapes, colours, banners)

These keep the look changeable from one place, so an AI (or a person)
can restyle the app without touching every screen.

1. **Shapes live in one file:** `app/lib/widgets/app_theme.dart`
   (`AppShapes`, `AppShape`, `AppBox`). Screens and widgets must not
   write `BorderRadius.circular(...)`, `Radius.circular(...)` or
   `Color(0x...)`. `app/test/ui_shape_guard_test.dart` fails if they do.
2. **Default is the square box.** Only pass `shape:` to `AppBox`
   (`soft`, `round`, `circle`, `sheet`, ...) when a page truly needs it.
3. **Need a new shape?** Add a value to `AppShape` and `AppShapes`,
   then use it by name. Never inline a one-off radius in a screen.
4. **Colours come from `AppColors`.** Do not add new hues.
5. **Banners:** the default story banner is the generated typographic
   banner. A publisher photo is shown only when the story carries
   `banner_rights: "approved"` (see `Story.bannerImageUrl`). Never
   hotlink or copy a publisher image without that flag.
6. **Do not change** the app ID (`com.sarangsho.plus`), signing
   config, bundled fonts, or published edition data while restyling.
7. Run `flutter analyze` and `flutter test` before you hand work back.

## 9. How to hand this repo to another AI

1. Give it this file + the repo. Nothing else is required.
2. It needs: a GitHub account with access to this private repo
   (Rudro connects it in that AI's settings), Flutter 3.35.7 + JDK 17
   to build the app, Python 3 (standard library only) to run the engine.
3. It must NOT get: the release keystore, `keystore.properties`, or
   any password. Release signing stays with Rudro/CAT.
4. First tasks that are safe to hand over: fix the §7 sample mismatch
   starting with the ADP story; grow the phrase bank (§4); wire
   `--learning-modules` into `run_v2_daily.py` for Edition 13+ (only
   after the proof run); carry the MJL fix + this snapshot's engine
   changes into the daily run's awareness (they are already in the
   local tree — the repo now matches it).
