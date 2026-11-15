# v2 gate decisions — independent recount and recommendation

Prepared: 2026-11-15 evening (Asia/Dhaka), by CAT's own re-run — not the builder's numbers.
Source files: `runs/2026-11-15/review-v2-2026-11-15.json`,
`runs/2026-11-15/app-format/data-2026-11-15.json`,
`runs/2026-11-15/app-format/bn-2026-11-15.json`, `publish_v2.py`.

## What I verified myself

Recounted all four longest-correct definitions straight from the 25 converted MCQs.
They match the review file exactly:

| Definition | Count | vs limit 10/25 |
|---|---|---|
| Worded rule — ties count | 14/25 | FAIL |
| v1 validator style — first letter reaching max wins | 8/25 | PASS |
| Unique longest only | 7/25 | PASS |
| Ties count, all-equal questions excluded | 7/25 | PASS |

## Check 8 (longest-correct) — recommendation: adopt "unique longest, all-equal excluded"

The worded rule fails only because of 7 questions where all four options are the
same length (Q16, Q18, Q19, Q22, Q23, Q24, Q25 — e.g. '40 / 60 / 70 / 49').
When every option ties, length gives a guesser zero signal, so counting those
as "longest-correct" is counting nothing. v1 never enforced the worded rule
either — its own validator used first-max-wins (8/25).

**Deeper catch the count hides:** 6 of the 7 remaining hits are the same flaw —
the correct option is the only one carrying a unit, while the three wrong ones
are bare numbers: Q13 '6.53 %' vs '5.9 / 7.2 / 8.2', Q14 '126.35 million',
Q15 '41 %', Q17 '1 billion', Q20 '৫৬০ কোটি', Q21 '800 km'. A guesser who
picks "the option with a unit" would get those right. Recommended fix before
the first live v2 edition (Step 8 question generation): put the same unit on
all four options, or strip it from all four. That alone would take the unique-
longest count from 7/25 to 1/25 (only Q12, the phrases question, left).

## Check 12 (number-token) — recommendation: false positive, numbers are there

Both "missing" numbers ARE in the Bangla summaries, in Bangla digits,
displaced after a colon by the v2 fact-line rendering:

- CA09: BN summary '…গত অক্টোবর শুনানির জন্য ওঠে: ১৪' — ১৪ present.
  (EN data file summary has it in place: 'গত ১৪ অক্টোবর'.)
- CA10: BN summary '…কমেছে কোটি ডলার…: ৫৬০ কোটি' — ৫৬০ present.

The checker fails because it looks for the Latin token '14' / '560' and never
matches Bangla digits — a checker limitation, not missing content. Recommended
fix: normalise Bangla digits to Latin inside the gate's own number-token check
(`publish_v2.py` line ~108, copied rules) before comparing. Do NOT touch the
v1-frozen `check_data.py`.

## What this means

With those two decisions, the 15 Nov dry-run gate goes from 13/15 to 15/15 —
no edition content changes needed for either. The remaining known gaps are
unchanged: CA question stems are still cloze fragments with 'কত' appended,
Bangla lines still telegraphic in places, Step 10 has the known stale-fixture
phrase check, Steps 4–6 have the known live-data flake.

## Still Rudro's call (spelled out, no shorthand)

1. Accept the longest-correct definition above (unique longest, all-equal excluded)?
2. Accept check 12 as a false positive, with the Bangla-digit fix to the gate check?
3. Accept the unit-on-all-options fix in Step 8 before the first live v2 edition?
4. Reset the tracker to 0 for v2 Day 1?
5. Grant auto-publish for later v2 editions once the gate is 15/15 (Edition 10
   tomorrow 16 Nov 08:00 still runs on v1 regardless; earliest v2 edition
   would be Edition 11 on 17 Nov, only if the fixes land and he approves)?
6. Flip the daily cron to v2?

Code pointers for whoever implements after approval: `longest_counts()` in
`publish_v2.py:146-176` already computes all four counts — check 8 just needs
to use the excluding-all-equal count instead of the worded count.

## DECIDED — 2026-11-15 21:10, Rudro: "teach them / other thing do yourself"

Rudro approved fixes 1–3 above and delegated the rest. All six are now
decided; the cron flip itself is NOT executed (instructions written for
the parent in `CRON_INSTRUCTIONS_V2.md`).

### Fix 1 — check 12 (number-token): DONE, verified

`publish_v2.py` `number_token_missing_checkdata()` now normalises the
EN summary's Bangla digits to Latin (the same `LATIN_DIGITS`
translation the BN side already used) before token extraction.
`check_data.py` (v1-frozen) untouched. Result on the 15 Nov dry-run:
check 12 PASS, 0 misses (CA09 '১৪', CA10 '৫৬০' now match).

### Fix 2 — check 8 (longest-correct definition): DONE, verified

The gate verdict uses the **"excl"** count from `longest_counts()`:
correct option longest-or-tied, excluding questions where all four
options tie in length. Definition recorded in `CONTRACTS.md` (check 8)
+ `rules/RULES.md` (gate summary) + this file. Result on the 15 Nov
dry-run: check 8 PASS, excl 7/25 (worded 14/25 / first-max 8/25 /
strict 7/25 still reported in the check detail for reference).

### Fix 3 — Step 8 unit flaw: DONE, verified end-to-end

Root cause: when the correct option was numeric, only it carried a
unit ("6.53 %" vs "5.9 / 7.2 / 8.2"), making it the unique longest
in 6 of the 7 unique-longest hits. `_build_mcq()` in
`step8_questions.py` now appends the fact's unit to ALL numeric
distractors (correct value and correct answer unchanged); `_fmt_number()`
now preserves the key's decimal places (a 2-decimal key like '6.53' no
longer gets 1-decimal distractors like '5.9'). Regression test
`test_step8_unit_fix` in `tests/test_step789.py` (28 checks: the six
live patterns '6.53 %', '126.35 million', '41 %', '1 billion',
'৫৬০ কোটি', '800 km' + 4 `_fmt_number` checks).
Proof: 15 Nov MCQs regenerated in `runs/_scratch-unit-fix/`
(327 Q&A, 129 MCQ, 2 analytical — identical counts and MCQ ids/order
to the original; 38 raw MCQs changed options, all correct answers
unchanged), re-converted to `app-format-fixed` staging, gate **15/15
with check 8 excl 1/25** (only Q12, the phrases question, remains).
Unique-longest 7 → 1 proven. Converted MCQs: same 25 questions/order/
correct letters; only Q13 ('6.53 %'), Q14 ('126.35 million'), Q15
('41 %'), Q17 ('1 billion'), Q20 ('৫৬০ কোটি'), Q21 ('800 km') changed.

### Gate after all three fixes: 15/15

`publish_v2.py --check` on the 15 Nov dry-run: **15/15, exit 0**
(check 8 excl 7/25, check 12 0 misses). Re-run after the verdict-text
fix (Edition 10 → Edition 11): still 15/15.

### Delegated decision (a) — tracker reset: DECIDED + IMPLEMENTED

Reset to 0 at the FIRST v2 edition. Edition 11 (17 Nov) = v2 Day 1.
Implemented in `publish_v2.py` (`_v2_run_counter`): `--publish` sets
`correct_consecutive_editions` to 1 at the first v2 edition (detected
by "no existing index entry whose review starts with 'v2 gate'") and
+1 per later v2 edition, rewriting `correct_rule` for the v2 gate in
BOTH index.json files; the entry review text says "First v2 edition
(v2 Day 1). Tracker reset to 0 at this edition" (later editions:
"Correct v2 edition N in a row"). Rows go to the NEW v2 tracker
`engine-v2/runs/tracker.md` (starts 0/7), never to the v1 tracker.
The v1 tracker and the live index are NOT touched now — the v1 run
is 7/7 and Edition 10 on v1 (16 Nov) may make it 8. `tracker.db`
recording stays manual (`db.py` cannot read v2 files).

### Delegated decision (b) — auto-publish grant: DECIDED, for LATER v2 editions only (SUPERSEDED 2026-11-15 23:31 — now covers Edition 11 too; see Addendum at the end)

Gate 15/15, approval reviewer "auto-15/15 (Rudro's rule 2026-11-15)".
The FIRST v2 edition (Edition 11) stays human-gated even at 15/15 —
that rule stands and is NOT delegated away. Recorded in
`CONTRACTS.md` (gate status paragraph), `rules/RULES.md`
(first-edition rule), `publish_v2.py` verdict text, `SWITCH_PLAN.md`.

### Delegated decision (c) — cron flip: DECIDED, NOT executed

The daily cron runs v1 on 16 Nov (Edition 10) and v2 from 17 Nov
(Edition 11). Exact replacement cron instructions are written in
`CRON_INSTRUCTIONS_V2.md` for the parent to apply. This agent did
NOT edit the cron, did NOT publish, sync, or reset anything live.

### Stale references fixed in the same pass

- `CONTRACTS.md`: gate status line (first v2 edition Edition 11, not
  10), check 8 + check 12 definitions, auto-publish grant paragraph,
  coverage example re-dated to Edition 11, step5-file requirement
  marked done (file exists since the 15 Nov dry-run).
- `rules/RULES.md`: gate summary (longest-correct definition) +
  first-edition rule (Edition 11, auto-publish granted for later).
- `publish_v2.py` verdict text: "Edition 10" → "Edition 11".
- `run_v2_daily.py`: docstring tracker paragraph + Edition 11
  fallback line.
- `SWITCH_PLAN.md`: status addendum at the top + the three
  operationally load-bearing "Edition 10" lines (preconditions,
  human-gate rule, tracker quote) moved to Edition 11.

### Addendum 2026-11-15 23:31 — Edition 11 auto-publishes too

Rudro tapped "Let Edition 11 auto-publish too": the first-edition human
gate is removed. The auto-publish grant now covers ALL v2 editions from
Edition 11 onward (gate 15/15, reviewer "auto-15/15 (Rudro's rule
2026-11-15)"). Updated: `CRON_INSTRUCTIONS_V2.md` (decision b + cron
body), `publish_v2.py` verdict text, `CONTRACTS.md` grant +
first-edition rule, `rules/RULES.md`, `SWITCH_PLAN.md` (top addendum +
§4). The tracker reset at Edition 11 (v2 Day 1, count 1) is unchanged.
The orchestrator (`run_v2_daily.py`) still stops at the human gate after
the gate — it never publishes on its own; auto-publish is the cron's
separate step (write approval file + `publish_v2.py --publish`). The
Edition 7 lesson (checks verify form, not content) still stands as a
warning in the run report.
