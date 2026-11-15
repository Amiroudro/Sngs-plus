#!/usr/bin/env python3
"""Weekly route-health check for the v2 source registry (SOURCES.md).

Stdlib only (plus the engine's own common + step1_collect parsers,
so results are exactly what the engine would see). Checks every
registry route — HTTP + freshness — and prints a per-source
alive/stale/blocked table with a summary line.

Exit 0: no live route regressed (a blocked route that starts
working prints "NEW — now works, consider wiring" and is good
news, not a failure).
Exit 1: at least one route that was live is now dead/stale.

Usage:  python3 tools/check_routes.py   (from engine-v2/)
Update SOURCES.md whenever this reports a change.
"""
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import common  # noqa: E402
import step1_collect as s1  # noqa: E402

YEAR = str(datetime.now(timezone.utc).year)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# (paper, method label, kind, target, expected, flaky_ok)
# kind: rss | sitemap | sitemap-index | bing
# expected: "live" | "blocked"  (stale counts as not-live)
# flaky_ok: an HTTP-200-but-0-items result is a known truncation,
# not a regression (Daily Star sitemap child only).
ROUTES = [
    ("Prothom Alo Bangla", "RSS /feed", "rss",
     "https://www.prothomalo.com/feed", "live", False),
    ("Prothom Alo Bangla", "news sitemap", "sitemap",
     "https://www.prothomalo.com/news_sitemap.xml", "live", False),
    ("Prothom Alo English", "RSS /feed", "rss",
     "https://en.prothomalo.com/feed", "live", False),
    ("Prothom Alo English", "news sitemap", "sitemap",
     "https://en.prothomalo.com/news_sitemap.xml", "live", False),
    ("Jugantor", "news sitemap", "sitemap",
     "https://www.jugantor.com/news_sitemap.xml", "live", False),
    ("The Business Standard", "sitemap index", "sitemap-index",
     "https://www.tbsnews.net/sitemap.xml", "live", False),
    ("The Daily Star", f"sitemap {YEAR} child", "sitemap",
     f"https://www.thedailystar.net/sitemaps/{YEAR}/sitemap-{YEAR}-1.xml",
     "live", True),
    ("bdnews24", "news sitemap", "sitemap",
     "https://bdnews24.com/news_sitemap.xml", "live", False),
    ("The Daily Star", "Bing site:thedailystar.net", "bing",
     "site:thedailystar.net", "live", False),
    ("The Business Standard", "Bing site:tbsnews.net", "bing",
     "site:tbsnews.net", "live", False),
    ("Dhaka Tribune", "Bing site:dhakatribune.com", "bing",
     "site:dhakatribune.com", "live", False),
    ("The Financial Express", "Bing site:thefinancialexpress.com.bd",
     "bing", "site:thefinancialexpress.com.bd", "live", False),
    ("Prothom Alo English", "Bing site:en.prothomalo.com", "bing",
     "site:en.prothomalo.com", "live", False),
    ("Ittefaq", "Bing site:ittefaq.com.bd", "bing",
     "site:ittefaq.com.bd", "live", False),
    ("Bangla Tribune", "Bing site:banglatribune.com", "bing",
     "site:banglatribune.com", "live", False),
    ("Jago News 24", "Bing site:jagonews24.com", "bing",
     "site:jagonews24.com", "live", False),
    ("bdnews24", "Bing site:bdnews24.com", "bing",
     "site:bdnews24.com", "live", False),
    ("UNB", "Bing site:unb.com.bd", "bing",
     "site:unb.com.bd", "live", False),
    ("BSS", "Bing site:bssnews.net", "bing",
     "site:bssnews.net", "live", False),
    ("New Age", "Bing site:newagebd.net", "bing",
     "site:newagebd.net", "live", False),
    # Blocked from this VM (expected — a route that starts working
    # is reported as NEW, not as a failure).
    ("Bangladesh Pratidin", "RSS", "rss",
     "https://www.bd-pratidin.com/rss", "blocked", False),
    ("Kaler Kantho", "RSS", "rss",
     "https://www.kalerkantho.com/rss", "blocked", False),
    ("Samakal", f"daily sitemap {TODAY}", "sitemap",
     f"https://samakal.com/sitemap/sitemap-daily-{TODAY}.xml",
     "blocked", False),
    ("Bonik Barta", "RSS", "rss",
     "https://www.bonikbarta.net/rss", "blocked", False),
    ("Bangla Tribune", "RSS (direct)", "rss",
     "https://www.banglatribune.com/rss", "blocked", False),
    ("Jago News 24", "RSS (direct)", "rss",
     "https://www.jagonews24.com/rss", "blocked", False),
    ("UNB", "RSS (direct)", "rss",
     "https://unb.com.bd/rss", "blocked", False),
    ("BSS", "RSS (direct)", "rss",
     "https://www.bssnews.net/rss", "blocked", False),
    ("New Age", "RSS (direct)", "rss",
     "https://www.newagebd.net/rss", "blocked", False),
    ("Dhaka Tribune", "/feed (direct)", "rss",
     "https://www.dhakatribune.com/feed", "blocked", False),
    ("The Financial Express", "sitemap", "sitemap",
     "https://thefinancialexpress.com.bd/sitemap.xml", "blocked", False),
    ("The Business Standard", "RSS", "rss",
     "https://www.tbsnews.net/rss.xml", "blocked", False),
    ("The Daily Star", "RSS", "rss",
     "https://www.thedailystar.net/rss.xml", "blocked", False),
]


def _fresh(dates):
    return bool(dates) and (datetime.now(timezone.utc) - max(dates)).days <= 2


def _parse(text, label):
    """Parse fetched text the way the engine would. Returns
    (items, latest_iso_or_None, format)."""
    if "<item>" in text:
        items = s1.parse_rss_items(text, label, "rss")
        fmt = "rss"
    elif "<news:title>" in text:
        items = s1.parse_news_sitemap(text, label)
        fmt = "news-sitemap"
    elif "<sitemapindex" in text:
        fmt = "sitemap-index"
        cutoff = datetime.now(timezone.utc) - timedelta(days=2)
        children = []
        for block in re.findall(r"<sitemap>(.*?)</sitemap>", text, re.S):
            loc = s1._grab(block, "loc")
            mod = s1._grab(block, "lastmod")
            dt = common.parse_pubdate(mod) if mod else None
            if loc and dt and dt >= cutoff:
                children.append(loc)
        return children, None, fmt
    elif "<urlset" in text:
        items = s1.parse_plain_sitemap(
            text, label,
            cutoff=datetime.now(timezone.utc) - timedelta(days=2))
        fmt = "plain-sitemap"
    else:
        return [], None, "not-a-feed"
    dates = [common.parse_pubdate(i.get("published") or "")
             for i in items if i.get("published")]
    dates = [d for d in dates if d]
    latest = max(dates).isoformat() if dates else None
    return items, latest, fmt


def check_one(paper, method, kind, target, expected, flaky_ok):
    """Returns (actual, items, latest, note) where actual is one of
    live / stale / blocked / flaky-empty."""
    url = target
    if kind == "bing":
        url = ("https://www.bing.com/news/search?q="
               + urllib.parse.quote(target) + "&format=rss")
    if not common.robots_allowed(url):
        return "blocked", 0, None, "blocked by robots.txt"
    try:
        text = common.fetch_text(url, timeout=15)
    except Exception as e:
        return "blocked", 0, None, f"fetch failed: {e}"
    if kind == "bing":
        items = s1.parse_rss_items(text, "Bing News", "bing")
        dates = [common.parse_pubdate(i.get("published") or "")
                 for i in items if i.get("published")]
        dates = [d for d in dates if d]
        latest = max(dates).isoformat() if dates else None
        if not items:
            return "blocked", 0, None, "HTTP 200, 0 items"
        return ("live" if _fresh(dates) else "stale", len(items), latest,
                f"HTTP 200, {len(items)} items")
    parsed, latest, fmt = _parse(text, paper)
    if fmt == "sitemap-index":
        if parsed:
            return "live", len(parsed), None, \
                f"HTTP 200, {len(parsed)} fresh child sitemap(s)"
        return "blocked", 0, None, "HTTP 200, no fresh child sitemaps"
    if fmt == "not-a-feed":
        return "blocked", 0, None, \
            f"HTTP 200, {len(text.encode('utf-8', 'ignore'))} bytes, not a feed"
    if not parsed:
        if flaky_ok:
            return "flaky-empty", 0, None, \
                "HTTP 200, 0 in-window items (known truncation)"
        return "blocked", 0, None, "HTTP 200, 0 items"
    dates = [common.parse_pubdate(i.get("published") or "")
             for i in parsed if i.get("published")]
    dates = [d for d in dates if d]
    return ("live" if _fresh(dates) else "stale", len(parsed), latest,
            f"HTTP 200, {len(parsed)} items ({fmt})")


def main():
    print("Sarangsho Plus engine v2 — route health check "
          f"({datetime.now(timezone.utc).date().isoformat()})")
    print(f"{'source':22s} {'method':38s} {'actual':12s} "
          f"{'items':>5s}  latest / note")
    alive = stale = blocked = flaky = regressions = new_routes = 0
    for paper, method, kind, target, expected, flaky_ok in ROUTES:
        actual, n, latest, note = check_one(
            paper, method, kind, target, expected, flaky_ok)
        verdict = ""
        if actual == "live":
            alive += 1
        elif actual == "stale":
            stale += 1
        elif actual == "flaky-empty":
            flaky += 1
        else:
            blocked += 1
        if expected == "live" and actual not in ("live", "flaky-empty"):
            verdict = "REGRESSION"
            regressions += 1
        elif expected == "blocked" and actual == "live":
            verdict = "NEW — now works, consider wiring"
            new_routes += 1
        elif expected == "blocked":
            verdict = "still blocked (expected)"
        elif actual == "flaky-empty":
            verdict = "flaky, known truncation (not a regression)"
        print(f"{paper[:22]:22s} {method[:38]:38s} {actual:12s} "
              f"{n:5d}  {latest or ''} {note} {verdict}")
    print(f"\nALIVE {alive} / STALE {stale} / BLOCKED {blocked} "
          f"/ FLAKY-EMPTY {flaky} — regressions: {regressions}, "
          f"newly working: {new_routes}")
    if regressions:
        print("REGRESSION: a live route is dead — update SOURCES.md "
              "and fix or drop the route.")
        return 1
    if new_routes:
        print("NOTE: a blocked route now works — update SOURCES.md "
              "and consider wiring it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
