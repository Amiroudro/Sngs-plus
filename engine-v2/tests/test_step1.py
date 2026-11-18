#!/usr/bin/env python3
"""Step 1 test — runnable as:  python3 tests/test_step1.py
(from engine-v2/, or from anywhere: paths are resolved from this file).

1. Runs a REAL fetch for 2026-11-14 via step1_collect.py and writes
   the batch to engine-v2/runs/_scratch-test-step1/ (a scratch dir —
   never into the shared runs/2026-11-14/ fixture or v1 dirs; a
   2026-11-15 re-run overwrote the original 14 Nov collect outputs
   because this test wrote there, and the raw 14 Nov files are lost).
   then prints a per-source success/dead table.
2. Dedup test on a known duplicate pair (same story from two
   sources + a Google News redirect of the same story): asserts
   ONE cluster, main = the official/daily article (not the portal
   or the redirect), cluster size recorded.
3. Unit asserts: strip_tracking, norm_bangla, robots_allowed.
4. Decision 1 (direct newspaper routes, no Google News): unit
   tests for the plain-sitemap and section-link parsers, plus live
   checks that every new route is either returning items or
   recorded dead/blocked/empty with a reason — never silent — and
   that the fresh count is materially above the 14 Nov baseline
   of 107 collected articles.
5. Slug-title checks (section 5 in main): title_source markers,
   extract_page_title, resolve_slug_titles.
6. Level 1 routes (wired 2026-11-15): PA Bangla + bdnews24 news
   sitemaps, seven new Bing site: queries, DROPPED records for the
   blocked papers (Pratidin, Kaler Kantho, Samakal, Bonik Barta).
Prints PASS/FAIL counts at the end. A route that fails is recorded
as dead in the table — never silently retried, never faked.
Exit code 0 only if every check passes.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import common  # noqa: E402
import step1_collect as s1  # noqa: E402

DATE = "2026-11-14"
# Scratch dir for the live fetch: this test must NEVER write into the
# shared runs/<date>/ fixture — a 2026-11-15 re-run overwrote the
# original 14 Nov collect outputs (876 fresh articles replaced the
# original 107; edition/page/decisions/report survive, raw collect
# files do not). The fetch date is still 2026-11-14; only the output
# dir is scratch.
RUN_DIR = BASE / "runs" / "_scratch-test-step1"

PASSES = []
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        PASSES.append(name)
        print(f"  PASS: {name}" + (f" — {detail}" if detail else ""))
    else:
        FAILURES.append(name)
        print(f"  FAIL: {name}" + (f" — {detail}" if detail else ""))


def main():
    print(f"=== Step 1 test — real fetch for {DATE} ===")
    # Scratch dir is wiped first so stale files cannot mask a failure.
    shutil.rmtree(RUN_DIR, ignore_errors=True)
    # 1. Real run (subprocess, exactly as a user would run it),
    # writing to the scratch dir — never to runs/<date>/.
    proc = subprocess.run(
        [sys.executable, str(BASE / "step1_collect.py"),
         "--date", DATE, "--out", str(RUN_DIR)],
        capture_output=True, text=True, cwd=str(BASE))
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    check("collector exit code 0", proc.returncode == 0,
          f"exit={proc.returncode}")

    articles_path = RUN_DIR / f"articles-{DATE}.json"
    sources_path = RUN_DIR / f"sources-{DATE}.json"
    clusters_path = RUN_DIR / f"clusters-{DATE}.json"
    for p in (articles_path, sources_path, clusters_path):
        check(f"output file exists: {p.name}", p.exists())

    articles = sources = clusters = None
    if articles_path.exists():
        articles = json.loads(articles_path.read_text(encoding="utf-8"))
    if sources_path.exists():
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
    if clusters_path.exists():
        clusters = json.loads(clusters_path.read_text(encoding="utf-8"))

    # Per-source success/dead table.
    print("\n--- per-source table (live run) ---")
    print(f"{'route':55s} {'items':>5s}  {'fresh?':6s}  last_success")
    if sources:
        for name, r in sources["sources"].items():
            status = "OK" if r.get("items") else "DEAD"
            print(f"{name[:55]:55s} {r.get('items', 0):5d}  "
                  f"{str(r.get('fresh')):6s}  {r.get('last_success') or '-'}"
                  f"   [{status}] {r.get('status')}")
        live = [n for n, r in sources["sources"].items()
                if r.get("items") and r.get("method") != "dropped"]
        check("at least one live route returned items", bool(live),
              f"{len(live)} live routes")
        check("at least one route is fresh", any(
            r.get("fresh") for r in sources["sources"].values()),
            "freshness = newest item within 2 days")
    if articles:
        check("articles file has >= 1 article", articles["collected"] >= 1,
              f"collected={articles['collected']}")
        check("article ids are a001-style, in order",
              all(a["id"] == f"a{i + 1:03d}"
                  for i, a in enumerate(articles["articles"]))
              if articles["articles"] else False)
        check("no article carries body text (Step 1 fetches none)",
              all(a.get("body_text", "") == ""
                  for a in articles["articles"]))
    if clusters:
        multi = [c for c in clusters["clusters"] if c["size"] > 1]
        print(f"\n[dedup-real] {len(clusters['clusters'])} clusters, "
              f"{len(multi)} with >1 member, "
              f"{sum(c['size'] for c in clusters['clusters'])} items clustered")
        for c in multi[:5]:
            print(f"  cluster size {c['size']} main={c['main_id']}: "
                  + " | ".join(
                      f"{m['source']}" for m in c["members_detail"]))

    # Decision 1 live checks: every new direct route is accounted
    # for — returning items, or recorded dead/blocked/empty with a
    # reason. (Daily Star section routes only appear when the
    # sitemap leg yields 0 fresh items, so they are checked
    # conditionally.)
    if sources:
        print("\n--- Decision 1 live checks (direct routes) ---")
        srcs = sources["sources"]
        core_new = ["TBS sitemap index", "Jugantor news sitemap",
                    "Prothom Alo Bangla", "Daily Star sitemap 2026"]
        tbs_children = [n for n in srcs if n.startswith("TBS sitemap 2026-")]
        check("TBS sitemap children present in report", bool(tbs_children),
              f"{tbs_children}")
        for name in core_new:
            r = srcs.get(name)
            accounted = bool(r) and (
                r.get("items", 0) > 0
                or "blocked" in str(r.get("status"))
                or "failed" in str(r.get("status"))
                or "0 items" in str(r.get("status"))
                or "child sitemap" in str(r.get("status")))
            check(f"new route accounted for: {name}", accounted,
                  f"{r.get('status') if r else 'MISSING from report'}")
        ds_sections = [n for n in srcs if n.startswith("Daily Star section:")]
        ds_sitemap_items = srcs.get("Daily Star sitemap 2026", {}).get("items", 0)
        check("Daily Star sections present OR sitemap leg delivered",
              bool(ds_sections) or ds_sitemap_items > 0,
              f"sections={ds_sections} sitemap_items={ds_sitemap_items}")
        live_new = [n for n, r in srcs.items()
                    if (n.startswith("TBS sitemap 2026-")
                        or n in ("Jugantor news sitemap",
                                 "Prothom Alo Bangla",
                                 "Daily Star sitemap 2026")
                        or n.startswith("Daily Star section:"))
                    and r.get("items", 0) > 0]
        check("at least two new direct routes returned items",
              len(live_new) >= 2, f"live new routes: {live_new}")
        if articles:
            # 14 Nov baseline was 107 collected; the new direct
            # routes must lift the count materially.
            check("collected materially above the 107 baseline",
                  articles["collected"] > 150,
                  f"collected={articles['collected']} (baseline 107)")
            # Items from a live new route must actually reach the
            # articles file (checked only for routes that delivered).
            by_source = {}
            for a in articles["articles"]:
                by_source.setdefault((a["source"], a["found_via"]), 0)
                by_source[(a["source"], a["found_via"])] += 1
            if srcs.get("Jugantor news sitemap", {}).get("items", 0) > 0:
                check("Jugantor sitemap items reach the articles file",
                      by_source.get(("Jugantor", "sitemap"), 0) > 0,
                      f"{by_source.get(('Jugantor', 'sitemap'), 0)} items")
            if any(srcs.get(n, {}).get("items", 0) > 0
                   for n in tbs_children):
                check("TBS sitemap items reach the articles file",
                      by_source.get(("The Business Standard", "sitemap"), 0) > 0,
                      f"{by_source.get(('The Business Standard', 'sitemap'), 0)} items")
            if srcs.get("Prothom Alo Bangla", {}).get("items", 0) > 0:
                check("Prothom Alo Bangla items reach the articles file",
                      by_source.get(("Prothom Alo Bangla", "rss"), 0) > 0,
                      f"{by_source.get(('Prothom Alo Bangla', 'rss'), 0)} items")

        # 6. Level 1 routes (wired 2026-11-15, Rudro's ask): two new
        # direct news sitemaps (PA Bangla, bdnews24) + seven new Bing
        # site: queries (Ittefaq, Bangla Tribune, Jago News 24,
        # bdnews24, UNB, BSS, New Age). Blocked papers (Pratidin,
        # Kaler Kantho, Samakal, Bonik Barta) must be recorded in
        # DROPPED, never silently missing.
        print("\n--- Level 1 routes (wired 2026-11-15) ---")
        pa_bn_fixture = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
 xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
<url><loc>https://www.prothomalo.com/bangladesh/test-story-1</loc>
<news:news><news:title>বাজেটে বরাদ্দ বাড়ল শিক্ষায়</news:title>
<news:publication_date>2026-11-14T10:00:00+06:00</news:publication_date>
</news:news></url>
<url><loc>https://www.prothomalo.com/bangladesh/test-story-2</loc>
<news:news><news:title>রেমিট্যান্স বেড়েছে অক্টোবরে</news:title>
<news:publication_date>2026-11-14T11:00:00+06:00</news:publication_date>
</news:news></url></urlset>"""
        pa_bn_items = s1.parse_news_sitemap(
            pa_bn_fixture, "Prothom Alo Bangla", found_via="sitemap")
        check("PA Bangla news sitemap fixture parses to 2 titled items",
              len(pa_bn_items) == 2
              and all(i["title_source"] == "feed" for i in pa_bn_items)
              and all(i["source"] == "Prothom Alo Bangla"
                      for i in pa_bn_items)
              and all(i["found_via"] == "sitemap" for i in pa_bn_items),
              f"n={len(pa_bn_items)}")
        bd24_fixture = pa_bn_fixture.replace(
            "prothomalo.com", "bdnews24.com").replace(
            "Prothom Alo Bangla", "bdnews24")
        bd24_items = s1.parse_news_sitemap(
            bd24_fixture, "bdnews24", found_via="sitemap")
        check("bdnews24 news sitemap fixture parses, source bdnews24",
              len(bd24_items) == 2
              and all(i["source"] == "bdnews24" for i in bd24_items)
              and all(i["found_via"] == "sitemap" for i in bd24_items),
              f"n={len(bd24_items)}")
        new_bing = ["site:ittefaq.com.bd", "site:banglatribune.com",
                    "site:jagonews24.com", "site:bdnews24.com",
                    "site:unb.com.bd", "site:bssnews.net",
                    "site:newagebd.net"]
        check("BING_QUERIES contains all 7 new Level 1 site: queries",
              all(q in s1.BING_QUERIES for q in new_bing),
              f"missing={[q for q in new_bing if q not in s1.BING_QUERIES]}")
        dropped_names = [n for n, _, _ in s1.DROPPED]
        check("DROPPED records the blocked Level 1 papers",
              all(any(k in n for n in dropped_names)
                  for k in ("Pratidin", "Kaler Kantho", "Samakal",
                            "Bonik Barta")),
              f"dropped={[n for n in dropped_names if any(k in n for k in ('Pratidin', 'Kaler', 'Samakal', 'Bonik'))]}")
        check("DOMAIN_SOURCES maps the new Level 1 domains",
              all(s1.source_from_url(f"https://{d}/x") == want
                  for d, want in
                  (("ittefaq.com.bd", "Ittefaq"),
                   ("banglatribune.com", "Bangla Tribune"),
                   ("jagonews24.com", "Jago News 24"),
                   ("bdnews24.com", "bdnews24"),
                   ("unb.com.bd", "UNB"), ("bssnews.net", "BSS"),
                   ("newagebd.net", "New Age"))),
              "domain->source mapping")
        if sources:
            srcs = sources["sources"]
            for name in ("Prothom Alo Bangla news sitemap",
                         "bdnews24 news sitemap"):
                r = srcs.get(name)
                accounted = bool(r) and (
                    r.get("items", 0) > 0
                    or "blocked" in str(r.get("status"))
                    or "failed" in str(r.get("status")))
                check(f"Level 1 sitemap route accounted for: {name}",
                      accounted,
                      f"{r.get('status') if r else 'MISSING from report'}")
            bing_live = [q for q in new_bing
                         if srcs.get(f"Bing News: {q}", {}).get("items", 0) > 0]
            check("at least 3 of the 7 new Bing site: queries returned items",
                  len(bing_live) >= 3, f"live: {bing_live}")
            if articles:
                by_source = {}
                for a in articles["articles"]:
                    by_source.setdefault((a["source"], a["found_via"]), 0)
                    by_source[(a["source"], a["found_via"])] += 1
                if srcs.get("Prothom Alo Bangla news sitemap",
                            {}).get("items", 0) > 0:
                    check("PA Bangla sitemap items reach the articles file",
                          by_source.get(("Prothom Alo Bangla", "sitemap"), 0) > 0,
                          f"{by_source.get(('Prothom Alo Bangla', 'sitemap'), 0)} items")
                if srcs.get("bdnews24 news sitemap",
                            {}).get("items", 0) > 0:
                    check("bdnews24 sitemap items reach the articles file",
                          by_source.get(("bdnews24", "sitemap"), 0) > 0,
                          f"{by_source.get(('bdnews24', 'sitemap'), 0)} items")
                new_bing_sources = sum(
                    by_source.get((s, "bing"), 0)
                    for s in ("Ittefaq", "Bangla Tribune", "Jago News 24",
                              "bdnews24", "UNB", "BSS", "New Age"))
                check("new Bing-domain items reach the articles file",
                      new_bing_sources > 0,
                      f"{new_bing_sources} items from the 7 new domains")

    # 2. Dedup test — hand-built known duplicate pair + redirect.
    print("\n--- dedup test (hand-built duplicate trio) ---")
    title = "Cabinet approves draft ordinance on public procurement"
    summary = ("The cabinet on Thursday approved the draft ordinance on "
               "public procurement, aiming to bring transparency to "
               "government purchases worth Tk 442 crore in the current "
               "fiscal year, officials said after the meeting.")
    trio = [
        {"title": title, "url": "https://www.bssnews.net/news/12345",
         "source": "BSS", "section": "", "published": "2026-11-14T05:00:00+00:00",
         "summary": summary, "found_via": "bing"},
        {"title": title, "url": "https://example-portal.com/news/xyz?utm_source=x",
         "source": "Example Portal", "section": "",
         "published": "2026-11-14T06:30:00+00:00",
         "summary": summary, "found_via": "bing"},
        {"title": title,
         "url": "https://news.google.com/rss/articles/CBMi12345?oc=5",
         "source": "Google News", "section": "",
         "published": "2026-11-14T06:00:00+00:00",
         "summary": summary, "found_via": "google-news"},
    ]
    # URL tracking is stripped before clustering (portal URL has utm_).
    trio = s1.dedupe_by_url(trio)
    check("strip_tracking inside dedupe removes utm_ from portal URL",
          "utm_source" not in trio[1]["url"], trio[1]["url"])
    found = s1.cluster_articles(trio)
    check("duplicate trio forms ONE cluster", len(found) == 1,
          f"clusters={len(found)}")
    if found:
        check("cluster size recorded as 3", len(found[0]) == 3,
              f"size={len(found[0])}")
        main = s1.pick_main(found[0])
        check("main article is the official source (BSS), not portal/redirect",
              main["source"] == "BSS" and "bssnews.net" in main["url"],
              f"main={main['source']} {main['url']}")
    # A clearly different story must NOT cluster with the trio.
    other = {"title": "Bangladesh beat Zimbabwe by 42 runs in Dhaka Test",
             "url": "https://example.com/sport/1", "source": "BSS",
             "section": "", "published": "2026-11-14T05:00:00+00:00",
             "summary": "Bangladesh won the Test match by 42 runs.",
             "found_via": "bing"}
    check("different story does not join the cluster",
          len(s1.cluster_articles(trio + [other])) == 2)
    # Same story 3 days apart must NOT cluster (48h window).
    stale_twin = dict(trio[0])
    stale_twin["published"] = "2026-11-11T05:00:00+00:00"
    stale_twin["url"] = "https://www.bssnews.net/news/99999"
    check("same story >48h apart does not cluster",
          len(s1.cluster_articles([trio[0], stale_twin])) == 2)

    # Real-batch dedup check, if the live batch has a multi cluster.
    if clusters:
        multi = [c for c in clusters["clusters"] if c["size"] > 1]
        if multi:
            c = multi[0]
            mains = {a["id"]: a for a in articles["articles"]}
            main = mains.get(c["main_id"])
            check("real multi-member cluster: main is not a Google redirect",
                  main is not None and "news.google.com" not in main["url"],
                  f"main={main['source'] if main else '?'}")

    # 3. Helper asserts.
    print("\n--- helper asserts ---")
    u = ("https://example.com/news/x?utm_source=google&utm_medium=cpc"
         "&fbclid=abc123&gclid=xyz&page=2#section")
    stripped = common.strip_tracking(u)
    check("strip_tracking removes utm_* and fbclid/gclid, keeps real params",
          "utm_source" not in stripped and "fbclid" not in stripped
          and "gclid" not in stripped and "page=2" in stripped
          and "#" not in stripped, stripped)
    check("norm_bangla converts ৪৪২ to 442",
          common.norm_bangla("টাকা ৪৪২ কোটি") == "টাকা 442 কোটি",
          common.norm_bangla("টাকা ৪৪২ কোটি"))
    check("norm_bangla removes zero-width chars",
          "​" not in common.norm_bangla("a​b‌c‍d﻿e")
          and common.norm_bangla("a​b‌c‍d﻿e") == "abcde")
    # 4. Decision 1 parser unit tests (no network).
    print("\n--- Decision 1 parser unit tests ---")
    check("_title_from_slug strips trailing id, reformats slug",
          s1._title_from_slug(
              "https://www.tbsnews.net/bangladesh/remittance-hits-record-high-1234567")
          == "Remittance Hits Record High")
    check("_title_from_slug unquotes percent-encoded slugs",
          s1._title_from_slug(
              "https://example.com/news/caf%C3%A9-prices-rise-99")
          == "Café Prices Rise")
    plain_xml = """<?xml version="1.0"?><urlset>
<url><loc>https://www.tbsnews.net/bangladesh/remittance-hits-record-high-1234567</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
<url><loc>https://www.tbsnews.net/videos/some-video-999</loc><lastmod>2026-11-14T11:00:00+06:00</lastmod></url>
<url><loc>https://www.tbsnews.net/bangladesh/old-story-111</loc><lastmod>2026-10-01T10:00:00+06:00</lastmod></url>
<url><loc>https://www.tbsnews.net/sports/cricket-win-222</loc><lastmod>2026-11-14T12:00:00+06:00</lastmod></url>
</urlset>"""
    cutoff = datetime(2026, 11, 12, tzinfo=timezone.utc)
    plain = s1.parse_plain_sitemap(plain_xml, "The Business Standard",
                                   "sitemap", cutoff=cutoff)
    check("parse_plain_sitemap keeps only in-window, non-video, "
          "non-sports items", len(plain) == 1,
          f"kept={len(plain)}")
    if plain:
        check("parse_plain_sitemap title comes from the slug",
              plain[0]["title"] == "Remittance Hits Record High",
              plain[0]["title"])
        check("parse_plain_sitemap source from the URL domain",
              plain[0]["source"] == "The Business Standard",
              plain[0]["source"])
        check("parse_plain_sitemap keeps lastmod as published",
              plain[0]["published"] == "2026-11-14T10:00:00+06:00",
              plain[0]["published"])
    section_html = """<div class="card"><a href="/news/bangladesh/news/eatery-vandalised-over-seating-row-4323221" aria-label="Eatery vandalised over seating row"></a><div class="card-info"><time class="rsi-ago" datetime="2026-11-14T00:00:00+06:00">2 HOUR(s)</time></div></div>
<div class="card"><a href="/news/bangladesh/news/undated-story-1"></a><div></div></div>
<div class="card"><a href="/news/bangladesh/news/old-story-2" aria-label="Old story"></a><div><time datetime="2026-11-01T00:00:00+06:00"></time></div></div>"""
    sec = s1.parse_section_links(
        section_html, "https://www.thedailystar.net", "The Daily Star",
        "section", cutoff=cutoff)
    check("parse_section_links keeps only the dated in-window card",
          len(sec) == 1, f"kept={len(sec)}")
    if sec:
        check("parse_section_links title comes from aria-label",
              sec[0]["title"] == "Eatery vandalised over seating row",
              sec[0]["title"])
        check("parse_section_links resolves relative URLs",
              sec[0]["url"] == "https://www.thedailystar.net/news/bangladesh/news/eatery-vandalised-over-seating-row-4323221",
              sec[0]["url"])
    # A section page with links but NO dates yields nothing — the
    # FE case: links exist, same-day cannot be verified.
    nodates_html = ('<a href="/bangladesh/some-story" '
                    'aria-label="Some story"></a>' * 3)
    check("parse_section_links drops dateless links (FE case)",
          s1.parse_section_links(
              nodates_html, "https://thefinancialexpress.com.bd",
              "The Financial Express", "section", cutoff=cutoff) == [])
    try:
        allowed_j = common.robots_allowed("https://www.jugantor.com/news_sitemap.xml")
        check("robots_allowed returns a bool for jugantor.com",
              isinstance(allowed_j, bool), f"allowed={allowed_j}")
    except Exception as e:
        check("robots_allowed returns a bool for jugantor.com", False, str(e))
    try:
        allowed = common.robots_allowed("https://www.thedailystar.net/news/1")
        check("robots_allowed returns a bool for thedailystar.net",
              isinstance(allowed, bool), f"allowed={allowed}")
    except Exception as e:
        check("robots_allowed returns a bool for thedailystar.net", False, str(e))
    # Real check: redirect gets body_error "no direct URL", no fetch.
    kept = [{"id": "a001", "title": title,
             "url": "https://news.google.com/rss/articles/CBMi12345?oc=5",
             "source": "Google News", "body_text": "", "body_error": ""}]
    ok, tried = s1.fetch_bodies_for_kept(kept)
    check("fetch_bodies_for_kept: redirect gets 'no direct URL', 0 tried",
          ok == 0 and tried == 0 and kept[0]["body_error"] == "no direct URL",
          f"ok={ok} tried={tried} err={kept[0]['body_error']}")

    # 5. Slug-title resolution unit tests (no network — fake fetcher).
    print("\n--- slug-title resolution unit tests ---")
    check("parse_plain_sitemap marks title_source 'slug'",
          plain and plain[0].get("title_source") == "slug",
          f"{plain[0].get('title_source') if plain else 'no items'}")
    rss_xml = """<?xml version="1.0"?><rss><channel>
<item><title>Budget passes in parliament</title><link>https://www.thedailystar.net/news/bangladesh/budget-passes-parliament-1</link><description>Parliament passed the budget.</description><pubDate>Fri, 14 Nov 2026 05:00:00 GMT</pubDate></item>
</channel></rss>"""
    rss_items = s1.parse_rss_items(rss_xml, "The Daily Star", "rss")
    check("parse_rss_items marks title_source 'feed'",
          len(rss_items) == 1 and rss_items[0].get("title_source") == "feed",
          f"{len(rss_items)} items")
    news_xml = """<?xml version="1.0"?><urlset>
<url><loc>https://www.jugantor.com/national/story-1</loc><news:title>Real Jugantor headline</news:title><news:publication_date>2026-11-14T05:00:00+00:00</news:publication_date></url>
</urlset>"""
    news_items = s1.parse_news_sitemap(news_xml, "Jugantor")
    check("parse_news_sitemap marks title_source 'feed'",
          len(news_items) == 1 and news_items[0].get("title_source") == "feed",
          f"{len(news_items)} items")
    html_og = ('<html><head>'
               '<meta property="og:title" content="Customs foil attempt to export ship propeller scrap">'
               '<title>Customs Foil Attempt Export Ship Propeller Scrap Copper | The Business Standard</title>'
               '</head><body><h1>Customs foil attempt to export ship propeller scrap</h1></body></html>')
    check("extract_page_title prefers og:title",
          s1.extract_page_title(html_og)
          == "Customs foil attempt to export ship propeller scrap",
          s1.extract_page_title(html_og))
    html_og_rev = ('<html><head>'
                   '<meta content="Govt targets budget support" property="og:title">'
                   '<title>Govt Targets Budget Support | The Business Standard</title>'
                   '</head></html>')
    check("extract_page_title reads og:title with content-first attributes",
          s1.extract_page_title(html_og_rev) == "Govt targets budget support",
          s1.extract_page_title(html_og_rev))
    html_title = ('<html><head><title>Flawed industrial data inflated GDP growth | The Business Standard</title>'
                  '</head><body><h1>Other heading</h1></body></html>')
    check("extract_page_title falls back to <title>, strips site suffix",
          s1.extract_page_title(html_title)
          == "Flawed industrial data inflated GDP growth",
          s1.extract_page_title(html_title))
    html_h1 = ('<html><head><title>The Business Standard</title></head>'
               '<body><h1>Bangladesh promotes jute as green alternative</h1></body></html>')
    check("extract_page_title falls back to first <h1> when <title> is the site name",
          s1.extract_page_title(html_h1)
          == "Bangladesh promotes jute as green alternative",
          s1.extract_page_title(html_h1))
    check("extract_page_title returns '' when no title exists",
          s1.extract_page_title(
              "<html><head></head><body>no title here</body></html>") == "")
    plain_junk = """<?xml version="1.0"?><urlset>
<url><loc>https://www.tbsnews.net/author/shahadat-shadhin</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
<url><loc>https://www.tbsnews.net/govt-ad/12112026-1602456</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
<url><loc>https://www.tbsnews.net/bangladesh/real-story-123</loc><lastmod>2026-11-14T10:00:00+06:00</lastmod></url>
</urlset>"""
    junk = s1.parse_plain_sitemap(plain_junk, "The Business Standard",
                                  "sitemap", cutoff=cutoff)
    check("parse_plain_sitemap drops author and govt-ad pages",
          len(junk) == 1 and junk[0]["title"] == "Real Story",
          f"kept={len(junk)}")
    html_date = ('<html><head>'
                 '<meta property="og:title" content="12/11/2026">'
                 '<title>Real headline after a date og:title | The Business Standard</title>'
                 '</head></html>')
    check("extract_page_title rejects a date-only og:title, falls through to <title>",
          s1.extract_page_title(html_date)
          == "Real headline after a date og:title",
          s1.extract_page_title(html_date))
    fake_pages = {
        "https://www.tbsnews.net/bangladesh/cabinet-approves-draft-ordinance-public-procurement-111":
            '<html><head><meta property="og:title" content="Cabinet approves draft ordinance on public procurement">'
            '<meta property="og:image" content="https://cdn.tbsnews.net/images/cabinet-ordinance.jpg">'
            '<title>Cabinet Approves Draft Ordinance Public Procurement | The Business Standard</title></head></html>',
    }
    real_fetch, real_robots = common.fetch_text, common.robots_allowed
    _fetch_calls = {}

    def _fake_fetch(url, timeout=20):
        _fetch_calls[url] = _fetch_calls.get(url, 0) + 1
        if url in fake_pages:
            return fake_pages[url]
        if url == "https://www.tbsnews.net/bangladesh/flaky-story-444":
            if _fetch_calls[url] == 1:
                raise Exception("boom once")
            return ('<html><head><meta property="og:title" '
                    'content="Flaky story resolves on retry">'
                    '<meta property="og:image" '
                    'content="/images/flaky-story.jpg"></head></html>')
        raise Exception("boom")

    try:
        common.fetch_text = _fake_fetch
        common.robots_allowed = lambda url: True  # noqa: E731
        arts = [
            {"id": "a001",
             "title": "Cabinet Approves Draft Ordinance Public Procurement",
             "url": "https://www.tbsnews.net/bangladesh/cabinet-approves-draft-ordinance-public-procurement-111",
             "source": "The Business Standard", "section": "",
             "published": "2026-11-14T05:00:00+00:00",
             "summary": "The cabinet approved the draft ordinance on public "
                        "procurement at a meeting on Thursday.",
             "found_via": "sitemap", "title_source": "slug",
             "body_text": "", "body_error": ""},
            {"id": "a002", "title": "Some Other Story That Fails To Fetch",
             "url": "https://www.tbsnews.net/bangladesh/some-other-story-222",
             "source": "The Business Standard", "section": "",
             "published": "2026-11-14T05:00:00+00:00",
             "summary": "", "found_via": "sitemap", "title_source": "slug",
             "body_text": "", "body_error": ""},
            {"id": "a003", "title": "Non Main Slug Story Member",
             "url": "https://www.tbsnews.net/bangladesh/non-main-member-333",
             "source": "The Business Standard", "section": "",
             "published": "2026-11-14T05:00:00+00:00",
             "summary": "", "found_via": "sitemap", "title_source": "slug",
             "body_text": "", "body_error": ""},
            {"id": "a004", "title": "Google Redirect Story",
             "url": "https://news.google.com/rss/articles/CBMi999?oc=5",
             "source": "Google News", "section": "",
             "published": "2026-11-14T05:00:00+00:00",
             "summary": "", "found_via": "google-news",
             "title_source": "slug", "body_text": "", "body_error": ""},
            {"id": "a005", "title": "Flaky Story That Fails Once",
             "url": "https://www.tbsnews.net/bangladesh/flaky-story-444",
             "source": "The Business Standard", "section": "",
             "published": "2026-11-14T05:00:00+00:00",
             "summary": "", "found_via": "sitemap", "title_source": "slug",
             "body_text": "", "body_error": ""},
        ]
        clus = [{"members": ["a001", "a003"], "main_id": "a001", "size": 2,
                 "members_detail": [
                     {"id": "a001", "title": arts[0]["title"],
                      "url": arts[0]["url"], "source": "The Business Standard"},
                     {"id": "a003", "title": arts[2]["title"],
                      "url": arts[2]["url"], "source": "The Business Standard"}]},
                {"members": ["a002"], "main_id": "a002", "size": 1,
                 "members_detail": [
                     {"id": "a002", "title": arts[1]["title"],
                      "url": arts[1]["url"], "source": "The Business Standard"}]},
                {"members": ["a004"], "main_id": "a004", "size": 1,
                 "members_detail": [
                     {"id": "a004", "title": arts[3]["title"],
                      "url": arts[3]["url"], "source": "Google News"}]},
                {"members": ["a005"], "main_id": "a005", "size": 1,
                 "members_detail": [
                     {"id": "a005", "title": arts[4]["title"],
                      "url": arts[4]["url"], "source": "The Business Standard"}]}]
        res, fail, secs = s1.resolve_slug_titles(
            arts, clus, max_workers=2, budget_seconds=60)
        check("resolve_slug_titles: main resolves to the page headline",
              arts[0]["title"]
              == "Cabinet approves draft ordinance on public procurement"
              and arts[0]["title_source"] == "page",
              arts[0]["title"])
        check("resolve_slug_titles: members_detail title updated for the resolved main",
              clus[0]["members_detail"][0]["title"]
              == "Cabinet approves draft ordinance on public procurement",
              clus[0]["members_detail"][0]["title"])
        check("resolve_slug_titles: fetch failure keeps the slug title",
              arts[1]["title"] == "Some Other Story That Fails To Fetch"
              and arts[1]["title_source"] == "slug",
              arts[1]["title"])
        check("resolve_slug_titles: non-main member untouched",
              arts[2]["title"] == "Non Main Slug Story Member"
              and arts[2]["title_source"] == "slug",
              arts[2]["title"])
        check("resolve_slug_titles: Google News redirect main skipped",
              arts[3]["title"] == "Google Redirect Story"
              and arts[3]["title_source"] == "slug",
              arts[3]["title"])
        check("resolve_slug_titles: one retry rescues a transient failure",
              arts[4]["title"] == "Flaky story resolves on retry"
              and arts[4]["title_source"] == "page",
              arts[4]["title"])
        check("resolve_slug_titles: counts (2 resolved, 1 failed)",
              res == 2 and fail == 1, f"resolved={res} failed={fail}")
        # og:image (Phase 0, ws5): the lead image URL comes from the
        # SAME fetch as the title — no second request per article.
        check("resolve_slug_titles: og:image captured for the resolved main",
              arts[0].get("image_url")
              == "https://cdn.tbsnews.net/images/cabinet-ordinance.jpg",
              arts[0].get("image_url", ""))
        check("resolve_slug_titles: relative og:image resolved against the article URL",
              arts[4].get("image_url")
              == "https://www.tbsnews.net/images/flaky-story.jpg",
              arts[4].get("image_url", ""))
        check("resolve_slug_titles: fetch failure leaves image_url empty",
              arts[1].get("image_url", "") == "",
              repr(arts[1].get("image_url")))
        check("resolve_slug_titles: non-main member carries no image_url",
              arts[2].get("image_url", "") == "",
              repr(arts[2].get("image_url")))
        check("resolve_slug_titles: no second HTTP request per article "
              "(image comes from the title fetch)",
              _fetch_calls.get(
                  "https://www.tbsnews.net/bangladesh/cabinet-approves-draft-ordinance-public-procurement-111", 0) == 1,
              f"calls={_fetch_calls}")
        # Evidence-quote invariant: decide the RESOLVED main; the
        # quote must be a verbatim substring of headline + summary.
        from step3_decide import decide
        d = decide(arts[0])
        check("evidence_quote still verbatim after title replacement",
              d["decision"] == "keep" and d["evidence_quote"]
              and d["evidence_quote"] in (arts[0]["title"] + " "
                                          + arts[0]["summary"]),
              f"decision={d['decision']} quote={d['evidence_quote']!r}")
    finally:
        common.fetch_text = real_fetch
        common.robots_allowed = real_robots

    # Paste support (switch build, 2026-11-15): v2 reads the same
    # paste file v1 does — engine/paste/paste-<day>.md, `## ` blocks.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "paste-2026-11-15.md"
        p.write_text(
            "## Cabinet approves draft ordinance on public procurement\n"
            "- Source: The Daily Star\n"
            "- URL: https://www.thedailystar.net/news/bangladesh/news/cabinet-approves-draft-ordinance-0000001\n"
            "- Published: 2026-11-15\n"
            "- Note: ordinance approved, test note\n"
            "## No URL here\n"
            "- Source: Nowhere\n",
            encoding="utf-8")
        arts, found = s1.read_paste_file("2026-11-15", path=p)
        check("read_paste_file: one article from one ## block",
              found and len(arts) == 1, f"found={found} n={len(arts)}")
        check("read_paste_file: found_via paste, summary = Note",
              arts[0]["found_via"] == "paste"
              and arts[0]["summary"] == "ordinance approved, test note"
              and arts[0]["source"] == "The Daily Star"
              and arts[0]["published"] == "2026-11-15",
              str(arts[0]))
        check("read_paste_file: block without URL skipped",
              all(a["url"] for a in arts), "")
        missing, found2 = s1.read_paste_file(
            "2026-11-15", path=Path(td) / "paste-2099-01-01.md")
        check("read_paste_file: missing file returns ([], False)",
              missing == [] and found2 is False, f"found={found2}")

    # 7. og:image extraction (Phase 0, ws5 — story banner images).
    # URL only, never downloaded; relative URLs resolved against the
    # article URL; only http(s) accepted.
    print("\n--- og:image extraction unit tests ---")
    _base = "https://www.tbsnews.net/bangladesh/some-story-123"
    check("extract_page_image: absolute og:image kept verbatim",
          s1.extract_page_image(
              '<meta property="og:image" content="https://cdn.tbsnews.net/img/x.jpg">',
              _base) == "https://cdn.tbsnews.net/img/x.jpg")
    check("extract_page_image: relative og:image resolved against the article URL",
          s1.extract_page_image(
              '<meta property="og:image" content="/images/x.jpg">',
              _base) == "https://www.tbsnews.net/images/x.jpg")
    check("extract_page_image: protocol-relative og:image inherits the article scheme",
          s1.extract_page_image(
              '<meta property="og:image" content="//cdn.example.com/x.jpg">',
              _base) == "https://cdn.example.com/x.jpg")
    check("extract_page_image: og:image:url (content-first attrs) accepted",
          s1.extract_page_image(
              '<meta content="https://cdn.example.com/y.jpg" property="og:image:url">',
              _base) == "https://cdn.example.com/y.jpg")
    check("extract_page_image: missing og:image returns ''",
          s1.extract_page_image(
              "<html><head><title>No image here</title></head></html>",
              _base) == "")
    check("extract_page_image: empty og:image returns ''",
          s1.extract_page_image(
              '<meta property="og:image" content="">', _base) == "")
    check("extract_page_image: data: URI rejected (never a downloaded file)",
          s1.extract_page_image(
              '<meta property="og:image" content="data:image/png;base64,AAA">',
              _base) == "")
    check("extract_page_image: non-http(s) scheme rejected",
          s1.extract_page_image(
              '<meta property="og:image" content="ftp://example.com/x.jpg">',
              _base) == "")
    check("extract_page_image: HTML entities in the URL unescaped",
          s1.extract_page_image(
              '<meta property="og:image" content="https://cdn.example.com/x.jpg?a=1&amp;b=2">',
              _base) == "https://cdn.example.com/x.jpg?a=1&b=2")
    check("extract_page_image: empty HTML returns ''",
          s1.extract_page_image("", _base) == "")

    print(f"\n=== RESULT: {len(PASSES)} PASS, {len(FAILURES)} FAIL ===")
    if FAILURES:
        print("Failures: " + ", ".join(FAILURES))
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
