"""Collect permitted public RSS metadata into the Sarangsho Plus SQLite database.

This deliberately stores feed metadata/excerpts only. It does not scrape article
pages, bypass paywalls, or generate summaries. Enable a source only after its
feed URL and publisher access rules have been checked.
"""
from __future__ import annotations

import hashlib
import ipaddress
import socket
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "sarangsho.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
USER_AGENT = "SarangshoPlusBot/0.1 (+https://github.com/Amiroudro/Sngs-plus)"
TIMEOUT_SECONDS = 15
MAX_FEED_BYTES = 5_000_000


def validate_public_feed_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Feed URL must use HTTPS and include a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in feed URLs are not allowed.")
    host = parsed.hostname.lower()
    if host in {"localhost"} or host.endswith(".localhost"):
        raise ValueError("Local feed hosts are not allowed.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve feed host: {host}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"Feed host resolves to a non-public address: {host}")


def fetch_feed(url: str) -> bytes:
    validate_public_feed_url(url)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"Feed returned HTTP {response.status}")
        body = response.read(MAX_FEED_BYTES + 1)
    if len(body) > MAX_FEED_BYTES:
        raise ValueError("Feed exceeded the 5 MB safety limit.")
    return body


def clean_text(value: object, limit: int = 4000) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] or None


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    sources = connection.execute(
        "SELECT id, name, feed_url FROM sources WHERE enabled = 1 AND feed_url IS NOT NULL AND feed_url != ''"
    ).fetchall()
    if not sources:
        print("No enabled sources have feed URLs. Add and verify a feed URL before enabling a source.")
        return 0

    inserted = 0
    checked = 0
    for source_id, source_name, feed_url in sources:
        checked += 1
        try:
            parsed = feedparser.parse(fetch_feed(feed_url))
            if parsed.bozo and not parsed.entries:
                raise ValueError(f"Feed parsing failed: {parsed.bozo_exception}")
            for entry in parsed.entries:
                link = clean_text(entry.get("link"), 2000)
                title = clean_text(entry.get("title"), 1000)
                if not link or not title:
                    continue
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = datetime(*published[:6], tzinfo=timezone.utc).isoformat() if published else None
                summary = clean_text(entry.get("summary") or entry.get("description"))
                content_hash = hashlib.sha256((title + "\n" + (summary or "")).encode("utf-8")).hexdigest()
                cursor = connection.execute(
                    """INSERT OR IGNORE INTO articles
                       (source_id, canonical_url, original_title, published_at,
                        language, excerpt, content_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (source_id, link, title, published_at, None, summary, content_hash),
                )
                inserted += cursor.rowcount
            connection.execute(
                "UPDATE sources SET last_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
                (source_id,),
            )
            connection.commit()
            print(f"OK  {source_name}: {len(parsed.entries)} feed entries")
        except Exception as exc:
            connection.rollback()
            print(f"ERR {source_name}: {exc}", file=sys.stderr)

    connection.close()
    print(f"Checked {checked} source(s); inserted {inserted} new article record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
