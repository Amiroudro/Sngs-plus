"""Collect permitted public RSS metadata into the Sarangsho Plus SQLite database.

This stores feed metadata/excerpts only. It does not scrape article pages,
bypass paywalls, or generate summaries. Enable a source only after its feed URL
and publisher access rules have been checked.
"""
from __future__ import annotations

import hashlib
import ipaddress
import socket
import sqlite3
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import feedparser

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "sarangsho.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
USER_AGENT = "SarangshoPlusBot/0.1 (+https://github.com/Amiroudro/Sngs-plus)"
TIMEOUT_SECONDS = 15
MAX_FEED_BYTES = 5_000_000
REDIRECT_LIMIT = 5


def validate_public_feed_url(url: str) -> None:
    """Allow only HTTPS URLs whose every resolved address is globally routable."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Malformed feed URL.") from exc

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Feed URL must use HTTPS and include a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in feed URLs are not allowed.")
    if port not in (None, 443):
        raise ValueError("Feed URLs may use only the standard HTTPS port.")

    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("Local feed hosts are not allowed.")

    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve feed host: {host}") from exc
    if not addresses:
        raise ValueError(f"Feed host has no resolved addresses: {host}")

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"Feed host resolves to a non-public address: {host}")


def validate_article_url(url: str) -> bool:
    """Accept only credential-free HTTPS article links from feed entries."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and port in (None, 443)
    )


class SafeRedirectHandler(HTTPRedirectHandler):
    """Revalidate every redirect target before urllib follows it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_feed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _PlainTextExtractor(HTMLParser):
    """Extract readable feed text while discarding executable/style content."""

    _BLOCKED = {"script", "style", "iframe", "object", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.blocked_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self._BLOCKED:
            self.blocked_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._BLOCKED and self.blocked_depth:
            self.blocked_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.blocked_depth:
            self.parts.append(data)


def clean_text(value: object, limit: int = 4000) -> str | None:
    if value is None:
        return None
    parser = _PlainTextExtractor()
    parser.feed(str(value))
    parser.close()
    text = " ".join(" ".join(parser.parts).split())
    return text[:limit] or None


def fetch_feed(url: str) -> bytes:
    validate_public_feed_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        },
    )
    opener = build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise RuntimeError(f"Feed returned HTTP {response.status}")
            body = response.read(MAX_FEED_BYTES + 1)
    except HTTPError:
        raise
    if len(body) > MAX_FEED_BYTES:
        raise ValueError("Feed exceeded the 5 MB safety limit.")
    return body


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    sources = connection.execute(
        "SELECT id, name, feed_url FROM sources "
        "WHERE enabled = 1 AND feed_url IS NOT NULL AND feed_url != ''"
    ).fetchall()
    if not sources:
        print("No enabled sources have feed URLs. Add and verify a feed URL before enabling a source.")
        connection.close()
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
                raw_link = clean_text(entry.get("link"), 2000)
                link = raw_link if raw_link and validate_article_url(raw_link) else None
                title = clean_text(entry.get("title"), 1000)
                if not link or not title:
                    continue
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = datetime(*published[:6], tzinfo=timezone.utc).isoformat() if published else None
                summary = clean_text(entry.get("summary") or entry.get("description"))
                content_hash = hashlib.sha256(
                    (title + "\n" + (summary or "")).encode("utf-8")
                ).hexdigest()
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
