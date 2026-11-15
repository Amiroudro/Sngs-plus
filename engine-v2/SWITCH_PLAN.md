# Sarangsho Plus — Switch Plan: v1 → v2 (Edition 11, 2026-11-17)

> **STATUS UPDATE — 2026-11-15 evening (Rudro, "teach them / other
> thing do yourself").** The target moved: **Edition 10 (16 Nov)
> stays on v1; the first v2 edition is Edition 11, Tuesday
> 2026-11-17, 08:00 Asia/Dhaka.** Where this plan says "Edition 10"
> as the first v2 edition, read "Edition 11". The rest of the plan
> still applies. The three gate blockers are fixed (check 12
> Bangla-digit normalisation, check 8 "excl" definition, Step 8 unit
> fix) and the 15 Nov dry-run gates **15/15**; `publish_v2.py` +
> `run_v2_daily.py` exist and are tested. Delegated decisions now
> recorded (see `GATE_DECISIONS_2026-11-15.md` +
> `CRON_INSTRUCTIONS_V2.md`): tracker resets to 0 at the first v2
> edition (Edition 11 = v2 Day 1, implemented in `publish_v2.py`
> `_v2_run_counter`); auto-publish granted for ALL v2 editions
> from Edition 11 onward (gate 15/15, reviewer "auto-15/15
> (Rudro's rule 2026-11-15)") — the first-edition human gate was
> removed by Rudro 2026-11-15 23:31. The cron
> is STILL NOT flipped — the parent applies
> `CRON_INSTRUCTIONS_V2.md`.

**Status:** plan only, written 2026-11-15. **Nothing in this plan has been
executed.** The cron is NOT flipped, nothing is published or synced, and
`engine/` (v1) is FROZEN — do not touch it.

**Decision:** Rudro confirmed the switch 2026-11-15 17:17 ("Go on.
implement it"). Target: **Edition 11, Tuesday 2026-11-17, 08:00
Asia/Dhaka**, is the first v2 edition — *only if* the wiring proves out
before then. The v2 publish gate is defined in
`engine-v2/CONTRACTS.md` ("V2 publish gate", 15 checks); this plan
says how the daily run executes it.

**Preconditions before the cron is flipped** (all must be true; if any
is false on the morning of 17 Nov, Edition 11 runs on v1 — see §7
Fallback; Edition 10 on 16 Nov runs on v1 regardless):
1. The v2→app converter exists and has produced a converted
   `editions/data-<date>.json` from a v2 dry run that passes
   `tools/validate_editions.py` (converter is a separate worker's job).
2. `engine-v2/publish_v2.py --check` exists and implements the 15
   gate checks in CONTRACTS.md (gate script is a separate build job;
   this plan only defines it).
3. `run_v2.py` writes the persisted Step 5 report
   `runs/<date>/step5-<date>.json` the gate requires (CONTRACTS.md
   gate check 3 — no such file exists today).
4. The paste gap in §2 is resolved one way or the other (implement
   paste support in v2, or Rudro accepts paste is ignored on 16 Nov).
5. A full dry run of the §3 run order has been executed end-to-end on
   a test date and its gate report reviewed by a human.

## 1. The cron file (exact file, current body)

File:
`~/workspace/goals/sarangsho-plus-engine-and-reader/crons/daily/sarangsho-plus-daily-engine__daily@08:00:00.md`
— id `sarangsho-plus-daily-engine`, `schedule: kind daily, timezone
Asia/Dhaka, time 08:00:00`, `enabled: true`, owner
`goal:sarangsho-plus-engine-and-reader`.

Its current body (verified by reading the file 2026-11-15) runs v1:
step 1 checks `~/workspace/sarangsho-plus/engine/paste/paste-YYYY-MM-DD.md`;
step 2 runs `cd ~/workspace/sarangsho-plus/engine &&
python3 run_daily.py --date YYYY-MM-DD --bodies`; step 4 contains the
v1 AUTO-PUBLISH RULE (Rudro 2026-11-13 00:18: 17/17 + longest-correct
≤10/25 auto-publishes, reviewer `"auto-17/17"`); step 5 finishes the
edition (BN overlay, index + tracker, app copy); step 6 syncs via the
browser route to `Amiroudro/sarangsho-plus-editions`.

**The flip is an edit to that one file, and nothing else.** Replace
steps 2–5 with the v2 run order in §3, replace the v1 auto-publish
rule with the v2 gate + human-gate rule in §4, and keep the schedule
(`08:00 Asia/Dhaka`), the paste deadline (07:30, §2), the browser
sync route (§6) and the reporting step unchanged. Do NOT change the
cron's id, schedule, owner or delivery. Do NOT delete the v1 body —
keep it in the file as a commented "v1 fallback" block (or in
`SWITCH_PLAN.md` §7) so a fallback run can be executed from it
without reconstructing v1 from memory.

## 2. The paste-file answer — VERIFIED: v2 does NOT pick up paste today

**Finding (verified from source, not from memory).** The string
`paste` occurs in `engine-v2/` in exactly three places, none of them
code that reads a file:
- `engine-v2/CONTRACTS.md:12` — `found_via` enum includes `"paste"`;
- `engine-v2/CONTRACTS.md:26` — "`summary`: RSS description (≤600
  chars) or paste note";
- `engine-v2/step1_collect.py:5` — docstring "no manual paste needed".

There is **no `read_paste_file` in `engine-v2/step1_collect.py`, no
`engine-v2/paste/` directory, and `collect()` never opens a paste
file** (checked with `grep -rn "paste" engine-v2/`). The contract
promises a `paste` value that the collector cannot produce.

By contrast v1 does read paste: `tools/collector/collect.py:386-415`,
`read_paste_file(day)` opens `ENGINE/paste/paste-<day>.md`
(`~/workspace/sarangsho-plus/engine/paste/paste-YYYY-MM-DD.md`),
splits on `^## ` blocks, and takes `- URL:`, `- Source:`,
`- Published:`, `- Note:` lines, emitting articles with
`found_via: "paste"` and `summary` = note. The v1 format (runbook §1):

```markdown
## <headline>
- Source: <publication>
- URL: <direct article URL>
- Published: <YYYY-MM-DD>
- Note: <one line — why it matters / key figures>
```

**Exact paste step for the v2 run (once implemented):**
1. By **07:30 Asia/Dhaka** on the edition date, Rudro may (optional
   only, never required) write
   `~/workspace/sarangsho-plus/engine/paste/paste-2026-11-16.md` in
   the v1 format above. Same path, same format, same deadline as v1
   (cron step 1) — do not invent a new paste location.
2. The v2 Step 1 collector merges it exactly as v1 does (articles
   with `found_via: "paste"`, `summary` = Note, direct URL only —
   a pasted Google News redirect gets no body and is dropped at
   Step 4 like any other redirect).
3. The run report states `paste_file_found: true/false` and
   `paste_count` (v1's freshness report carries both fields).

**Gap to close before Edition 10 (small, copy-adapt — no v1 import,
per the v2 no-imports rule in CONTRACTS.md):** copy-adapt v1's
`read_paste_file` into `engine-v2/step1_collect.py`, call it from
`collect()`, and add a test (a paste file with one article appears
in `articles-<date>.json` with `found_via: "paste"`). **If that is
not done before 16 Nov 08:00, the honest position is: paste is
ignored for Edition 10 and Rudro must be told so before the run —
do NOT let him paste articles believing they will be included.**
Paste is optional-only in both engines (v1 proof 8 Nov: 407
articles with no paste file at all), so a missed paste implementation
does not block the edition — it only blocks Rudro's extra articles.

## 3. The new run script and run order (design — do not implement the flip here)

**Recommended: a new thin orchestrator, `engine-v2/run_v2_daily.py`,
not a flag on `run_v2.py`.** Reason: `run_v2.py` is the dry-run tool
("Nothing is published", `run_v2.py:1-13`); keeping it dry-run-only
means a dry run can never publish by accident. The orchestrator
imports `run_v2.run(date, fresh=True)` and then runs the
convert → gate → (approval) → publish → BN → index/tracker → sync
steps in order. (Alternative considered and rejected: adding
`--publish` to `run_v2.py` — one entry point, but it mixes a
dry-run tool with a publishing tool; the separate orchestrator is
safer and the cron calls exactly one command either way.)

**Cron command (replaces
`python3 run_daily.py --date YYYY-MM-DD --bodies`):**

```bash
cd ~/workspace/sarangsho-plus/engine-v2 && python3 run_v2_daily.py --date YYYY-MM-DD
```

`--date` defaults to today (Asia/Dhaka) if omitted; the orchestrator
always collects fresh (`fresh=True` — never reuse a stale
`articles-<date>.json`, which is `run_v2.py`'s default when the file
already exists). There is no v1 `--bodies` equivalent: v2 fetches
bodies only for Step-3-kept articles inside `run_v2.py` Step 4
(`fetch_bodies_for_kept`). There is no Claude Project step in v2 at
all — Steps 4–10 are deterministic code, which is the whole point
of the rebuild (no pack, no `--author`, no import step).

**Run order (each step stops the run on failure; nothing after a
failed step runs):**

| # | Step | Command / action | Output |
|---|---|---|---|
| 1 | Paste check | §2: read `engine/paste/paste-<date>.md` if present (07:30 deadline) | `paste_file_found`, `paste_count` in run report |
| 2 | v2 run (Steps 1–10) | `run_v2.run(date, fresh=True)` via `run_v2_daily.py` | `engine-v2/runs/<date>/edition-<date>.json`, `page-`, `questions-`, `srs-`, `vocab-<date>.json`, plus the new `step5-<date>.json` (gate check 3) |
| 3 | Convert to app format | Converter (separate worker): `edition-<date>.json` → `editions/data-<date>.json` (v1 app shape: `edition_date`, `edition_day`, `coverage`, `status`, `counts`, `stories`, `words`, `revision_words`, `phrases`, `mcqs`, `sources`) + copy to `app/assets/editions/data-<date>.json`. Selects the 25 MCQs from the ~114–118 raw MCQs, shuffles keys (see gate checks 8–9). | `editions/data-<date>.json` |
| 4 | Gate check | `python3 publish_v2.py --date <date> --check` (new script; reads v2 run outputs + converted file) | `engine-v2/runs/<date>/review-v2-<date>.json` (`N/15 passed` + longest-correct count + letter distribution) |
| 5 | Human gate — Edition 10 | **STOP. Rudro reviews.** Even at 15/15. See §4. | `engine-v2/runs/<date>/approval-<date>.json` (`approved: true/false`, reviewer, notes) written by Rudro |
| 6 | Publish (only with approval) | `python3 publish_v2.py --date <date> --publish` — copies converted file to `editions/` with `status: "published"`, sets `edition_day` from the date, flips the review file's status to `published` (v1 `publish.py --publish` does both of these; the v2 script must too — the Edition 8 tracker bug was exactly a review file left saying `draft`). XLSX/PDF exports: v1's `publish.py` exports both; whether Edition 10 needs them is an OPEN item for the converter worker (§8) — if they are not built, the run report must say so, not pretend they exist. | `editions/data-<date>.json` (published), `runs/<date>/published-<date>.json` |
| 7 | Bengali overlay | Build `app/assets/editions/bn-<date>.json` from the published converted EN file, same as v1 cron step 5a: stories dict (at least `headline`/`summary`/`why_it_matters`/`exam_facts`/`key_people`/`figures`), mcqs dict `"1"`–`"25"` (`question`/`options`/`explanation`), correct letters unchanged, authentic newspaper Bengali, Bangla digits, figures/dates/names/money EXACT. Validate: shape asserts + number-token check (gate check 12). **If the BN build fails, STOP: do not sync, report plainly.** | `app/assets/editions/bn-<date>.json` |
| 8 | Index + tracker (v2 terms) | (a) Update `editions/index.json` AND `app/assets/editions/index.json` identically: append the new entry (`edition_date`, `file`, `status: "published"`, `review` text, counts, `sources` = distinct story source URLs, `coverage` = the gate-verified label) and update `correct_consecutive_editions` per §8 (recommendation: reset — see below). (b) Update `runs/tracker.md` (row → Published, note "Correct v2 edition N/7"). (c) Tracker DB: **v1's `engine/db.py --record` CANNOT be reused unchanged** — it reads v1 run files (`articles-`, `events-`, `import-report-`, `review-` in `engine/runs/`, `db.py:36-66`) that a v2 run never produces. Either extend `db.py` with a v2-aware record path or record the v2 row by hand in `tracker.md` + a v2 note in `tracker.db`; decide before Edition 10 and write the choice here. | index.json ×2, tracker.md, tracker.db |
| 9 | Sync | Browser route, same as v1 (cron step 6): browser task signed in as Amiroudro uploads the 3 changed files (`editions/data-<date>.json`, `app/assets/editions/bn-<date>.json`, `editions/index.json`) to `editions/` in `Amiroudro/sarangsho-plus-editions` via the GitHub web UI, commit `Sarangsho Plus Edition 10 (2026-11-16) sync`, watch the Actions pages-build run, verify the live index serves the new edition (200, correct count, correct_consecutive). Do NOT use `push_editions.py` in the run (connector push needs a fresh approval card each write). A failed sync NEVER blocks the local publish: the edition stays published locally and sync is retried when Rudro is present. | Live index verified |
| 10 | Report | Report to Rudro in the Sarangsho Plus side chat: collected/keep/maybe/reject, page items, vocab, gate result `N/15` + longest-correct count, whether it published or stopped at the gate, live-site verification, links to run outputs, what is missing, what he needs to do. | Run report |

**Coverage label (gate check 11, in the converter's hands):** v2 has
no coverage function (`engine-v2/common.py` contains no coverage
code). The converter must write `coverage` into the converted file
using the v1 formula (`engine/common.py:57-64`, `coverage_label`):
previous day 07:47 Dhaka → today 07:47 Dhaka. For Edition 10:
`"15 Nov 2026, 7:47 AM to 2026-11-16, 7:47 AM (Asia/Dhaka)"`.
The gate verifies the string exactly; the index entry must match it
character for character.

## 4. The v2 gate in the cron (replaces the v1 auto-publish rule)

The v1 rule (cron step 4, Rudro 2026-11-13 00:18) — 17/17 + longest-
correct ≤10/25 auto-publishes with reviewer `"auto-17/17"` — **does
not transfer to v2**. It was scoped to v1's 17-check list, and v2's
gate is a different 15-check list (CONTRACTS.md). The new cron text
must say:

- Run `publish_v2.py --check`. If it is below 15/15 OR longest-
  correct is above 10/25, STOP at the human gate: do not publish,
  report the failing checks / count to Rudro.
- **Edition 11 auto-publishes on 15/15 like every later v2 edition.**
  (First-edition human gate removed by Rudro 2026-11-15 23:31.)
  The Edition 7 lesson still stands: spot-check MCQs against
  sources when reviewing an auto-published edition.
- Auto-publish under the v2 gate was GRANTED by Rudro 2026-11-15
  ("other thing do yourself"; extended to Edition 11 on 2026-11-15
  23:31): gate 15/15, reviewer "auto-15/15 (Rudro's rule
  2026-11-15)". Until the cron is flipped per
  `CRON_INSTRUCTIONS_V2.md`, every v2 edition still stops at the
  human gate.
- Never invent stories, words, MCQs, figures or source URLs. If
  collection yields too little real news for a full edition, say so
  honestly and ship the draft short (≥12 items only) or not at all —
  do not auto-publish a short draft.

## 5. Resolver §2b — VERIFIED: not a routine v2 step; exception-only rescue

**Finding (verified from `step1_collect.py`).** v2 still *calls* the
Google News route (`collect_googlenews`, `step1_collect.py:495-505`,
`GN_QUERIES` — the same 9 queries as v1), BUT:
- `news.google.com/robots.txt` disallows `/rss/` for generic
  crawlers, and `_fetch_route` checks `robots_allowed` before ANY
  fetch (`step1_collect.py`, docstring lines 17–20 and `_fetch_route`).
  A strict robots check therefore records the Google News route dead
  rather than fetching it. (Caveat: on a robots.txt *fetch failure*
  the helper fails open and allows the fetch — so the route can
  still yield items occasionally; the gate does not rely on it being
  dead.)
- Even when Google News items DO arrive, they cannot reach the page:
  `pick_main` prefers a direct publisher URL over a redirect within
  the same tier (`step1_collect.py: pick_main` key), and
  `fetch_bodies_for_kept` gives Google News redirects `body_error
  "no direct URL"` — `run_v2.py` Step 4 then drops no-body items
  (25 dropped on 15 Nov). Gate check 5 also forbids any
  `news.google.com` source URL on the page.

**Answer: the v2 run does NOT need the §2b `resolve.py` step as a
routine step.** Do not run it on every edition, and do not wire it
into `run_v2.py` (v1 deliberately left it unwired for the same reason).

**The remaining case — Bing aggregator-only links — is real, and
§2b is the rescue for it.** Bing News RSS unwraps its `url=`
parameter to a direct publisher URL, but Bing can return a
syndication instead of the original (v1's known miss: Reuters LNG
surfaced only as the MSN syndication; `resolve.py`'s
`KNOWN_PUBLISHERS` deliberately excludes aggregators). v2 maps
`msn.com` to source `"MSN"` (`step1_collect.py:243-244`), and an
MSN-only story in a cluster with no publisher copy could become the
main (tier 2, but unopposed) and reach the page with a fetchable
body. Gate check 5 forbids aggregator-only sourcing. So the rule is:

- If a kept story that matters is aggregator-only (MSN or similar),
  run the resolver exactly as v1 §2b, by hand, on that story only:
  ```bash
  python3 ../tools/collector/resolve.py --title "<headline>" --source "<publication>" --date YYYY-MM-DD
  ```
  Exit 0 prints a verified direct publisher URL (page fetched,
  title shares ≥4 distinctive tokens with the headline, body
  ≥500 chars); substitute that URL as the story's source. Exit 1
  means not resolved and the story stays dropped — never substitute
  an aggregator URL or invent a slug. Routes: TBS sitemap slug
  match, then Bing News RSS (keyword query first, then full
  headline). Known misses carry over: Reuters originals, BSS (403).
- If no kept story is aggregator-only, §2b does not run at all that
  day, and the run report says so in one line.

## 6. Sync step

Unchanged from v1 (cron step 6, §3 step 9 above): browser route,
3 files, verify the live index. The v2 edition is a normal
`editions/data-<date>.json` + `bn-<date>.json` + `index.json` by the
time sync runs, so sync needs no v2-specific change — *provided the
converter output is byte-compatible with the v1 app shape*, which is
the converter worker's contract to meet. If the converter changes
the app shape, the app must be updated first and this plan must be
revised; do not sync a shape the app cannot read.

## 7. Fallback — exact conditions and how to switch back

**Fallback means: that day's edition runs on v1 instead of v2.**
The v1 engine, cron body (kept as a fallback block, §1) and runbook
are untouched, so a fallback is a real option, not a rebuild.

**Trigger conditions (any one triggers the fallback decision):**
1. The v2 run crashes, or `stats.collected < 10`, or page items
   `< 12` after Step 7 (thin day below the gate floor).
2. The converter fails (crash, or output fails
   `tools/validate_editions.py`) — no converted file, no gate.
3. The gate fails (below 15/15, or longest-correct > 10/25) AND the
   failure is not fixable by a re-run of the same inputs within the
   morning (e.g. a converter bug, a Step 5 systemic failure).
4. The BN overlay build fails and cannot be fixed in the morning.
5. Any precondition in the header of this plan is false on the
   morning of 16 Nov.

**Fallback is NOT triggered by:** a sync failure (local publish
stands, retry sync later — v1 rule); an empty editorial slot with a
recorded reason (gate check 13 passes); a thin-but-≥12 page.

**How to switch back (one day only):**
1. Decide by **10:00 Asia/Dhaka** at the latest — the v1 path still
   needs its Claude Project pack step and review, and the v1 runbook
   aims to publish before noon. A fallback decided after 10:00
   risks no edition at all that day; if it is after 10:00, prefer
   shipping nothing and saying so over rushing v1.
2. Run the v1 day exactly as the (preserved) v1 cron body says:
   `cd ~/workspace/sarangsho-plus/engine &&
   python3 run_daily.py --date YYYY-MM-DD --bodies`, Claude pack,
   `summarise_exam.py --import-pack`, `publish.py --check` (v1 17/17
   rule — the v1 auto-publish grant still applies to a v1 edition),
   BN, index, tracker, browser sync.
3. Report plainly: which v2 step failed, what the v1 edition is,
   and that the v2 switch is retried the next day unless Rudro
   says otherwise.
4. **A fallback day does not flip the cron back.** The cron stays
   v2; the next day runs v2 again. A permanent return to v1 needs
   Rudro's explicit call, not an operator decision.
5. If v2 fails AND the v1 fallback also fails, ship nothing that
   day. Report the failure plainly. Never pad, never invent.

**Edition numbering on a fallback day:** the day's edition is still
"Edition 10" (the 10th daily edition, 16 Nov) — but it is a v1
edition, and it does NOT count toward the v2 tracker (§8). The next
successful v2 edition is the first v2 edition, whatever its date.

## 8. What happens to the v1 7/7 tracker — RECOMMENDATION: reset, new v2 run

**Verified current state.** `editions/index.json` (read 2026-11-15):
`correct_consecutive_editions: 7`, `correct_rule: "An edition counts
as correct only if published after passing the full review checklist
with no failures (17 checks since the 2026-11-11 audit fixes; 12
checks before). … Editions 9-15 Nov 2026 each passed 17/17 and are
published, so the run is 7."` The 7-run is Editions 9–15 Nov
(9, 10, 11, 12, 13, 14, 15 Nov), each 17/17. `engine/db.py --status`
counts the same way (published + `review_passed == review_total`).

**Recommendation: RESET `correct_consecutive_editions` to 0 on the
switch, and start a new v2 run with Edition 10 as v2 Day 1.**
- **Why:** the 7/7 was a proof of the *v1 pipeline* under the *v1
  17-check list*. A v2 edition passes a different 15-check gate
  (different checks, different counts, different engine, different
  MCQ selection). Keeping the count running would claim "8/7" for an
  edition that never passed the checklist the 7 was counted under —
  that is the same category of dishonesty as the stale coverage line
  and the Edition 8 tracker bug. The honest tracker statement is:
  "v1 proof complete: 7/7 (9–15 Nov, 17/17 each). v2 proof starts
  Edition 11 (17 Nov): 0/7 under the v2 gate."
- **How:** on the first v2 publish, set
  `correct_consecutive_editions` to 1 (that edition), and rewrite
  `correct_rule` to name the v2 gate explicitly, e.g.: "An edition
  counts as correct only if published after passing the full v2
  publish gate with no failures (15 checks, CONTRACTS.md 'V2 publish
  gate'). The v1 run (Editions 9–15 Nov 2026, 17/17 each, 7/7) is
  complete and recorded in runs/tracker.md; it does not carry into
  the v2 count. Target: 7 correct consecutive v2 editions before any
  charge (ENGINE_DESIGN §10)." Keep the v1 7/7 in `runs/tracker.md`
  notes and in the `correct_rule` history text — reset the number,
  do not erase the record.
- **Alternative considered and rejected:** keep counting (Edition 10
  would read "8/7"). Rejected: it mixes two different checklists
  into one number and would overstate the proof on the day the
  pipeline changed. Also rejected: freezing the tracker at 7
  forever — the target (7 correct before charging) must be
  re-proven for the pipeline that will actually serve readers.
- **If Edition 10 runs on v1 (fallback, §7):** the v1 edition
  counts under the v1 rule (it would be an 8th consecutive v1
  correct edition), but the v2 count stays 0 until the first v2
  edition publishes. Say which count moved in the run report.

## 9. Edition 10 timeline (Mon 2026-11-16, Asia/Dhaka)

- **07:30** — paste deadline (§2). No paste file = normal run.
- **08:00** — cron fires; `run_v2_daily.py` (§3 steps 1–4).
  Expected wall time ~6 min for the v2 run (5m32s on 15 Nov) +
  converter + gate.
- **~08:15** — gate report ready. **STOP at the human gate.**
  Rudro reviews the converted edition.
- **Before noon** — Rudro approves (or requests corrections);
  publish → BN → index/tracker → browser sync → report.
- If the gate fails or the converter fails, the fallback decision
  is made by **10:00** (§7).

## 10. What still needs Rudro's call

1. **Auto-publish grant for later v2 editions (separate).** The gate
   defines the checks; it does not grant auto-publish. Edition 10
   is human-gated regardless. If Rudro later grants auto-publish
   under the v2 gate (15/15 + longest-correct ≤10/25), record it
   with a date, the same way the v1 grant was recorded
   (2026-11-13 00:18), and update the cron — do not assume it.
2. **Tracker reset (§8).** Recommendation is reset to a new v2 run;
   if Rudro would rather keep counting, he must say so explicitly
   — the default in this plan is reset, because keeping the count
   would misstate what was proven.
3. **Paste on 16 Nov (§2).** If paste support is not implemented in
   v2 before the run, Rudro should know his pasted articles will
   be ignored that day.
4. **The open items in §3 step 6 (XLSX/PDF exports) and §3 step 8c
   (tracker.db v2 recording)** — operator decisions, but Rudro
   should see them in the run report if they change what he
   receives.

## 11. Sources for every factual claim in this plan

- Cron file + v1 auto-publish rule: `goals/sarangsho-plus-engine-and-reader/crons/daily/sarangsho-plus-daily-engine__daily@08:00:00.md`
  (steps 1, 2, 4, 5, 6 quoted in §1).
- v1 run order + thin-day rule + resolver §2b: `engine/PHASE2_RUNBOOK.md`
  (§§1, 1b, 2, 2b, 4, 5, 6); v1 counts floor `MIN_STORIES = 12`,
  `engine/publish.py:38`; v1 checklist 17 checks,
  `engine/publish.py: checklist()`.
- v2 pipeline + outputs: `engine-v2/run_v2.py` (Steps 1–10, dry-run
  only); `engine-v2/CONTRACTS.md` (contracts + V2 publish gate).
- v2 collector routes, Google News robots note, paste absence:
  `engine-v2/step1_collect.py` (docstring lines 1–60,
  `collect_googlenews` 495–505, `pick_main`, `fetch_bodies_for_kept`,
  `resolve_slug_titles`); `grep -rn "paste" engine-v2/` (3 hits,
  all non-code).
- v1 paste implementation: `tools/collector/collect.py:386-415`.
- Resolver: `tools/collector/resolve.py` (verified-candidate rule:
  title overlap ≥4, body ≥500 chars; `KNOWN_PUBLISHERS` excludes
  aggregators); `tools/collector/README.md` (§ "Resolving a
  Google-News-only story").
- Longest-correct + letter balance definitions:
  `tools/validate_editions.py:115-120` (`longest_letter`),
  `:424` (letter distribution 5–8 each); raw v2 keys all `ক`,
  `engine-v2/step8_questions.py:383`, verified on
  `engine-v2/runs/2026-11-15/questions-2026-11-15.json` (118 MCQs).
- Coverage label: `engine/common.py:45-64`
  (`coverage_start` / `coverage_label`); v2 has no coverage code
  (`grep coverage engine-v2/common.py` — no hits).
- BN shape + number-token check: `app/assets/editions/bn-2026-11-15.json`
  (stories dict, mcqs `"1"`–`"25"`); `engine/runs/2026-11-11/build_bn.py:187-204`.
- Tracker state: `editions/index.json`
  (`correct_consecutive_editions: 7`, `correct_rule` quoted in §8);
  `engine/db.py:36-66` (`--record` reads v1 run files).
- Latest v2 state + known gaps: `engine-v2/runs/TEST_REPORT_2026-11-15-slugfix.md`
  (810 collected, 87 keep / 196 maybe / 494 reject, 60 final, 15 page,
  0/15 slug headlines, 343 Q&A / 118 MCQ / 2 analytical, 461 SRS,
  vocab 20/10/5 no shortfall, editorial filled; remaining gaps:
  8 slug non-mains, TBS Crawl-delay: 10 not honoured, Step 6 Bangla
  still telegraphic, SCI skew).

## 12. Hard constraints honoured

- `engine/` (v1) untouched. Cron not flipped. Nothing published
  or synced. No BD-EDU re-added (v2 topics remain the 10 in
  `rules/RULES.md`; this plan adds no topic). Decider rubric
  unchanged (the mislabel fixes are a separate worker's job; this
  plan duplicates none of them).
