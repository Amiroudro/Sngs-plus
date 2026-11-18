# Sarangsho Plus Engine v2 — Source Registry

**Maintained registry, not a one-time list.** Last verified: **2026-11-15**
(probe with the engine's own fetcher; see `tools/check_routes.py` for
the weekly health check). "Fresh" = newest item within 2 days of the
probe. Level 1 = GPT's 50-source directory core (15 papers), adopted
2026-11-15 at Rudro's ask.

**How a paper is reached, in order:** RSS → news sitemap → plain
sitemap → section-page links → Bing News RSS `site:` query (the
discovery layer — how the engine actually reaches papers whose
direct routes are dead). **Google News RSS is OUT** (robots.txt
disallows `/rss/search`); the v2 collector never fetches it.
**Bing News RSS is the discovery layer** and is always kept.

**Status words:** `live` = a route returns fresh items; `stale` =
returns items but the newest is older than 2 days; `blocked` =
403 / 404 / connection closed / challenge page / SPA shell.
A blocked route stays blocked in this file — never silently retried,
never invented. When a route's status changes, update this file and
`tools/check_routes.py` together.

## Separate rights gate — do not confuse route health with permission

The route statuses below describe technical reachability only. They do
**not** authorize automated collection, page inspection or article-body
processing. The rights registry (`engine-v2/rights_registry.py`,
repo-only, not part of the working engine) holds 55 publisher records,
**0 enabled**. Bing News is an approved discovery host in this registry,
not a licence to process the publishers' content it finds.

Note (2026-11-18): the working engine-v2 in this repo does **not**
currently enforce the rights registry at collection time — the registry
is policy, not an operating control (see `phase0-audit-system-b.md`).
Do not report any publisher as an active v2 content source until its
permission evidence and enablement are recorded in the rights registry,
and do not claim the collector enforces it until the wiring exists.

## Level 1 — core daily monitoring (wired)

| Paper | Method (wired) | Freshness evidence (2026-11-15 probe) | Status |
|---|---|---|---|
| Prothom Alo Bangla | RSS `/feed` + news sitemap `/news_sitemap.xml` | feed 55 items; sitemap 470 items, latest 17:30 UTC | live |
| Prothom Alo English | RSS `/feed` + news sitemap + Bing `site:en.prothomalo.com` | feed fresh; sitemap ~80 items/48 h | live |
| Jugantor | news sitemap | ~500 items/48 h | live |
| Ittefaq | Bing `site:ittefaq.com.bd` (direct 403) | 12 items, latest 08:40 UTC | live via Bing |
| The Daily Star | sitemap child `sitemaps/2026/sitemap-2026-1.xml` + section pages (fallback) + Bing `site:thedailystar.net` | sitemap flaky (truncated reads lose the tail); sections cover the gap | live |
| Dhaka Tribune | Bing `site:dhakatribune.com` (direct 403/404 everywhere) | Bing fresh | live via Bing |
| New Age | Bing `site:newagebd.net` (direct 403) | 12 items, latest 08:32 UTC | live via Bing |
| The Financial Express | Bing `site:thefinancialexpress.com.bd` (sitemap IncompleteRead) | Bing fresh | live via Bing |
| The Business Standard | sitemap index → fresh children + Bing `site:tbsnews.net` | children fresh | live |
| bdnews24 | news sitemap `/news_sitemap.xml` + Bing `site:bdnews24.com` | sitemap 124 items, latest 17:09 UTC; Bing 11 items, fresh | live |
| Bangla Tribune | Bing `site:banglatribune.com` (direct 403/404/closed) | 12 items, latest 09:05 UTC | live via Bing |
| Jago News 24 | Bing `site:jagonews24.com` (direct 403) | 6 items, latest 09:05 UTC | live via Bing |

## Level 1 — blocked from this VM (recorded, not wired)

| Paper | What was tried (2026-11-15) | Exact failure |
|---|---|---|
| Bangladesh Pratidin | RSS, /feed, /sitemap.xml, /news_sitemap.xml, /news-sitemap.xml; Bing `site:bd-pratidin.com` | HTTP 403 on every direct route; Bing returns 0 items |
| Kaler Kantho | RSS, /sitemap.xml; Bing `site:kalerkantho.com` | HTTP 403 direct; Bing items exist but latest is 31 Jul 2026 (stale) |
| Samakal | sitemap index + daily children | Index loads (2,513 daily children) but every daily child is HTTP 403 — Cloudflare "Just a moment..." challenge page (verified with curl as well as urllib) |
| Bonik Barta | /rss, /rss.xml, /sitemap.xml, /news_sitemap.xml, /sitemap_index.xml; Bing `site:bonikbarta.net` | HTTP 200 on every path but all return the same 61 KB SPA shell — no feed endpoints at conventional paths; Bing latest is 10 Sep 2024 (stale) |

## Agencies — verification-only (not news sources for the page)

| Agency | Method | Evidence |
|---|---|---|
| BSS | Bing `site:bssnews.net` (direct 403) | 11 items, latest 00:55 UTC, fresh. Tier 0 in main-picking (official source first). |
| UNB | Bing `site:unb.com.bd` (direct 404 on /rss, /feed, /sitemap.xml) | 12 items, latest 08:36 UTC, fresh. |

## Level 2 — extended coverage (targets, NOT wired)

Wire only after a Level 1 gap is proven on a real dry-run. The cheap
first test for any of these is a Bing `site:` query; a direct route
needs the same RSS → sitemap → section probe as Level 1.

Bangla national: আমাদের সময়, জনকণ্ঠ, মানবজমিন, নয়া দিগন্ত,
ইনকিলাব, দেশ রূপান্তর, আজকের পত্রিকা, কালবেলা, যায়যায়দিন,
দৈনিক বাংলা, দৈনিক সংবাদ, দৈনিক সংগ্রাম, সময়ের আলো,
আলোকিত বাংলাদেশ, আমার দেশ, আমার সংবাদ, দৈনিক দিনকাল.
English: The Business Post, Daily Sun, The Daily Observer,
Bangladesh Post, The Bangladesh Today, The Asian Age.
Digital-first: Banglanews24, Dhaka Post, Risingbd, Barta24,
Sarabangla, NewsBangla24, Daily Bangladesh.

## Level 3 — regional and specialist (targets, NOT wired)

Regional: দৈনিক আজাদী (Chattogram), দৈনিক পূর্বকোণ (Chattogram),
দৈনিক করতোয়া (Bogura/north), সোনালী সংবাদ (Rajshahi).
Specialist: শেয়ার বিজ (financial). Purpose: local developments,
agriculture, banking, industry, infrastructure, regional
administration — only when a Level 1/2 gap is proven.

## What changed 2026-11-15 (this wiring)

- **Wired direct:** Prothom Alo Bangla news sitemap (470 items),
  bdnews24 news sitemap (124 items).
- **Wired Bing:** Ittefaq, Bangla Tribune, Jago News 24, bdnews24,
  UNB, BSS, New Age (all fresh on the probe).
- **Recorded blocked:** Bangladesh Pratidin, Kaler Kantho, Samakal,
  Bonik Barta (see table above).
- The engine already read the English five + Prothom Alo Bangla
  + Jugantor; the Bangla gap is now narrowed to Pratidin,
  Kaler Kantho, Samakal and Bonik Barta — all four blocked from
  this VM, none reachable even via Bing with fresh items.

## Weekly health check

Run `python3 tools/check_routes.py` (stdlib only). It checks every
route in this registry (HTTP + freshness) and prints a per-source
alive/stale/blocked table with a summary line. Exit 1 if a route
that was live is now dead (a regression); a blocked route that
starts working prints `NEW — now works, consider wiring` (exit 0).
Update this file whenever the check reports a change.
