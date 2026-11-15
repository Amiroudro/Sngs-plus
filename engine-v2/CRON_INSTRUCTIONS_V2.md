# Sarangsho Plus — v2 cron instructions (for the parent to apply)

Written 2026-11-15 evening. **This file is instructions only — the cron
was NOT edited by this task.** The parent applies the update below with
`cron.update` (same job id `sarangsho-plus-daily-engine`).

## WHEN to apply

**After the 16 Nov 08:00 run has finished, and before 17 Nov 08:00.**
Edition 10 (16 Nov) must run on v1 under the OLD body. The new body
below makes the 17 Nov run (Edition 11) the first v2 edition. Do NOT
apply this before 16 Nov 08:00 — the 16 Nov run would switch to v2 a
day early.

## Decisions this body encodes (Rudro, 2026-11-15 21:10)

- (a) **Tracker reset to 0 at the first v2 edition.** Edition 11
  (17 Nov) = v2 Day 1. Implemented in `publish_v2.py`
  (`_v2_run_counter`): `--publish` sets
  `correct_consecutive_editions` to 1 at the first v2 edition and +1
  per later v2 edition, rewriting `correct_rule` for the v2 gate in
  BOTH index.json files. Rows go to the v2 tracker
  (`engine-v2/runs/tracker.md`), never to the v1 tracker. The run
  agent does NOT touch the counter by hand — the publish script does
  it. The v1 run closed at 7/7; do not touch the live index/tracker
  before Edition 11.
- (b) **Auto-publish grant for LATER v2 editions only.** Gate 15/15,
  approval reviewer `"auto-15/15 (Rudro's rule 2026-11-15)"`. The
  FIRST v2 edition (Edition 11) stays human-gated even at 15/15.
- (c) **Cron flip timed for Edition 11.** Daily 08:00 Asia/Dhaka,
  unchanged; delivery to the Sarangsho Plus side chat, unchanged.

## What changes vs the v1 body

- Engine command: `run_v2_daily.py` (engine-v2) instead of
  `run_daily.py` (engine/). The orchestrator runs paste check → v2
  run → convert → export → gate → STOP. It never syncs and never
  auto-publishes on its own.
- Gate: 15 checks (`publish_v2.py --check`), not 17. Longest-correct
  is the gate's check 8 ("excl" definition: unique longest,
  all-equal questions excluded, ≤10/25) — the run agent does NOT
  count it by hand from the draft JSON any more.
- No translation subagents: v2 writes native Bangla; the converter
  produces `bn-<date>.json` and gate check 12 validates it.
- Publish copies the staged data/bn/index files, sets the tracker
  count, appends the v2 tracker.md row, and writes
  `published-<date>.json` + `tracker-record-<date>.json`.
  `tracker.db` recording stays MANUAL (`db.py` cannot read v2 files)
  — the run report must say so.
- Sync (browser route) and reporting are otherwise unchanged.

## EXACT REPLACEMENT BODY (paste verbatim into cron.update)

> Sarangsho Plus daily engine run (v2, from Edition 11, 2026-11-17).
> Owner: Rudro. Goal: produce one new daily edition, working toward
> 7 correct consecutive v2 editions (the v1 run closed at 7/7 —
> TARGET REACHED, Editions 9–15 Nov 2026; the v2 count reset to 0 at
> the first v2 edition, Edition 11 = v2 Day 1).
>
> Each run, for today's date in Asia/Dhaka:
> 1. Check ~/workspace/sarangsho-plus/engine/paste/paste-YYYY-MM-DD.md
>    first — Rudro pastes important articles he read by 07:30. Use it
>    as the paste fallback; never invent articles.
> 2. Run the v2 engine: cd ~/workspace/sarangsho-plus/engine-v2 &&
>    python3 run_v2_daily.py --date YYYY-MM-DD
>    This runs paste check → v2 run (Steps 1–10) → convert to app
>    format (staging only) → export XLSX + PDF → gate → STOP. Exit 0
>    at 15/15 ("ready for review"); exit 1 below 15/15. It never
>    syncs and never publishes on its own. Follow
>    ~/workspace/sarangsho-plus/engine-v2/CONTRACTS.md (the 15-check
>    v2 gate), ~/workspace/sarangsho-plus/engine-v2/SWITCH_PLAN.md
>    and ~/workspace/sarangsho-plus/engine-v2/rules/RULES.md. Do NOT
>    call any paid API; there is no key. Do NOT touch engine/ (v1) —
>    it is FROZEN.
> 3. GATE + PUBLISH RULE (v2, Rudro's rules 2026-11-15). The gate is
>    python3 publish_v2.py --date YYYY-MM-DD --check → 15/15
>    (the orchestrator already ran it; the review file is
>    runs/YYYY-MM-DD/review-v2-YYYY-MM-DD.json). Longest-correct is
>    the gate's check 8 (unique longest, all-equal questions
>    excluded, ≤10/25) — do not count it by hand.
>    - FIRST v2 EDITION (Edition 11, 17 Nov 2026): even at 15/15,
>      STOP at the human gate. Do NOT write an approval file, do NOT
>      publish. Report to Rudro in the side chat with the gate result
>      (15/15 + the longest-correct excl count), the edition counts
>      and the PDF/XLSX links; he reviews the edition himself and
>      writes runs/YYYY-MM-DD/approval-YYYY-MM-DD.json (approved:
>      true, reviewer "Rudro") when he is satisfied.
>    - LATER v2 EDITIONS (Edition 12 onward): if the gate is 15/15,
>      publish automatically. To publish: write
>      runs/YYYY-MM-DD/approval-YYYY-MM-DD.json with approved:true,
>      reviewer "auto-15/15 (Rudro's rule 2026-11-15)", and notes
>      stating the auto-approval (15/15 + the longest-correct excl
>      count), then run python3 publish_v2.py --date YYYY-MM-DD
>      --publish. The publish step copies the staged data/bn files
>      to editions/ and app/assets/editions/, appends the index entry
>      to both index.json files, sets correct_consecutive_editions
>      (1 at the first v2 edition, +1 per later v2 edition) and
>      rewrites correct_rule for the v2 gate, appends the row to the
>      v2 tracker (engine-v2/runs/tracker.md), and writes
>      published-YYYY-MM-DD.json + tracker-record-YYYY-MM-DD.json.
>      tracker.db recording stays manual (db.py cannot read v2 run
>      files) — say so in the run report.
>    - If the gate is below 15/15, STOP at the human review gate: do
>      NOT publish, and report to Rudro in the side chat with the
>      failing checks / the longest-correct count and what he needs
>      to do (review, fix, approve). Never invent stories, words,
>      MCQs, figures or source URLs. If collection yields too little
>      real news for a full edition, say so honestly and ship the
>      draft short (and do not auto-publish a short draft — stop at
>      the gate).
>    - Honest limit of this rule: the 15 checks verify form, not
>      content against sources (the Edition 7 lesson — a wrong MCQ
>      auto-published once under the v1 rule) — say so in the run
>      report when an edition auto-publishes.
> 4. AFTER an edition is published in this run: verify the published
>    files before syncing — editions/data-YYYY-MM-DD.json and
>    app/assets/editions/bn-YYYY-MM-DD.json exist with status
>    "published", both index.json files carry the new entry AND the
>    updated correct_consecutive_editions, the v2 tracker.md has the
>    new row, and runs/YYYY-MM-DD/review-v2-YYYY-MM-DD.json says
>    status "published". (No translation subagents: v2 writes native
>    Bangla; the converter produced the bn file and gate check 12
>    validated it. If the BN file is missing or the gate's check 12
>    failed, the edition would not have published — do not sync,
>    report the failure plainly in the side chat.)
> 5. SYNC via the browser route (primary since 2026-11-13 — the
>    connector push asks Rudro for a fresh approval card on every
>    write, which is why he demanded this change; do NOT use
>    push_editions.py in this run): start a browser task signed in
>    as Amiroudro to upload the 3 changed files
>    (editions/data-YYYY-MM-DD.json,
>    app/assets/editions/bn-YYYY-MM-DD.json, editions/index.json)
>    to the editions/ folder of Amiroudro/sarangsho-plus-editions
>    via the GitHub web UI (Add file → Upload files), commit to
>    main with message "Sarangsho Plus Edition N (YYYY-MM-DD)
>    sync", then watch the Actions "pages build and deployment" run
>    and verify the live index
>    https://amiroudro.github.io/sarangsho-plus-editions/editions/index.json
>    serves the new edition (200, correct count,
>    correct_consecutive — expect 1 for Edition 11, the v2 run).
>    Note: run #1 (43097664534 attempt #2) is stuck "Queued" since
>    12 Nov and cannot be cancelled — it does NOT block new runs
>    (proven 12 Nov by run #2, which succeeded in seconds). If the
>    browser sync fails, do NOT fall back to the connector push
>    (Rudro is asleep and cannot tap the card); report the failure
>    plainly in the side chat and stop. A failed sync NEVER blocks
>    the local publish: the edition stays published locally and the
>    sync is retried the next time Rudro is present.
>    push_editions.py remains the fallback only when Rudro is
>    present and asks for it.
> 6. Report back to Rudro in this chat (the Sarangsho Plus side
>    chat) with: collected/keep/maybe/reject counts, edition counts
>    (stories/words/phrases/MCQs/revision), gate result (15/15) +
>    longest-correct excl count, whether it auto-published or stopped
>    at the gate, the live-site verification (index shows the new
>    edition or not), links to the draft PDF/XLSX and RUN_REPORT.md,
>    what is missing, and what he needs to do if it stopped at the
>    gate. If a run fails, report the failure plainly instead of
>    retrying silently.
> 7. If the v2 run itself fails (collection, decide, convert, or
>    gate crash) before 10:00 Asia/Dhaka, fall back to v1 for that
>    day: run the v1 engine per the old runbook
>    (~/workspace/sarangsho-plus/engine/PHASE2_RUNBOOK.md) and say
>    plainly in the side chat that the day fell back to v1 and why.
>    After 10:00, do not start a v1 fallback — report the failure
>    and stop. Do not edit ~/MEMORY.md in the run; observations go
>    to the daily log.

## cron.update parameters (everything else unchanged)

- id: `sarangsho-plus-daily-engine`
- title: `Sarangsho Plus daily engine run` (unchanged)
- schedule: daily, time `08:00:00`, timezone `Asia/Dhaka` (unchanged)
- delivery: Sarangsho Plus side chat `ea4c0dab-0963-4d7e-a116-c0eab84ddfc3`
  (unchanged)
- owner: `goal:sarangsho-plus-engine-and-reader` (unchanged)
- mode: `task`, enabled: `true` (unchanged)

## After applying

Verify with `cron.view sarangsho-plus-daily-engine` that the body is
the v2 body above and the next run is 17 Nov 08:00 Asia/Dhaka (the
16 Nov run must already have fired on v1 before this is applied).
