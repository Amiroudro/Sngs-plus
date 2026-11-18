#!/usr/bin/env python3
"""Shared helpers for the Sarangsho Plus engine v2 (Step 1+).

Stdlib only. No imports from v1 (engine/, tools/collector/) — logic
here is adapted, not imported. Every helper is specified in
CONTRACTS.md under "Shared helpers (common.py)".

User-Agent: the SarangshoPlus UA is used for every fetch, so hosts
see one consistent, identifiable crawler.
"""
import html as _html
import re
import ssl
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

try:
    from zoneinfo import ZoneInfo
    _DHAKA = ZoneInfo("Asia/Dhaka")
except Exception:  # pragma: no cover - zoneinfo data missing
    from datetime import timedelta
    _DHAKA = timezone(timedelta(hours=6))

UA_STRING = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "SarangshoPlus-Collector/2.0 (free daily news collector)")
UA = {"User-Agent": UA_STRING}

_BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_ZERO_WIDTH = ("​", "‌", "‍", "﻿")  # U+200B, U+200C, U+200D, U+FEFF

# Query params that carry tracking, not identity. strip_tracking()
# drops these (plus any utm_* param) and drops the fragment.
_TRACKING_PARAMS = {
    "fbclid", "gclid", "gbraid", "wbraid", "msclkid", "mc_cid",
    "mc_eid", "_ga", "_gl", "fb_action_ids", "fb_source", "dclid",
    "vero_id", "yclid", "igshid",
}

# robots.txt cache: host -> list of (allowed: bool, pattern: str) rules
# for the applicable user-agent group, or None if the fetch failed
# (fail-open: a failed robots fetch must not block a source).
_ROBOTS_CACHE = {}
# hosts whose robots.txt fetch failed, with the error, so a run can
# report that the allow decision was fail-open rather than verified.
ROBOTS_FETCH_FAILURES = {}


def fetch(url, timeout=25):
    """Fetch a URL as bytes with the SarangshoPlus UA. Raises on error.

    Some servers (Daily Star) close the connection mid-read; the
    partial bytes are usually most of the page, so return those
    instead of failing outright.
    """
    import http.client
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except http.client.IncompleteRead as e:
        if e.partial:
            return e.partial
        raise


def fetch_text(url, timeout=25):
    """Fetch a URL as (lossy) UTF-8 text. Raises on error."""
    return fetch(url, timeout).decode("utf-8", "ignore")


# Lines that are site chrome, not article text. Anything containing
# one of these markers is dropped from a fetched body. The "CUT"
# markers end the body entirely (related-news sections follow them).
CHROME_SUBSTRINGS = (
    "Last modified", "Last updated", "Illustration:", "File photo",
    "Photo:", "Keep updated", "Google news channel", "Subscribe",
    "newsletter", "Staff Correspondent", "MOST VIEWED",
    "Advertisement", "Follow us", "EMAIL US", "All rights reserved",
    "Copyright", "Privacy Policy", "Comment Policy", "About Us",
    "Contact us", "TBS NEWS AT", "TBS World", "Technical Partner",
    "Representational Photo", "sponsored content", "min read",
)
CHROME_STARTS = ("Read ", "Read:", "Photo:", "Caption:")
# A line that is exactly one of these ends the article: the related-
# news section follows. (Exact match only — a mid-article "Read more"
# interstitial is dropped as a line, never a cut.)
CUT_HEADERS = (
    "related news", "related articles", "more news", "more stories",
    "latest news",
)
# A line CONTAINING one of these (lowercased) ends the article too.
# TBS (2026-11-18): every TBS article page ends with a comments
# disclaimer ("While most comments will be posted...") followed by a
# bare-headline sidebar list ("No more wage boards...", "MJL
# Bangladesh develops 5-acre green, automated warehouse complex...").
# The sidebar headlines have no article body behind them, but the
# MJL one carries a number ("5-acre"), so Step 4 extracted it as a
# fact and Step 5 passed it (the quote IS verbatim in the fetched
# page) — 34 of 123 items on 18 Nov, all TBS, all carrying that
# disclaimer line immediately before the list. Cutting at the
# disclaimer removes the whole sidebar; the "TBS News of the day" /
# "TBS Stories" markers are defence in depth for pages where the
# disclaimer is absent.
CUT_SUBSTRINGS = (
    "while most comments will be posted",
    "tbs news of the day",
    "tbs stories",
)
# A line STARTING with one of these is a related-news link, not
# article text: drop the line, keep what follows.
RELATED_STARTS = ("read more", "also read", "related:", "read also")


def clean_body_text(html, title=""):
    """Article HTML -> clean body text, with site chrome removed.

    Unlike clean_html() (which collapses everything to one string),
    this keeps paragraph boundaries so related-news blocks, captions,
    bylines and newsletter CTAs can be dropped line by line. The body
    is anchored at the article title when given, so nav headers above
    the title never reach the filter. Returns plain text.
    """
    text = re.sub(r"<script.*?</script>|<style.*?</style>|"
                  r"<noscript.*?</noscript>", " ", html or "", flags=re.S)
    # Strip <head> only: the <title> inside it would false-anchor the
    # title search. (Do NOT strip header/nav/aside/footer: sites nest
    # article content inside <header> and unclosed site headers make a
    # non-greedy strip eat the article itself — seen on TBS.)
    text = re.sub(r"<head\b.*?</head>", " ", text, flags=re.S | re.I)
    text = re.sub(r"</(p|div|li|h[1-6]|article|section|tr|blockquote)>",
                  "\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    if title:
        i = text.find(title[:40])
        if i >= 0:
            text = text[i:]
    out = []
    seen_body = False   # a real paragraph (>150 chars) seen yet
    in_related = False  # inside a related-news block before the body
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if line.lower() in CUT_HEADERS:
            # A related-news header AFTER the body ends the article;
            # BEFORE the body it is a sidebar block: skip it and its
            # headlines until the first real paragraph appears.
            if seen_body:
                break
            in_related = True
            continue
        if seen_body and any(m in line.lower() for m in CUT_SUBSTRINGS):
            # TBS comments disclaimer / sidebar section header: the
            # article body is over; everything after is a headline
            # list, not article text (see CUT_SUBSTRINGS).
            break
        if in_related:
            if len(line) > 150:
                in_related = False
                seen_body = True
            else:
                continue
        if len(line) > 150:
            seen_body = True
        if any(m in line for m in CHROME_SUBSTRINGS):
            continue
        if any(line.startswith(s) for s in CHROME_STARTS):
            continue
        if line.lower().startswith(RELATED_STARTS):
            continue  # interstitial related link: drop just this line
        if len(line) < 25 and not re.search(r"[.!?।]", line) \
                and not re.search(r"\d", line):
            continue  # nav rail / stray fragment
        out.append(line)
    body = " ".join(out)
    if len(body) < 200:
        # JS-rendered pages (MSN): the article text lives in JSON-LD.
        m = re.search(r'"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"',
                      html or "")
        if m:
            try:
                import json as _json
                ld = _json.loads('"' + m.group(1) + '"')
                if len(ld) > len(body):
                    body = ld
            except Exception:
                pass
    # Keep line boundaries: a related-headline line must not glue onto
    # the next article sentence (Step 4 splits on newlines too).
    return "\n".join(out) if len(body) >= 200 else body


def clean_html(text):
    """Strip scripts/styles/tags from HTML, unescape entities, collapse
    whitespace. Returns plain text."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>",
                  " ", text or "", flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return _html.unescape(re.sub(r"\s+", " ", text)).strip()


def parse_pubdate(raw):
    """Parse an RSS/ISO pub date into an aware datetime (UTC if the
    input has no zone), or None if it cannot be parsed."""
    if not raw:
        return None
    raw = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raw += "T12:00:00+00:00"
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def norm_bangla(text):
    """Normalise Bangla/English text for comparison: Unicode NFC,
    Bangla digits -> English digits, zero-width chars removed."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_BANGLA_DIGITS)
    for ch in _ZERO_WIDTH:
        text = text.replace(ch, "")
    return text


def strip_tracking(url):
    """Remove tracking query params (utm_*, fbclid, gclid, ...) and any
    fragment from a URL. The rest of the URL is left untouched, so two
    links to the same article with different tracking collapse to one."""
    if not url:
        return url
    try:
        parts = urllib.parse.urlparse(url)
        kept = [(k, v) for k, v in urllib.parse.parse_qsl(
            parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
            and k.lower() not in _TRACKING_PARAMS]
        query = urllib.parse.urlencode(kept)
        return urllib.parse.urlunparse(
            (parts.scheme, parts.netloc, parts.path, parts.params,
             query, ""))
    except Exception:
        return url


def ngrams(text, n):
    """Character n-grams of the normalised text (lowercased, so
    'Cabinet' and 'cabinet' match). Returns a set; if the text is
    shorter than n, the whole text is the single gram."""
    text = norm_bangla(text or "").lower()
    if not text:
        return set()
    if len(text) < n:
        return {text}
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def _pattern_to_regex(pattern):
    """Convert one robots.txt path pattern to a regex: '*' matches any
    sequence, a trailing '$' anchors the end, otherwise the pattern
    matches as a prefix (RFC 9309)."""
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    out = []
    for ch in pattern:
        if ch == "*":
            out.append(".*")
        else:
            out.append(re.escape(ch))
    return re.compile("^" + "".join(out) + ("$" if anchored else ""))


def _robots_rules_for_host(host):
    """Fetch + parse host's robots.txt; return the rule list for the
    most specific applicable user-agent group, or None on fetch
    failure (fail-open, recorded in ROBOTS_FETCH_FAILURES). Cached
    per host for the life of the process (one run)."""
    if host in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[host]
    url = "https://" + host + "/robots.txt"
    try:
        text = fetch_text(url, timeout=10)
    except Exception as e:
        ROBOTS_FETCH_FAILURES[host] = str(e)
        _ROBOTS_CACHE[host] = None
        return None
    # Parse into groups: [(agent_token, [(allowed, pattern), ...]), ...]
    groups, current = [], None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            token = value.lower()
            current = next((g for g in groups if g[0] == token), None)
            if current is None:
                current = (token, [])
                groups.append(current)
        elif key in ("allow", "disallow") and current is not None:
            if value == "":
                continue  # "Disallow:" with empty value = allow all
            current[1].append((key == "allow", value))
    # Applicable group: the longest agent token that is a prefix of
    # our UA product tokens, else "*". (Our UA has no named group on
    # any host checked, so "*" is what normally applies.)
    ua_tokens = ["sarangshoplus-collector", "mozilla"]
    best, best_len = None, -1
    for token, rules in groups:
        if token == "*":
            if best is None:
                best = rules
            continue
        if any(t.startswith(token) for t in ua_tokens) and len(token) > best_len:
            best, best_len = rules, len(token)
    if best is None:
        best = []
    _ROBOTS_CACHE[host] = best
    return best


def robots_allowed(url):
    """True if the host's robots.txt allows fetching this URL for our
    crawler. Longest matching rule wins; on a tie Allow wins; no
    matching rule means allowed. On robots.txt fetch failure, allow
    (fail-open) and record the failure in ROBOTS_FETCH_FAILURES.
    Always returns a bool."""
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return True
    if not host:
        return True
    host = host[4:] if host.startswith("www.") else host
    rules = _robots_rules_for_host(host)
    if rules is None:
        return True  # fail-open, failure recorded
    path = urllib.parse.urlparse(url).path or "/"
    best_len, best_allow = -1, True
    for allowed, pattern in rules:
        if _pattern_to_regex(pattern).match(path):
            plen = len(pattern.rstrip("$").replace("*", ""))
            if plen > best_len or (plen == best_len and allowed):
                best_len, best_allow = plen, allowed
    return best_allow


def robots_fetch_failures():
    """Copy of {host: error} for robots.txt fetches that failed
    (those hosts were treated as allowed, fail-open)."""
    return dict(ROBOTS_FETCH_FAILURES)


def today_dhaka():
    """Today's date (YYYY-MM-DD) in Asia/Dhaka."""
    return datetime.now(_DHAKA).date().isoformat()
