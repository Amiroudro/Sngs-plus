# Implementation roadmap and release gates

The order below follows dependencies in the current repositories. Each phase must be independently testable and reversible.

## Phase 0 — Stabilize the existing product

**Work**
- Fix the edition index contract and scheduled synchronization.
- Keep the source archive validator and Android data validator aligned.
- Enforce robots fail-closed and publisher rights at every collection stage.
- Ensure generated Bangla starts as `needs_review`; only explicit human approval may publish it.
- Reconcile stale engine integration documentation.
- Ensure Android, API and website builds pass.

**Exit criteria**
- Existing editions load from bundled assets and remote download.
- The canonical edition index has the same schema for both app and archive.
- No unapproved publisher route is fetched.
- No robots-fetch failure silently permits collection.
- No structural translation check is treated as human approval.
- CI passes on a clean checkout.

## Phase 1 — Shared data contract and importer/exporter

**Work**
- Review the existing SQL schema and migrations.
- Implement deterministic import from approved Engine v2 run outputs into build-time SQLite.
- Add stable article/event/entity/question identifiers.
- Add migration 004 for entities, aliases, relationships, perspectives and deep analysis only after reviewing current columns.
- Export schema-versioned JSON packages.
- Add referential-integrity and source-provenance checks.

**Exit criteria**
- A sample run can be imported twice without duplicate records.
- Stable IDs survive a second run and a changed headline.
- Exported package validates against JSON schema.
- No package contains a fact or relationship without source references.

## Phase 2 — News intelligence

**Features**
- Three-level summaries.
- Persistent story timeline.
- Multiple newspaper perspectives.

**Exit criteria**
- A multi-day event has one persistent event ID.
- Event matching is reviewable and ambiguous matches are not auto-merged.
- Perspective records contain original Sarangsho-authored notes and source links, not copied article text.
- Deep analysis separates verified facts from interpretation.
- Old editions without new fields still render.

## Phase 3 — Examination intelligence

**Features**
- Daily BCS and Bank challenge.
- Subject/topic question bank.
- Mixed mock test and revision challenge.

**Exit criteria**
- Every question has a stable ID, exam track, topic, explanation and source.
- Answer keys pass editorial review.
- Past-question provenance is verified before applying that label.
- Test selection is deterministic and reproducible.
- Offline attempt and score recording works.

## Phase 4 — Personal learning analytics

**Work**
- Add on-device attempt-level event storage.
- Migrate existing small SharedPreferences state without data loss.
- Add export/restore.

**Exit criteria**
- Existing bookmarks, reading state, mistakes and SRS data survive migration.
- Question attempts are counted once.
- Topic accuracy and time ranges are calculated from actual records.
- No personal progress is published to the public repository.
- Export/restore round-trip test passes.

## Phase 5 — Knowledge discovery

**Features**
- Knowledge Graph.
- Ask Sarangsho offline retrieval.

**Exit criteria**
- Every graph edge has two valid entity IDs and evidence.
- Graph rendering is limited to a focused neighbourhood.
- Search indexes include Bangla and English.
- Search returns source-linked records and has a no-result state.
- Search works without network access.

## Phase 6 — World and statistical data

**Features**
- World Affairs Explorer.
- Data & Fact Explorer.

**Exit criteria**
- Time-sensitive records have `as_of` dates.
- Indicator definitions, units, frequency and reference period are visible.
- Actual, preliminary, estimate and projection values are distinguished.
- Every indicator series has an official or appropriately licensed source.
- Charts work offline after package download.

## Phase 7 — Unified release

- Integrate Android and Astro website.
- Test low-bandwidth and offline use.
- Verify older app versions ignore optional fields safely.
- Test corrupt manifest, bad checksum, interrupted download and rollback.
- Run Android release build and install it on a real device.
- Publish only after the full release gate passes.

## Required test matrix

| Area | Minimum checks |
|---|---|
| Edition compatibility | All historical editions parse; optional fields absent; unknown fields ignored |
| Importer | Idempotency, stable IDs, duplicate URL and event merge/split |
| Rights | Disabled, expired, metadata-only, page-metadata and body licences |
| Robots | Allowed, disallowed, malformed URL, timeout and server error |
| Timelines | Event date vs publication time, corrections, duplicate articles |
| Perspectives | Source attribution, disagreement preservation, no copied body text |
| Questions | Answer key, source reference, difficulty, exam track, expiry |
| Analytics | Exactly-once attempts, percentages, migration, export/restore |
| Graph | Missing node, duplicate alias, cycle, invalid edge, expired relation |
| Search | Bangla/English, aliases, digit normalization, zero-width characters, ranking |
| World data | As-of date, officeholder changes, source provenance |
| Statistics | Units, period, revisions, estimates, projections, missing values |
| Delivery | Checksum, interrupted download, invalid JSON, atomic promotion, rollback |
| UI | Light/dark, small/large, 200% text, Bangla fonts, offline and loading states |

## Branch and release discipline

- Feature work happens on short-lived branches.
- Do not push directly to `main`.
- Do not overwrite public edition history to make tests pass.
- Do not disable a failing validator without replacing it with a stronger check.
- Keep a known-good APK and data manifest for rollback.
- A green build is necessary, not sufficient: editorial and rights approvals are separate gates.
