# Editorial scoring contract: triage vs exam relevance

The Engine v2 score and the Sarangsho Plus score measure different things.
They must remain separate fields. Do not multiply or relabel the engine's
0–3 value as a 0–10 score.

## Two independent scores

### Engine triage score (0–3)

This is an editorial processing decision:

- 0: reject from expanded processing under the current rubric
- 1: maybe / low-confidence or support-only match
- 2: keep
- 3: high-significance keep

It answers: **Should the pipeline spend additional processing effort on this item?**

### App exam relevance (0–10)

This is a reader-facing study value score. It answers: **How useful is this item
for durable general knowledge and the user's competitive-exam tracks?**

Assess separately using:
- Bangladesh/public-affairs syllabus relevance
- BCS and government recruitment relevance
- Bangladesh Bank and banking/economics relevance
- institutional, constitutional, legal and policy significance
- international organisations, diplomacy and global affairs
- science, technology, climate, agriculture, health and education relevance
- durable factual value and public impact

Record a short reason and the relevant exam track(s). A story can be
editorially significant but have modest exam value, or be a small event with
high value for a particular exam topic.

## Reader-facing treatment

| App score | Treatment |
|---|---|
| 8–10 | Detailed balanced Bangla and English explanation, key facts, context, vocabulary and exam practice |
| 5–7 | Concise bilingual explanation, essential facts and a small practice set |
| 2–4 | Short factual note, central details and source links |
| 0–1 | Retain searchable metadata and archive record; no expanded study note |

## Retention rule

A triage decision of 0 or 1 must not erase an accessible article from the
source archive. Retain its metadata, source URL, publication time, language,
collection status and triage reason. The app can keep it out of the main
briefing while preserving search and audit access.

## Human review

Urgent public-safety stories, disputed claims, sensitive allegations and
stories with conflicting figures require a review flag regardless of score.
The score never substitutes for fact checking or editorial judgement.

## Implementation requirement

Persist at least:
- `engine_decision` and `engine_score_0_3`
- `exam_relevance_score_0_10` and `exam_relevance_reason`
- `exam_tracks`
- `retention_status` (`full_note`, `short_note`, `archive_only`)
- `review_required` and `review_reason`

This contract is a specification. The current Engine v2 code has not yet
implemented the separate 0–10 app score.
