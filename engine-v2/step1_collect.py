#!/usr/bin/env python3
"""Sarangsho Plus Engine v2 — Step 1: Collect.

One job only: collect today's news, automatically, free, with no
manual paste needed. Stdlib only. No imports from v1 (engine/,
tools/collector/) — the working v1 collector's logic was adapted,
not imported. Never writes into v1 directories.

Routes (verified live from this VM; see
tools/collector/ROUTES.md for the full table):
  * Bing News RSS — PRIMARY. Direct publisher URLs, unwrapped from
    the apiclick `url=` parameter. Queries cover Bangladesh,
    economy, politics, bank, education/jobs, and site: searches
    for the five papers.
  * Google News RSS — DISCOVERY. Redirect links are kept as-is
    (they open the real article in a browser); no body is fetched
    from them. NOTE: news.google.com/robots.txt disallows /rss/
    for generic crawlers, so a strict robots check marks this
    route dead — recorded honestly in the per-source report
    rather than fetched anyway.
  * Prothom Alo English /feed — RSS, direct URLs, bodies fetchable.
  * Prothom Alo news sitemap — the sitemap leg of the per-paper
    chain (RSS first, then news sitemap, then section links).
  * TBS sitemap index — the index loads; its 2026 children
    (sitemap-2026-1.xml, 50,000 URLs; sitemap-2026-2.xml) carry
    lastmod dates. Plain sitemaps have no titles, so the title is
    derived from the URL slug (never invented) — and then, for
    cluster mains only, the real headline is fetched from the
    article page itself (og:title, then <title>, then <h1>) before
    Step 3 decides, so no page item ever shows a slug headline.
    The same fetch also captures the article's lead image
    (og:image, resolved against the article URL, http(s) only) as
    ``image_url`` on the article record — the URL only, never
    downloaded; "" when the page carries none.
    Only children whose lastmod is within 2 days are fetched, and
    only items with lastmod in the window are kept.
  * Daily Star sitemap — the index is IncompleteRead from this VM,
    so the 2026 child (sitemaps/2026/sitemap-2026-1.xml) is wired
    directly. It is flaky: the server often closes mid-read and
    the tail (newest items) is lost, so on a truncated fetch it
    yields 0 fresh items. When it yields 0, the section-page leg
    runs instead (see below).
  * Daily Star section pages — last-resort leg, only when the
    sitemap leg yields 0 fresh items. Section cards carry
    <time datetime="...">, so only same-window items are kept;
    title comes from the card's aria-label, never invented.
  * Jugantor news sitemap — Bangla daily; a real news sitemap
    (news:title + news:publication_date), ~500 items in 48 h.
  * Prothom Alo Bangla /feed — RSS, 55 items, fresh.
  * Prothom Alo Bangla news sitemap (Level 1, wired 2026-11-15) —
    real news sitemap, ~470 items in 48 h, fresh. Overlaps the
    /feed leg heavily; URL dedup collapses the overlap.
  * bdnews24 news sitemap (Level 1, wired 2026-11-15) — real news
    sitemap, ~124 items, fresh. Its /rss and /feed paths return
    the homepage HTML, not a feed.
  * Bing site: queries (Level 1, wired 2026-11-15) — the ONLY
    working route from this VM for Ittefaq, Bangla Tribune,
    Jago News 24, bdnews24 (redundant with its sitemap, kept for
    consistency with the five English papers), UNB and BSS
    (verification-only agencies) and New Age — all fresh on the
    2026-11-15 probe.
  * Editorial Bing News RSS — path-qualified site: queries for
    the opinion/editorial sections (/opinion, /thoughts for TBS,
    /editorial for FE), tagged section="editorial",
    found_via="editorial". UNQUOTED queries only — quoted
    "site:..." queries return 0 items.

DROPPED (verified stale/blocked, kept visible, never silently
retried): TBS RSS (latest 12 Nov 2021), Daily Star RSS (latest
1 Jun 2026), Dhaka Tribune (every route 403/404 — entirely
unreachable from this VM), New Age (403), Daily Observer
(unreachable), BSS (403), Kaler Kantho (403), Ittefaq (403),
FE sitemap (IncompleteRead; its section page has links but no
publish dates in the static HTML, so same-day cannot be
verified), Daily Star sitemap index (IncompleteRead — the 2026
child is wired directly instead). Level 1 probe 2026-11-15 adds:
Bangladesh Pratidin (403 on every route; Bing site: returns 0
items), Samakal (sitemap index loads but every daily child is
403 — Cloudflare challenge page, verified with curl too),
Bonik Barta (every path returns the same 61 KB SPA shell; Bing
site: latest Sep 2024, stale), Bangla Tribune / Jago News 24 /
UNB / BSS / New Age direct routes (403/404/closed — all reached
via Bing site: queries instead).

Robots: common.robots_allowed() is checked before ANY fetch
(source feeds, sitemaps, and article bodies). A disallowed
source is recorded dead with that reason, not fetched.

Dedup (exactly per the user's script): strip tracking parts of
URLs; normalise Bangla text (NFC, Bangla digits -> English,
zero-width removed); compare title + first 200 characters by
character 3-5-gram overlap; boost the match if numbers, dates or
names are shared; cluster within 48 hours. Main article picked
by: official source/BSS first, then established dailies, then
portals; then earliest; then most detailed. Cluster size is
stored for information ONLY — it must NEVER affect keep/reject,
and later steps must not read it for decisions.

Full text is fetched ONLY for Step-3-kept articles: this module
does NOT fetch bodies by default. fetch_bodies_for_kept() fetches
body text for a given list of kept article dicts (direct URLs
only; Google News redirects get body_error "no direct URL").
The --bodies flag does nothing unless --keep-ids <file> is given.

Usage:
  python3 step1_collect.py --date YYYY-MM-DD [--bodies --keep-ids FILE]
  python3 step1_collect.py --check [--date YYYY-MM-DD]
  python3 step1_collect.py --sources

Outputs (runs/<date>/):
  articles-<date>.json  {"date", "collected", "articles": [...]}
    — every collected item (one per unique URL), ids a001... in
      collection order. Duplicates are NOT dropped from this file:
      they are grouped in clusters-<date>.json, and Step 3 decides
      only each cluster's main article (see clusters file).
  sources-<date>.json   per-source {"method","status","items","fresh",
                        "latest_item","last_success"}
  clusters-<date>.json  [{"members": [ids], "main_id": "...",
                        "size": N, "members_detail": [...]}]
    — every member id resolves to an article in articles-<date>.json.
"""
import argparse
import concurrent.futures
import html as _html
import json
import re
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

VERSION = "2.3.0"
BASE = Path(__file__).resolve().parent
STATE_PATH = BASE / "state" / "sources.json"
RUNS_DIR = BASE / "runs"

BING_QUERIES = [
    "Bangladesh",
    "Bangladesh economy",
    "Bangladesh politics",
    "Bangladesh bank",
    "Bangladesh education jobs",
    "site:thedailystar.net",
    "site:tbsnews.net",
    "site:dhakatribune.com",
    "site:thefinancialexpress.com.bd",
    "site:en.prothomalo.com",
    # Level 1 (added 2026-11-15): Bangla + digital + agency papers
    # whose direct routes are dead from this VM — Bing is the only
    # working route for them (probe 2026-11-15, all fresh).
    "site:ittefaq.com.bd",
    "site:banglatribune.com",
    "site:jagonews24.com",
    "site:bdnews24.com",
    "site:unb.com.bd",
    "site:bssnews.net",
    "site:newagebd.net",
]
EDITORIAL_BING_QUERIES = [
    "site:thedailystar.net/opinion",
    "site:en.prothomalo.com/opinion",
    "site:tbsnews.net/thoughts",
    "site:thefinancialexpress.com.bd/editorial",
    "site:dhakatribune.com/opinion",
]
GN_QUERIES = [
    "Bangladesh",
    "Bangladesh economy",
    "Bangladesh politics",
    "Bangladesh bank",
    "Bangladesh education jobs",
    "site:thedailystar.net",
    "site:tbsnews.net",
    "site:dhakatribune.com",
    "site:thefinancialexpress.com.bd",
]
PROTHOM_ALO_FEED = "https://en.prothomalo.com/feed"
PROTHOM_ALO_NEWS_SITEMAP = "https://en.prothomalo.com/news_sitemap.xml"
TBS_SITEMAP_INDEX = "https://www.tbsnews.net/sitemap.xml"
DAILY_STAR_SITEMAP_FMT = ("https://www.thedailystar.net/sitemaps/{year}/"
                          "sitemap-{year}-1.xml")
JUGANTOR_NEWS_SITEMAP = "https://www.jugantor.com/news_sitemap.xml"
PROTHOM_ALO_BN_FEED = "https://www.prothomalo.com/feed"
PROTHOM_ALO_BN_NEWS_SITEMAP = "https://www.prothomalo.com/news_sitemap.xml"
BDNEWS24_NEWS_SITEMAP = "https://bdnews24.com/news_sitemap.xml"
DAILY_STAR_BASE = "https://www.thedailystar.net"
# Last-resort leg for the Daily Star: section front pages. Only run
# when the sitemap leg yields 0 fresh items (see collect()).
DAILY_STAR_SECTIONS = [
    ("https://www.thedailystar.net/news/bangladesh", "Bangladesh"),
    ("https://www.thedailystar.net/business", "Business"),
    ("https://www.thedailystar.net/news/world", "World"),
]

DROPPED = [
    ("The Daily Star RSS", "https://www.thedailystar.net/rss.xml",
     "HTTP 200 but latest item 1 Jun 2026 (stale) — rechecked 15 Nov 2026"),
    ("TBS RSS", "https://www.tbsnews.net/rss.xml",
     "HTTP 200 but latest item 12 Nov 2021 (stale) — rechecked 15 Nov 2026"),
    ("Dhaka Tribune /feed", "https://www.dhakatribune.com/feed",
     "HTTP 404; /rss and /rss.xml 403, sitemap 403, section pages 403 — "
     "entirely unreachable from this VM (rechecked 15 Nov 2026)"),
    ("New Age", "https://www.newagebd.net/",
     "HTTP 403 (Cloudflare) on homepage, RSS and sitemap — rechecked 15 Nov 2026"),
    ("The Daily Observer", "https://www.observerbd.com/",
     "unreachable from this VM"),
    ("BSS", "https://www.bssnews.net/",
     "HTTP 403"),
    ("Kaler Kantho", "https://www.kalerkantho.com/rss",
     "HTTP 403 on RSS and sitemap (rechecked 15 Nov 2026)"),
    ("Ittefaq", "https://www.ittefaq.com.bd/rss",
     "HTTP 403 on RSS and sitemap (rechecked 15 Nov 2026)"),
    ("Financial Express sitemap", "https://thefinancialexpress.com.bd/sitemap.xml",
     "IncompleteRead (0 bytes) on every attempt from this VM; section "
     "page has article links but no publish dates in the static HTML, "
     "so same-day cannot be verified (rechecked 15 Nov 2026)"),
    ("Daily Star sitemap index", "https://www.thedailystar.net/sitemap.xml",
     "IncompleteRead (0 bytes) from this VM — the 2026 child sitemap "
     "is wired directly instead (rechecked 15 Nov 2026)"),
    # Level 1 probe, 2026-11-15 (all direct attempts from this VM).
    ("Bangladesh Pratidin", "https://www.bd-pratidin.com/rss",
     "HTTP 403 on RSS, /feed and every sitemap tried; Bing site: "
     "query returns 0 items — unreachable from this VM"),
    ("Kaler Kantho", "https://www.kalerkantho.com/rss",
     "HTTP 403 on RSS and sitemap (rechecked 15 Nov 2026); Bing "
     "site: query returns items but latest is 31 Jul 2026 (stale)"),
    ("Samakal", "https://samakal.com/sitemap/sitemap-daily-2026-11-15.xml",
     "sitemap index loads (2,513 daily children) but every daily "
     "child is 403 — Cloudflare 'Just a moment...' challenge page "
     "(verified with curl as well as urllib, 15 Nov 2026)"),
    ("Bonik Barta", "https://www.bonikbarta.net/rss",
     "HTTP 200 on every path tried (/rss, /rss.xml, /sitemap.xml, "
     "/news_sitemap.xml) but all return the same 61 KB SPA shell — "
     "no feed endpoints at conventional paths; Bing site: query "
     "latest is 10 Sep 2024 (stale)"),
    ("Bangla Tribune (direct)", "https://www.banglatribune.com/rss",
     "HTTP 403 on /rss, 404 on /feed, connection closed on "
     "/sitemap.xml — direct dead; reached via Bing site: query"),
    ("Jago News 24 (direct)", "https://www.jagonews24.com/rss",
     "HTTP 403 on /rss, /feed and /sitemap.xml — direct dead; "
     "reached via Bing site: query"),
    ("UNB (direct)", "https://unb.com.bd/rss",
     "HTTP 404 on /rss, /feed and /sitemap.xml — no feed endpoints; "
     "reached via Bing site: query (verification-only agency)"),
    ("BSS (direct)", "https://www.bssnews.net/rss",
     "HTTP 403 on /rss and /feed — direct dead; reached via Bing "
     "site: query (verification-only agency)"),
    ("New Age (direct)", "https://www.newagebd.net/rss",
     "HTTP 403 on /rss and /sitemap.xml — direct dead; reached via "
     "Bing site: query"),
]

# Keep substantive editorial categories in the candidate set. Relevance is
# decided by the downstream editorial classifier, not by URL section alone.
# Exclude only clearly non-article or site-chrome paths here.
SKIP_URL_PARTS = ["/fashion/", "/opinion/cartoon", "/videos/",
                  "/author/", "/govt-ad/"]

DOMAIN_SOURCES = {
    "thedailystar.net": "The Daily Star",
    "tbsnews.net": "The Business Standard",
    "dhakatribune.com": "Dhaka Tribune",
    "thefinancialexpress.com.bd": "The Financial Express",
    "en.prothomalo.com": "Prothom Alo English",
    "prothomalo.com": "Prothom Alo Bangla",
    "jugantor.com": "Jugantor",
    "ittefaq.com.bd": "Ittefaq",
    "samakal.com": "Samakal",
    "bonikbarta.net": "Bonik Barta",
    "bdnews24.com": "bdnews24",
    "banglatribune.com": "Bangla Tribune",
    "jagonews24.com": "Jago News 24",
    "unb.com.bd": "UNB",
    "kalerkantho.com": "Kaler Kantho",
    "bd-pratidin.com": "Bangladesh Pratidin",
    "apnews.com": "AP News",
    "bssnews.net": "BSS",
    "daily-sun.com": "Daily Sun",
    "newagebd.net": "New Age",
    "observerbd.com": "The Daily Observer",
    "nytimes.com": "The New York Times",
    "bbc.com": "BBC",
    "reuters.com": "Reuters",
    "aljazeera.com": "Al Jazeera",
}

# Main-article ranking tiers (official first, then dailies, then portals).
OFFICIAL_SOURCES = {"BSS", "Bangladesh Sangbad Sangstha"}
DAILY_SOURCES = {
    "The Daily Star", "The Business Standard", "Dhaka Tribune",
    "The Financial Express", "Prothom Alo English", "Prothom Alo",
    "Prothom Alo Bangla", "Jugantor", "Ittefaq", "Samakal",
    "Bonik Barta", "bdnews24", "Bangla Tribune", "Jago News 24",
    "Bangladesh Pratidin", "Kaler Kantho", "UNB",
    "Daily Sun", "New Age", "The Daily Observer", "AP News", "BBC",
    "Reuters", "Al Jazeera", "The New York Times",
}

# Dedup: mean character n-gram Jaccard (n=3,4,5) at or above this
# similarity clusters two items (before the shared-token boost).
SIMILARITY_THRESHOLD = 0.50
# Boost added when the pair shares a number, a date or a name.
SHARED_TOKEN_BOOST = 0.15
CLUSTER_WINDOW = timedelta(hours=48)


def source_from_url(url):
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""
    host = host[4:] if host.startswith("www.") else host
    if host in DOMAIN_SOURCES:
        return DOMAIN_SOURCES[host]
    for dom, name in DOMAIN_SOURCES.items():
        if host.endswith("." + dom):
            return name
    if host.endswith(".msn.com") or host == "msn.com":
        return "MSN"
    return host.replace("-", " ").title() if host else ""


def _grab(block, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
    if not m:
        return ""
    v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m.group(1), flags=re.S)
    return _html.unescape(re.sub(r"<[^>]+>", "", v)).strip()


def _direct_url(link):
    """Bing News RSS wraps the publisher URL in an apiclick link:
    .../apiclick.aspx?...&url=<urlencoded publisher URL>&..."""
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        if "url" in qs and qs["url"]:
            return qs["url"][0]
    except Exception:
        pass
    return link


def _is_direct(url):
    return "news.google.com" not in url and "bing.com/news/apiclick" not in url


def parse_rss_items(text, default_source, found_via, section=""):
    items = []
    for block in re.findall(r"<item>(.*?)</item>", text, re.S):
        title = _grab(block, "title")
        link = _grab(block, "link")
        if not title or not link:
            continue
        if found_via in ("bing", "editorial"):
            link = _direct_url(link)
        link = common.strip_tracking(link)
        source = _grab(block, "source") or default_source
        if not _grab(block, "source"):
            m = re.search(r"<source[^>]*>([^<]+)</source>", block)
            if m:
                source = _html.unescape(m.group(1)).strip()
        if found_via in ("bing", "editorial") and (not source or source == default_source):
            source = source_from_url(link) or default_source
        desc = common.clean_html(_grab(block, "description"))[:600]
        pub = _grab(block, "pubDate") or _grab(block, "dc:date")
        if any(p in link for p in SKIP_URL_PARTS):
            continue
        items.append({"title": title, "url": link, "source": source,
                      "section": section, "published": pub, "summary": desc,
                      "found_via": found_via, "title_source": "feed"})
    return items


def parse_news_sitemap(text, default_source, found_via="rss"):
    """Parse a Google news sitemap: <url> blocks with <loc>,
    <news:title> and <news:publication_date>. No description exists
    in a sitemap, so summary stays empty (never invented)."""
    items = []
    for block in re.findall(r"<url>(.*?)</url>", text, re.S):
        link = common.strip_tracking(_grab(block, "loc"))
        title = _grab(block, "news:title")
        pub = _grab(block, "news:publication_date") or _grab(block, "lastmod")
        if not title or not link:
            continue
        if any(p in link for p in SKIP_URL_PARTS):
            continue
        items.append({"title": title, "url": link,
                      "source": source_from_url(link) or default_source,
                      "section": "", "published": pub, "summary": "",
                      "found_via": found_via, "title_source": "feed"})
    return items


def _title_from_slug(url):
    """Derive a readable title from an article URL slug. The title is
    the slug itself (hyphens -> spaces, trailing numeric id stripped)
    — never invented, just reformatted. Used only for plain sitemaps,
    which carry no <news:title>."""
    try:
        slug = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        slug = urllib.parse.unquote(slug)
        slug = re.sub(r"-\d+$", "", slug)  # trailing article id
        title = slug.replace("-", " ").strip().title()
        return title
    except Exception:
        return ""


def parse_plain_sitemap(text, default_source, found_via="sitemap",
                        cutoff=None):
    """Parse a PLAIN sitemap (<url> blocks with <loc> + <lastmod>,
    no titles — TBS and Daily Star). Titles are derived from the URL
    slug. When `cutoff` (an aware datetime) is given, blocks older
    than it are skipped inline, so a 50,000-URL yearly file yields
    only the in-window items instead of 50,000 stale ones."""
    items = []
    for block in re.findall(r"<url>(.*?)</url>", text, re.S):
        link = common.strip_tracking(_grab(block, "loc"))
        if not link:
            continue
        pub = _grab(block, "lastmod")
        if cutoff and pub:
            dt = common.parse_pubdate(pub)
            if dt and dt < cutoff:
                continue
        if any(p in link for p in SKIP_URL_PARTS):
            continue
        title = _title_from_slug(link)
        if not title:
            continue
        items.append({"title": title, "url": link,
                      "source": source_from_url(link) or default_source,
                      "section": "", "published": pub, "summary": "",
                      "found_via": found_via, "title_source": "slug"})
    return items


def parse_section_links(text, base_url, default_source, found_via="section",
                        cutoff=None):
    """Parse a section front page for article links. Each article card
    must carry a <time datetime="..."> — links without a parseable
    date are dropped, because same-day cannot be verified for them
    (the FE section page fails exactly this test: links, no dates).
    The title comes from the card link's aria-label, never invented.
    Only items at/after `cutoff` are kept (None keeps all)."""
    items, seen = [], set()
    for m in re.finditer(r"<a\s[^>]*href=\"([^\"]+)\"[^>]*>", text, re.I):
        href = _html.unescape(m.group(1)).strip()
        if not href.startswith("/") or href in seen:
            continue
        if not re.match(r"^/(news|business|opinion|sports)/", href):
            continue
        if any(p in href for p in SKIP_URL_PARTS):
            continue
        tag = m.group(0)
        label = re.search(r'aria-label="([^"]+)"', tag)
        if not label:
            continue
        title = _html.unescape(label.group(1)).strip()
        if not title:
            continue
        # The card's <time datetime="..."> follows the link.
        tm = re.search(r"<time[^>]*datetime=\"([^\"]+)\"",
                       text[m.end():m.end() + 2000], re.I)
        if not tm:
            continue
        pub = tm.group(1)
        dt = common.parse_pubdate(pub)
        if not dt:
            continue
        if cutoff and dt < cutoff:
            continue
        link = common.strip_tracking(
            urllib.parse.urljoin(base_url, href))
        seen.add(href)
        items.append({"title": title, "url": link,
                      "source": source_from_url(link) or default_source,
                      "section": "", "published": pub, "summary": "",
                      "found_via": found_via, "title_source": "feed"})
    return items


# ---------------------------------------------------------------- state

def load_state():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                          encoding="utf-8")


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------- route fetching

def _fetch_route(url, name, report, method, state):
    """Fetch one route, respecting robots.txt. Returns the raw text
    or None. Every outcome (ok / robots-blocked / fetch failed) is
    recorded in `report` and, on success, in the persisted state."""
    if not common.robots_allowed(url):
        report[name] = {"method": method,
                        "status": "blocked by robots.txt",
                        "items": 0, "fresh": False, "latest_item": None,
                        "last_success": state.get(name, {}).get("last_success")}
        return None
    try:
        text = common.fetch_text(url)
    except Exception as e:
        report[name] = {"method": method,
                        "status": f"fetch failed: {e}",
                        "items": 0, "fresh": False, "latest_item": None,
                        "last_success": state.get(name, {}).get("last_success")}
        return None
    state[name] = {"method": method, "last_success": _now_iso()}
    return text


def _report_items(name, report, method, items, state):
    dates = [common.parse_pubdate(i["published"]) for i in items]
    dates = [d for d in dates if d]
    latest = max(dates).isoformat() if dates else None
    is_fresh = bool(dates) and (datetime.now(timezone.utc) - max(dates)).days <= 2
    report[name] = {"method": method,
                    "status": f"HTTP 200, {len(items)} items",
                    "latest_item": latest, "items": len(items),
                    "fresh": is_fresh,
                    "last_success": state.get(name, {}).get("last_success")}
    return is_fresh


def collect_bing(report, state):
    all_items = []
    for q in BING_QUERIES:
        url = ("https://www.bing.com/news/search?q="
               + urllib.parse.quote(q) + "&format=rss")
        name = f"Bing News: {q}"
        text = _fetch_route(url, name, report, "bing-rss", state)
        if text is None:
            continue
        items = parse_rss_items(text, "Bing News", "bing")
        _report_items(name, report, "bing-rss", items, state)
        all_items.extend(items)
    return all_items


def collect_editorial_bing(report, state):
    all_items = []
    for q in EDITORIAL_BING_QUERIES:
        url = ("https://www.bing.com/news/search?q="
               + urllib.parse.quote(q) + "&format=rss")
        name = f"Editorial Bing: {q}"
        text = _fetch_route(url, name, report, "bing-rss-editorial", state)
        if text is None:
            continue
        items = parse_rss_items(text, "Bing News", "editorial",
                                section="editorial")
        _report_items(name, report, "bing-rss-editorial", items, state)
        all_items.extend(items)
    return all_items


def collect_googlenews(report, state):
    all_items = []
    for q in GN_QUERIES:
        url = ("https://news.google.com/rss/search?q="
               + urllib.parse.quote(q) + "&hl=en-GB&gl=BD&ceid=BD:en")
        name = f"Google News: {q}"
        text = _fetch_route(url, name, report, "google-news-rss", state)
        if text is None:
            continue
        items = parse_rss_items(text, "Google News", "google-news")
        _report_items(name, report, "google-news-rss", items, state)
        all_items.extend(items)
    return all_items


def collect_prothomalo(report, state):
    name = "Prothom Alo English"
    text = _fetch_route(PROTHOM_ALO_FEED, name, report, "rss", state)
    if text is None:
        return []
    items = parse_rss_items(text, name, "rss")
    _report_items(name, report, "rss", items, state)
    return items


def collect_prothomalo_sitemap(report, state):
    name = "Prothom Alo English news sitemap"
    text = _fetch_route(PROTHOM_ALO_NEWS_SITEMAP, name, report, "sitemap", state)
    if text is None:
        return []
    items = parse_news_sitemap(text, "Prothom Alo English",
                               found_via="sitemap")
    _report_items(name, report, "sitemap", items, state)
    return items


def _window_cutoff():
    """Start of the 2-day collection window, from right now."""
    return datetime.now(timezone.utc) - timedelta(days=2)


def collect_tbs_sitemap(report, state):
    """TBS sitemap index -> its fresh children (plain sitemaps,
    titles from slugs). Only children whose <lastmod> is inside
    the 2-day window are fetched."""
    name = "TBS sitemap index"
    text = _fetch_route(TBS_SITEMAP_INDEX, name, report, "sitemap-index",
                        state)
    if text is None:
        return []
    cutoff = _window_cutoff()
    children = []
    for block in re.findall(r"<sitemap>(.*?)</sitemap>", text, re.S):
        loc = _grab(block, "loc")
        mod = _grab(block, "lastmod")
        if not loc:
            continue
        dt = common.parse_pubdate(mod) if mod else None
        if dt and dt >= cutoff:
            children.append(loc)
    report[name] = {"method": "sitemap-index",
                    "status": f"HTTP 200, {len(children)} fresh child "
                              f"sitemap(s)",
                    "items": len(children), "fresh": bool(children),
                    "latest_item": None,
                    "last_success": state.get(name, {}).get("last_success")}
    all_items = []
    for child in children:
        cname = "TBS sitemap " + child.rsplit("/", 1)[-1].replace(
            "sitemap-", "").replace(".xml", "")
        ctext = _fetch_route(child, cname, report, "sitemap", state)
        if ctext is None:
            continue
        items = parse_plain_sitemap(ctext, "The Business Standard",
                                    "sitemap", cutoff=cutoff)
        _report_items(cname, report, "sitemap", items, state)
        all_items.extend(items)
    return all_items


def collect_dailystar_sitemap(report, state, day):
    """Daily Star yearly sitemap child, wired directly (the index is
    IncompleteRead from this VM). The server often closes mid-read
    and the tail — the newest items — is lost, so a truncated fetch
    yields 0 fresh items; that is recorded honestly, and collect()
    then falls back to the section-page leg."""
    year = (day or "")[:4] or str(datetime.now(timezone.utc).year)
    url = DAILY_STAR_SITEMAP_FMT.format(year=year)
    name = f"Daily Star sitemap {year}"
    text = _fetch_route(url, name, report, "sitemap", state)
    if text is None:
        return []
    items = parse_plain_sitemap(text, "The Daily Star", "sitemap",
                                cutoff=_window_cutoff())
    _report_items(name, report, "sitemap", items, state)
    return items


def collect_dailystar_sections(report, state):
    """Last-resort leg for the Daily Star: section front pages.
    Only links with a <time datetime="..."> inside the window are
    kept (same-day verifiable)."""
    cutoff = _window_cutoff()
    all_items = []
    for url, section in DAILY_STAR_SECTIONS:
        name = f"Daily Star section: {section}"
        text = _fetch_route(url, name, report, "section", state)
        if text is None:
            continue
        items = parse_section_links(text, DAILY_STAR_BASE,
                                    "The Daily Star", "section",
                                    cutoff=cutoff)
        _report_items(name, report, "section", items, state)
        all_items.extend(items)
    return all_items


def collect_jugantor(report, state):
    """Jugantor (Bangla daily) news sitemap — real news sitemap
    with titles and publication dates."""
    name = "Jugantor news sitemap"
    text = _fetch_route(JUGANTOR_NEWS_SITEMAP, name, report, "sitemap",
                        state)
    if text is None:
        return []
    items = parse_news_sitemap(text, "Jugantor", found_via="sitemap")
    _report_items(name, report, "sitemap", items, state)
    return items


def collect_prothomalo_bn(report, state):
    """Prothom Alo Bangla /feed — RSS, direct URLs."""
    name = "Prothom Alo Bangla"
    text = _fetch_route(PROTHOM_ALO_BN_FEED, name, report, "rss", state)
    if text is None:
        return []
    items = parse_rss_items(text, name, "rss")
    _report_items(name, report, "rss", items, state)
    return items


def collect_prothomalo_bn_sitemap(report, state):
    """Prothom Alo Bangla news sitemap (Level 1, wired 2026-11-15):
    real news sitemap, ~470 items in 48 h, fresh. The /feed leg
    above overlaps it heavily; URL dedup collapses the overlap."""
    name = "Prothom Alo Bangla news sitemap"
    text = _fetch_route(PROTHOM_ALO_BN_NEWS_SITEMAP, name, report,
                        "sitemap", state)
    if text is None:
        return []
    items = parse_news_sitemap(text, "Prothom Alo Bangla",
                               found_via="sitemap")
    _report_items(name, report, "sitemap", items, state)
    return items


def collect_bdnews24_sitemap(report, state):
    """bdnews24 news sitemap (Level 1, wired 2026-11-15): real news
    sitemap, ~124 items, fresh. Its /rss and /feed paths return the
    homepage HTML, not a feed — the sitemap is the only direct
    route that works."""
    name = "bdnews24 news sitemap"
    text = _fetch_route(BDNEWS24_NEWS_SITEMAP, name, report, "sitemap",
                        state)
    if text is None:
        return []
    items = parse_news_sitemap(text, "bdnews24", found_via="sitemap")
    _report_items(name, report, "sitemap", items, state)
    return items


# ---------------------------------------------------------------- dedup

def _numbers(text):
    return set(re.findall(r"\d+", common.norm_bangla(text or "")))


def _names(text):
    """Capitalised words (length >= 3) — a rough proxy for proper
    names in English headlines; used only for the shared-token boost."""
    return {w for w in re.findall(r"[A-Z][a-z]{2,}", text or "")}


def _compare_text(item):
    """The text dedup compares: normalised title + first 200 chars
    of the summary (the body is not fetched in Step 1)."""
    return common.norm_bangla(
        (item.get("title") or "") + " " + (item.get("summary") or "")[:200])


def _similarity(a, b):
    """Mean character n-gram Jaccard (n=3,4,5) over the compare text,
    plus SHARED_TOKEN_BOOST if the pair shares a number, a date or a
    name. Returns (score, boosted: bool)."""
    ta, tb = _compare_text(a), _compare_text(b)
    sims = []
    for n in (3, 4, 5):
        ga, gb = common.ngrams(ta, n), common.ngrams(tb, n)
        if not ga or not gb:
            sims.append(0.0)
        else:
            sims.append(len(ga & gb) / len(ga | gb))
    score = sum(sims) / len(sims)
    boosted = bool((_numbers(ta) & _numbers(tb))
                   or (_names(a.get("title") or "")
                       & _names(b.get("title") or "")))
    if boosted:
        score += SHARED_TOKEN_BOOST
    return score, boosted


def _within_window(a, b):
    pa = common.parse_pubdate(a.get("published") or "")
    pb = common.parse_pubdate(b.get("published") or "")
    if not pa or not pb:
        return True  # undated items cannot be ruled out by time
    return abs(pa - pb) <= CLUSTER_WINDOW


def cluster_articles(items):
    """Greedy clustering in collection order. Each item joins the
    first existing cluster whose representative (first member) is
    similar enough AND within 48 hours; otherwise it starts a new
    cluster. Returns a list of clusters (lists of item dicts)."""
    clusters = []
    for item in items:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            if not _within_window(item, rep):
                continue
            score, _ = _similarity(item, rep)
            if score >= SIMILARITY_THRESHOLD:
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters


def _source_tier(source):
    if source in OFFICIAL_SOURCES:
        return 0
    if source in DAILY_SOURCES:
        return 1
    return 2


def pick_main(cluster):
    """Main article of a cluster: official source/BSS first, then
    established dailies, then portals; then earliest published;
    then most detailed (longest title + summary). A direct
    publisher URL beats a Google News redirect within the same tier."""
    def key(a):
        pub = common.parse_pubdate(a.get("published") or "")
        return (_source_tier(a.get("source") or ""),
                0 if _is_direct(a.get("url") or "") else 1,
                pub or datetime.max.replace(tzinfo=timezone.utc),
                -(len(a.get("title") or "") + len(a.get("summary") or "")))
    return min(cluster, key=key)


def dedupe_by_url(items):
    """Collapse identical (tracking-stripped) URLs, keeping a direct
    publisher URL over a Google News redirect for the same story."""
    by_url, order = {}, []
    for a in items:
        url = common.strip_tracking(a["url"])
        a["url"] = url
        prev = by_url.get(url)
        if prev is None:
            by_url[url] = a
            order.append(a)
        elif _is_direct(url) and not _is_direct(prev["url"]):
            by_url[url] = a
            order[order.index(prev)] = a
    return order


# ---------------------------------------------------------------- bodies

def fetch_bodies_for_kept(articles):
    """Fetch body text for a given list of kept article dicts (Step 3
    output). Direct URLs only: Google News redirects get body_error
    "no direct URL". A robots.txt disallow gets body_error
    "robots.txt disallows". Returns (ok, tried). Mutates the dicts
    in place (body_text / body_error)."""
    ok = tried = 0
    for a in articles:
        a.setdefault("body_text", "")
        a.setdefault("body_error", "")
        if not _is_direct(a.get("url") or ""):
            a["body_text"] = ""
            a["body_error"] = "no direct URL"
            continue
        if not common.robots_allowed(a["url"]):
            a["body_text"] = ""
            a["body_error"] = "robots.txt disallows"
            continue
        tried += 1
        body = ""
        last_err = ""
        for _attempt in range(2):  # one retry: servers often close mid-read
            try:
                body = common.clean_body_text(
                    common.fetch_text(a["url"]), title=a.get("title") or "")
                last_err = ""
                break
            except Exception as e:
                last_err = str(e)
        if body:
            a["body_text"] = body[:4000]
            a["body_error"] = ""
            ok += 1
        else:
            a["body_text"] = ""
            a["body_error"] = last_err
    return ok, tried


# ------------------------------------------------------- slug titles
# Plain sitemaps (TBS, Daily Star) carry no titles, so Step 1 first
# derives a readable title from the URL slug — and then, for cluster
# mains only, replaces it with the real headline fetched from the
# article page itself. This runs BEFORE Step 3 decides: Step 3's
# evidence_quote must be a verbatim substring of the headline +
# summary, so the real title has to be in place first. A titled
# source is always preferred when one exists (TBS has no news
# sitemap — /news-sitemap.xml, /news_sitemap.xml and
# /sitemaps/news.xml all 404, checked 2026-11-15 — and its RSS is
# stale since 12 Nov 2021; article pages carry a clean og:title and
# robots.txt allows article URLs).

TITLE_RESOLVE_WORKERS = 4
TITLE_RESOLVE_BUDGET_SECONDS = 300

_KNOWN_SITE_SUFFIXES = {
    "the business standard", "tbs", "the daily star", "daily star",
    "prothom alo", "jugantor", "the financial express",
    "financial express", "dhaka tribune", "daily sun", "new age",
    "the daily observer", "bss", "bangladesh sangbad sangstha",
    "bdnews24", "bangla tribune", "jago news 24", "ittefaq", "unb",
    "samakal", "bonik barta", "kaler kantho", "bangladesh pratidin",
}


def _strip_site_suffix(title):
    """"Headline | The Business Standard" -> "Headline". Only a
    trailing separator + a KNOWN site name is stripped; anything
    else is left untouched."""
    m = re.match(r"^(.*?)\s*[|\-–—]\s*([^|\-–—]+)$", (title or "").strip())
    if m and m.group(2).strip().lower() in _KNOWN_SITE_SUFFIXES:
        return m.group(1).strip()
    return (title or "").strip()


def _is_bare_date(title):
    """A title that is just a date ("12/11/2026") or a bare year is
    not a headline — it is a govt-ad / archive page's og:title.
    Reject it so the caller falls through to the next title source
    (or keeps the slug title)."""
    t = (title or "").strip()
    return bool(re.fullmatch(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}", t)
                or re.fullmatch(r"(19|20)\d{2}", t))


def extract_page_title(html_text):
    """Real headline from an article page's HTML: og:title first,
    then <title>, then the first <h1>. Site-name suffixes are
    stripped. Returns "" when nothing usable is found — the caller
    keeps the slug-derived title. Never invents a title, never
    uses body text as a headline."""
    if not html_text:
        return ""
    # og:title: scan <meta ...> tags; property/content may appear in
    # either order inside the tag.
    for tag in re.finditer(r"<meta\s+[^>]*>", html_text, re.I):
        attrs = dict(re.findall(r"([\w-]+)\s*=\s*[\"']([^\"']*)[\"']",
                                tag.group(0)))
        if (attrs.get("property", "").lower() == "og:title"
                and attrs.get("content", "").strip()):
            t = _strip_site_suffix(
                _html.unescape(attrs["content"]).strip())
            if t and t.lower() not in _KNOWN_SITE_SUFFIXES \
                    and not _is_bare_date(t):
                return t
    m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.S | re.I)
    if m:
        t = _strip_site_suffix(
            _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip())
        if t and t.lower() not in _KNOWN_SITE_SUFFIXES \
                and not _is_bare_date(t):
            return t
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.S | re.I)
    if m:
        t = _strip_site_suffix(
            _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip())
        if t and t.lower() not in _KNOWN_SITE_SUFFIXES \
                and not _is_bare_date(t):
            return t
    return ""


def extract_page_image(html_text, page_url):
    """Lead image URL from an article page's HTML: the og:image
    content (og:image:url is the same property under another name).
    Relative URLs are resolved against the article URL; only
    http(s) URLs are accepted — a data: URI, another scheme, or an
    empty value returns "". The URL is stored only, never
    downloaded: the app hotlinks the publisher's image with
    attribution. Returns "" when no usable og:image exists."""
    if not html_text:
        return ""
    for tag in re.finditer(r"<meta\s+[^>]*>", html_text, re.I):
        attrs = dict(re.findall(r"([\w-]+)\s*=\s*[\"']([^\"']*)[\"']",
                                tag.group(0)))
        if attrs.get("property", "").lower() not in (
                "og:image", "og:image:url"):
            continue
        raw = _html.unescape(attrs.get("content", "") or "").strip()
        if not raw:
            return ""
        resolved = urllib.parse.urljoin(page_url or "", raw)
        if resolved.startswith(("http://", "https://")):
            return resolved
        return ""
    return ""


def _resolve_one_title(article):
    """Fetch one article page and return its real headline, or ""
    on any failure (robots-disallowed, fetch error, no usable
    title). One retry: servers often close mid-read (the same
    reason fetch_bodies_for_kept retries). The caller keeps the
    slug title on failure."""
    return _resolve_one_page(article)[0]


def _resolve_one_page(article):
    """Fetch one article page and return (real headline, lead image
    URL). ONE fetch serves both: the og:image is extracted from the
    same HTML the headline comes from — never a second request per
    article. On any failure both are "" and the caller keeps the
    slug title and an empty image_url."""
    url = article.get("url") or ""
    if not url or not _is_direct(url):
        return "", ""
    if not common.robots_allowed(url):
        return "", ""
    for _attempt in range(2):
        try:
            html_text = common.fetch_text(url, timeout=20)
            return (extract_page_title(html_text),
                    extract_page_image(html_text, url))
        except Exception:
            continue
    return "", ""


def resolve_slug_titles(articles, clusters=None, max_workers=TITLE_RESOLVE_WORKERS,
                        budget_seconds=TITLE_RESOLVE_BUDGET_SECONDS):
    """Replace slug-derived titles with real headlines for cluster
    mains, BEFORE Step 3 decides. Only mains are fetched: non-mains
    never reach Step 3 or the page, so their slug titles are left
    alone (and honestly marked title_source="slug"). The same fetch
    also captures each main's lead image URL (og:image, resolved
    against the article URL, http(s) only) on the article record as
    ``image_url`` — "" when the page carries none. Mutates the
    article dicts in place (title, title_source, image_url) and the
    clusters' members_detail titles for resolved mains. Fetches run
    in a small thread pool and the whole pass is time-boxed: when
    the budget runs out, remaining mains keep their slug titles.
    Returns (resolved, failed, seconds)."""
    by_id = {a.get("id"): a for a in articles if a.get("id")}
    if clusters is None:
        mains = [a for a in articles
                 if a.get("title_source") == "slug"]
    else:
        main_ids = [c.get("main_id") for c in clusters]
        mains = [by_id[i] for i in main_ids
                 if i in by_id and by_id[i].get("title_source") == "slug"]
    mains = [a for a in mains if _is_direct(a.get("url") or "")]
    resolved = failed = 0
    start = time.monotonic()
    if not mains:
        return 0, 0, 0.0
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers) as pool:
        futures = {pool.submit(_resolve_one_page, a): a for a in mains}
        try:
            done, _ = concurrent.futures.wait(
                futures, timeout=budget_seconds,
                return_when=concurrent.futures.ALL_COMPLETED)
        except Exception:
            done = set()
        for fut, art in futures.items():
            art.setdefault("image_url", "")
            if fut not in done:
                failed += 1  # over budget: slug title kept
                continue
            try:
                title, image_url = fut.result()
            except Exception:
                title, image_url = "", ""
            if image_url:
                art["image_url"] = image_url
            if title:
                art["title"] = title
                art["title_source"] = "page"
                resolved += 1
            else:
                failed += 1
        pool.shutdown(wait=False, cancel_futures=True)
    if clusters is not None:
        detail_by_id = {}
        for c in clusters:
            for d in c.get("members_detail", []):
                detail_by_id[d.get("id")] = d
        for art in mains:
            if art.get("title_source") == "page":
                d = detail_by_id.get(art.get("id"))
                if d is not None:
                    d["title"] = art["title"]
    return resolved, failed, time.monotonic() - start


# ---------------------------------------------------------------- collect

PASTE_DIR = Path(__file__).resolve().parent.parent / "engine" / "paste"


def read_paste_file(day, path=None):
    """Optional extra only. Same file, format and 07:30 deadline as
    v1 (see SWITCH_PLAN.md §2): engine/paste/paste-<day>.md, `## `
    blocks with `- URL:`, `- Source:`, `- Published:`, `- Note:`.
    Returns (articles, found). Articles carry found_via "paste"
    and summary = Note; a pasted Google News redirect gets no body
    and is dropped at Step 4 like any other redirect."""
    p = Path(path) if path is not None else PASTE_DIR / f"paste-{day}.md"
    if not p.exists():
        return [], False
    text = p.read_text(encoding="utf-8")
    articles = []
    for b in re.split(r"^##\s+", text, flags=re.M)[1:]:
        lines = b.strip().splitlines()
        if not lines:
            continue
        title, url, source, pub, note = lines[0].strip(), "", "", "", ""
        for ln in lines[1:]:
            m = re.match(r"-\s*URL:\s*(\S+)", ln)
            if m:
                url = m.group(1).strip()
            m = re.match(r"-\s*Source:\s*(.+)", ln)
            if m:
                source = m.group(1).strip()
            m = re.match(r"-\s*Published:\s*(.+)", ln)
            if m:
                pub = m.group(1).strip()
            m = re.match(r"-\s*Note:\s*(.+)", ln)
            if m:
                note = m.group(1).strip()
        if url and title:
            articles.append({"title": title, "url": url,
                             "source": source or "Pasted by operator",
                             "section": "", "published": pub,
                             "summary": note, "found_via": "paste"})
    return articles, True


def collect(day, bodies=False, keep_ids=None):
    """Run all routes for `day` (YYYY-MM-DD). Returns
    (articles, report, clusters, meta) where articles is every
    collected item (ids a001... in collection order), clusters
    groups them by story with one main article each, and meta
    carries counts. Step 3 decides only cluster mains. Bodies are
    fetched only when bodies=True AND a keep_ids set is given;
    --bodies alone does nothing."""
    state = load_state()
    report, all_items = {}, []
    for fn in (collect_bing, collect_googlenews, collect_prothomalo,
               collect_prothomalo_sitemap, collect_editorial_bing,
               collect_tbs_sitemap, collect_jugantor,
               collect_prothomalo_bn, collect_prothomalo_bn_sitemap,
               collect_bdnews24_sitemap):
        all_items.extend(fn(report, state))
    ds_items = collect_dailystar_sitemap(report, state, day)
    all_items.extend(ds_items)
    if not ds_items:
        # Sitemap leg came back empty (usually a truncated fetch) —
        # fall back to the section-page leg, the last resort.
        all_items.extend(collect_dailystar_sections(report, state))
    # Paste (optional extra, same file/format/deadline as v1):
    # engine/paste/paste-<day>.md, merged before dedup so a pasted
    # article competes normally for cluster main.
    paste_articles, paste_found = read_paste_file(day)
    if paste_articles:
        all_items.extend(paste_articles)
    report["paste"] = {"method": "paste",
                       "status": (f"found, {len(paste_articles)} articles"
                                  if paste_found else "no paste file"),
                       "items": len(paste_articles),
                       "fresh": paste_found,
                       "latest_item": (paste_articles[0]["title"]
                                       if paste_articles else None),
                       "last_success": (datetime.now(timezone.utc).isoformat()
                                        if paste_found else None)}
    save_state(state)
    for name, url, why in DROPPED:
        report[f"DROPPED: {name}"] = {"method": "dropped", "status": why,
                                      "items": 0, "fresh": False,
                                      "latest_item": None, "last_success": None}
    uniq = dedupe_by_url(all_items)
    cutoff = (datetime.fromisoformat(day) - timedelta(days=2)).replace(
        tzinfo=timezone.utc)
    kept, dropped_stale = [], 0
    for a in uniq:
        pub = common.parse_pubdate(a.get("published") or "")
        if pub and pub < cutoff:
            dropped_stale += 1
            continue
        kept.append(a)
    # Ids in collection order, before clustering, so cluster member
    # ids are stable and auditable.
    for i, a in enumerate(kept, 1):
        a["id"] = f"a{i:03d}"
        a.setdefault("body_text", "")
        a.setdefault("body_error", "")
        # Lead image URL (og:image), filled by resolve_slug_titles
        # below for fetched cluster mains only; "" everywhere else
        # (feed-titled mains are never fetched, so they carry none).
        a.setdefault("image_url", "")
    raw_clusters = cluster_articles(kept)
    # articles = every kept item, ids consecutive in collection
    # order; clusters group them and name one main per story.
    articles = kept
    clusters = []
    for members in raw_clusters:
        main = pick_main(members)
        clusters.append({
            "members": [m["id"] for m in members],
            "main_id": main["id"],
            # NOTE: size is informational only. It must NEVER affect
            # keep/reject, and later steps must not read it for
            # decisions — it exists so a human can see how widely a
            # story was carried.
            "size": len(members),
            "members_detail": [{"id": m["id"], "title": m["title"],
                                "url": m["url"], "source": m["source"]}
                               for m in members],
        })
    body_ok = body_tried = 0
    if bodies and keep_ids:
        wanted = [a for a in articles if a["id"] in keep_ids]
        body_ok, body_tried = fetch_bodies_for_kept(wanted)
    # Titles: plain-sitemap mains still carry slug-derived titles.
    # Resolve the real headline from the article page for every
    # cluster main NOW — before Step 3 decides, so every
    # evidence_quote is drawn from the real headline. Non-mains
    # keep their slug titles (they never reach Step 3 or the page).
    title_resolved, title_failed, title_secs = resolve_slug_titles(
        articles, clusters)
    meta = {"dropped_stale": dropped_stale,
            "paste_file_found": paste_found,
            "paste_count": len(paste_articles),
            "raw_items": len(all_items), "unique_items": len(uniq),
            "body_ok": body_ok, "body_tried": body_tried,
            "title_resolved": title_resolved,
            "title_failed": title_failed,
            "title_seconds": round(title_secs, 1),
            "robots_fetch_failures": common.robots_fetch_failures()}
    return articles, report, clusters, meta


def print_report(report):
    fresh_n = sum(1 for r in report.values()
                  if r.get("fresh") and r.get("method") != "dropped")
    print(f"[step1] fresh routes: {fresh_n}")
    for name, r in report.items():
        flag = ("FRESH" if r.get("fresh")
                else ("dropped" if r.get("method") == "dropped"
                      else "stale/failed"))
        line = f"  [{flag}] {name}: {r['status']}"
        if r.get("latest_item"):
            line += f" | latest {r['latest_item']}"
        if r.get("last_success"):
            line += f" | last_success {r['last_success']}"
        print(line)


def _load_keep_ids(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return {str(x) for x in data}
    except Exception:
        pass
    return {ln.strip() for ln in text.splitlines() if ln.strip()}


def main():
    ap = argparse.ArgumentParser(
        prog="step1_collect",
        description="Sarangsho Plus engine v2 — Step 1: Collect (v" + VERSION + ")")
    ap.add_argument("--date", default=common.today_dhaka(),
                    help="edition date YYYY-MM-DD (default: today Asia/Dhaka)")
    ap.add_argument("--bodies", action="store_true",
                    help="fetch bodies — only with --keep-ids (Step-3-kept articles)")
    ap.add_argument("--keep-ids", default=None,
                    help="file with kept article ids (one per line, or a JSON list)")
    ap.add_argument("--out", default=None,
                    help="output dir (default: runs/<date>)")
    ap.add_argument("--check", action="store_true",
                    help="freshness report only; write no files")
    ap.add_argument("--sources", action="store_true",
                    help="list collection routes with live/dead status from state")
    args = ap.parse_args()

    if args.sources:
        state = load_state()
        print(f"Sarangsho Plus engine v2 Step 1 v{VERSION} — routes:")
        print("  Bing News RSS (primary, direct URLs):")
        for q in BING_QUERIES:
            name = f"Bing News: {q}"
            ls = state.get(name, {}).get("last_success")
            print(f"    - {q} | last_success: {ls or 'never checked'}")
        print("  Google News RSS (discovery, redirect links):")
        for q in GN_QUERIES:
            name = f"Google News: {q}"
            ls = state.get(name, {}).get("last_success")
            print(f"    - {q} | last_success: {ls or 'never checked'}")
        print(f"  Prothom Alo English /feed: {PROTHOM_ALO_FEED} | "
              f"last_success: {state.get('Prothom Alo English', {}).get('last_success') or 'never checked'}")
        print(f"  Prothom Alo English news sitemap: {PROTHOM_ALO_NEWS_SITEMAP} | "
              f"last_success: {state.get('Prothom Alo English news sitemap', {}).get('last_success') or 'never checked'}")
        print("  Editorial Bing RSS (path-qualified site: queries, tag editorial):")
        for q in EDITORIAL_BING_QUERIES:
            name = f"Editorial Bing: {q}"
            ls = state.get(name, {}).get("last_success")
            print(f"    - {q} | last_success: {ls or 'never checked'}")
        print(f"  TBS sitemap index: {TBS_SITEMAP_INDEX} | "
              f"last_success: {state.get('TBS sitemap index', {}).get('last_success') or 'never checked'}")
        for cname in ("TBS sitemap 2026-1", "TBS sitemap 2026-2"):
            print(f"    - {cname} | last_success: "
                  f"{state.get(cname, {}).get('last_success') or 'never checked'}")
        print(f"  Daily Star sitemap (child wired directly): "
              f"{DAILY_STAR_SITEMAP_FMT.format(year=datetime.now(timezone.utc).year)} | "
              f"last_success: {state.get('Daily Star sitemap ' + str(datetime.now(timezone.utc).year), {}).get('last_success') or 'never checked'}")
        print("  Daily Star section pages (last resort, only when the "
              "sitemap leg yields 0 fresh items):")
        for url, section in DAILY_STAR_SECTIONS:
            ls = state.get(f"Daily Star section: {section}", {}).get("last_success")
            print(f"    - {section} ({url}) | last_success: {ls or 'never checked'}")
        print(f"  Jugantor news sitemap: {JUGANTOR_NEWS_SITEMAP} | "
              f"last_success: {state.get('Jugantor news sitemap', {}).get('last_success') or 'never checked'}")
        print(f"  Prothom Alo Bangla /feed: {PROTHOM_ALO_BN_FEED} | "
              f"last_success: {state.get('Prothom Alo Bangla', {}).get('last_success') or 'never checked'}")
        print(f"  Prothom Alo Bangla news sitemap: {PROTHOM_ALO_BN_NEWS_SITEMAP} | "
              f"last_success: {state.get('Prothom Alo Bangla news sitemap', {}).get('last_success') or 'never checked'}")
        print(f"  bdnews24 news sitemap: {BDNEWS24_NEWS_SITEMAP} | "
              f"last_success: {state.get('bdnews24 news sitemap', {}).get('last_success') or 'never checked'}")
        print("  Dropped (verified stale/blocked — dead by design):")
        for name, url, why in DROPPED:
            print(f"    - {name}: {why}")
        return 0

    day = args.date
    keep_ids = _load_keep_ids(args.keep_ids) if args.keep_ids else None
    if args.bodies and not keep_ids:
        print("[step1] --bodies given without --keep-ids: bodies are "
              "fetched ONLY for Step-3-kept articles, so nothing to do.")
    articles, report, clusters, meta = collect(
        day, bodies=args.bodies, keep_ids=keep_ids)
    print_report(report)
    print(f"[step1] raw items: {meta['raw_items']}, after URL dedup: "
          f"{meta['unique_items']}, dropped stale: {meta['dropped_stale']}, "
          f"articles: {len(articles)} in {len(clusters)} clusters")
    print(f"[step1] slug titles resolved for mains: "
          f"{meta.get('title_resolved', 0)} page / "
          f"{meta.get('title_failed', 0)} kept slug "
          f"({meta.get('title_seconds', 0)}s)")
    if meta["robots_fetch_failures"]:
        print(f"[step1] robots.txt fetch failures (fail-open, allowed): "
              f"{meta['robots_fetch_failures']}")
    if args.bodies and keep_ids:
        print(f"[step1] bodies fetched: {meta['body_ok']}/{meta['body_tried']} kept URLs")
    if args.check:
        fresh_n = sum(1 for r in report.values()
                      if r.get("fresh") and r.get("method") != "dropped")
        print(f"[step1] CHECK: {fresh_n} fresh routes, {len(articles)} "
              f"articles in window (no files written)")
        return 0 if fresh_n and articles else 1
    outdir = Path(args.out) if args.out else RUNS_DIR / day
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"articles-{day}.json").write_text(
        json.dumps({"date": day, "collected": len(articles),
                    "articles": articles},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / f"sources-{day}.json").write_text(
        json.dumps({"date": day, "sources": report},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / f"clusters-{day}.json").write_text(
        json.dumps({"date": day, "clusters": clusters},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[step1] {day}: {len(articles)} articles in "
          f"{len(clusters)} clusters. Wrote {outdir}/")
    return 0 if articles else 1


if __name__ == "__main__":
    raise SystemExit(main())
