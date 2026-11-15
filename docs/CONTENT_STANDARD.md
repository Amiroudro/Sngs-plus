# Sarangsho Plus content standard

**Purpose:** Turn accessible journalism into reliable, bilingual knowledge for readers and competitive-exam candidates. This is the editorial contract for every generated article, event brief, fact, vocabulary item and question.

## 1. Non-negotiable rules

1. Do not invent a headline, article, quotation, figure, date, source, author, official statement or corroborating outlet.
2. Preserve the original publisher, headline, canonical URL, language and publication/update timestamps.
3. Write original summaries that are materially shorter than the source. Do not reproduce full articles or defeat paywalls, logins, robots rules or technical access controls.
4. Distinguish **reported fact**, **official claim**, **allegation**, **analysis**, **background context** and **AI explanation**.
5. Attach important factual claims to the source article or an authoritative primary source. Several outlets repeating one wire report do not automatically count as independent confirmation.
6. Keep uncertainty visible. If reliable sources disagree, describe the disagreement and do not silently select one version.
7. English and Bangla editions must carry the same underlying facts, names, dates, quantities, attribution and uncertainty. Bangla should be natural, not word-for-word translation.
8. Correct errors with a traceable update. Do not silently overwrite a published fact or erase the earlier version.

## 2. Article-level record

Every collected article should retain:

- Stable internal ID and canonical URL
- Publisher/source ID, publisher name and original headline
- Author only when supplied and relevant; never use author names as filler
- Published time, updated time, fetched time and timezone where known
- Original language and accessible excerpt/content status
- Content hash and duplicate/canonicalisation result
- Topic/category, geography and people/institutions/entities
- Collection status, extraction method and any access limitation

A feed item containing only metadata or an excerpt must be labelled as such. An excerpt is not a full article.

## 3. Event clustering

Group articles only when they describe the same underlying event or continuing development. Preserve every article-to-event link. Store each publisher's contribution separately so the system can show which outlets independently report a fact.

Event status should distinguish at least: developing, updated, settled and corrected. A new article should not automatically overwrite the event's earlier chronology.

## 4. Exam relevance score

Score each article from **0 to 10**. Record the score, a short reason and the reviewer/model that assigned it.

| Score | Treatment |
|---|---|
| 8–10 | Full balanced bilingual note, key facts, context, vocabulary, exam questions and revision points |
| 5–7 | Concise bilingual note, key facts, relevant context and a small practice set |
| 2–4 | Short archive note with the central fact and source link |
| 0–1 | Retain metadata for search/audit; no expanded study note |

The score measures durable public significance and plausible syllabus relevance, not popularity or political preference. Consider public impact, national/international significance, policy or economic consequences, novelty, institutional importance and exam usefulness. Use an urgent editorial override for immediate public-safety information and record the reason.

## 5. Required structure for a high-relevance story

### Source and status
- Original headline, publisher, publication/update time and source link
- Topic, location, event status and exam relevance score
- Clear label for developing, disputed, corrected or incomplete information

### Bangla explanation
Aim for **80–150 words** for an important article. Start with the actual event or decision. State who did what, where and when, the confirmed details, and any material uncertainty. Do not begin with empty phrases such as “প্রতিবেদনে বলা হয়েছে”, “খবরে জানা যায়” or “সূত্র অনুযায়ী”. Retain attribution when the distinction between a claim and an established fact matters.

### English explanation
Aim for **40–80 words** for an important article. Explain the same event and facts in clear English, without adding a detail absent from the evidence.

### Key facts
Use compact, individually traceable entries for:
- People, offices, institutions and organisations
- Dates, locations, decisions, laws and agreements
- Figures with units, period, geographic scope and source
- Sequence of events and confirmed outcomes

Never detach a number from its unit or reference period. Preserve the difference between a proposed, approved, enacted, effective and implemented measure.

### Why it matters
Explain the actual public, economic, constitutional, social, scientific or diplomatic consequence. Avoid generic claims that everything is “important for BCS”.

### Background and connections
Add only context that helps explain the story. Link it where relevant to the Constitution, public administration, economics, banking, geography, history, science, international organisations or Bangladesh's foreign relations. Mark stable background separately from new reporting.

### Vocabulary
For high-relevance English-language items, select **5–10 useful words or phrases**, not random difficult words. Each entry should contain:
- Word/phrase and Bangla pronunciation
- Part of speech
- Contextual Bangla meaning and a concise English definition
- Useful synonyms and antonyms where genuine
- A natural example sentence
- Source article or topic link

For medium-relevance stories, use fewer items. Do not force vocabulary into stories where it adds no learning value. Deduplicate against the cumulative vocabulary bank and retain multiple meanings when context changes.

### Exam practice
Write questions only from supported facts or clearly labelled stable background:
- MCQs with one defensible correct answer, plausible distractors and a brief explanation
- Short factual questions for names, dates, institutions, places, figures and definitions
- Analytical prompts only when the article supports analysis

Keep an answer key. Cite the fact or source that supports each answer. Never present speculative predictions as likely exam questions.

### Five-minute revision
End important notes with a compact recall sheet: central event, essential facts, one or two concepts, and the exam connection. It must be possible to revise without rereading the whole note.

## 6. Verification protocol

Prioritise primary sources when they are available and relevant: gazettes, laws, official notices, ministry and regulator releases, Bangladesh Bank, Bangladesh Bureau of Statistics, Election Commission, Parliament, courts, public datasets, treaty texts and international organisations' original publications.

For each material number or official decision:
1. Capture the value or exact decision and its unit/scope.
2. Record the source and publication/reference date.
3. Compare with the original primary document when available.
4. Check whether the number is preliminary, revised, projected, nominal, real, fiscal-year or calendar-year data.
5. Flag contradictions, missing methods, stale data or unsupported claims.

A source count is not a quality score. Do not claim independent confirmation unless the reporting is genuinely independent.

## 7. Duplicate and developing-story handling

- Canonicalise URLs and deduplicate identical articles without deleting source records.
- Detect near-duplicate headlines and copied wire stories; retain their provenance.
- Cluster updates into a continuing event while preserving a dated chronology.
- Surface corrections and material changes.
- Do not present an old article as today's news just because it remains in the database.

## 8. Editorial language

Use direct, specific prose. Put the event first. Avoid filler, repeated facts, sensational adjectives, irrelevant columnist/editor names and headline-only explanations. Never pad a note to reach a word count. A shorter accurate note is better than a longer speculative one.

## 9. Review and publication states

Use explicit states such as:
- **Collected:** metadata captured; not yet verified
- **Processed:** summary and facts drafted
- **Needs review:** disputed, sensitive, high-impact or uncertain
- **Verified:** key facts checked against suitable sources
- **Published:** passed the required review
- **Corrected/withdrawn:** a visible correction or removal record exists

High-impact, sensitive, fast-changing and disputed stories require human review before prominent publication. Automation must not mark its own unsupported output as verified.

## 10. Current implementation boundary

The repository is a foundation build. A source listed in a planning document is not an enabled feed. An article is not collected until a real source item has been fetched and recorded. No story, summary, vocabulary item or question should be displayed as current until the underlying record and source status exist.
