# Sarangsho Plus — Phase 2 Runbook

How to run one day, end to end. Read this before the first real run.

## Daily schedule (SET — cron `sarangsho-plus-daily-engine`)

- **08:00 Asia/Dhaka, daily** — the engine runs automatically
  (`run_daily.py`, first run Sun 8 Nov 08:00). **No manual paste is
  needed.** Collection is fully automated by the Sarangsho Plus
  Collector (`tools/collector/collect.py`): Bing News RSS + Google
  News RSS + Prothom Alo English feed + editorial Bing routes for
  all five papers (added 2026-11-11, audit Fix 2) — all free, no API
  key. **AUTO-PUBLISH RULE (Rudro, 2026-11-13):** a draft that passes
  the full 17-check review AND has the correct answer longest-or-tied
  in at most 10 of 25 MCQs publishes itself (auto-approval recorded
  in `approval-YYYY-MM-DD.json`, reviewer "auto-17/17"); the run then
  builds the Bengali overlay, updates the index + tracker, and syncs
  to GitHub Pages via the browser route. Anything below 17/17, over
  10 longest-correct, or short of a full edition stops at the human
  review gate for Rudro. Honest limit: the 17 checks include proxy
  checks and manual spot-checks (5 lead figures, opinion attribution)
  that no longer get a human eye on auto-published editions.
- **Morning** — Claude Project step (Rudro pastes the prompt, saves
  the JSON pack) and the review/approval step. These two are the
  only manual steps left.
- **Before noon** — publish, if approved.

## 1. Collection is automatic (paste is optional only)

The Collector runs itself. If Rudro happens to read an article the
feeds missed, he *may* add it to `engine/paste/paste-YYYY-MM-DD.md`
— one block per article — but nothing breaks if he does not. The
8 Nov proof: a run with **no paste file at all collected 407 unique
articles**; the paste file added only 7 net-new articles out of 319.

```markdown
## <headline>
- Source: <publication>
- URL: <direct article URL>
- Published: <YYYY-MM-DD>
- Note: <one line — why it matters / key figures>
```

Paste **articles you actually read** — never paste a headline without
opening the article. The engine fetches body text itself
(`--bodies`); if a site blocks the fetch, that article is recorded
with a body error and its summary must come from the Note field or
from a second source.

Verified routes (full table: `tools/collector/ROUTES.md`):
- **Bing News RSS (primary)** — direct publisher URLs, extracted
  from the `url=` parameter. Queries: Bangladesh, economy, politics,
  bank, education/jobs, site: Daily Star / TBS / Dhaka Tribune /
  Financial Express / Prothom Alo.
- **Google News RSS (discovery)** — very fresh (79 items dated 7 Nov
  for "Bangladesh" alone) but links are opaque Google redirects and
  no body can be fetched from them (verified). Items keep their
  Google News link, which opens the real article in a browser.
- **Prothom Alo English /feed (primary)** — 10 items, all fresh,
  direct URLs, bodies fetchable.
- **Editorial Bing RSS (added 2026-11-11, audit Fix 2)** — one
  path-qualified `site:` query per paper (Daily Star `/opinion`,
  Prothom Alo `/opinion`, TBS `/thoughts`, FE `/editorial`, Dhaka
  Tribune `/opinion`), tagged `editorial`. Expected ~12–16 unique
  fresh opinion items/day (was 2–4). DT has no other working route
  from this VM (403 Cloudflare).
- **Dropped (verified):** TBS RSS (latest 2021), Daily Star RSS
  (latest Jun 2026), Dhaka Tribune /feed (404), New Age (403),
  Observer (unreachable), BSS (403). FE sitemap and Daily Star
  sitemap index are flaky from this VM and not relied on.
- **Never used:** Sarangsho's own API; any paid API.

## 1b. What the ranker does now (revised 2026-11-11, audit Fix 1)

Read this before trusting a kept list. The old ranker scored raw
body text (site navigation) with max-of-one keywords and broke
97-point ties alphabetically. The new ranker:
- Scores on **title + RSS description + cleaned body** (navigation
  stripped; raw body never scored). Bangladesh relevance comes from
  title/description (30) or cleaned body only (15).
- **Graded keyword counting:** 5 points per distinct keyword hit,
  capped at 25 per component. One incidental word scores 5, not 25.
- **Tie-break:** (-score, -n_sources, -credibility, title).
- **Hard skips are skips:** sport, entertainment/celebrity, crime,
  accidents, village fights, matrimonial ads — recorded in the
  borderline list, never silently dropped.
- **Selection test:** each event is marked `exam_answerable` (could
  it help answer a 45th–47th BCS written question?). Recorded in
  `events-<day>.json`.
- **Editorial slot:** 1 slot per edition for the best
  editorial/opinion/analysis with score >= 60 AND exam_answerable.
  No flat boost. The slot MAY STAY EMPTY on a thin day.
- **Thin day stays thin:** a quality floor (default 40) — events
  below it are never kept to fill the count of 15. 15 is the
  ceiling, not the floor. If the day yields 12 good stories, 12 is
  the edition. Skips are recorded with a reason in the borderline
  list so the same trivia does not resurface.

## 2. Run the engine (stops at the human gate)

```bash
cd ~/workspace/sarangsho-plus/engine
python3 run_daily.py --date YYYY-MM-DD --bodies
```

Or check collection alone first:

```bash
python3 ../tools/collector/collect.py --check --date YYYY-MM-DD
```

Check the printed counts. Expect: ~19 fresh routes, ~320 unique
articles in the 2-day window, ~250 events, 15 kept, the rest
borderline. Bodies fetch for roughly half of direct URLs (bot
protection blocks the rest — recorded, not hidden). If collection
yields <10 articles, read the freshness report — a feed may be
down — and do not pad the edition.

## 2b. Rescue a Google-News-only story (added 2026-11-14)

After ranking, if a kept or promoted-borderline story is
Google-News-only, do NOT drop it straight away — try the resolver
first. It is deliberately not wired into `run_daily.py`: run it
only on the handful of stories that matter, then add the verified
direct URL to the story's sources before the Claude prompt step.

```bash
python3 ../tools/collector/resolve.py --title "<Google News headline>" \
    --source "<publication>" --date YYYY-MM-DD
```

Exit 0 prints a verified direct publisher URL (page fetched, title
shares >=4 distinctive tokens with the headline, body >=500 chars);
exit 1 means not resolved and the story stays dropped — never
substitute an aggregator URL or invent a slug. Routes: TBS sitemap
slug match, then Bing News RSS (keyword query first, then full
headline). Verified live 2026-11-14: Islami Bank Tk6,000cr equity
injection -> TBS direct URL; paraquat ban -> who.int original.
Known misses: Reuters LNG (Bing surfaces only the MSN syndication)
and BSS stories (403 from this VM).

Coverage line (fixed 2026-11-14): `common.coverage_label(day)` now
returns the previous day 07:47 Dhaka as the window start, so
Edition 9 (15 Nov) will read "14 Nov 2026, 7:47 AM to 2026-11-15,
7:47 AM" instead of the stale "7 Nov 2026" start the 9–14 Nov data
files carried (8 Nov genuinely starts 7 Nov). The published
Edition 8 file itself still carries the stale line (index was
always correct); do not rewrite published history for it.

## 3. Claude Project step (the AI brain — free)

1. Open the Claude Project (the English-daily one, or a Sarangsho
   Plus project with the same instructions).
2. Paste `runs/<date>/claude-prompt-<date>.md` **and** the articles
   file `runs/<date>/articles-<date>.json` (or paste the article
   texts).
3. Claude returns a JSON pack. Save it exactly as
   `runs/<date>/reviewed-pack-<date>.json` (no extra prose).
4. Import it:

```bash
python3 summarise_exam.py --date YYYY-MM-DD --import-pack runs/YYYY-MM-DD/reviewed-pack-YYYY-MM-DD.json --author claude
# --author agent  if the operator wrote the pack acting as the Claude Project (see Fix 5 above)
```

The importer checks: every story source URL was actually collected;
words are not duplicates of any earlier edition; MCQ split is
10 vocab + 2 phrases + 13 current affairs; every MCQ traces to a
story in this edition. **New since 2026-11-11 (audit Fix 3):** no
Google-News-only story; every story must have readable source text
(a description or a fetched body) — title-only is rejected;
opinion-sourced stories must carry attribution; exam_facts must add
>=2 new facts beyond the summary; if the ranker reserved the
editorial slot, a story must carry category "Editorial & Opinion".
Problems are printed, not hidden. Fix the pack and re-import — never edit the draft JSON by hand to make a
check pass.

**Pack authorship (audit Fix 5) — record it every time.** Pass
`--author claude` when the pack came from Rudro's Claude Project as
designed, or `--author agent` when the operator wrote it acting as
the Claude Project. It is recorded in `import-report-<date>.json`
and in the tracker notes, and the RUN_REPORT must state the same in
one line ("Pack written by: Claude Project" / "Pack written by:
operator (agent), acting as the Claude Project"). Never leave it
`unknown` on a real run — the audit found no edition was ever
summarised by the Claude Project as designed, and the record must
say so honestly when that is the case.

## 4. Review (Rudro — the gate)

```bash
python3 publish.py --date YYYY-MM-DD --check
```

Read the draft (`runs/<date>/draft-<date>.json`, plus the draft
`.pdf` / `.xlsx` in the same folder) and the checklist
(`runs/<date>/review-<date>.json`). The checklist is now **17
checks** (audit Fix 4): the original 12 form checks, plus
13. every summary carries a figure (lead-figure proxy),
14. no Google-News-only story,
15. >=1 Editorial & Opinion story (or the slot empty by design),
16. exam_facts add >=2 new facts beyond the summary,
17. no opinion claim presented as fact.
Checks 13 and 17 are automated proxies PLUS a manual spot-check
the reviewer must do — the review JSON lists them under
`manual_spot_checks`:
- **13:** open the source of 5 stories; does each summary carry the
  article's LEAD figure (the 119%, not a side number)?
- **17:** open any story whose sources include an `/opinion/` or
  `/editorial/` URL; is every claim from it attributed?
Confirm both in the approval notes. A pass that skips them is not
a pass.

Check in particular:

- Every figure against its source article (open 2–3 at random).
- Every MCQ answer against its explanation and its source story.
  (This exact check caught the 7 Nov ChatGPT digest's first-render
  MCQ/key mismatch — it is the reason the gate exists.)
- No story that is really a repeat of yesterday's edition, unless
  it is a genuinely new development (flagged as follow-up).
- Bangla only where verified (words/phrases). No invented Bangla
  story summaries.
- **Thin day:** 12–15 stories passes the counts check. If the draft
  is short, say so in the report — do not pad it.

Then write `runs/<date>/approval-<date>.json`:

```json
{"approved": true, "reviewer": "Rudro", "date": "2026-11-08",
 "notes": "Checked MCQs 1-25 against key; figures in CA01/CA10 verified."}
```

Or `{"approved": false, "corrections": ["..."]}` — the engine will
refuse to publish and the corrections go back to step 3.

## 5. Publish

```bash
python3 publish.py --date YYYY-MM-DD --publish
python3 db.py --record runs/YYYY-MM-DD
```

Publish copies the edition to `editions/data-YYYY-MM-DD.json`
(status: published) and exports the XLSX + PDF. Then check the
tracker:

```bash
python3 db.py --status
```

**After publishing, push the editions to the public GitHub Pages
repo so the app fetches them automatically** (Rudro approved
automatic updates 2026-11-12; the app's default index URL is
https://amiroudro.github.io/sarangsho-plus-editions/editions/index.json):

```bash
python3 push_editions.py --message "Sarangsho Plus editions sync YYYY-MM-DD"
```

The script mirrors `editions/` (EN files + `index.json`) and the
Bengali overlays to `Amiroudro/sarangsho-plus-editions`. It never
blocks publishing: it always exits 0 and logs `PUSH OK` /
`PUSH FAILED` to `push_editions.log` — report that line, do not
retry silently, do not republish to fix a push. (The repo must
exist and be in the Muse GitHub App installation, and Pages must be
enabled on it — see `push_editions.py`. Until then the push fails
and the app keeps showing its bundled editions.)

## 6. The 7-day correctness tracker

`runs/tracker.md` (and `tracker.db`) record, per edition: date,
collected / events / kept / borderline, story-word-phrase-MCQ
counts, review pass/fail, status (draft/published), and notes.
**An edition counts as correct only if it was published after
passing the full checklist with no failures — now 17/17.**
Day 1 is 8 Nov 2026 (published, review 11/12 — short one story).
The count stands at **3/7** (Editions 3/4/5 of 9/10/11 Nov published
2026-11-12, each 17/17). Do not charge anyone before 7/7
(design §10). **Every RUN_REPORT must carry one line stating who
wrote the pack** (Claude Project, or operator acting as it — see
Fix 5 in section 3).

## 7. If something goes wrong

| Symptom | What to do |
|---|---|
| Collect finds <10 articles | Read the freshness report — a feed may be down. Optionally paste what you read (step 1). Do not pad the edition. |
| Import reports problems | Fix the pack, re-import. Do not hand-edit the draft. |
| Review fails on counts | Ship the draft short and say so (like 8 Nov), or add a real story. Never invent one. |
| A published edition has an error | Fix it, note the correction in the edition file, do not silently rewrite history (design §7 Learn). |
| Claude pack has duplicate words | Importer drops them to borderline automatically; the words list will be short — add new words from the articles. |
| Two kept stories look like the same event | Event grouping is title-based; same-topic different-angle stories can both be kept (e.g. garment wage protests vs an unrest analysis). Decide at review; the borderline list is the audit trail. |
