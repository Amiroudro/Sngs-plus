# Conversion rules — renovated editions v1 → learning-module v2

Date: 2026-11-18. Author: conversion worker. Authority: Rudro's order
2026-11-18 02:02 ("make the existing days contents like the new model") +
full discretion 02:03 ("do it on your own way. be the bestest").
Model: `renovation/LEARNING_MODULE_MODEL_V2.md` (confirmed by Rudro 02:00).
Source shape: `renovation/RENOVATION_SPEC.md` (v1, 8-part format).

Scope: 16 renovated editions, 1–16 Nov 2026, 225 stories, in
`renovated-editions/data-YYYY-MM-DD.json`, plus the identical app-bundle
copies `app/assets/editions/data-YYYY-MM-DD.json`. Edition 11
(`data-2026-11-17.json`) has NO learning_module — out of scope, untouched.
`bn-*.json` carries no learning_module — untouched. `editions/` (live feed)
NOT touched; sync listed in the conversion report.

## Non-negotiable rules

1. **Verified facts stay byte-identical.** `verified_facts` is copied with no
   change of any kind (v1 has 4 inner shapes; all kept as-is).
2. **Content only moves between sections — never rewritten.** Every string
   in the new sections is a verbatim substring or the whole verbatim text
   of a v1 string, except mechanical reshapes listed below (key renames,
   dict→list with order preserved, splitting a list string on `;`/`,`).
3. **Never invent GK.** No new fact, definition, role, source name or URL
   is added. If GK cannot be verified, the per-section marker
   `"যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"` is kept (see rule 9).
4. **Nothing dropped silently.** Every v1 `exam_notes` point, paragraph
   and pre-split institution lands in `institutions` or `extra_knowledge`
   (or the marker). Anything that does not split cleanly is placed in the
   closest fitting section and LISTED in the conversion report.
5. **All other story fields byte-identical** (headline, summary, sources,
   mcqs, words, phrases, exam_qa, …). Only `learning_module` and the two
   top-level keys change.

## Target shape (per story, keys in this order)

`hero, news_summary, verified_facts, topic_gk, institutions,
extra_knowledge, mcq_practice, written_prep, vocabulary, revision,
deep_prep`. `exam_notes` is DROPPED. Per edition:
`renovation_format: "learning-module-v2"`, `renovation_date: "2026-11-18"`.

## Per-section transforms

### hero — keep verbatim
All v1 keys kept (`figure`, `label`, plus `note`/`source` where present —
15 stories carry `note`, 30 carry `source`; dropping them would lose
content). No change.

### news_summary → {text, source: {publication, date, url}}
`text` is the v1 summary string, verbatim. `source` is resolved from the
story's OWN `sources` list (never guessed):
- v1 already `{text, source: {…}}` (42 stories): keep the object verbatim.
- v1 `{text, source_line: "… — <url>"}` (14): take the URL, match it to the
  story source with that URL, use that source's publication/date/url.
- v1 `{text, source: "<Bangla name>, <Bangla date>"}` (12, all 16 Nov):
  match by Bangla publication name (প্রথম আলো (ইংরেজি) → Prothom Alo
  English; দ্য বিজনেস স্ট্যান্ডার্ড → The Business Standard; বিবিসি → BBC;
  দ্য ডেইলি স্টার → The Daily Star) and date against the story's sources.
- v1 plain string (157): source = the story's FIRST listed source
  (`sources[0]`, the pipeline's lead source), as {publication, date, url}.
- Every story has ≥1 source and every `sources[0]` has all three fields
  (verified by recount before converting).

### verified_facts — byte-identical (rule 1)

### topic_gk — keep verbatim
v1 inner shape is kept as-is (`intro`/`facts`/`distinctions`/`sources`, or
`title`/`text` in 15 stories). It is NOT reshaped into the model's
`tables` form: the v1 facts are `{fact, source}` strings with no
label/value split, and inventing labels would be rewriting. Consequence
for the Story screen: render `topic_gk.facts` (list) and
`topic_gk.distinctions` (`{title, text}`), not `tables`. The marker string
is kept as-is where present (6 stories).

### institutions / extra_knowledge — the split (from exam_notes only)
`topic_gk` is NOT mined for terms: the lesson stays intact. Only
`exam_notes` is split. Sources for each new entry: the exam_notes
`sources` names joined with `"; "` (verbatim names; those are the sources
the v1 worker cited for these notes as a whole — per-point attribution
cannot be recovered, and none is invented).

**Institution** — a named body with a role in the story's domain. The
point's head (before the first `:`, `—` or `(`) is, or contains, a named
organisation/body, AND the point states what it is or does.
Head signals: an org keyword (মন্ত্রণালয়, কমিশন, বোর্ড, ব্যাংক, সংস্থা,
ফেডারেশন, অ্যাসোসিয়েশন, কর্তৃপক্ষ, বিভাগ, আদালত, ট্রাইব্যুনাল,
বিশ্ববিদ্যালয়, পরিষদ, ইনস্টিটিউট, কাউন্সিল, সংসদ, দপ্তর, অধিদপ্তর,
অধিদফতর, গ্রুপ, সচিবালয়, কোম্পানি, কর্পোরেশন, ব্যুরো, এজেন্সি,
ফাউন্ডেশন, চেম্বার, সমিতি, ইউনিয়ন, সরকার, মন্ত্রিসভা, কমিটি, সেল,
ইউনিট, সার্ভিস, বাহিনী, এক্সচেঞ্জ), an ALL-CAPS acronym (BGMEA, BKMEA,
NBR, BBS, IDA, …) or a Bangla acronym attested in the corpus
(`ACRONYMS`, built from parenthesised expansions + a hand list of body
acronyms — বিজিএমইএ, এনইসি, ডাইফ, বিপিএসসি, ইউজিসি, দুদক, ওইসিডি,
একনেক, আইএমইডি, বিবিএস, বিডা, আইসিজে, আইএমএফ, ইআরডি, সিডিপি, …).
Which keyword decides is the LAST keyword-bearing word of the head
("আন্তঃব্যাংক ডলার দর" is a rate, not a bank — "দর" decides; "বাংলাদেশ
ইনস্টিটিউট অব প্ল্যানার্স" is a body — "ইনস্টিটিউট" decides). A head
that is a known body acronym (`MANUAL_BODIES`) is an institution even
when its rest is a bare fact ("বিপিএসসি: সংবিধানের ১৩৭–১৪১ অনুচ্ছেদ").
A bare acronym head is an institution ONLY with org/role evidence in
the rest (NCQG, GNI are terms, not bodies). A parenthesised year/note
("(২০২৪)", "(২০১৫, কপ২১)") is NOT a full_name — it stays attached to
the name; only a real expansion becomes `full_name`.
Role signals: the point is `Name: <role>` / `Name (Full name): <role>` /
`Name হলো/হচ্ছে <role>` / contains দায়িত্ব, ভূমিকা, কাজ, গঠন, গঠিত,
নিয়ন্ত্রক, তদারকি, পরিচালনা, শীর্ষ, সংগঠন, প্রতিষ্ঠা, প্রতিষ্ঠিত,
নজরদারি, অধীন, কার্যকর. A head of the form "ACRONYM + descriptive
words" ("বিইআরসি জ্বালানি খাতের নিয়ন্ত্রক সংস্থা: …") takes the acronym
as `name` and the descriptive words join the role.
Entry: `{name, full_name?, role, source}`. `name` = the short name as
written (acronym or name); `full_name` = the parenthesised expansion when
the point gives one; `role` = the point minus the `Name:` / `Name (…):`
prefix, stripped — or the whole point when no clean prefix exists.
Examples (v1 sample): Planning Commission / NEC / ECNEC / IMED / DPP;
বিজিএমইএ, বিজিআইডব্লিউএফ, মজুরি বোর্ড, শ্রম ও কর্মসংস্থান মন্ত্রণালয়,
বাংলাদেশ ব্যাংক, বিশ্বব্যাংক, আইডিএ.

**Extra knowledge** — a term, concept, law, scheme, index or process the
reader needs, with its meaning. Head signals: `Term (Expansion): …`,
`Term-এর পূর্ণরূপ: …`, `Term = Expansion`, `Term মানে …`, `ধারা N …`
(anchored at the start — "শ্রম আইনের ধারা ১৩(১)" counts, a mid-sentence
"ধারা ৬২৭" inside "মনে রাখার কৌশল: মজুরি ধারা ৬২৭" does not),
`Term বলতে … বোঝায়`, `Term হলো …`, or a head carrying a concept keyword
(নীতি, হার, সূচক, তহবিল, চুক্তি, আইন, ধারা, পদ্ধতি, ব্যবস্থা, কাঠামো,
মডেল, প্রক্রিয়া, কর, শুল্ক, ভর্তুকি, ঋণ, রিজার্ভ, মুদ্রানীতি, বাজেট,
পরিকল্পনা, কৌশল, সমীক্ষা, জরিপ, প্রতিবেদন, স্কোর, রেটিং, দর, আদেশ,
নিয়ন্ত্রণ, সংবিধি, কংগ্রেস, ইনিশিয়েটিভ, বিমানবন্দর). Exam-tip label
heads ("পরীক্ষায় আসে:", "মনে রাখার সংখ্যা:", "মুখস্থ রাখুন:") are terms
with the label as `term`. A head with no keyword but ≤ 40 chars and no
verb is a term (medium confidence).
Entry: `{term, full_name?, meaning, source}`. `term` = the head verbatim;
`meaning` = the definition clause, or the whole point when inseparable.
Examples: Public Investment, PIM, Feasibility Study, নীতি সুদহার,
রিজার্ভ, ঘাটতি অর্থায়ন, বাংলাদেশ শ্রম আইন ২০০৬ ধারা ১৩৮/১৩৯, LEAP,
PEDP-5.

**Continuation fragments.** v1 points are sometimes sentence fragments
continuing the previous point ("এর চেয়ারম্যান … থাকেন।", "প্রতিষ্ঠা
১৯৭২", "বাংলাদেশ ক্যারাটে যোগ দেয় ২০১০ সালে"). A remainder fragment is
MERGED into the previous entry's role/meaning (appended, verbatim) when
it starts with এর/এটি/তার/তাদের/সেটি/সেটা, contains "এমন", starts with
a continuation starter (লক্ষ্য, উদ্দেশ্য, ফলে, এতে, তাতে, এছাড়া, আরও,
অর্থাৎ, প্রতিষ্ঠা, মোট, …), contains a year and is ≤ 60 chars, is a
short (≤ 30 chars) verbless fragment, repeats a word (≥ 4 chars) from
the previous entry's name/term, or its first word appears in the
previous entry's role/meaning. It is NOT merged when it starts with
"এই"/"ওই" (demonstrative + new subject). Merged fragments are joined
with "। " when the existing text has no terminal punctuation — the "।"
is a separator between verbatim fragments, not new content. Every merge
is logged.

**A fragment starting with a year/number** ("২০২৬ সালের বোর্ড গঠিত
১ নভেম্বর।") is never treated as a headed definition — it falls through
to remainder/merge.

**Compound points.** A point naming TWO institutions joined by `;`
(e.g. "বিজিএমইএ (…) …; বিকেএমইএ (…) …") is split on `;` and each
segment classified on its own. A point is split ONLY when two distinct
institution heads are present — `;` inside a single role clause (e.g.
"…সদস্য: চেয়ারম্যান, …; নির্দিষ্ট শিল্পে আরও দুজন…") is NOT split.

**Pre-split institutions (36 stories).** v1 `exam_notes.institutions`
is a mix of dicts (`{name, role}`, 69 — already model-shaped) and strings
(27, `Name: role`). Dicts are kept as-is with the `source` key added
(joined exam_notes source names, per the source rule above); strings are
parsed with the institution rule (`Name: role` → `{name, role, source}`).
Pre-split entries are placed FIRST in `institutions`, then institutions
found in the notes, in point order.

**The `text` paragraph (13 stories, all 13 Nov).** All are exam-orientation
paragraphs ("…বিসিএস/ব্যাংক … নিয়মিত বিষয়। মনে রাখো: …"). They are
neither institutions nor terms. Placed FIRST in `extra_knowledge` as
`{term: "পরীক্ষার জন্য মনে রাখুন", meaning: <text verbatim>, source}`.
The term is a fixed section label, not invented GK content.

**Remainder.** A point that is neither an institution nor a term (a general
exam fact or cross-cutting statement, e.g. "পোশাকশিল্প মোট রপ্তানির প্রায়
৮০ শতাংশ আনে — …") goes to `extra_knowledge` as
`{term: <head phrase verbatim — text before the first '—' / ':' / '।' /
';' when ≤ 50 chars, else the first five words verbatim>, meaning: <whole
point verbatim>, source}`. Every remainder is logged and listed in the
conversion report by edition + story id. No remainder is dropped.
Hand-checked overrides live in `renovation/conversion-overrides.json`
(7 entries: 5 continuation merges, 1 forced standalone remainder, 1
hand-split term); the converter logs them with confidence `override`.

## Same-name re-mentions: MERGE, never drop
A body or term often appears twice in one story — once in the
pre-split `institutions` list and again in the notes (or twice in the
notes) — and the second mention usually adds NEW content (e.g. the
pre-split BMET role says what it does; the notes BMET point gives its
English full name and its role as the official source of migration
data). Dropping the second mention LOSES that content (found by the
nothing-dropped verification pass, 2026-11-18). So:

- Same name + same section → append the new role/meaning to the
  existing entry with the continuation separator (`। ` when the
  existing text has no terminal punctuation); if the new text already
  contains the old one, the new text replaces it; if the old contains
  the new, nothing changes. A missing `full_name` is added to the
  existing entry (key order: name/term, full_name, role/meaning,
  source).
- Term re-mentioned as an institution (or vice versa) → merge into
  whichever entry exists first; if a term turns out to be a body, the
  entry is PROMOTED to institutions with its meaning carried over as
  the role.
- The log flags these as `dedup-merge` (`same-name` /
  `cross-section` / `promoted`); the summary counts them.

## Continuation merges — named-body guard
A remainder fragment merges into the previous entry only if it does
NOT name a different body/term already seen in this story. A common
word in the previous entry's role (e.g. "বিদেশে" in BMET's role) must
not pull a sentence about the consulate into BMET — the fragment
belongs to the body it names.

## Classifier fixes from the sampling audit (2026-11-18)
Found by hand-sampling converted stories (not by counts):

- **Parens are not type signal.** `keyword_type` ignores parenthesised
  content: it is an expansion/translation, not the head's own type.
  ("বিনিময় হার (Exchange Rate)" was misread as an organisation
  because of the English word Exchange inside the parens; it is a
  concept and belongs in extra_knowledge.)
- **Generic field labels are not bodies.** A point led by "সদর দপ্তর",
  "প্রধান কার্যালয়" or "সদর কার্যালয়" (e.g. "সদর দপ্তর ইনচিওন, দক্ষিণ
  কোরিয়া।" — an HQ fragment of the previous body) returns remainder,
  so the continuation logic can attach it to that body ("সদর" is a
  continuation starter). A point led by "প্রস্তাবিত"/"পরিকল্পিত"/
  "সম্ভাব্য" is a proposal, not a body ("প্রস্তাবিত দুই বিভাগ"), and
  likewise returns remainder.
- **Latin-acronym bodies.** Points often head with the Latin acronym
  ("NBR = National Board of Revenue ...", "UNFCCC: ...", "এনপিএসবি
  (ন্যাশনাল পেমেন্ট সুইচ বাংলাদেশ): ..."). `LATIN_BODIES` (the Latin
  forms of the manual bodies plus UNHCR, UNEP, UNFCCC, BOESL, IDA,
  DTCA, PPPA, BAKSAL, GCF, EDCF, NPSB) is checked in the "=" branch,
  the colon/dash head branch, the paren-head branch and the
  acronym-leading-token branch, so those heads become institutions.
  Concepts that merely look like acronyms (RMG, NPL, GNI, NCQG, LC,
  CEPA, HSIA, COP) stay terms. এনপিএসবি was added to MANUAL_BODIES.
- **Parens are type signal only in the head's own language.**
  `keyword_type` ignores a parenthesised span only when it holds no
  Bangla characters (a Latin expansion/translation); a Bangla paren
  keeps its signal. A paren holding a citation qualifier ("কলাম
  অনুযায়ী") is not an expansion at all (`_is_expansion` rejects
  অনুযায়ী/অনুসারে/মতে).
- **Same body, two spellings, one entry.** Dedup keys include the
  base name and the bare acronym of a "Name (ACR)" head, so a
  pre-split "গ্রিন ক্লাইমেট ফান্ড (GCF)" and a later bare "GCF" merge
  into one institution instead of listing the body twice.

### news_summary — source date normalisation
A kept-verbatim `source` object whose `date` is a Bangla-digit
`YYYY-MM-DD` (12 stories, all 14 Nov) is transliterated to Latin ISO
digits — same date, other script — so the app can parse it. Nothing
else in the object changes.

### mcq_practice — mechanical reshape, content verbatim
`options` dict `{A,B,C,D}` → list `[A, B, C, D]` (order preserved);
`correct` letter → 0-based index (A=0 … D=3). `question` and
`explanation` verbatim. The `no` key (120 MCQs) is kept. Assert: exactly
4 options, correct in A–D, explanation non-empty. (Model shape; the
Story screen reads list + index.)

### written_prep → {short: {question, outline}, analytical: {question, outline}}
- v1 dict `{short_question, short_outline, analytical_question,
  analytical_outline}` (86): key rename only.
- v1 dict `{short, analytical}` (12): inner keys already
  `{question, outline}` — kept.
- v1 list of 2 (127): classify each item by `type` first
  (সংক্ষিপ্ত প্রশ্ন / সংক্ষিপ্ত / short → short; বিশ্লেষণধর্মী প্রশ্ন /
  বিশ্লেষণধর্মী / analytical → analytical); else by question text
  (`(সংক্ষিপ্ত প্রশ্ন)` / `সংক্ষেপে` → short; `বিশ্লেষণ` → analytical);
  else by position ([0] = short, [1] = analytical). Outline key
  `outline` / `model_outline` / `model_answer_outline` → `outline`.

### vocabulary — mechanical reshape
`{word, bangla_meaning, example, synonym, antonym}` →
`{word, meaning_bn, example, synonyms, antonyms}`. `synonym`/`antonym`
strings are split on `;` then `,` and stripped (empty pieces dropped);
a value with no separator becomes a one-element list. Text verbatim.
Assert: exactly 5 per story.

### revision — mechanical rename
Flashcards `{question, answer}` → `{q, a}`; `{q, a}` kept.
`next_revision` kept verbatim. Assert: 3–5 flashcards, 2 next-revision
questions.

### deep_prep — keep verbatim (list of 4–6 titles)

## Marker stories (6)
2026-11-02 CA09, 2026-11-08 CA06, 2026-11-08 CA09, 2026-11-10 CA09,
2026-11-10 CA14, 2026-11-11 CA11 — `topic_gk` AND `exam_notes` are both
the marker string in v1. For these, `institutions` and `extra_knowledge`
are BOTH the same marker string (per-section marker rule, v2 model).

## Verification (all re-run from the converted files)
- Recount: 225 stories; every story carries all 11 keys in order; no
  `exam_notes` key anywhere; `renovation_format` = "learning-module-v2"
  on all 16 editions.
- Per-story counts: `mcq_practice` exactly 4 with `correct` + `explanation`
  each; `vocabulary` 5; `revision` 3–5 flashcards + 2 next-revision;
  `deep_prep` 4–6.
- `verified_facts` byte-identical vs the v1 backup (hash comparison).
- All other story fields byte-identical vs the v1 backup.
- Sample the splits by hand (≥15 stories across editions; more if unsure),
  checking institutions vs extra_knowledge placement, sources present,
  nothing invented or dropped.
- Run `tools/validate_editions.py`: it compares canonical `editions/` with
  `app/assets/editions/` — it CANNOT pass in full until the live-feed sync
  (browser route) lands, because `editions/` stays v1 by order. Run it
  (a) as a baseline before converting, (b) on a scratch tree of converted
  canonical + asset copies (must print ALL EDITIONS PASS), and (c) on the
  real tree after converting (expect ONLY the 16 byte-identity failures
  for the pending sync; every other check must pass).
- After converting, copy the 16 converted files to `app/assets/editions/`
  and verify byte-identical hashes with the staging copies.

## Backup
Before writing anything: `renovated-editions-v1-backup-2026-11-18/`
(full `renovated-editions/` tree + `app/assets/editions/data-*.json` +
`app/assets/editions/index.json` as they were).
