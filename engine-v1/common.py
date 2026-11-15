#!/usr/bin/env python3
"""Sarangsho Plus — Phase 2 engine, shared helpers.

No API keys, no paid services, stdlib only (except exporters, which
import openpyxl / reportlab lazily). Nothing here invents content:
every article carries its source URL and how it was found.
"""
import json
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # ~/workspace/sarangsho-plus/
ENGINE = Path(__file__).resolve().parent
EDITIONS_DIR = ROOT / "editions"
EDITION_1 = ROOT / "data-2026-11-07.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "SarangshoPlus-Engine/2.0 (daily edition collector)"}

# Design §5 Module 1 — v1 source list.
SOURCES = [
    ("The Daily Star", "rss", "https://www.thedailystar.net/rss.xml"),
    ("The Business Standard", "rss", "https://www.tbsnews.net/rss.xml"),
    ("Prothom Alo English", "rss", "https://en.prothomalo.com/feed"),
    ("Dhaka Tribune", "rss", "https://www.dhakatribune.com/feed"),
    ("The Financial Express", "sitemap", "https://thefinancialexpress.com.bd/sitemap.xml"),
    ("New Age", "rss", "https://www.newagebd.net/rss"),
    ("The Daily Observer", "rss", "https://observerbd.com/rss.xml"),
]

# Coverage window for an edition: previous edition's cutoff (07:47 Dhaka)
# up to this edition's cutoff (07:47 Dhaka). Stored per run.
# COVERAGE_START is the legacy constant for the first edition (7 Nov);
# every later edition's window starts the previous day — use
# coverage_start(day) / coverage_label(day) so the data file, the prompt
# and the ranker's outdated-as-new floor all agree with the index.
# (Fix 2026-11-14: Editions 8-13 all carried the stale "7 Nov 2026"
# start in their data files while the index correctly showed D-1.)
COVERAGE_START = "2026-11-07T07:47:00+06:00"


def coverage_start(day: str) -> datetime:
    """Start of edition `day`'s coverage window: previous day 07:47 Dhaka.

    `day` is YYYY-MM-DD. For the first edition (2026-11-08, whose window
    genuinely starts 7 Nov) this returns 2026-11-07T07:47+06:00, matching
    the legacy constant; for every later day it returns (day - 1) 07:47.
    """
    prev = date.fromisoformat(day) - timedelta(days=1)
    return datetime.combine(prev, datetime.min.time().replace(hour=7, minute=47),
                            tzinfo=timezone(timedelta(hours=6)))


def coverage_label(day: str) -> str:
    """Full coverage string for edition `day`, matching the index format:
    "13 Nov 2026, 7:47 AM to 2026-11-14, 7:47 AM (Asia/Dhaka)"."""
    start = coverage_start(day)
    return (f"{start.day} {start.strftime('%b %Y')}, 7:47 AM to "
            f"{day}, 7:47 AM (Asia/Dhaka)")


def today() -> str:
    return date.today().isoformat()


def fetch(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_text(url: str, timeout: int = 25) -> str:
    return fetch(url, timeout).decode("utf-8", "ignore")


def clean_html(text: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>",
                  " ", text or "", flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    import html as _html
    return _html.unescape(re.sub(r"\s+", " ", text)).strip()


# Boilerplate patterns for strip_boilerplate(): phrases that are site
# chrome, never article prose. Kept deliberately short and conservative
# — a phrase here must be near-certainly navigation, not content.
_BOILER_RE = re.compile(
    r"(subscribe|sign in|sign up|log in|cookie|privacy policy|terms of use|"
    r"all rights reserved|advertisement|follow us on|download (?:the|our) app|"
    r"leave a comment|related stories|related news|also read|read more|most popular|"
    r"trending now|take our survey|site feedback)",
    re.I)


def strip_boilerplate(text: str) -> str:
    """Drop site-navigation / chrome from a fetched article body.

    Fetched bodies are whitespace-collapsed (see clean_html), so
    line-based rules do not work. Instead, split into sentences and
    drop:
      * any single "sentence" over 500 chars — a nav/menu dump has no
        sentence-ending punctuation, so it arrives as one giant run
        (verified: a TBS body starts with a ~900-char menu run);
      * sentences that are mostly Capitalised words (menu/label runs);
      * sentences matching the boilerplate phrase list.
    Real prose sentences survive: they are <500 chars, mostly
    lowercase, and do not match the boilerplate list. Verified
    2026-11-11 on the 10 Nov bodies: the TBS nav runs are gone and
    real prose survives; 2/33 bodies (Yahoo, Bloomberg) keep small
    nav fragments, so a cleaned body can still carry 1-2 stray
    keywords — bounded, and the ranker scores title+description
    first (see clean_rank.py). Some genuine long sentences and
    embedded headlines are lost — acceptable, the RSS description
    and the surviving sentences carry the article.
    Returns "" for empty / trivially short input.
    """
    if not text or len(text.strip()) < 50:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    kept = []
    seen_starts = set()
    for s in parts:
        s = s.strip()
        if not s:
            continue
        # A site's nav menu appears twice in a fetched body (header +
        # footer copies, sometimes truncated). Drop a sentence whose
        # opening words repeat an earlier sentence's opening words —
        # real articles do not repeat a sentence verbatim.
        start = " ".join(re.findall(r"[a-z]+", s.lower())[:6])
        if start in seen_starts:
            continue
        seen_starts.add(start)
        if len(s) > 500:
            continue
        words = re.findall(r"[A-Za-z]+", s)
        if len(words) >= 3:
            caps = sum(1 for w in words if w[0].isupper())
            if caps / len(words) >= 0.7:
                continue
        if len(s) < 25 and not re.search(r"[a-z]{4,}", s):
            continue
        if _BOILER_RE.search(s):
            continue
        kept.append(s)
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


def new_fact_tokens(summary, exam_facts):
    """How much NEW material exam_facts adds beyond the summary.

    Counts distinct content words (lowercased, len>3, not stopwords)
    plus distinct number tokens present in exam_facts but NOT in the
    summary. A restatement scores ~0-2; two genuinely new facts
    (names, figures, usage data) score 5+. Used by the importer's
    exam_facts rule and review check 16 — one definition, one
    threshold, so the two agree. (Audit Fix 3.3 / Fix 4.16.)
    """
    stop = set("""a an the of in on at to for and or by with from as is are was
    were be been it its this that these those after before over under
    into about has have had will would can could should may might
    than then there here when which who whom what""".split())

    def content_words(text):
        return {w for w in re.findall(r"[a-z]+", (text or "").lower())
                if len(w) > 3 and w not in stop}

    def numbers(text):
        return set(re.findall(r"\d[\d,.]*", text or ""))

    s_w, f_w = content_words(summary), content_words(exam_facts)
    s_n, f_n = numbers(summary), numbers(exam_facts)
    return len(f_w - s_w) + len(f_n - s_n)


OPINION_URL_MARKERS = ("/opinion/", "/editorial/", "/analysis/",
                       "/thoughts/", "/op-ed/")
ATTRIBUTION_MARKERS = ("argues", "argue", "says", "according to",
                       "columnist", "editorial", "opinion", "estimates",
                       "estimate", "claims", "warns", "notes", "points out",
                       "the author", "in the writer")


def has_attribution(text):
    """True if the text attributes its claims to a source (audit
    Fix 3.4 / Fix 4.17). A bare assertion with no attribution marker
    fails — an opinion claim must be framed as someone's view."""
    low = (text or "").lower()
    return any(m in low for m in ATTRIBUTION_MARKERS)


def parse_pubdate(raw: str):
    """Return an aware datetime or None. Handles RFC-822 and ISO.
    A date-only value (e.g. '2026-11-07') is treated as noon UTC that
    day, so it is not wrongly penalised as 'before the coverage start'."""
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


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def previous_editions():
    """All published/draft editions known to the engine, oldest first.
    Edition 1 (7 Nov) is the seed; later editions live in editions/."""
    out = []
    if EDITION_1.exists():
        out.append(load_json(EDITION_1))
    if EDITIONS_DIR.exists():
        for p in sorted(EDITIONS_DIR.glob("data-*.json")):
            try:
                out.append(load_json(p))
            except Exception:
                pass
    return out


def previous_headwords():
    """Lower-cased headwords/phrases already used, for de-duplication."""
    seen = set()
    for ed in previous_editions():
        for w in ed.get("words", []) + ed.get("revision_words", []):
            hw = w.get("Headword / phrase", "")
            if hw:
                seen.add(hw.strip().lower())
        for p in ed.get("phrases", []):
            ph = p.get("Phrase", "")
            if ph:
                seen.add(ph.strip().lower())
    return seen


def previous_story_titles():
    titles = []
    for ed in previous_editions():
        for s in ed.get("stories", []):
            titles.append((ed.get("edition_date", "?"), s.get("id", "?"),
                           s.get("headline", "")))
    return titles
