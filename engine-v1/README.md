# Sarangsho Plus — Phase 2 Daily Engine

Approved design: `~/workspace/sarangsho-plus/ENGINE_DESIGN.md` v1.0.
Phase 2 = run Modules 1–6 for a new day end-to-end, with the human
review gate. Target: **7 correct consecutive editions** before any
charge (design §10). This is day 1 of 7.

## Modules (files)

| Step | File | What it does |
|---|---|---|
| 1 Collect | `tools/collector/collect.py` (Sarangsho Plus Collector) | Bing News RSS (direct URLs) + Google News RSS (discovery) + Prothom Alo feed + editorial Bing routes (one path-qualified `site:` query per paper, tagged `editorial`). Fully automated, free, no paste needed; paste file is optional only. Freshness report per route. `--bodies` fetches article text from direct URLs. `collect.py --check` = freshness only; `--sources` = route list. Old `engine/collect.py` is superseded (kept for reproducibility of the 8 Nov proof run). |
| 2 Clean | `clean_rank.py` | Event grouping (same event in several papers = one story; figure-token matching + merge pass + outlet-suffix stripping). Boilerplate stripping of fetched bodies (`common.strip_boilerplate`) — raw body text is never scored. |
| 3 Rank | `clean_rank.py` | 0–100, public weights: Bangladesh 30, importance 25, exam 25, novelty 10, credibility 10; penalties −10/−5/−20. Scores on title + RSS description + cleaned body; graded keyword counting (5/distinct hit, cap 25); tie-break (-score, -n_sources, -credibility, title). Hard skips (sport/entertainment/crime/accident/village fight/matrimonial) are recorded skips. 1 reserved editorial slot (score >=60 + exam_answerable, may stay empty). Quality floor 40 — thin day stays thin. Top ~15 kept; rest → borderline list |
| 4 Summarise | `summarise_exam.py --prompt` | Generates the Claude Project prompt + pack template from the ranked events. Rules revised 2026-11-11: description + cleaned body to ~6,000 chars; mandatory causal-chain structure (lead + headline number → cause → numbers → consequence → exam hook); exam_facts must add >=2 new facts; attribution for opinion sources; no body → no summary; no Google-News-only story. |
| 5 Exam-Generate | `summarise_exam.py --import-pack` | Validates a reviewed pack (JSON) and assembles the draft edition: word de-duplication vs all previous editions, SRS revision (1-3-7-14-30-60), MCQ traceability, plus the Fix 3 import checks (Google-News-only, no readable text, attribution, exam_facts add new facts, editorial-slot category). `--author agent|claude` records who wrote the pack. |
| 6 Publish | `publish.py` | `--check` review checklist (17 checks since 2026-11-11: 12 form + 5 content, incl. 2 manual spot-checks); `--publish` only after a human approval file exists. Exports 6-sheet XLSX + A4 PDF |
| Track | `db.py` | SQLite tracker (`tracker.db`): counts per stage, review result, status, pack authorship in notes |

`common.py` holds the source list, date helpers, previous-edition index
and word de-duplication. `run_daily.py` runs steps 1–3 + the prompt,
then **stops at the human gate**. Nothing here auto-publishes.

## The daily flow (see PHASE2_RUNBOOK.md for the full version)

```
python3 run_daily.py --date YYYY-MM-DD --bodies
# paste claude-prompt-<date>.md into the Claude Project, save the JSON reply as
# runs/<date>/reviewed-pack-<date>.json
python3 summarise_exam.py --date YYYY-MM-DD --import-pack runs/<date>/reviewed-pack-<date>.json
python3 publish.py --date YYYY-MM-DD --check
# Rudro writes runs/<date>/approval-<date>.json (approved: true/false)
python3 publish.py --date YYYY-MM-DD --publish
python3 db.py --record runs/<date>
```

## Honest limits (proven by the 8 Nov proof run + the Collector verification, 2026-11-07)

- **Collection is now fully automated — paste is optional.** The
  Sarangsho Plus Collector (`tools/collector/`) uses Bing News RSS
  (direct publisher URLs), Google News RSS (discovery; its links are
  opaque redirects and no body can be fetched from them — verified),
  and Prothom Alo English /feed (fresh, direct). Verified 2026-11-07:
  19 fresh routes; a no-paste run collected 407 unique articles for
  7 Nov; 319–321 for 8 Nov. Dropped as stale/blocked: TBS RSS (2021),
  Daily Star RSS (Jun 2026), Dhaka Tribune /feed (404), New Age
  (403), Observer (unreachable), BSS (403). FE sitemap and Daily Star
  sitemap index are flaky from this VM and not relied on. Full table:
  `tools/collector/ROUTES.md`.
- **Bodies fetch for about half of direct URLs** (36/69 on 8 Nov).
  Bot protection (403 / connection resets) blocks the rest — recorded
  with a body error, never invented. Summarise works from title +
  source + description + body where available.
- **Prothom Alo's feed is a rolling top-10.** Stories drop off it
  within hours. The Collector's other routes cover for it.
- **No paid API, no key.** The AI brain is Rudro's Claude Project
  (free). `run_daily.py` never calls an API. Sarangsho's API is never
  used.
- **Never invent.** Collect drops stale items, Rank penalises
  single-source/press-release/outdated items, Import rejects source
  URLs that were not collected, and Publish blocks anything failing
  the checklist. If collection yields too little for a full
  15/20/10/25 edition, the draft ships short and says so — see the
  8 Nov proof run (14/15 stories).

## Bugs found and fixed during the proof run

1. No recency filter — Feb–Jun 2026 and 2021 RSS items were ranked
   in. Fixed: Collect drops items published >2 days before run date.
2. Substring sport filter — "Awami League" matched "league" and a
   police-attack story was filed as sport. Fixed: whole-word match
   and "league"/"runs" removed from the sport list.
3. `&apos;` entities in feed titles were not unescaped. Fixed.
4. FE sitemap items had slug-derived titles (invented headlines).
   Fixed: sitemap returns no articles, only a counted reading list.
5. Bing News RSS items had no `<source>` element — every item was
   attributed to "Bing News". Fixed (Collector): source derived from
   the direct URL's domain.
6. Google News RSS `<source url="...">Name</source>` was missed by
   the plain-tag grab — every item was attributed to "Google News".
   Fixed (Collector): explicit attribute-tolerant match.
7. Same event kept as 2–3 stories (World Bank $300m in three
   wordings). Fixed (clean_rank): figure-token matching
   ("$300 million" = "$300m" = "US$300mil"), an order-independent
   merge pass, and stripping the trailing outlet suffix from titles
   before keyword comparison. Verified: 8 Nov re-rank gives 1 World
   Bank event (9 sources, 9 articles) instead of 3.
8. Collector source names polluted by subdomains
   ("Today.Thefinancialexpress.Com.Bd"). Fixed: subdomain-aware
   domain matching.

## Layout

```
engine/
  collect.py  clean_rank.py  summarise_exam.py  publish.py
  db.py  run_daily.py  common.py
  paste/paste-YYYY-MM-DD.md      # OPTIONAL extra articles (never required)
  runs/YYYY-MM-DD/               # one folder per day (all artefacts)
  runs/tracker.md                # 7-day correctness tracker (human-readable)
  tracker.db                     # same, in SQLite
  README.md  PHASE2_RUNBOOK.md
tools/collector/
  collect.py  README.md  ROUTES.md   # Sarangsho Plus Collector (the collector)
editions/data-YYYY-MM-DD.json    # published editions only (none yet)
```
