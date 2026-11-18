# Sarangsho Plus 2.0: architecture overview

**Status:** proposed implementation blueprint, not yet implemented  
**Repository audit date:** 18 November 2026  
**Scope:** the nine planned features, implemented without a required AI service or paid backend

## Executive decision

Upgrade the existing product in place. Keep the Flutter Android application, Astro website, Python Engine v2, and public `sarangsho-plus-editions` repository. Add a shared, versioned intelligence-data layer that both clients can consume.

Do not create nine independent services or databases. Do not replace the current edition format. Do not introduce a cloud database just to support offline reading and study.

The target flow is:

```text
Private Sngs-plus repository
  Engine v2 + editorial rules + schemas + tests
              |
              v
Build-time structured processing
  SQLite import/export where useful
  deterministic validation and editorial approval
              |
              v
Public sarangsho-plus-editions repository
  daily editions + versioned intelligence packages
              |
       GitHub Pages / static files
              |
       +------+------+
       |             |
       v             v
Flutter app       Astro website
local cache       static rendering
local progress    no personal learner data
```

## What already exists

This plan is based on the actual repository, not a blank-slate design.

| Existing component | Current responsibility | Upgrade implication |
|---|---|---|
| `app/lib/models.dart` | Edition, Story, vocabulary, MCQ and learning-module models | Extend these models compatibly |
| `app/lib/data/loader.dart` | Loads bundled edition JSON and Bangla overlays | Extend the existing loader |
| `app/lib/services/edition_download_service.dart` | Downloads and caches edition files | Reuse its HTTP, validation and offline-fallback behaviour |
| `app/lib/state/app_state.dart` | Settings, reading state, bookmarks, quiz history, mistakes and revision state in SharedPreferences | Keep small preferences here; add durable attempt-level storage only when needed |
| `app/lib/screens/search_screen.dart` | Basic substring search over currently loaded content | Replace ranking and coverage, not the whole screen |
| `app/lib/screens/current_affairs_screen.dart` | Date-grouped current-affairs browsing | Add event-level timelines alongside date browsing |
| `app/lib/screens/quiz_screen.dart` | Edition MCQs, vocabulary practice and mistake review | Extend the current quiz experience |
| `Story.learningModule` | Existing multi-section learning material | Reuse it; do not create a parallel learning-module format |
| `engine-v2/run_v2.py` | Existing news-processing pipeline | Add a post-validation exporter, not a replacement pipeline |
| `engine-v2/publish_v2.py` | Existing publish gate | Intelligence packages must pass an equivalent gate |
| `database/schema.sql` and migrations 001–003 | Build-time article, event, fact, evidence, question, vocabulary, rights and translation structures | Useful foundation, but not yet an operational importer |
| `backend/app/main.py` | Read-only edition API | Not required for the static/offline feature architecture |
| Public editions repository | Published edition JSON and archive validation | Remains the distribution source |

### Important current limitations

- The Android app currently has no local SQLite dependency. Its personal state is stored in SharedPreferences.
- The private SQL schema and migrations exist, but Engine v2 does not yet import every run into those tables.
- Current search is basic text matching, not a cross-edition retrieval engine.
- The current timeline is grouped by publication date, not by persistent event identity.
- There is no implemented entity graph, world-affairs dataset or statistical indicator explorer.
- The publisher-rights registry currently has 55 candidate records disabled. Collection must remain blocked until each required permission scope is explicitly approved.
- The app and website must not treat structural translation checks as human editorial approval.

## Design principles

1. **Offline first.** A downloaded edition or intelligence package remains usable without a network connection.
2. **Static distribution first.** Publish versioned JSON through the existing public repository and GitHub Pages.
3. **One content contract.** Android and the website consume the same approved package data.
4. **Source traceability.** Every material fact, question, statistic, entity relationship and perspective has a source reference.
5. **Human approval for editorial claims.** Algorithms can detect candidates and validate structure; they cannot certify factual accuracy.
6. **Rights-aware processing.** Metadata, page metadata, article-body processing and republication are separate permission scopes.
7. **Backward compatibility.** Existing editions remain readable when optional new fields are absent.
8. **No AI dependency in the first release.** Retrieval, ranking, graph rendering, question selection and analytics use deterministic code.
9. **No unnecessary infrastructure.** No paid model API, mandatory user account, cloud learner database or dedicated server.

## The nine features

| Feature | First implementation |
|---|---|
| Three-level summaries | Quick, comprehensive and editor-reviewed deep analysis using existing Story fields plus one optional structured object |
| Story Timeline | Persistent event IDs linked to articles across editions |
| Multiple Newspaper Perspectives | Rights-cleared metadata and original comparison notes grouped by event |
| Daily BCS & Bank Challenge | Curated question bank, deterministic selection, explanations and source links |
| Knowledge Graph | Relational entities and relationships exported as small JSON neighbourhoods |
| Personal Learning Analytics | Private, on-device event history and deterministic calculations |
| Ask Sarangsho | Local bilingual search and retrieval, not a pretend chatbot |
| World Affairs Explorer | Curated, dated country, institution, treaty and event datasets |
| Data & Fact Explorer | Source-attributed indicator series with units, periods and estimate status |

## Delivery order

1. Stabilize existing CI, data synchronization, rights enforcement and publish contracts.
2. Define stable IDs and versioned intelligence schemas.
3. Implement event identity, timelines, summaries and source perspectives.
4. Expand the question bank and daily challenge.
5. Add local attempt-level learning analytics and backup/restore.
6. Add entity relationships and offline search.
7. Add curated world and statistical datasets.
8. Integrate, measure offline behaviour and release progressively.

See [FEATURES.md](FEATURES.md), [DATA_CONTRACTS.md](DATA_CONTRACTS.md), [PACKAGE_DELIVERY.md](PACKAGE_DELIVERY.md), [ROADMAP_AND_TESTS.md](ROADMAP_AND_TESTS.md) and [FREE_OPERATIONS.md](FREE_OPERATIONS.md).

## Release rule

A feature is not complete when its screen renders. It is complete only when its data contract, source traceability, offline behaviour, compatibility, tests and rollback path are verified.
