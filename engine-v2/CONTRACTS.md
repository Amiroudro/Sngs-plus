# Engine v2 — Data Contracts (shared by all steps)

All JSON is UTF-8, `ensure_ascii=False`. All modules are stdlib-only
Python 3. No imports from v1 (`engine/`, `tools/collector/`) — copy and
adapt logic instead. Every module lives in `engine-v2/` and is runnable
as `python3 <module>.py` from that directory.

## Article (Step 1 output)
```json
{"id": "a001", "title": "...", "url": "...", "source": "The Daily Star",
 "section": "", "published": "2026-11-14T05:30:00+00:00", "summary": "...",
 "found_via": "bing|google-news|rss|editorial|paste",
 "title_source": "feed|slug|page",
 "body_text": "", "body_error": ""}
```
- `id`: `a001`, `a002`, ... in collection order.
- `title_source`: where the headline came from — "feed" (headline
  from an approved RSS / news-sitemap / discovery result), "slug" (derived
  from the URL slug; plain sitemaps carry no titles), "page" (headline
  extracted from an article page only when separate page-metadata permission
  is approved — og:title, then <title>, then first <h1>). Without that
  permission the collector must not fetch the article page to resolve a slug.
  A main whose page fetch fails keeps its slug title (title_source stays
  "slug") — never invented.
- `summary`: RSS description (≤600 chars) or paste note. Never full text.
- `body_text`: filled ONLY for Step-3-kept articles (Step 4 fetches it).
  Empty string otherwise. `body_error` explains a failed fetch.

## Step 1 outputs (runs/<date>/)
- `articles-<date>.json`: {"date", "collected", "articles": [...]}
- `sources-<date>.json`: per-source {"method","status","items","fresh",
  "latest_item","last_success"} — `last_success` is the ISO time of the
  last successful fetch for that source (persisted in
  `engine-v2/state/sources.json` across runs so dead sources stay visible).
- `clusters-<date>.json`: [{"members": [ids], "main_id": "...",
  "size": N}] — cluster size is informational only, never used by later steps.

## Publisher rights gate (Step 1)

The operational policy is loaded from state/source_rights.json by
rights_registry.py. Unknown domains are denied by default. The collector
must keep these permissions separate:

- Metadata collection: metadata_status=approved, non-empty metadata_scope,
  permission evidence, and a current reviewed_at/review_due_at window.
- Article-page headline extraction: page_metadata_status=approved with
  separate page_metadata_scope/evidence and a current review window, or a
  body licence that explicitly covers page processing.
- Article-body fetching: body_status=licensed, non-empty body_scope,
  permission evidence, and a current review window. A metadata-only or
  RSS-headline permission never unlocks article bodies.
- Aggregator discovery: Bing/Google News are discovery hosts only. Every
  resolved publisher URL must pass the publisher metadata gate before it is
  retained in the collected article set.
- Robots policy is independent. A rights approval never overrides a
  robots.txt disallow; a robots.txt fetch failure denies the request.

The JSON registry is the Engine's operational policy source. The SQLite
source_rights_reviews table is a separate application audit store and is
not automatically synchronised yet. Changes to either store alone do not
constitute publisher activation.

## Step 2 output (article + two fields)
- `priority`: "normal" | "low"
- `prefilter_reason`: "" | e.g. "crime-section" | "keyword-let-through"
- Log: `runs/<date>/prefilter-log-<date>.md` — one line per deprioritised
  headline (date, title, source, reason), human-scannable.

## Step 3 decision (one per article)
```json
{"id": "a001", "decision": "keep|maybe|reject", "score": 0|1|2|3,
 "topic_primary": "BD-GOV", "topic_secondary": "INT-ORG",
 "evidence_quote": "exact substring of headline/summary",
 "reason": "one line"}
```
- `topic_primary`: "" when decision is reject (score 0) or maybe with no
  named topic (score 1). `topic_secondary`: "" unless a second topic
  clearly applies.
- `evidence_quote`: "" only for reject. Every keep MUST have a non-empty
  quote that is a verbatim substring of the headline + summary text.
- The decider reads the rubric, topics and lexicon from RULES.md at
  runtime (via `rules_loader.py`) — no hardcoded topic lists in code.
  Topics: 10 (BD-GOV, BD-ECO, BD-BANK, BD-NATL, INT-ORG,
  INT-REL, ENV, SCI, SPORT, PEOPLE).
- **Support-only cap (Decision 4, 2026-11-15):** a hit on Support terms
  only (no Strong term matched in any topic) scores at most 1 (maybe),
  for ALL topics. Exempt: a crime/accident story rescued by an
  instrument (law/ordinance/commission/directive/policy).
- **Score-3 first/record signal (Proposal 1, 2026-11-15):** a first or
  record in the headline, with a number and a date in the article,
  scores 3 (topic = the headline's Strong-hit topic). Schedule phrases
  ("first phase", "প্রথম ধাপ") are not achievements.
- **Rankings/indexes (Proposal 2, 2026-11-15):** maybe by default.
  Awards keep (score 2) when a Bangladeshi institution or person is
  involved. A ranking/index keeps (score 2) when the article states
  Bangladesh's rank/position; with a number and a date as well it
  scores 3. A ranking with no Bangladesh position stays maybe — unless
  the story carries a Strong topic hit AND a number, in which case it
  is decided on its own merits (the ranking rule is for stories ABOUT
  a ranking, not substantive stories that merely cite one). A ranking
  story that matched no lexicon term at all is assigned a topic from
  its subject (hunger/poverty -> BD-ECO, corruption -> BD-GOV,
  passport -> INT-REL, development -> BD-NATL, else PEOPLE).
- `decide(article, allow_opinion=False)`: the news path always uses
  False (opinion columns reject). `score_editorial(article)` scores
  one opinion piece for the মতামত slot with the same rubric except
  the opinion-reject does not apply; the slot takes the best-scoring
  editorial of the day, only if it scores 2 or higher.
- The 6 script examples are the test suite (tests/test_step3.py):
  1. "Cabinet approves draft ordinance on [subject]" → keep, 3, BD-GOV,
     quote contains "approved the draft ordinance".
  2. "IMF board approves [amount] tranche for Bangladesh" → keep, 3, INT-ORG.
  3. "Minister says economy will improve soon" → reject, 0.
  4. "Bank robbery in [district]" → reject, 0 (not BD-BANK).
  5. "After [violent crime], High Court issues [N] directives on [subject]"
     → keep, 2, BD-GOV; instrument only.
  6. "Bangladesh win one match in a bilateral series" → maybe, 1;
     "Bangladesh win a major tournament final" → keep, 2, SPORT.
  (The examples use [blanks] for invented details; the test fills them
  with plausible values and asserts decision + score + topic.)

## Step 4 fact (one per fact line)
```json
{"what": "...", "value": "...", "unit": "", "date": "2026-11-14",
 "status": "happened|scheduled|proposed|forecast", "quote": "exact article sentence"}
```
- `value`: "" and `date`: "উল্লেখ নেই" when unstated (never invent).
- Article summary for an item: {"facts": [fact, ...] (max 5),
  "why_important": "[পটভূমি] ..."} — the why-line is marked as background.
- **`facts_en` (Proposal 8, 2026-11-15):** every kept story also
  carries an English fact list, same shape as `facts`. For
  English-language articles it is the same facts. For Bangla-language
  articles it is the translator's rendering (glossary-based "what",
  same value/unit/date/status, same verbatim quote; "উল্লেখ নেই"
  dates become "not stated"). Step 5 rules apply to its numbers and
  names. Carried on the page item (see Step 7) and therefore in the
  edition JSON for every story.

## Step 5 check result
```json
{"item_id": "...", "ok": true|false,
 "failures": [{"fact": "...", "check": "quote|number|name", "detail": "..."}],
 "action": "keep|drop_fact|verify", "facts_kept": 3}
```
- Fewer than 2 facts kept → item dropped (action "drop").

## Step 6 output
Same shape as Step 4, with `bangla_lines`: [1–5 fact lines in cholito
Bangla] and `why_important_bn`. Glossary terms from RULES.md applied;
first mention of a foreign name/organisation gets the English in
brackets. Bengali digits in Bangla text.

## Step 7 daily page (runs/<date>/page-<date>.json)
```json
{"date": "2026-11-14",
 "at_a_glance": [{"event": "...", "date": "...", "key_fact": "...", "status": "..."}],
 "sections": {"বাংলাদেশ (রাজনীতি, আইন, প্রশাসন)": [item, ...], ...},
 "changes": ["...", "..."],
 "maybe_items": [{"title": "...", "url": "...", "source": "..."}],
 "top_news": ["dated one-liners"],
 "gk_footer": "...",
 "editorial": {"label": "মতামত",
               "item": {"headline": "...", "source": "...", "url": "...",
                        "summary": "...", "score": 2,
                        "topic_primary": "BD-ECO"} | null,
               "empty_reason": "..."}}
```
- Item: {"id","headline","score","topic_primary","fact_lines":[...],
  "why_important","status","sources":[{"name","url"}],
  "facts_en":[{Step 4 fact, in English}...],
  "focus_paragraph": "..." (score-3 items only, when the fact list
  supports 3 sentences — see below)}.
- Sections in the RULES.md order, empty ones omitted. Max 15 full items.
- **Page order (Decision 5, 2026-11-15): score desc, then newest first**
  (by published time); collection order breaks exact ties only.
- **Focus paragraph (Proposal 7, 2026-11-15):** for score-3 items
  only, an optional `focus_paragraph` field — 3–4 sentences built ONLY
  from the item's verified fact list + its [পটভূমি] line, shape
  প্রসঙ্গ → তথ্য → বিশ্লেষণ → উপসংহার (headline as context, the
  item's own fact lines, the [পটভূমি] line, the key fact repeated as
  a memory hook). Omitted when the fact list cannot support 3
  sentences (fewer than 1 fact line, or no why line). Every number/name
  in it passes the Step 5 check: fact-line numbers are verified facts,
  and headline numbers are dropped when they do not appear in the
  article body — TBS-sitemap headlines are slug-derived and sometimes
  express a figure in a different unit than the body ("Tk159 Crore"
  vs "1.59 billion"), so such a token is removed rather than carried
  as an unverified fact (headline words stay).
- **Editorial slot (Decision 2, 2026-11-15):** one editorial of the day,
  rendered outside the 15 news items and never counted in them, clearly
  labelled মতামত (opinion). The item carries headline/source/url/summary
  only — never full opinion text. When no editorial scores 2+, `item`
  is null and `empty_reason` says why.

## Step 8 questions (runs/<date>/questions-<date>.json)
- Q&A: {"id","question","answer","fact_id","source_quote"}
- MCQ: {"id","stem","options": {"ক": "...", "খ": "...", "গ": "...", "ঘ": "..."},
  "key": "ক", "source_quote": "...",
  "why_wrong": {"ক": "...", "খ": "...", "গ": "...", "ঘ": "..."}}
  The engine outputs the key in canonical order and NEVER shuffles —
  the app shuffles at render time.
- **Analytical (Proposal 9, 2026-11-15):** at most 2 per edition, only
  from score-3 items: {"id","question","answer","fact_id",
  "source_quote","kind": "analytical","is_analysis": true,
  "checked": true}. The stem asks for an implication or a solution;
  the answer restates the item's own fact quotes + its [পটভূমি] line
  only, prefixed "বিশ্লেষণ (তথ্যের ভিত্তিতে, নতুন তথ্য নয়)". No
  analytical question is emitted when the item has fewer than 2 facts
  or no why line. Analytical questions are NOT SRS cards.

## Step 9 SRS state (runs/<date>/srs-<date>.json)
```json
{"date": "2026-11-14",
 "cards": [{"fact_id": "...", "question_id": "...", "question": "...",
   "next_review": "2026-11-15", "interval_days": 1, "repetitions": 0,
   "reported": false}]}
```
- Missed → next_review = today + 1/3/7/14 days by repetitions (1st miss
  +1, then +3, +7, +14). `reported: true` removes the card until review.

## Step 10 vocabulary (runs/<date>/vocab-<date>.json)
```json
{"date": "2026-11-15",
 "words": [{"Headword / phrase": "...", "IPA": "...",
   "Bangla phonetic": "...", "Part of speech / type": "...",
   "Difficulty": "...", "Bangla meaning": "...",
   "English definition": "...", "Synonyms": "...", "Antonyms": "...",
   "Word family / derivatives": "...", "Collocations / patterns": "...",
   "Original example": "...", "Newspaper context note": "...",
   "Source publication": "...", "Article headline": "...",
   "Publication date": "...", "Direct source URL": "...",
   "BCS / Bank relevance": "...", "Priority": "High|Medium"}],
 "phrases": [{"Phrase": "...", "Type": "...", "Bangla meaning": "...",
   "English explanation": "...", "Usage / register": "...",
   "Original example 1": "...", "Original example 2": "...",
   "Common collocations / grammar pattern": "...",
   "Source publication": "...", "Article headline": "...",
   "Publication date": "...", "Direct source URL": "...",
   "Exam value": "..."}],
 "revision_words": [same shape as "words"],
 "stats": {"bank_words": 281, "bank_phrases": 68,
   "matched_words": 52, "matched_phrases": 7,
   "words": 20, "phrases": 10, "revision_words": 5,
   "short_words": false, "short_phrases": false,
   "short_revision": false}}
```
- Field names match the v1 app contract exactly (see
  editions/data-2026-11-14.json). 20 words + 10 phrases + 5 revision.
- Every word/phrase occurs verbatim in a kept article; "Original
  example" is a verbatim sentence from that article (fact quote
  preferred). Bengali meaning comes from the editable bank
  (rules/vocab_bank.json). IPA/phonetic/synonyms/antonyms/family/
  collocations are reused from an earlier v1 edition when the word
  appeared there, else "". Shortfalls are reported in stats, never
  filled by invention.
- Revision words are copied verbatim from the previous editions' word
  lists (last v2 dry-run vocab, else the v1 editions dir), excluding
  today's 20 words.

## Shared helpers (common.py)
- `fetch(url, timeout)` / `fetch_text(url)` with the SarangshoPlus UA.
- `clean_html(text)` → plain text.
- `parse_pubdate(raw)` → aware datetime or None.
- `norm_bangla(text)`: Unicode NFC, Bangla digits → English digits,
  zero-width chars removed.
- `strip_tracking(url)`: remove utm_*, fbclid, gclid and other tracking
  query params; drop fragments.
- `ngrams(text, n)`: character n-grams of normalised text.
- `robots_allowed(url)`: fetch + parse robots.txt (cached per host per run),
  respect User-agent: * rules; on fetch failure, deny (fail-closed) and record.
- `today_dhaka()` → YYYY-MM-DD in Asia/Dhaka.

## V2 publish gate

**Status:** defined 2026-11-15, for the v1 → v2 switch (first v2 edition:
Edition 11, 2026-11-17 — Edition 10 on 2026-11-16 stays v1). This gate is scoped to v2. The v1 auto-publish
rule (17/17 checks + longest-correct ≤10/25, granted by Rudro 2026-11-13)
was scoped to v1's checklist and is NOT carried over: a v2 edition is
correct only if it passes every check below, and the v1 17/17 number
means nothing for v2.

**Auto-publish grant (Rudro 2026-11-15, delegated — "other thing do
yourself"):** for LATER v2 editions only, an edition passing 15/15
may auto-publish with approval reviewer "auto-15/15 (Rudro's rule
2026-11-15)". The FIRST v2 edition (Edition 11) is human-gated
regardless — it stops for Rudro's eyes even at 15/15. The grant
covers auto-publish only; it does not cover the cron flip (timed
for Edition 11, see `CRON_INSTRUCTIONS_V2.md`) or the tracker
reset (to 0 at the first v2 edition, Edition 11 = v2 Day 1).

**Pass definition:** ALL numbered checks pass. One failure stops the
edition at the human gate — no publish, no sync, no partial fix by
hand-editing a converted file. A failure is fixed by fixing the engine /
converter input and re-running, never by editing the output to make a
check pass (same rule as v1's importer: "never edit the draft JSON by
hand to make a check pass", PHASE2_RUNBOOK §3).

**Where the gate runs:** a new script, `engine-v2/publish_v2.py`
(built 2026-11-15; gate 15/15 on the 15 Nov dry-run). `--check` reads
the v2 run outputs in `engine-v2/runs/<date>/` AND the converted
app-format file `editions/data-<date>.json`, and writes
`engine-v2/runs/<date>/review-v2-<date>.json` with one result per check
(`passed` / `total`). `--publish` runs only when
`engine-v2/runs/<date>/approval-<date>.json` says `approved: true`
(same approval-file shape as v1's `publish.py --publish`).

**FIRST-EDITION RULE (Edition 11, 2026-11-17): Edition 11 stops at
the human gate for Rudro's eyes even if it passes every check
below.** The Edition 7 lesson is why: a wrong MCQ auto-published
once under the v1 rule because the checks verified form, not
content. Auto-publish under this v2 gate for LATER editions was
granted by Rudro 2026-11-15 ("other thing do yourself"): gate
15/15, approval reviewer "auto-15/15 (Rudro's rule 2026-11-15)".
The first v2 edition is NOT covered by that grant.

### The checks

1. **Run completed.** `run_v2.py` finished without crashing;
   `engine-v2/runs/<date>/edition-<date>.json` exists with `engine:
   "v2"`; `stats.collected >= 10` (below 10, read the freshness
   report — a feed may be down — do not pad, do not publish).
2. **Page completeness — thin day stays thin.** Page items
   (sum over `page.sections`) are **12–15**. 15 is the ceiling
   (`MAX_ITEMS = 15`, `step7_page.py:61`); 12 is the floor, the same
   floor as v1 (`MIN_STORIES = 12`, `engine/publish.py:38` — v1 once
   shipped 12 stories honestly unpadded). Below 12: gate FAIL, no
   publish, fallback decision (see SWITCH_PLAN.md). Never pad with a
   weak story to reach 15.
3. **Step 5 evidence — 0 violations on the page.** For every page
   item, the Step 5 result is `action == "keep"` and `failures == []`
   (0 quote / number / name violations, `step5_check.py:207-256`).
   Any page item with action `"verify"` (marked যাচাই করুন) or
   `"drop_fact"` FAILS the gate. Note the pipeline default is looser
   than this gate: `run_v2.py` lets `"verify"` items onto the page
   and drops only `"drop"` items — the gate is deliberately stricter.
   **Persisted-evidence requirement:** the per-item Step 5 results
   are NOT in any file `run_v2.py` writes today (page items carry no
   `check` field, `step7_page.py:321-346`; article bodies are not
   written back to `articles-<date>.json` — verified 2026-11-15:
   page items have no `check`/`body_text`, articles file has no
   `body_text`). So since the 15 Nov dry-run, `run_v2.py` writes
   `runs/<date>/step5-<date>.json` with one record
   per kept item (`item_id`, `action`, `failures`, `facts_kept`); the
   gate reads that file, and a missing file is a FAIL. Re-running
   Step 5 from re-fetched bodies is not an acceptable substitute —
   it would check different text than the edition was built from.
4. **`facts_en` present and consistent.** Every page item carries a
   non-empty `facts_en` list (15/15 in the 15 Nov dry run); every
   `facts_en` entry has the same value / unit / date / status as the
   verified fact it renders, and every number in `facts_en` is a
   number in the verified fact list. (Step 5 rules apply to
   `facts_en` numbers and names — CONTRACTS.md, Step 4.)
5. **Sources are real and direct.** Every page item has ≥1 source
   with an `http(s)` URL. No page item's source URL contains
   `news.google.com`. No page item is sourced only from an
   aggregator/syndicator (e.g. `msn.com` — `step1_collect.py:243-244`
   maps it to source "MSN") unless the original publisher URL was
   substituted by a verified `resolve.py` run (see SWITCH_PLAN.md
   §2b). A Google-News-only story cannot reach the page through the
   normal path anyway: `fetch_bodies_for_kept` gives Google News
   redirects `body_error "no direct URL"` and `run_v2.py` Step 4
   drops no-body items (25 dropped on 15 Nov).
6. **No slug headlines on the page.** Every page item's article has
   `title_source` in `{"feed", "page"}` in
   `runs/<date>/articles-<date>.json`; **0 page items with
   `title_source == "slug"`**. (15 Nov dry run: 0/15 slug on the
   page, 8 slug non-mains remaining — non-mains never reach the
   page, `step1_collect.py: resolve_slug_titles`.)
7. **MCQ count and traceability (converted file).** The converted
   file `editions/data-<date>.json` has exactly **25 MCQs**; every
   MCQ traces to a page story id in the same edition, has exactly 4
   options, and its key is one of its options. No MCQ uses
   "সবগুলো" / "কোনোটিই নয়" as an option and no stem is negative
   (Step 8 rules, `rules/RULES.md` STEP 8). The raw v2 file is NOT
   the input here: `runs/<date>/questions-<date>.json` holds 114–118
   MCQs on a normal day, and the converter selects the 25.
8. **MCQ longest-correct ≤ 10/25 — computed from the converted
   25, unique longest with all-equal questions excluded.**
   The gate script computes this from `editions/data-<date>.json`
   (the converted file), NOT from the raw v2 questions file. For
   each of the 25 MCQs, the longest option is the one with the
   greatest option-text length
   (`tools/validate_editions.py:115-120`, `longest_letter`); the
   verdict count is the **"excl" count** from
   `publish_v2.py:longest_counts()`: the correct option is
   longest-or-tied, EXCLUDING questions where all four options
   tie in length (equal length by design — e.g. single-number
   options — where length gives a guesser zero signal).
   **Pass: excl count ≤ 10.** (Definition set by Rudro 2026-11-15;
   the v1 cron's worded "longest-or-tied-longest" rule is NOT the
   v2 verdict — on 15 Nov it gives 14/25 and fails only on the 7
   all-equal questions. The worded, first-max-wins and
   strict-longest counts are still reported in the check detail
   for reference.)
   Counting from the raw v2 MCQs would be meaningless: the engine
   outputs every key in canonical order (`"key": "ক"`,
   `step8_questions.py:383`; verified 15 Nov: all 118 raw MCQ keys
   are `ক`, the app/converter shuffles at render time).
9. **MCQ letter balance 5–8 per letter.** On the same converted
   25 MCQs, after the converter's key shuffle, each letter A–D
   holds **5–8** correct answers (20–30% per letter,
   `tools/validate_editions.py:424`). A pre-shuffle count is
   meaningless for the same reason as check 8 (all raw keys `ক`).
10. **Vocabulary 20/10/5, no undocumented shortfall.**
    `runs/<date>/vocab-<date>.json` stats: `words == 20`,
    `phrases == 10`, `revision_words == 5`, and
    `short_words == short_phrases == short_revision == false`.
    Any `short_* == true` is a FAIL — shortfalls are reported, never
    filled by invention (`rules/RULES.md` STEP 10).
11. **Coverage label correct.** The converted file's `coverage`
    field equals the v1-format label for that date: previous day
    07:47 Dhaka → today 07:47 Dhaka, e.g. for Edition 11
    (2026-11-17): `"16 Nov 2026, 7:47 AM to 2026-11-17, 7:47 AM
    (Asia/Dhaka)"` (`engine/common.py:57-64`, `coverage_label`).
    The v2 engine has NO coverage function
    (`engine-v2/common.py` contains no coverage code — verified
    2026-11-15), so the converter must write this label; the gate
    verifies the string exactly, and the index entry's coverage
    must match it character for character. (This is the stale-line
    bug that bit Editions 8–14 in v1 — never again by construction.)
12. **Bengali overlay shape + number-token check.**
    `app/assets/editions/bn-<date>.json` exists with `status:
    "published"`; it covers exactly the same story ids and MCQ
    numbers `1`–`25` as the English converted file, with correct
    letters unchanged; shape asserts pass; the number-token check
    passes with **0 misses** — every number in each English summary
    appears in its Bengali summary (Bengali digits), per the v1
    `build_bn.py` check (e.g. `engine/runs/2026-11-11/build_bn.py:
    187-204`). The gate's own number-token check normalises
    Bangla digits to Latin on BOTH sides before comparing
    (Rudro 2026-11-15): an untranslated English summary carrying
    Bangla-digit tokens (CA09 '১৪', CA10 '৫৬০' on 15 Nov) matches
    them instead of failing on numbers that are present. BN
    hygiene: no ASCII digits, no "Tk", no English month names in
    the Bengali prose.
13. **Editorial slot state recorded.** `page.editorial` is present:
    either `item` is non-null with `score >= 2` (filled), or `item`
    is null and `empty_reason` is a non-empty string (empty by
    design). An empty slot with a recorded reason PASSES — it is
    not a failure. The gate report records filled/empty + headline
    or reason.
14. **Analytical questions ≤ 2, SRS recorded.** `analytical` count
    in the edition is ≤ 2 and every analytical question comes from
    a score-3 item (`step8_questions.py:498`,
    `ANALYTICAL_MAX_PER_EDITION = 2`); SRS card count is recorded
    in the gate report (461 on 15 Nov). Analytical questions are
    NOT SRS cards.
15. **Edition validator clean.** `python3
    tools/validate_editions.py` passes on the converted edition
    (any FAIL is a gate failure; a longest-correct FLAG is not a
    substitute for check 8 — the validator's flag threshold is
    informational, the gate's ≤10/25 is binding).

**Gate report.** `review-v2-<date>.json` records, per check:
pass/fail + detail (counts, the longest-correct number, the letter
distribution, editorial filled/empty + reason, coverage string
checked). The daily run report quotes the gate result verbatim
(`N/15 passed`) plus the longest-correct count — the same reporting
discipline as v1's `17/17 + longest-correct` line.
