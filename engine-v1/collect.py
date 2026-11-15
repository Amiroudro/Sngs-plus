#!/usr/bin/env python3
"""Module 1 — Collect (ENGINE_DESIGN §5). SUPERSEDED 2026-11-07.

This file is kept for reproducibility of the 8 Nov 2026 proof run
only. The daily engine now collects with the Sarangsho Plus Collector
at tools/collector/collect.py (run_daily.py calls that instead):
fully automated, free, no paste needed — Bing News RSS (direct
publisher URLs) + Google News RSS (discovery) + Prothom Alo feed,
with the paste file as an optional extra only. See
tools/collector/README.md and tools/collector/ROUTES.md for the
verified routes. Do not extend this file; fix collection in the
Collector instead.

Original docstring (for the record):
Tries RSS first, then sitemaps, then article pages. Records exactly how
each article was found and how fresh each source is — it never pretends
a stale feed is live.

Proven staleness (re-checked 2026-11-07/08 by this engine):
  Daily Star RSS  — 200 OK but latest item 1 Jun 2026 (STALE).
  TBS RSS         — 200 OK but latest items 2019/2021 (STALE).
  Dhaka Tribune /feed — 404.
  Financial Express rss.xml — returns the homepage HTML, not a feed.
  New Age / Observer RSS — 403 (Cloudflare).
  Prothom Alo English /feed — FRESH on 2026-11-07 (10 items, all 7 Nov).
  FE sitemap — 200 OK, 79 URLs (usable as a link list).

Paste fallback (the reliable route): the operator pastes the articles
they read that day into engine/paste/paste-YYYY-MM-DD.md, one block per
article:
    ## <headline>
    - Source: <publication>
    - URL: <direct article URL>
    - Published: <date, optional>
    - Note: <one line, optional>
Collect merges paste articles with feed articles, de-duplicates by URL,
drops items older than the coverage window (when a date is known) and
writes runs/<date>/articles-<date>.json + a freshness report.

Usage:
  python3 collect.py --date 2026-11-08 [--bodies] [--out runs/2026-11-08]
  --bodies  also fetches each article page and stores cleaned body text
            (first ~4000 chars) so Summarise works from real text.
Only stdlib. No API key.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SOURCES, fetch, fetch_text, clean_html, parse_pubdate,
                    save_json, today)

SKIP_URL_PARTS = ["/sports/", "/sports", "/entertainment/", "/lifestyle/",
                  "/fashion/", "/opinion/cartoon"]
KEEP_HINTS = ["econom", "bank", "trade", "inflation", "budget", "policy",
              "reform", "election", "parliament", "diploma", "foreign",
              "climate", "energy", "remittance", "export", "import", "wage",
              "labour", "education", "health", "governance", "court",
              "recruit", "admission", "police", "accident", "rally"]


def sanitize_xml(raw: bytes) -> bytes:
    text = raw.decode("utf-8", "ignore")
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;)[a-zA-Z]+;", " ", text)
    return text.encode("utf-8")


def parse_rss_items(raw_text, source, day):
    items = []
    for block in re.findall(r"<item>(.*?)</item>", raw_text, re.S):
        def grab(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
            if not m:
                return ""
            v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m.group(1), flags=re.S)
            return v.strip()
        title = re.sub(r"<[^>]+>", "", grab("title")).strip()
        import html as _html
        title = _html.unescape(title)
        link = grab("link")
        desc = clean_html(grab("description"))[:600]
        pub = grab("pubDate") or grab("dc:date")
        if not title or not link:
            continue
        if any(p in link for p in SKIP_URL_PARTS):
            continue
        items.append({"title": title, "url": link, "source": source,
                      "section": "", "published": pub, "summary": desc,
                      "found_via": "rss"})
    return items


def try_rss(source, url, day, report):
    try:
        raw = fetch(url)
    except Exception as e:
        report[source] = {"method": "rss", "status": f"fetch failed: {e}",
                          "items": 0, "fresh": False}
        return []
    text = raw.decode("utf-8", "ignore")
    if "<item>" not in text and "<rss" not in text[:500]:
        report[source] = {"method": "rss", "status": "returned non-RSS content "
                          "(probably homepage HTML)", "items": 0, "fresh": False}
        return []
    try:
        ET.fromstring(sanitize_xml(raw))
    except Exception:
        pass  # regex fallback below handles malformed feeds
    items = parse_rss_items(text, source, day)
    dates = [parse_pubdate(i["published"]) for i in items]
    dates = [d for d in dates if d]
    latest = max(dates).isoformat() if dates else None
    fresh = False
    if dates:
        newest = max(dates)
        fresh = (datetime.now(timezone.utc) - newest).days <= 2
    report[source] = {"method": "rss", "status": f"HTTP 200, {len(items)} items",
                      "latest_item": latest, "items": len(items), "fresh": fresh}
    return items


def try_sitemap(source, url, day, report):
    try:
        text = fetch_text(url)
    except Exception as e:
        report[source] = {"method": "sitemap", "status": f"fetch failed: {e}",
                          "items": 0, "fresh": False}
        return []
    if "<urlset" not in text:
        report[source] = {"method": "sitemap",
                          "status": "not a urlset (sitemap index or HTML)",
                          "items": 0, "fresh": False}
        return []
    urls = re.findall(r"<loc>(.*?)</loc>", text)
    mods = re.findall(r"<lastmod>(.*?)</lastmod>", text)
    if not mods:
        # A sitemap is a link list, not headlines: slug-derived titles
        # would be invented headlines. Record the count honestly and
        # return no articles — the operator reads these via paste.
        report[source] = {"method": "sitemap",
                          "status": f"HTTP 200, {len(urls)} urls but no "
                          "<lastmod> dates — no headlines extractable, "
                          "use as a reading list / paste source",
                          "items": 0, "fresh": False}
        return []
    items = []
    for u, m in zip(urls, mods):
        if any(p in u for p in SKIP_URL_PARTS):
            continue
        items.append({"title": u.rstrip("/").split("/")[-1].replace("-", " "),
                      "url": u, "source": source, "section": "",
                      "published": m, "summary": "",
                      "found_via": "sitemap"})
    dates = [parse_pubdate(m) for m in mods]
    dates = [d for d in dates if d]
    latest = max(dates).isoformat() if dates else None
    fresh = bool(dates) and (datetime.now(timezone.utc) - max(dates)).days <= 2
    report[source] = {"method": "sitemap",
                      "status": f"HTTP 200, {len(urls)} urls",
                      "latest_item": latest, "items": len(items), "fresh": fresh}
    return items


def read_paste_file(path: Path):
    """Parse engine/paste/paste-YYYY-MM-DD.md. Returns (articles, count)."""
    if not path.exists():
        return [], False
    text = path.read_text(encoding="utf-8")
    articles = []
    blocks = re.split(r"^##\s+", text, flags=re.M)
    for b in blocks[1:]:
        lines = b.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        url = source = pub = note = ""
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


def fetch_bodies(articles):
    n = 0
    for a in articles:
        try:
            body = clean_html(fetch_text(a["url"]))
            # Cut site chrome: start at the headline if present.
            i = body.find(a["title"][:40])
            a["body_text"] = (body[i:i + 4000] if i >= 0 else body[:4000])
            n += 1
        except Exception as e:
            a["body_text"] = ""
            a["body_error"] = str(e)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today())
    ap.add_argument("--bodies", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    day = args.date
    outdir = Path(args.out) if args.out else Path(__file__).resolve().parent / "runs" / day
    outdir.mkdir(parents=True, exist_ok=True)
    report, all_items = {}, []
    for source, method, url in SOURCES:
        if method == "rss":
            got = try_rss(source, url, day, report)
        else:
            got = try_sitemap(source, url, day, report)
        print(f"[collect] {source}: {report[source]['status']} "
              f"(fresh={report[source]['fresh']})")
        all_items.extend(got)
    paste_path = Path(__file__).resolve().parent / "paste" / f"paste-{day}.md"
    pasted, found = read_paste_file(paste_path)
    if found:
        print(f"[collect] paste file: {len(pasted)} articles")
        all_items.extend(pasted)
    else:
        print(f"[collect] paste file: none ({paste_path.name} not found)")
    # De-duplicate by URL, keep first; drop items older than the coverage window (when a date is known) and
    seen, uniq, dropped_stale = set(), [], 0
    from datetime import timedelta
    cutoff = (datetime.fromisoformat(day) - timedelta(days=2)).replace(
        tzinfo=timezone.utc)  # run date - 2 days: older items are stale
    for a in all_items:
        if a["url"] in seen:
            continue
        seen.add(a["url"])
        pub = parse_pubdate(a.get("published") or "")
        if pub and pub < cutoff:
            dropped_stale += 1
            print(f"[collect] dropping stale item ({a.get('published')[:28]}): "
                  f"{a['title'][:60]}", file=sys.stderr)
            continue
        uniq.append(a)
    if args.bodies:
        n = fetch_bodies(uniq)
        print(f"[collect] bodies fetched: {n}/{len(uniq)}")
    save_json(outdir / f"articles-{day}.json",
              {"date": day, "collected": len(uniq), "articles": uniq})
    save_json(outdir / f"freshness-{day}.json",
              {"date": day, "sources": report,
               "paste_file_found": found, "paste_count": len(pasted),
               "dropped_stale": dropped_stale})
    print(f"[collect] {day}: {len(uniq)} unique articles "
          f"({len(pasted)} pasted). Wrote {outdir}/articles-{day}.json")
    fresh_n = sum(1 for r in report.values() if r["fresh"])
    print(f"[collect] fresh sources: {fresh_n}/{len(report)} — "
          "RSS is stale for most papers; paste fallback is the reliable route.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
