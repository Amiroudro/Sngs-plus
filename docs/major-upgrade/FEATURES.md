# Feature specifications

This document defines the first non-AI implementation of each planned feature. It deliberately reuses existing application models and screens where possible.

## 02. Three-level summaries

### Reuse

The existing Story model already has a one-line summary, summary/detail fields, key facts, explanatory fields and a multi-section `learningModule`. The learning module includes exam-oriented material such as topic knowledge, exam notes, institutions, extra knowledge, MCQ practice, written preparation, vocabulary, revision and deep preparation.

Do not duplicate those fields or rename them in a breaking migration.

### Reader levels

| Level | Data source | Purpose |
|---|---|---|
| Quick | Existing `one_liner` | The essential development in one or two sentences |
| Comprehensive | Existing `summary`, `what_happened`, key facts and `why_it_matters` | What happened, the evidence and immediate context |
| Deep analysis | New optional `deep_analysis` object | Background, chronology, verified evidence, implications, competing explanations and unresolved questions |

The deep-analysis object is editorial content, not a longer model-generated paraphrase. It is required only for selected high-value stories.

### Proposed object

```json
{
  "deep_analysis": {
    "background": "...",
    "chronology": [],
    "verified_facts": [],
    "implications": [],
    "competing_explanations": [],
    "unresolved_questions": [],
    "source_refs": [],
    "review_status": "needs_review"
  }
}
```

Each fact and interpretation must be distinguishable. A source reference supports the claim; it does not automatically prove the interpretation.

### Acceptance

- Old editions without `deep_analysis` render normally.
- Quick and comprehensive levels are available for every story that already has the corresponding fields.
- Deep analysis is shown only when its review status is approved.
- Every factual claim has at least one source reference.
- Editorial interpretation is labelled separately from verified facts.

## 03. Story Timeline

### Reuse

The build-time schema already has `events` and `event_articles`. The app's Current Affairs screen already groups stories by date, but that is not an event timeline.

### Required behaviour

A reader opens an event and sees developments in event-date order, with publication time shown separately. Each timeline item links to one or more articles and their sources.

### Identity rules

- An article ID must remain stable across daily editions. Use a normalized canonical URL registry, not run-local IDs such as `a001`.
- An event ID must be permanent and registry-backed. Similarity scores may suggest an event match; they must not silently merge two events.
- Event merges and splits require an auditable editorial correction.
- Store both `event_date` and `reported_at`; they are not interchangeable.

### Acceptance

- A story can be followed across multiple edition dates.
- Corrections and updates remain visible.
- Duplicate articles do not create duplicate timeline events.
- Ambiguous clustering is sent to review rather than silently merged.

## 04. Multiple Newspaper Perspectives

### Reuse

Use the event-to-article relationships and fact-evidence records. Do not copy full article bodies into a comparison record.

### Comparison layout

For one event, show:
- Publication, headline, publication time and original link.
- A short Sarangsho-authored summary of each report.
- Facts corroborated by multiple permitted sources.
- Differences in figures, chronology or attribution.
- Material information reported by only one source.
- What remains unverified.

Do not label a publication biased, partisan or unreliable from a single story. Any source-level assessment needs a published methodology and evidence.

### Rights requirements

A public URL is not a republication licence. Each publisher must have an explicit permission record for the relevant activity. Until then, show only information that is independently permitted, such as limited bibliographic metadata and links. Do not retain RSS descriptions as article excerpts when the grant does not allow it.

### Acceptance

- Every comparison item links to its original source.
- Conflicting figures remain separate and are not averaged.
- The system distinguishes corroboration from repetition.
- No article text is republished without the necessary rights.

## 06. Daily BCS & Bank Challenge

### Reuse

The app already has edition MCQs, quiz history, mistakes and vocabulary revision. Engine v2 has a question-generation sidecar and the database schema has questions and options.

### Question record

```json
{
  "question_uid": "Q-...",
  "edition_date": "2026-11-18",
  "exam_tracks": ["BCS", "BANK"],
  "subject": "Bangladesh Affairs",
  "topic": "Constitution",
  "difficulty": "medium",
  "question_type": "single_best_answer",
  "stem_en": "...",
  "stem_bn": "...",
  "options": [],
  "correct_option_uid": "...",
  "explanation_en": "...",
  "explanation_bn": "...",
  "source_refs": [],
  "review_status": "needs_review",
  "valid_until": null
}
```

A question is not a genuine past question merely because it resembles one. Past-question labels require a verifiable exam, year and source.

### Modes

- Daily challenge from approved edition facts.
- Subject/topic practice.
- Mixed timed mock test.
- Revision of previously incorrect and due questions.

Selection is deterministic and records the chosen question IDs, so a challenge can be reproduced and reviewed.

### Acceptance

- Every answer key is source-supported and reviewed.
- Questions have a clear exam track, subject and topic.
- Duplicate questions are detected.
- Timed tests, scoring and explanations work offline.
- Current-affairs questions expire or are marked time-sensitive when appropriate.

## 07. Knowledge Graph

### First version

Use relational tables and JSON exports, not a graph database.

Entity types include people, institutions, countries, laws, treaties, policies, companies and concepts. Relationship types must come from a controlled vocabulary such as `member_of`, `governs`, `established_by`, `signed`, `reports_to` and `related_to`.

Every relationship has evidence, validity dates and a review status.

### UI

Render a focused neighbourhood around one selected entity. Use Flutter's custom painting and pan/zoom interaction. Do not load or draw the whole graph at once.

### Acceptance

- No relationship points to a missing entity.
- Time-sensitive relationships have validity dates.
- Disputed relationships are labelled.
- A graph node opens the underlying story, source or profile.

## 08. Personal Learning Analytics

### Current limitation

AppState currently stores small preferences and learning state in SharedPreferences. It does not retain a complete per-question attempt history, so accurate topic-level performance cannot yet be calculated.

### Local event model

Store question attempts, reading events and vocabulary reviews on the device. A question attempt records the question ID, selected answer, correctness, timestamp, response time, exam track and topic.

No personal learning history is uploaded to the public editions repository.

### Metrics

- Accuracy by subject and topic.
- Weekly reading and practice activity.
- Repeatedly missed concepts.
- Vocabulary review consistency.
- Retention on repeated attempts.
- Due revision backlog.

Use transparent calculations. Do not present a small sample as a reliable mastery score.

### Acceptance

- An attempt is recorded once.
- Percentages use the actual number of attempts.
- Data survives restarts and app upgrades.
- Users can export and restore their learning data.
- Clearing app data is not silently described as a backup.

## 09. Ask Sarangsho

### First release is search, not generative AI

Search approved stories, event timelines, facts, entities, vocabulary, questions and statistical indicators. Return ranked records with dates and source links.

### Retrieval pipeline

1. Normalize Bangla and English text.
2. Normalize Bengali/Latin digits and zero-width characters.
3. Expand known aliases.
4. Match exact phrases and terms.
5. Rank results with a deterministic relevance score such as BM25.
6. Expand related entities and events.
7. Return source-linked results.

Start with a generated inverted index and pure Dart ranking. Benchmark before adding SQLite FTS5 or another native dependency.

Bangla normalization must be tested with real inflections and compound terms. English Porter stemming is not a Bangla tokenizer.

### Acceptance

- Search works offline over downloaded packages.
- Every answer-like result links to the record that supports it.
- Search does not invent an answer when no relevant source exists.
- Bangla and English queries both work.

## 10. World Affairs Explorer

Start with a small, well-sourced collection relevant to Bangladesh, then expand. Do not begin by trying to maintain every country and officeholder at once.

Initial content:
- Country profiles and capitals.
- International organizations.
- Treaties and agreements.
- Bangladesh's membership and diplomatic relationships.
- Major international events.

Every time-sensitive field has an `as_of` date, source URL and verification status. Use official/open datasets with licence attribution. Do not call an external API every time a profile opens.

### Acceptance

- Current officeholders have an as-of date and source.
- Historical officeholders are not overwritten.
- Country and organization aliases support bilingual search.
- Offline profiles remain usable.

## 11. Data & Fact Explorer

### Observation contract

Each observation records indicator ID, country, value, unit, frequency, reference period, publication date, source, retrieval date and status.

Status distinguishes actual, preliminary, estimate, projection and revised values.

### Initial Bangladesh indicators

Inflation, GDP growth, remittance, foreign-exchange reserves, export earnings, imports, population and unemployment. Confirm definitions and official source series before adding a chart.

### Acceptance

- Units and reference periods are always visible.
- Estimates are not presented as actual values.
- Revisions retain a traceable history.
- Different definitions are never silently combined.
- Each chart can open the original source.

