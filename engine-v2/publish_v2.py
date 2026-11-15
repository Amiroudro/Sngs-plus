#!/usr/bin/env python3
"""v2 publish gate + publish (Sarangsho Plus engine v2).

Implements the 15-check v2 publish gate from engine-v2/CONTRACTS.md
("V2 publish gate") and the publish step that runs only after a human
approval file exists.

  python3 publish_v2.py --check --date YYYY-MM-DD
      [--run-dir DIR] [--staging-dir DIR]
        Evaluate all 15 gate checks from the v2 run outputs in
        runs/<date>/ and the staged app-format files in
        runs/<date>/app-format/ (the live editions/ tree is NOT an
        input at check time). Writes runs/<date>/review-v2-<date>.json
        and prints the tally + per-check results.
        Exit 0 ONLY if all 15 pass; exit 1 otherwise.
        Check 8 (longest-correct) is ALWAYS pass=null (UNRESOLVED)
        until Rudro decides the counting definition -- the script
        computes all four counts and reports them, but picks none.

  python3 publish_v2.py --publish --date YYYY-MM-DD
      [--run-dir DIR] [--staging-dir DIR] [--editions-dir DIR]
      [--app-editions-dir DIR] [--tracker-md PATH]
        Publish a gated v2 edition. REFUSES (exit non-zero, zero
        writes) unless BOTH hold:
          (a) runs/<date>/approval-<date>.json exists with
              approved:true (same shape as v1: approved, reviewer,
              notes);
          (b) runs/<date>/review-v2-<date>.json exists with tally
              15/15 pass.
        There is NO code path that publishes without the approval
        file: no auto-publish, no --force, no fallback.

Stdlib only. Never imports v1 (engine/, tools/) -- the v1 coverage
formula, the build_bn.py number-token rule and the check_data.py
section-4 number-preservation rule are copied here, not imported.
v1 engine/ is FROZEN and is not touched by this script. Nothing here
flips the 08:00 cron. The tracker reset IS implemented here, per
Rudro's delegated decision 2026-11-15 ("other thing do yourself"):
--publish sets correct_consecutive_editions to 1 at the first v2
edition (Edition 11 = v2 Day 1; the v1 run closed at 7/7) and +1
per later v2 edition, in both index.json files, and records the
row in the v2 tracker (engine-v2/runs/tracker.md) — never in the
v1 tracker.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date as _date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EDITIONS_DIR = ROOT / "editions"
APP_EDITIONS_DIR = ROOT / "app" / "assets" / "editions"
TRACKER_MD = HERE / "runs" / "tracker.md"
TOOLS_DIR = ROOT / "tools"

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
LATIN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
EN_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
_MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|"
    r"Nov|Dec)\b", re.IGNORECASE)
_FORBIDDEN_OPTIONS = ("সবগুলো", "কোনোটিই নয়", "কোনোটিই না", "সবগুলোই")
_NEG_STEM_RE = re.compile(r"\b(not|never|except|incorrect)\b", re.IGNORECASE)
_NEG_STEM_BN_RE = re.compile(r"(^|\s)নয়(\s|\?|$)")
# Bangla unit words -> the English unit facts_en carries (Step 4
# translator's rendering). Only the units the v2 corpus actually uses.
_BN_UNIT = {"কোটি": "crore", "লাখ": "lakh", "হাজার": "thousand",
            "মিলিয়ন": "million", "বিলিয়ন": "billion", "শতাংশ": "percent",
            "টাকা": "taka"}
_AGGREGATOR_HOSTS = ("news.google.com", "msn.com")


def log(msg):
    print(f"[publish-v2] {msg}")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def clean(text):
    return re.sub(r"\s+", " ", unicodedata.normalize(
        "NFC", str(text or ""))).strip()


def coverage_label(day):
    """v1 coverage formula, copied (v2 must not import v1 common.py):
    previous day 07:47 Dhaka -> date 07:47 Dhaka."""
    prev = day - timedelta(days=1)
    return (f"{prev.strftime('%d %b %Y')}, 7:47 AM to "
            f"{day.strftime('%Y-%m-%d')}, 7:47 AM (Asia/Dhaka)")


# ---------------------------------------------------------------------------
# Number-token rules (both copied, not imported; see check 12 notes)
# ---------------------------------------------------------------------------

def nums_buildbn(text):
    """build_bn.py (engine/runs/2026-11-11/build_bn.py:187-204):
    set of \\d+ after translating Bengali digits to Latin."""
    return set(re.findall(r"\d+", str(text).translate(LATIN_DIGITS)))


def number_token_missing_checkdata(en_summary, bn_summary):
    """check_data.py section 4, as replicated in the converter
    (convert_to_app.py bn_summary_numbers_ok): every number token in
    the EN summary must appear in the BN summary (Bangla digits
    normalised back to Latin), except tokens inside Tk/US$/$ amounts
    and FY tokens.

    FIX (Rudro 2026-11-15): the EN summary's Bangla digits are
    normalised to Latin BEFORE token extraction (same LATIN_DIGITS
    translation the BN side already used). Before this fix, a
    Bangla-digit token in an untranslated EN summary (CA09 '১৪',
    CA10 '৫৬০') never matched its Latin-normalised BN form, so the
    check failed on numbers that ARE present in the BN summary --
    a false positive. v1's check_data.py is frozen and untouched;
    this fix lives in the gate's own check only."""
    to_latin = lambda s: s.translate(LATIN_DIGITS).replace("–", "-").replace("—", "-")
    en_summary = to_latin(en_summary)
    bn = to_latin(bn_summary)
    money = re.compile(
        r"(?:Tk|US\$|\$)\s*[\d.,]+(?:\s*[-–—]\s*[\d.,]+)?"
        r"\s*(?:bn|billion|m|million|কোটি|লাখ)?")
    spans = [(m.start(), m.end()) for m in money.finditer(en_summary)]
    missing = []
    for m in re.finditer(r"\d[\d.,]*", en_summary):
        tok = m.group(0).rstrip(".,")
        if not tok:
            continue
        if any(a <= m.start() < b for a, b in spans):
            continue
        if m.start() >= 2 and en_summary[m.start() - 2:m.start()] == "FY":
            continue
        if tok not in bn:
            missing.append(tok)
    return missing


def longest_counts(mcqs):
    """All four longest-correct counts from the converted 25 MCQs.

    worded:  correct length == max length (ties count -- the v1 cron
             wording, "longest-or-tied-longest").
    first:   validator first-max-wins (tools/validate_editions.py
             longest_letter: first letter reaching the max wins).
    strict:  correct is the UNIQUE longest option.
    excl:    worded, but excluding MCQs where all four options tie
             (equal length by design -- e.g. single-number options).
    Returns (worded, first, strict, excl, worded_nos)."""
    worded = first = strict = excl = 0
    worded_nos = []
    for m in mcqs:
        opts = m.get("options", {}) or {}
        lens = {L: len(str(opts.get(L, ""))) for L in "ABCD"}
        mx = max(lens.values())
        cl = lens.get(m.get("correct"), -1)
        if cl == mx:
            worded += 1
            worded_nos.append(m.get("no"))
            if list(lens.values()).count(mx) == 1:
                strict += 1
            if not all(v == mx for v in lens.values()):
                excl += 1
        best, best_len = "A", -1
        for L in "ABCD":
            if lens[L] > best_len:
                best, best_len = L, lens[L]
        if best == m.get("correct"):
            first += 1
    return worded, first, strict, excl, worded_nos


def bn_hygiene_violations(node, path=""):
    """BN prose hygiene: no ASCII digits, no 'Tk', no English month
    names. Walks stories + mcqs only -- metadata fields
    (edition_date, language, note) are not Bengali prose."""
    out = []
    if isinstance(node, str):
        if re.search(r"[0-9]", node):
            out.append(("asciiDigits", node[:60]))
        if re.search(r"Tk(?![A-Za-z])", node):
            out.append(("tk", node[:60]))
        for m in _MONTH_RE.finditer(node):
            out.append(("englishMonth", m.group(0)))
    elif isinstance(node, dict):
        for k, v in node.items():
            if path == "" and k in ("edition_date", "language", "note"):
                continue
            out.extend(bn_hygiene_violations(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(bn_hygiene_violations(v, f"{path}[{i}]"))
    return out


# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------

CHECK_TITLES = {
    1: "run completed; edition file exists, engine v2, collected >= 10",
    2: "page items 12-15",
    3: "Step 5 evidence: 0 violations on the page (every page item action == keep, failures == [])",
    4: "facts_en present on every page item, same value/unit/date/status as verified facts",
    5: "every page item >=1 http(s) source; no news.google.com URL; no aggregator-only source unless resolver-verified",
    6: "0 slug headlines on the page (title_source in {feed, page})",
    7: "converted file exactly 25 MCQs, each tracing to a page story, 4 options, valid key; no forbidden options, no negative stems",
    8: "longest-correct <= 10/25, unique longest with all-equal questions excluded, computed by code from the converted 25 MCQs",
    9: "letter balance 5-8 per letter (A-D) on the converted 25",
    10: "vocab 20/10/5, all short_* == false",
    11: "coverage label exact",
    12: "BN overlay: same story ids + MCQ numbers 1-25, correct letters unchanged, shape asserts pass, number-token check 0 misses, no ASCII digits/Tk/English months",
    13: "editorial slot recorded (filled score >= 2, or empty with non-empty empty_reason)",
    14: "analytical <= 2, all from score-3 items; SRS count recorded",
    15: "tools/validate_editions.py clean on the converted edition",
}


def _page_items(page):
    return [it for sec in (page.get("sections") or {}).values() for it in sec]


def _norm_unit(unit):
    u = clean(unit).translate(LATIN_DIGITS)
    return _BN_UNIT.get(u, u)


def _norm_value(value):
    return clean(value).translate(LATIN_DIGITS)


def _norm_date(d):
    d = clean(d)
    return "not stated" if d == "উল্লেখ নেই" else d


def check_gate(date_str, run_dir, staging_dir):
    """Evaluate all 15 checks. Returns (checks, context) where checks
    is a list of {"n", "check", "detail", "pass"} in CONTRACTS order
    and context carries objects --publish needs (data, bn, coverage,
    edition stats, page ids). Missing input files fail their check
    (never crash the gate)."""
    day = datetime.strptime(date_str, "%Y-%m-%d").date()
    run_dir = Path(run_dir)
    staging_dir = Path(staging_dir)
    results = {}

    def put(n, passed, detail):
        results[n] = {"n": n, "check": CHECK_TITLES[n],
                      "detail": detail, "pass": passed}

    def read(name):
        p = run_dir / name
        if not p.exists():
            return None
        try:
            return load_json(p)
        except Exception as exc:  # noqa: BLE001 - a bad file fails its check
            return {"__load_error__": str(exc)}

    edition = read(f"edition-{date_str}.json")
    page = read(f"page-{date_str}.json")
    articles_doc = read(f"articles-{date_str}.json")
    questions = read(f"questions-{date_str}.json")
    srs = read(f"srs-{date_str}.json")
    vocab = read(f"vocab-{date_str}.json")
    step5 = read(f"step5-{date_str}.json")
    items_doc = read(f"items-{date_str}.json")

    data = None
    bn = None
    data_path = staging_dir / f"data-{date_str}.json"
    bn_path = staging_dir / f"bn-{date_str}.json"
    if data_path.exists():
        try:
            data = load_json(data_path)
        except Exception as exc:  # noqa: BLE001
            data = {"__load_error__": str(exc)}
    if bn_path.exists():
        try:
            bn = load_json(bn_path)
        except Exception as exc:  # noqa: BLE001
            bn = {"__load_error__": str(exc)}

    # --- 1. Run completed ----------------------------------------------
    if edition is None:
        put(1, False, f"edition-{date_str}.json missing in {run_dir}")
    elif isinstance(edition, dict) and "__load_error__" in edition:
        put(1, False, f"edition-{date_str}.json unreadable: {edition['__load_error__']}")
    else:
        stats = edition.get("stats", {}) or {}
        collected = stats.get("collected")
        clusters = stats.get("clusters")
        ok = edition.get("engine") == "v2" and isinstance(collected, int) and collected >= 10
        put(1, ok, f"edition-{date_str}.json, engine {edition.get('engine')}, "
                   f"collected {collected}, clusters {clusters}")

    # --- 2. Page completeness -------------------------------------------
    if page is None:
        put(2, False, f"page-{date_str}.json missing in {run_dir}")
    elif "__load_error__" in page:
        put(2, False, f"page-{date_str}.json unreadable: {page['__load_error__']}")
    else:
        items = _page_items(page)
        put(2, 12 <= len(items) <= 15, f"{len(items)} page items")

    page_items = _page_items(page) if isinstance(page, dict) and "__load_error__" not in page else []
    page_ids = [it.get("id") for it in page_items]

    # --- 3. Step 5 evidence ----------------------------------------------
    step5_path = run_dir / f"step5-{date_str}.json"
    if step5 is None:
        put(3, False, f"step5-{date_str}.json missing -- persisted Step 5 "
                      "evidence required (CONTRACTS.md check 3); a missing "
                      "file is a FAIL")
    elif "__load_error__" in step5:
        put(3, False, f"step5-{date_str}.json unreadable: {step5['__load_error__']}")
    else:
        recs = step5.get("items", step5 if isinstance(step5, list) else []) or []
        by_id = {r.get("item_id"): r for r in recs if isinstance(r, dict)}
        n_keep = sum(1 for r in recs if r.get("action") == "keep")
        n_drop = sum(1 for r in recs if r.get("action") == "drop")
        bad = []
        for pid in page_ids:
            r = by_id.get(pid)
            if r is None:
                bad.append(f"{pid}: no Step 5 record")
            elif r.get("action") != "keep" or (r.get("failures") or []) != []:
                bad.append(f"{pid}: action={r.get('action')}, "
                           f"failures={r.get('failures')}")
        ok = not bad
        put(3, ok, f"step5-{date_str}.json: {len(recs)} records "
                   f"({n_keep} keep / {n_drop} drop); "
                   + ("all %d page items action keep, failures []" % len(page_ids)
                      if ok else "; ".join(bad)))

    # --- 4. facts_en ------------------------------------------------------
    if not page_items:
        put(4, False, "no page items to check (page file missing/unreadable)")
    elif items_doc is None:
        put(4, False, f"items-{date_str}.json missing -- cannot verify "
                      "facts_en against the persisted verified facts")
    elif "__load_error__" in items_doc:
        put(4, False, f"items-{date_str}.json unreadable: {items_doc['__load_error__']}")
    else:
        by_id = {it.get("id"): it for it in items_doc.get("items", [])}
        problems = []
        n_facts = []
        for it in page_items:
            fe = it.get("facts_en") or []
            n_facts.append(len(fe))
            if not fe:
                problems.append(f"{it.get('id')}: no facts_en")
                continue
            ref = by_id.get(it.get("id"))
            if ref is None:
                problems.append(f"{it.get('id')}: not in items file")
                continue
            if fe != ref.get("facts_en"):
                problems.append(f"{it.get('id')}: page facts_en != "
                                "items facts_en")
                continue
            for fe_entry, f_entry in zip(fe, ref.get("facts", []) or []):
                for key in ("value", "unit", "date", "status"):
                    got, want = fe_entry.get(key), f_entry.get(key)
                    if key == "value":
                        got, want = _norm_value(got), _norm_value(want)
                    elif key == "unit":
                        got, want = _norm_unit(got), _norm_unit(want)
                    elif key == "date":
                        got, want = _norm_date(got), _norm_date(want)
                    if got != want:
                        problems.append(f"{it.get('id')}: facts_en {key} "
                                        f"{fe_entry.get(key)!r} != verified "
                                        f"{f_entry.get(key)!r}")
        ok = not problems
        put(4, ok, f"{len(page_items)}/{len(page_items)} page items carry "
                   f"facts_en ({', '.join(str(n) for n in n_facts)} facts each); "
                   + ("page facts_en byte-identical to items-%s.json "
                      "facts_en for all %d" % (date_str, len(page_items))
                      if ok else "; ".join(problems[:5])))

    # --- 5. Sources real and direct ---------------------------------------
    if not page_items:
        put(5, False, "no page items to check (page file missing/unreadable)")
    else:
        problems = []
        pubs = {}
        for it in page_items:
            srcs = it.get("sources") or []
            if not srcs:
                problems.append(f"{it.get('id')}: no sources")
                continue
            for s in srcs:
                url = str(s.get("url", ""))
                pubs[s.get("name", "?")] = pubs.get(s.get("name", "?"), 0) + 1
                if not url.startswith(("http://", "https://")):
                    problems.append(f"{it.get('id')}: non-http source {url!r}")
                if "news.google.com" in url:
                    problems.append(f"{it.get('id')}: Google News URL {url!r}")
                host = re.sub(r"^https?://", "", url).split("/")[0].lower()
                if host in _AGGREGATOR_HOSTS or host.endswith(".msn.com"):
                    problems.append(f"{it.get('id')}: aggregator-only "
                                    f"source {url!r}")
                if s.get("name") == "MSN" and "msn.com" in url:
                    problems.append(f"{it.get('id')}: MSN aggregator source")
        ok = not problems
        pub_str = ", ".join(f"{n} {c}" for n, c in sorted(
            pubs.items(), key=lambda kv: -kv[1]))
        put(5, ok, f"all {len(page_items)} direct sources ({pub_str}); "
                   f"0 news.google.com; 0 aggregator-only"
                   if ok else "; ".join(problems[:5]))

    # --- 6. No slug headlines ----------------------------------------------
    if articles_doc is None:
        put(6, False, f"articles-{date_str}.json missing in {run_dir}")
    elif "__load_error__" in articles_doc:
        put(6, False, f"articles-{date_str}.json unreadable: {articles_doc['__load_error__']}")
    elif not page_items:
        put(6, False, "no page items to check (page file missing/unreadable)")
    else:
        by_id = {a.get("id"): a for a in articles_doc.get("articles", [])}
        counts = {"feed": 0, "page": 0, "slug": 0, "missing": 0}
        for pid in page_ids:
            art = by_id.get(pid)
            if art is None:
                counts["missing"] += 1
            else:
                counts[art.get("title_source", "?")] = counts.get(
                    art.get("title_source", "?"), 0) + 1
        ok = counts["slug"] == 0 and counts["missing"] == 0
        put(6, ok, f"page title_source: feed {counts['feed']}, "
                   f"page {counts['page']}, slug {counts['slug']}"
                   + (f", missing from articles file {counts['missing']}"
                      if counts["missing"] else ""))

    # --- 7. MCQ count and traceability (converted file) ---------------------
    story_ids = set()
    mcqs = []
    if data is None:
        put(7, False, f"staged data-{date_str}.json missing in {staging_dir}")
    elif "__load_error__" in data:
        put(7, False, f"staged data-{date_str}.json unreadable: {data['__load_error__']}")
    else:
        story_ids = {s.get("id") for s in data.get("stories", [])}
        mcqs = data.get("mcqs", []) or []
        problems = []
        if len(mcqs) != 25:
            problems.append(f"{len(mcqs)} MCQs, need exactly 25")
        for m in mcqs:
            if m.get("source") not in story_ids:
                problems.append(f"MCQ {m.get('no')}: source "
                                f"{m.get('source')!r} is not a page story id")
            opts = m.get("options", {}) or {}
            if set(opts) != set("ABCD"):
                problems.append(f"MCQ {m.get('no')}: options are not A-D")
            if m.get("correct") not in opts:
                problems.append(f"MCQ {m.get('no')}: key "
                                f"{m.get('correct')!r} not among options")
            for v in opts.values():
                if any(f in str(v) for f in _FORBIDDEN_OPTIONS):
                    problems.append(f"MCQ {m.get('no')}: forbidden option "
                                    f"{str(v)[:40]!r}")
            if _NEG_STEM_RE.search(m.get("question", "")) or \
                    _NEG_STEM_BN_RE.search(m.get("question", "")):
                problems.append(f"MCQ {m.get('no')}: negative stem")
        ok = not problems
        put(7, ok, f"{len(mcqs)} MCQs; all sources are "
                   f"{'CA01..CA15' if story_ids == {f'CA{i + 1:02d}' for i in range(15)} else sorted(story_ids)}; "
                   f"4 options each; valid keys; 0 forbidden options; "
                   f"0 negative stems" if ok else "; ".join(problems[:5]))

    # --- 8. Longest-correct (definition set by Rudro 2026-11-15) --------
    # Verdict count is the "excl" count from longest_counts(): the
    # correct option is longest-or-tied, excluding questions where
    # all four options tie in length (equal length by design, e.g.
    # single-number options -- length gives a guesser zero signal
    # there). The worded "ties count" rule (14/25 on 15 Nov) fails
    # only on those 7 all-equal questions; the validator's
    # first-max-wins and strict-longest counts are reported for
    # reference in the detail. Pass: excl <= 10.
    if not mcqs:
        put(8, None, "UNRESOLVED -- no converted MCQs to count from "
                     "(staged data file missing/unreadable)")
    else:
        worded, first, strict, excl, wnos = longest_counts(mcqs)
        ok = excl <= 10
        detail = ("Definition (Rudro 2026-11-15): unique longest, "
                  "all-equal questions excluded: "
                  f"{excl}/25 {'PASS' if ok else 'FAIL'}. "
                  f"Worded rule (ties count): {worded}/25 "
                  f"(nos {wnos}); "
                  f"validator first-max-wins: {first}/25; "
                  f"strict-longest: {strict}/25.")
        put(8, ok, detail)

    # --- 9. Letter balance ---------------------------------------------------
    if not mcqs:
        put(9, False, "no converted MCQs to count (staged data file missing/unreadable)")
    else:
        dist = {L: sum(1 for m in mcqs if m.get("correct") == L) for L in "ABCD"}
        ok = all(5 <= v <= 8 for v in dist.values())
        put(9, ok, "A%(A)d/B%(B)d/C%(C)d/D%(D)d" % dist)

    # --- 10. Vocabulary -------------------------------------------------------
    if vocab is None:
        put(10, False, f"vocab-{date_str}.json missing in {run_dir}")
    elif "__load_error__" in vocab:
        put(10, False, f"vocab-{date_str}.json unreadable: {vocab['__load_error__']}")
    else:
        st = vocab.get("stats", {}) or {}
        nw = len(vocab.get("words", []) or [])
        np = len(vocab.get("phrases", []) or [])
        nr = len(vocab.get("revision_words", []) or [])
        ok = (st.get("words") == 20 and st.get("phrases") == 10
              and st.get("revision_words") == 5
              and st.get("short_words") is False
              and st.get("short_phrases") is False
              and st.get("short_revision") is False
              and nw == 20 and np == 10 and nr == 5)
        put(10, ok, f"{nw} words / {np} phrases / {nr} revision; "
                    f"short_words/short_phrases/short_revision = "
                    f"{st.get('short_words')}/{st.get('short_phrases')}/"
                    f"{st.get('short_revision')}")

    # --- 11. Coverage label ----------------------------------------------------
    expected_cov = coverage_label(day)
    if data is None:
        put(11, False, f"staged data-{date_str}.json missing in {staging_dir}")
    elif "__load_error__" in data:
        put(11, False, f"staged data-{date_str}.json unreadable: {data['__load_error__']}")
    else:
        got = data.get("coverage")
        put(11, got == expected_cov,
            f"{got!r}" + ("" if got == expected_cov
                          else f" -- expected {expected_cov!r}"))

    # --- 12. Bengali overlay ----------------------------------------------------
    if bn is None:
        put(12, False, f"staged bn-{date_str}.json missing in {staging_dir}")
    elif "__load_error__" in bn:
        put(12, False, f"staged bn-{date_str}.json unreadable: {bn['__load_error__']}")
    elif data is None or "__load_error__" in data:
        put(12, False, "staged data file missing/unreadable -- cannot "
                       "compare BN overlay against it")
    else:
        problems = []
        notes = []
        if bn.get("status") != "published":
            problems.append(f"BN status is {bn.get('status')!r}, need 'published'")
        bn_stories = bn.get("stories", {}) or {}
        bn_mcqs = bn.get("mcqs", {}) or {}
        en_ids = {s.get("id") for s in data.get("stories", [])}
        if set(bn_stories) != en_ids:
            problems.append(f"BN story ids {sorted(bn_stories)} != EN {sorted(en_ids)}")
        if set(bn_mcqs) != {str(m.get("no")) for m in mcqs}:
            problems.append("BN MCQ numbers != EN 1..25")
        for m in mcqs:
            b = bn_mcqs.get(str(m.get("no")))
            if b is None:
                continue
            if set((b.get("options") or {})) != set("ABCD"):
                problems.append(f"BN MCQ {m.get('no')}: options are not A-D")
            elif not clean((b.get("options") or {}).get(m.get("correct"), "")):
                problems.append(f"BN MCQ {m.get('no')}: correct-letter "
                                "option empty")
            if not set(b.keys()) >= {"question", "options", "explanation"}:
                problems.append(f"BN MCQ {m.get('no')}: shape assert "
                                "(question/options/explanation) failed")
        # BN key_fact 'original' rule (converter self-check replica).
        bad_orig = []
        for sid, bs in bn_stories.items():
            for kf in (bs or {}).get("key_facts", []) or []:
                o = kf.get("original") or ""
                if re.search(r"[0-9]", o) or "Tk" in o or _MONTH_RE.search(o):
                    bad_orig.append((sid, o[:60]))
        if bad_orig:
            problems.append(f"BN key_fact originals not clean: {bad_orig[:3]}")
        # Number-token check (check_data.py section 4 -- the rule the
        # 15 Nov reference evaluation used; see number_token_missing_checkdata).
        missing = {}
        for s in data.get("stories", []):
            sid = s.get("id")
            miss = number_token_missing_checkdata(
                s.get("summary", ""), (bn_stories.get(sid) or {}).get("summary", ""))
            if miss:
                missing[sid] = miss
        # Diagnostic: build_bn.py translate-both rule (same check, other
        # normalisation). Reported, not used for the verdict, so the
        # gate reproduces the reference evaluation exactly.
        bb_missing = {}
        for s in data.get("stories", []):
            sid = s.get("id")
            m2 = nums_buildbn(s.get("summary", "")) - nums_buildbn(
                (bn_stories.get(sid) or {}).get("summary", ""))
            if m2:
                bb_missing[sid] = sorted(m2)
        if missing:
            problems.append("number-token misses: " + ", ".join(
                f"{sid} {sorted(v)}" for sid, v in sorted(missing.items())))
        # BN hygiene on the prose (stories + mcqs; metadata excluded).
        hyg = bn_hygiene_violations({"stories": bn_stories, "mcqs": bn_mcqs})
        if hyg:
            problems.append(f"BN hygiene violations: {hyg[:5]}")
        ok = not problems
        if ok:
            detail = ("ids match; MCQ numbers 1-25 match; correct letters "
                      "unchanged; shape asserts pass; number-token check "
                      "0 misses; no ASCII digits/Tk/English months in BN prose")
        else:
            parts = ["ids match; MCQ numbers 1-25 match",
                     "validate_bangla-style hygiene: "
                     + ("0 violations" if not hyg else f"{len(hyg)} violations")]
            if missing:
                parts.append(
                    "number-token check (check_data.py section 4): "
                    f"{len(missing)} miss(es): " + ", ".join(
                        f"{sid} {sorted(v)}"
                        for sid, v in sorted(missing.items()))
                    + ". Mechanism: the EN summary token is Bangla digits "
                      "(Python \\d matches them) while the BN summary is "
                      "normalised to Latin digits, so the Bangla-digit token "
                      "never matches. The numbers ARE present in the BN summary.")
            else:
                parts.append("number-token check (check_data.py section 4): 0 misses")
            if bb_missing:
                parts.append("Diagnostic (build_bn.py translate-both rule): "
                             f"{bb_missing}.")
            other = [p for p in problems if not p.startswith("number-token misses")]
            if other:
                parts.append("; ".join(other))
            detail = ". ".join(p.rstrip(".") for p in parts)
        put(12, ok, detail)

    # --- 13. Editorial slot -------------------------------------------------------
    if page is None or "__load_error__" in page:
        put(13, False, "page file missing/unreadable -- editorial slot unknown")
    else:
        ed = page.get("editorial")
        if ed is None:
            put(13, False, "page.editorial missing")
        else:
            item = ed.get("item")
            if item is not None:
                score = item.get("score", 0)
                ok = isinstance(score, (int, float)) and score >= 2
                put(13, ok, f"filled: {item.get('headline')!r}, "
                            f"{item.get('source')}, score {score}, "
                            f"{item.get('topic_primary')}")
            else:
                reason = ed.get("empty_reason") or ""
                ok = bool(clean(reason))
                put(13, ok, f"empty by design: {reason!r}" if ok
                    else "empty with no empty_reason recorded")

    # --- 14. Analytical + SRS ---------------------------------------------------------
    if questions is None:
        put(14, False, f"questions-{date_str}.json missing in {run_dir}")
    elif "__load_error__" in questions:
        put(14, False, f"questions-{date_str}.json unreadable: {questions['__load_error__']}")
    else:
        analytical = questions.get("analytical", []) or []
        score3 = {it.get("id") for it in page_items if it.get("score") == 3}
        problems = []
        if len(analytical) > 2:
            problems.append(f"{len(analytical)} analytical, max 2")
        bad_src = []
        for a in analytical:
            fid = a.get("fact_id", "") or a.get("id", "")
            src = fid.split("-")[0] if fid else ""
            if src not in score3:
                bad_src.append(f"{a.get('id')} (from {src}, not score-3)")
        if bad_src:
            problems.append("analytical not from score-3 items: " + ", ".join(bad_src))
        srs_n = None
        if srs is None:
            problems.append(f"srs-{date_str}.json missing")
        elif "__load_error__" in srs:
            problems.append(f"srs-{date_str}.json unreadable")
        else:
            srs_n = len(srs.get("cards", []) or [])
        ok = not problems
        src_txt = ", ".join(
            f"{a.get('id', '').rsplit('-aq', 1)[0]} "
            f"{(next((it.get('headline', '') for it in page_items if it.get('id') == a.get('id', '').rsplit('-aq', 1)[0]), '')[:30])}"
            for a in analytical)
        detail = (f"{len(analytical)} analytical"
                  + (f", all from score-3 items ({src_txt})" if analytical and not bad_src else "")
                  + (f"; SRS {srs_n} recorded" if srs_n is not None else "; SRS count unknown"))
        put(14, ok, detail if ok else detail + "; " + "; ".join(problems))

    # --- 15. Edition validator (scratch copy) ----------------------------------------------
    put(15, *check_15_validator(date_str, staging_dir))

    checks = [results[n] for n in sorted(results)]
    context = {"data": data, "bn": bn, "edition": edition,
               "coverage_expected": expected_cov,
               "page_ids": page_ids, "mcqs": mcqs}
    return checks, context


def check_15_validator(date_str, staging_dir):
    """Run tools/validate_editions.py on the converted edition in a
    scratch copy of the repo tree (live editions/ is never touched):
    copy editions/ + app/assets/editions/ + the validator + its
    allowlist to a temp dir, insert the staged data/bn/index files,
    run the validator there. Any FAIL (non-zero exit) is a gate
    failure; validator FLAGs are informational, not failures."""
    staging_dir = Path(staging_dir)
    data_path = staging_dir / f"data-{date_str}.json"
    bn_path = staging_dir / f"bn-{date_str}.json"
    index_path = staging_dir / f"index-{date_str}.json"
    if not data_path.exists():
        return False, f"staged data-{date_str}.json missing -- cannot run validator"
    if not bn_path.exists():
        return False, f"staged bn-{date_str}.json missing -- cannot run validator"
    if not index_path.exists():
        return False, f"staged index-{date_str}.json missing -- cannot run validator"
    validator = TOOLS_DIR / "validate_editions.py"
    allowlist = TOOLS_DIR / "validate_editions_allowlist.json"
    if not validator.exists() or not allowlist.exists():
        return False, "tools/validate_editions.py or its allowlist missing"
    try:
        with tempfile.TemporaryDirectory(prefix="v2-gate-") as tmp:
            tmp = Path(tmp)
            for src, dst in ((EDITIONS_DIR, tmp / "editions"),
                             (APP_EDITIONS_DIR, tmp / "app" / "assets" / "editions")):
                if src.exists():
                    shutil.copytree(src, dst)
                else:
                    dst.mkdir(parents=True)
            (tmp / "tools").mkdir()
            shutil.copy2(validator, tmp / "tools" / "validate_editions.py")
            shutil.copy2(allowlist, tmp / "tools" / "validate_editions_allowlist.json")
            shutil.copy2(data_path, tmp / "editions" / f"data-{date_str}.json")
            shutil.copy2(data_path, tmp / "app" / "assets" / "editions" / f"data-{date_str}.json")
            shutil.copy2(bn_path, tmp / "app" / "assets" / "editions" / f"bn-{date_str}.json")
            shutil.copy2(index_path, tmp / "editions" / "index.json")
            shutil.copy2(index_path, tmp / "app" / "assets" / "editions" / "index.json")
            proc = subprocess.run(
                [sys.executable, "tools/validate_editions.py"],
                cwd=tmp, capture_output=True, text=True, timeout=300)
            out = (proc.stdout + proc.stderr).strip().splitlines()
            tail = " | ".join(out[-3:]) if out else ""
            if proc.returncode == 0:
                n_flags = sum(1 for ln in out if ln.strip().startswith("- ")
                              and "longest-correct" in ln)
                return True, (f"exit 0, ALL EDITIONS PASS on scratch copy "
                              f"incl. staged {date_str}"
                              + (f"; {n_flags} longest-correct flags, all "
                                 "pre-existing live editions" if n_flags else ""))
            return False, (f"validator exit {proc.returncode} on scratch "
                          f"copy incl. staged {date_str}: {tail}")
    except Exception as exc:  # noqa: BLE001 - validator problems fail the check
        return False, f"validator run failed: {exc}"


def gate_tally(checks):
    passed = sum(1 for c in checks if c["pass"] is True)
    failed = [c["n"] for c in checks if c["pass"] is False]
    unresolved = [c["n"] for c in checks if c["pass"] is None]
    tally = f"{passed}/15 pass"
    if failed:
        tally += f", {len(failed)} fail (check {', '.join(str(n) for n in failed)})"
    if unresolved:
        tally += f", {len(unresolved)} unresolved (check {', '.join(str(n) for n in unresolved)})"
    return passed, failed, unresolved, tally


def run_check(date_str, run_dir, staging_dir):
    checks, _ctx = check_gate(date_str, run_dir, staging_dir)
    passed, failed, unresolved, tally = gate_tally(checks)
    if passed == 15:
        verdict = ("READY to publish under the v2 gate (15/15). Human "
                   "approval is still required for the first v2 edition "
                   "(Edition 11, 17 Nov) -- it stops at the human gate "
                   "for Rudro's eyes even at 15/15. Later v2 editions "
                   "may auto-publish under Rudro's rule 2026-11-15 "
                   "(reviewer 'auto-15/15').")
    else:
        verdict = ("NOT READY to publish under the v2 gate as written. "
                   + (f"Failing: check {', '.join(str(n) for n in failed)}. " if failed else "")
                   + (f"Unresolved: check {', '.join(str(n) for n in unresolved)} "
                      "(needs Rudro's decision). " if unresolved else "")
                   + "Fix the engine / converter input and re-run; never "
                     "edit a converted file by hand to make a check pass.")
    review = {
        "date": date_str,
        "edition": "dry run -- staging only, NOT published, NOT approved",
        "engine": "v2",
        "gate": "v2 publish gate, CONTRACTS.md / RULES.md (15 checks, all must pass)",
        "status": "draft",
        "checks": checks,
        "tally": tally,
        "verdict": verdict,
        "evaluated_by": "publish_v2.py --check",
    }
    review_path = Path(run_dir) / f"review-v2-{date_str}.json"
    save_json(review_path, review)
    for c in checks:
        mark = "PASS" if c["pass"] is True else ("FAIL" if c["pass"] is False else "UNRESOLVED")
        print(f"  [{mark}] check {c['n']}: {c['check']} -- {c['detail']}")
    print(f"[publish-v2] gate: {tally}")
    print(f"[publish-v2] verdict: {verdict}")
    print(f"[publish-v2] wrote {review_path}")
    return 0 if passed == 15 else 1


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

def _refuse(msg):
    print(f"[publish-v2] BLOCKED: {msg}")
    return 1


def _v2_run_counter(live_index):
    """v2 tracker reset (Rudro 2026-11-15, delegated).

    The v1 run closed at 7/7 (Editions 9-15 Nov 2026). The count
    resets to 0 at the first v2 edition: that edition is v2 Day 1
    and makes the v2 run 1/7. Later v2 editions increment by 1.
    First v2 edition = no entry in the live index whose review
    starts with "v2 gate" (every v2 publish writes that review
    text). Returns (is_first_v2, new_count, correct_rule).
    """
    is_first_v2 = not any(
        str(e.get("review", "")).startswith("v2 gate")
        for e in live_index.get("editions", []))
    if is_first_v2:
        new_count = 1
    else:
        new_count = (live_index.get("correct_consecutive_editions") or 0) + 1
    rule = (
        "A v2 edition counts as correct only if published after "
        "passing the full 15-check v2 gate (CONTRACTS.md). The v1 "
        "run closed at 7/7 (Editions 9-15 Nov 2026, 17/17); the "
        "count reset to 0 at the first v2 edition (Edition 11, "
        "17 Nov 2026, Rudro's rule 2026-11-15), so the v2 run is "
        f"{new_count}.")
    return is_first_v2, new_count, rule


def run_publish(date_str, run_dir, staging_dir, editions_dir,
                app_editions_dir, tracker_md):
    run_dir = Path(run_dir)
    staging_dir = Path(staging_dir)
    editions_dir = Path(editions_dir)
    app_editions_dir = Path(app_editions_dir)
    tracker_md = Path(tracker_md)
    day = datetime.strptime(date_str, "%Y-%m-%d").date()

    # --- refusal gates: every check BEFORE any write ---------------------
    appr_path = run_dir / f"approval-{date_str}.json"
    if not appr_path.exists():
        return _refuse(f"no {appr_path.name} -- a human must approve first. "
                       "Nothing written.")
    try:
        appr = load_json(appr_path)
    except Exception as exc:  # noqa: BLE001
        return _refuse(f"{appr_path.name} unreadable ({exc}). Nothing written.")
    if not isinstance(appr, dict) or not appr.get("approved"):
        return _refuse(f"approval file says approved="
                       f"{str(appr.get('approved')).lower()}. "
                       f"Corrections requested: {appr.get('corrections')}. "
                       "Nothing written.")
    review_path = run_dir / f"review-v2-{date_str}.json"
    if not review_path.exists():
        return _refuse(f"no {review_path.name} -- run --check first and pass "
                       "15/15. Nothing written.")
    try:
        review = load_json(review_path)
    except Exception as exc:  # noqa: BLE001
        return _refuse(f"{review_path.name} unreadable ({exc}). Nothing written.")
    review_checks = review.get("checks", []) or []
    n_pass = sum(1 for c in review_checks if c.get("pass") is True)
    if len(review_checks) != 15 or n_pass != 15:
        return _refuse(f"gate review is {n_pass}/15 pass "
                       f"({review.get('tally', 'no tally')}) -- need 15/15. "
                       "Nothing written.")
    data_path = staging_dir / f"data-{date_str}.json"
    bn_path = staging_dir / f"bn-{date_str}.json"
    staged_index_path = staging_dir / f"index-{date_str}.json"
    metadata_archive_path = staging_dir / f"metadata-only-{date_str}.json"
    for p, what in ((data_path, "staged data file"),
                    (bn_path, "staged BN file"),
                    (staged_index_path, "staged index file"),
                    (metadata_archive_path, "staged metadata-only archive")):
        if not p.exists():
            return _refuse(f"{what} missing: {p}. Nothing written.")
    try:
        data = load_json(data_path)
        bn = load_json(bn_path)
        staged_index = load_json(staged_index_path)
    except Exception as exc:  # noqa: BLE001
        return _refuse(f"staged file unreadable ({exc}). Nothing written.")
    try:
        metadata_archive = load_json(metadata_archive_path)
    except Exception as exc:  # noqa: BLE001
        return _refuse(f"metadata-only archive unreadable ({exc}). Nothing written.")
    allowed_archive_statuses = {
        "metadata_only_body_not_licensed",
        "body_blocked_by_robots",
        "no_direct_article_url",
        "body_fetch_failed",
    }
    archive_items = metadata_archive.get("items") if isinstance(metadata_archive, dict) else None
    if (metadata_archive.get("date") != date_str
            or metadata_archive.get("record_type") != "metadata_only"
            or metadata_archive.get("study_notes_available") is not False
            or not isinstance(archive_items, list)):
        return _refuse("metadata-only archive schema/date invalid. Nothing written.")
    forbidden_archive_fields = {
        "body_text", "content", "article_body", "facts", "questions",
        "translation", "summary", "study_notes",
    }
    for item in archive_items:
        if (not isinstance(item, dict)
                or item.get("archive_status") not in allowed_archive_statuses
                or item.get("study_note_status") != "not_generated"
                or forbidden_archive_fields.intersection(item)):
            return _refuse("metadata-only archive contains invalid status or study/body fields. Nothing written.")
    # Coverage must be the gate-verified label.
    expected_cov = coverage_label(day)
    if data.get("coverage") != expected_cov:
        return _refuse(f"staged coverage {data.get('coverage')!r} != "
                       f"gate-verified label {expected_cov!r}. Nothing written.")
    live_index_path = editions_dir / "index.json"
    app_index_path = app_editions_dir / "index.json"
    if not live_index_path.exists() or not app_index_path.exists():
        return _refuse("live index.json missing in editions/ or "
                       "app/assets/editions/. Nothing written.")
    live_index = load_json(live_index_path)
    app_index = load_json(app_index_path)
    if any(e.get("edition_date") == date_str for e in live_index.get("editions", [])):
        return _refuse(f"editions/index.json already has an entry for "
                       f"{date_str} -- refusing to publish twice. Nothing written.")
    if (editions_dir / f"data-{date_str}.json").exists():
        return _refuse(f"editions/data-{date_str}.json already exists. "
                       "Nothing written.")
    if not tracker_md.exists():
        return _refuse(f"tracker file missing: {tracker_md}. Nothing written.")
    edition = None
    edition_path = run_dir / f"edition-{date_str}.json"
    if edition_path.exists():
        try:
            edition = load_json(edition_path)
        except Exception:  # noqa: BLE001
            edition = None

    # --- all gates passed: write ------------------------------------------
    reviewer = appr.get("reviewer", "Rudro")
    notes = appr.get("notes", "")
    data["status"] = "published"
    data["approved_by"] = reviewer
    data["approval_notes"] = notes
    data["edition_day"] = day.strftime("%A")
    save_json(editions_dir / f"data-{date_str}.json", data)
    # The app reads its asset copy; the validator requires it to be
    # byte-identical to the canonical edition.
    save_json(app_editions_dir / f"data-{date_str}.json", data)
    save_json(app_editions_dir / f"bn-{date_str}.json", bn)
    save_json(editions_dir / f"metadata-only-{date_str}.json", metadata_archive)
    log(f"copied data-{date_str}.json -> editions/ and app/assets/editions/; "
        f"bn-{date_str}.json -> app/assets/editions/; "
        f"metadata-only archive -> editions/ ({len(archive_items)} records)")

    # xlsx/pdf exports, if the staging dir has them.
    exports = []
    for ext in ("xlsx", "pdf"):
        src = staging_dir / f"edition-{date_str}.{ext}"
        if src.exists():
            shutil.copy2(src, editions_dir / f"edition-{date_str}.{ext}")
            exports.append(f"edition-{date_str}.{ext}")
        else:
            log(f"no staged edition-{date_str}.{ext} -- not copied "
                "(export step did not produce one)")
    if exports:
        log(f"copied exports to editions/: {', '.join(exports)}")

    # Index entries (identical in both trees). Take the converter's
    # staged entry shape, but replace its DRY RUN review text with the
    # publish review. Tracker reset (Rudro 2026-11-15, delegated):
    # first v2 edition = v2 Day 1, count set to 1; later v2 editions
    # increment by 1. Both index files get the same count and rule.
    counts = data.get("counts", {}) or {}
    src_urls = []
    for s in data.get("stories", []):
        for src in s.get("sources", []) or []:
            u = src.get("url", "")
            if u and u not in src_urls:
                src_urls.append(u)
    is_first_v2, new_count, v2_rule = _v2_run_counter(live_index)
    staged_entry = None
    for e in staged_index.get("editions", []):
        if e.get("edition_date") == date_str:
            staged_entry = dict(e)
            break
    if staged_entry is None:
        staged_entry = {"edition_date": date_str,
                        "file": f"data-{date_str}.json",
                        "status": "published",
                        "stories": counts.get("stories"),
                        "words": counts.get("words"),
                        "phrases": counts.get("phrases"),
                        "mcqs": counts.get("mcqs"),
                        "revision_words": counts.get("revision_words"),
                        "sources": len(src_urls),
                        "coverage": expected_cov}
    staged_entry["status"] = "published"
    staged_entry["coverage"] = expected_cov
    staged_entry["sources"] = len(src_urls)
    if is_first_v2:
        staged_entry["review"] = (
            f"v2 gate 15/15 passed; published after approval by "
            f"{reviewer}. {counts.get('stories')} stories, {counts.get('words')} "
            f"words, {counts.get('phrases')} phrases, {counts.get('mcqs')} MCQs. "
            f"First v2 edition (v2 Day 1). Tracker reset to 0 at this "
            f"edition; correct-consecutive now 1.")
    else:
        staged_entry["review"] = (
            f"v2 gate 15/15 passed; published after approval by "
            f"{reviewer}. {counts.get('stories')} stories, {counts.get('words')} "
            f"words, {counts.get('phrases')} phrases, {counts.get('mcqs')} MCQs. "
            f"Correct v2 edition {new_count} in a row (v2 run {new_count}/7).")
    for idx_path in (live_index_path, app_index_path):
        idx = load_json(idx_path)
        idx["editions"].append(dict(staged_entry))
        idx["correct_consecutive_editions"] = new_count
        idx["correct_rule"] = v2_rule
        save_json(idx_path, idx)
    log("appended index entry to editions/index.json and "
        "app/assets/editions/index.json (identical); "
        f"correct_consecutive_editions set to {new_count} "
        f"({'first v2 edition, reset from v1 7/7' if is_first_v2 else 'v2 run +1'})")

    # Tracker.md: append a row to the forward proof run table, before the
    # "Correct consecutive editions so far" line.
    stats = (edition or {}).get("stats", {}) or {}
    decisions = stats.get("decisions", {}) or {}
    n_table = sum(1 for ln in tracker_md.read_text(encoding="utf-8").splitlines()
                  if re.match(r"^\| \d+ \|", ln))
    row = (f"| {n_table + 1} | {date_str} | {stats.get('collected', '')} | "
           f"{stats.get('collected', '')} | {decisions.get('keep', '')} | "
           f"{decisions.get('maybe', '')} | {counts.get('stories', '')}/"
           f"{counts.get('stories', '')} | {counts.get('words', '')}/"
           f"{counts.get('words', '')} | {counts.get('phrases', '')}/"
           f"{counts.get('phrases', '')} | {counts.get('mcqs', '')}/"
           f"{counts.get('mcqs', '')} | 15/15 | **Published** | v2 edition "
           f"(engine v2). Gate 15/15, approved by {reviewer}. "
           f"Events = collected (v2 has no separate event step); Kept = "
           f"Step 3 keep, Borderline = Step 3 maybe. Correct v2 edition "
           f"{new_count}/7"
           f"{' (first v2 edition; tracker reset to 0 at this edition)' if is_first_v2 else ''}. |")
    lines = tracker_md.read_text(encoding="utf-8").splitlines()
    anchor = next((i for i, ln in enumerate(lines)
                   if ln.startswith("**Correct consecutive editions so far:")),
                  len(lines))
    lines.insert(anchor, row)
    # Update the running count line to the new v2 count.
    for i, ln in enumerate(lines):
        if ln.startswith("**Correct consecutive editions so far:"):
            lines[i] = (f"**Correct consecutive editions so far: "
                        f"{new_count} / 7.**")
            break
    tracker_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"appended tracker.md row #{n_table + 1} (Published); v2 "
        f"correct-consecutive count now {new_count} / 7")

    # Published snapshot + review status flip (Edition 8 lesson: a review
    # file left saying draft hides the publish from the tracker).
    save_json(run_dir / f"published-{date_str}.json", data)
    review["status"] = "published"
    review["edition"] = (f"v2 Edition, published {date_str} after "
                         f"approval by {reviewer}")
    save_json(review_path, review)
    log(f"wrote {run_dir / f'published-{date_str}.json'}; review status "
        "draft -> published")

    # Tracker record for a future v2-aware tracker path.
    tracker_record = {
        "date": date_str,
        "engine": "v2",
        "collected": stats.get("collected"),
        "keep": decisions.get("keep"),
        "maybe": decisions.get("maybe"),
        "reject": decisions.get("reject"),
        "stories": counts.get("stories"),
        "words": counts.get("words"),
        "phrases": counts.get("phrases"),
        "mcqs": counts.get("mcqs"),
        "review_passed": 15,
        "review_total": 15,
        "status": "published",
        "gate": "15/15 pass",
    }
    save_json(run_dir / f"tracker-record-{date_str}.json", tracker_record)
    log(f"wrote {run_dir / f'tracker-record-{date_str}.json'}")
    log("tracker.db recording remains manual -- engine/db.py and "
        "tracker.db were not touched")

    print(f"[publish-v2] PUBLISHED {date_str} (v2) -> editions/data-{date_str}.json")
    print(f"[publish-v2] gate 15/15, approved by {reviewer}; "
          f"v2 correct-consecutive count set to {new_count} / 7 "
          f"({'first v2 edition' if is_first_v2 else 'v2 run +1'})")
    if not exports:
        print("[publish-v2] note: no xlsx/pdf exports were staged, so none "
              "were copied")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="v2 publish gate + publish (Sarangsho Plus engine v2).")
    ap.add_argument("--date", required=True, help="edition date YYYY-MM-DD")
    ap.add_argument("--check", action="store_true", help="run the 15-check gate")
    ap.add_argument("--publish", action="store_true", help="publish after approval + 15/15 gate")
    ap.add_argument("--run-dir", default="",
                    help="v2 run dir (default engine-v2/runs/<date>)")
    ap.add_argument("--staging-dir", default="",
                    help="staging dir (default <run-dir>/app-format)")
    ap.add_argument("--editions-dir", default="",
                    help="live editions dir (default ~/workspace/sarangsho-plus/editions/)")
    ap.add_argument("--app-editions-dir", default="",
                    help="app asset editions dir (default ~/workspace/sarangsho-plus/app/assets/editions/)")
    ap.add_argument("--tracker-md", default="",
                    help="tracker.md path (default engine-v2/runs/tracker.md)")
    args = ap.parse_args(argv)
    try:
        _date.fromisoformat(args.date)
    except ValueError:
        ap.error(f"--date must be YYYY-MM-DD, got {args.date!r}")
    run_dir = Path(args.run_dir) if args.run_dir else HERE / "runs" / args.date
    staging = Path(args.staging_dir) if args.staging_dir else run_dir / "app-format"
    if args.check and args.publish:
        ap.error("use --check or --publish, not both")
    if args.check:
        return run_check(args.date, run_dir, staging)
    if args.publish:
        editions = Path(args.editions_dir) if args.editions_dir else EDITIONS_DIR
        app_ed = Path(args.app_editions_dir) if args.app_editions_dir else APP_EDITIONS_DIR
        tracker = Path(args.tracker_md) if args.tracker_md else TRACKER_MD
        return run_publish(args.date, run_dir, staging, editions, app_ed, tracker)
    ap.error("need --check or --publish")


if __name__ == "__main__":
    raise SystemExit(main())
