# Corrected learning_module model — v2 (PROPOSAL, awaiting Rudro's confirmation)

Date: 2026-11-18. Status: proposed, NOT implemented. Workstream 2 is HELD until Rudro confirms this model.

## What was wrong with the v1 model

The renovation spec (`RENOVATION_SPEC.md`, 17 Nov) reshaped ChatGPT's ADP sample.
The sample has its OWN sections for institutions and extra knowledge. The spec folded
them away: the institutions section (Planning Commission, NEC, ECNEC, IMED, DPP)
was folded into `exam_notes`, and the extra-knowledge list (Public Investment, PIM,
Feasibility Study, …) was folded into `topic_gk` / `exam_notes`. The renovated
stories therefore do not carry the sample's sections. The v2 model below restores
the sample's demonstrated article flow as its own sections.

Note: the ADP story itself IS in Edition 11 (17 Nov) as CA03
("ADP implementation hits record low of 6.53% in July-October"; a second ADP story
is CA10). Edition 11 carries NO learning_module at all (old v2 format), so the
renovation never applied the format to the ADP story — but the story is in an
edition. That makes Edition 11 CA03 the golden test case: the engine-generated
module for it can be compared section-by-section against ChatGPT's sample.

## The model — 11 sections, in the sample's article order

Per story, `learning_module` carries these keys, in this order. Per edition,
`renovation_format: "learning-module-v2"` and `renovation_date: "<generation date>"`.

### 1. `hero` — the figure, big, with a caption
```json
{"figure": "৬.৫৩%", "label": "ADP implementation rate, July–October"}
```
The single most exam-askable number. Same shape as v1.

### 2. `news_summary` — short Bangla summary + source line
```json
{"text": "…2–4 sentences, lead with the key number, NOT a headline restatement…",
 "source": {"publication": "The Business Standard", "date": "2026-11-15",
            "url": "https://www.tbsnews.net/…"}} 
```
Bangla-first cholito, Bangla digits. The source is an explicit object (not buried
in the text) so the app can render it as a link line. NO মূল সারাংশ section
(Rudro's cut stands).

### 3. `verified_facts` — the facts table (proposal's additional part)
```json
[{"label": "ব্যয়", "value": "২০,১৬০ কোটি টাকা", "date": "১৫ নভেম্বর ২০২৬",
  "source": "TBS"}]
```
Every fact from the story's own data only (`summary` / `exam_facts` / `key_facts` /
`figures` / `sources`). Never a news fact that is not in the story data.

### 4. `topic_gk` — the topic lesson (with tables and differences)
```json
{"intro": "ADP কী…",
 "tables": [{"title": "ADP at a glance", "rows": [{"label": "…", "value": "…"}]}],
 "distinctions": [{"a": "ADP", "b": "RADP",
                   "points": ["…", "…"]}],
 "sources": [{"name": "Banglapedia — …", "url": "https://…"}]}
```
What the thing is, a facts table, key distinctions (e.g. ADP vs RADP). Grounded
ONLY in authoritative sources (Banglapedia, official govt sites, Bangladesh Bank,
BBS, UN bodies, or the source newspaper's own explainer). Every GK block carries
its source name + URL.

### 5. `institutions` — its OWN section (was folded into `exam_notes` in v1)
```json
[{"name": "Planning Commission", "full_name": "…",
  "role": "…one line…", "source": "plancomm.gov.bd"},
 {"name": "NEC", "full_name": "National Economic Council", "role": "…"},
 {"name": "ECNEC", "role": "…"},
 {"name": "IMED", "full_name": "Implementation Monitoring and Evaluation Division",
  "role": "…"},
 {"name": "DPP", "full_name": "Development Project Proposal/Proforma", "role": "…"}]
```
One entry per institution, name + role in one line, source where the role is
stated. Same verified-sources rule as `topic_gk`.

### 6. `extra_knowledge` — its OWN section (was folded into `topic_gk`/`exam_notes` in v1)
```json
[{"term": "Public Investment", "meaning": "…one line…", "source": "…"},
 {"term": "PIM", "full_name": "Public Investment Management", "meaning": "…"},
 {"term": "Feasibility Study", "meaning": "…"}]
```
Related concepts the reader needs, term + one-line meaning + source.

### 7. `mcq_practice` — 4 MCQs, answers + explanations REQUIRED
```json
[{"question": "…", "options": ["…", "…", "…", "…"],
  "correct": 0, "explanation": "…one line…"}]
```
The sample's MCQ block is interactive and hides answers ("submit and see
results"). The engine MUST still carry `correct` + `explanation` per question —
the app reveals them on tap. Correct letters balanced across the 4 (no letter
more than twice). No "সবগুলো"/"কোনোটিই নয়" options, no negative stems.

### 8. `written_prep` — (proposal's additional part)
```json
{"short": {"question": "…", "outline": ["…", "…"]},
 "analytical": {"question": "…", "outline": ["…", "…", "…"]}}
```
1 short question + 1 analytical question, each with a model-answer outline
(2–4 bullets, not an essay).

### 9. `vocabulary` — (proposal's additional part)
```json
[{"word": "…", "meaning_bn": "…", "example": "…(from the story where possible)…",
  "synonyms": ["…"], "antonyms": ["…"]}]
```
5 English words per story. Words must appear in the story or be standard topic
vocabulary. Prefer the edition's existing word list where a word belongs to this
story (match by the word's `Article headline`).

### 10. `revision` — (proposal's additional part)
```json
{"flashcards": [{"q": "…", "a": "…"}],
 "next_revision": ["…?", "…?"]}
```
3–5 flashcards from the story's verified facts + GK, plus 2 "next revision"
questions.

### 11. `deep_prep` — the topic list
```json
["…", "…", "…", "…"]
```
4–6 related topics for separate lessons (titles only, no content).

## What happened to `exam_notes`?

DROPPED as a separate key in v2 — proposed. In the sample's flow there is no
separate exam-notes section: its content now lives in its proper sections
(`institutions`, `extra_knowledge`, `topic_gk`). The 16 renovated editions keep
their v1 `exam_notes` (backward-compatible; the app renders whatever keys a file
carries). If Rudro prefers, `exam_notes` can stay as an OPTIONAL overflow key for
exam-focused definitions not covered elsewhere — confirm below.

## Rules that stand (unchanged from the spec)

- News facts and GK facts in SEPARATE sections with SEPARATE source labels.
- GK only from verified sources with name + URL; unverifiable GK gets the explicit
  marker `"যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"` — per section, never guessed.
  (In v1 the marker covered `topic_gk`/`exam_notes` as a whole; in v2 it applies
  per section: `topic_gk`, `institutions`, or `extra_knowledge` individually.)
- Bangla-first cholito, Bangla digits in Bangla text, English proper nouns/acronyms
  in brackets on first mention.
- Existing edition MCQs stay untouched in the file; `mcq_practice` is separate.
- Keep every existing story field byte-identical; ADD `learning_module` only.

## Engine consequences (for workstream 2, after confirmation)

- Deterministic from existing pipeline outputs: `hero`, `news_summary`,
  `verified_facts` (Step 4/5 fact list), `mcq_practice` (Step 8), `written_prep`
  (Step 8 analytical/short), `vocabulary` (Step 10), `revision` (Step 9 SRS),
  `deep_prep` (story topics).
- `topic_gk`, `institutions`, `extra_knowledge` need verified content: from a new
  curated rules knowledge file with sourced entries, or the per-section marker.
  The engine must never invent institution facts.
- Gate check 15 must validate the v2 shape (all 11 keys present, `mcq_practice`
  4/story with answers, no empty-string GK without the marker) AND keep the
  renovated standard (exactly 2 EN + 2 BN exam Q&A per story).
- Acceptance test: generate the module for Edition 11 CA03 (the ADP story) and
  compare it section-by-section against ChatGPT's ADP sample.

## Open questions for Rudro

1. Confirm the 11-section model above (hero, news_summary, verified_facts,
   topic_gk, institutions, extra_knowledge, mcq_practice, written_prep,
   vocabulary, revision, deep_prep).
2. `exam_notes`: drop it as proposed, or keep it as an optional overflow key?
3. `news_summary.source` as an explicit object (shown above) — or keep the
   source line as plain text inside the summary?
