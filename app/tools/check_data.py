#!/usr/bin/env python3
"""Sarangsho Plus app data checks.

Run:  python3 tools/check_data.py

Verifies, WITHOUT the Flutter SDK:
 1. The bundled asset JSONs are byte-identical to the source editions.
 2. Every story id / word headword / MCQ number the app can reference
    exists in the source JSONs (and the Bengali overlays cover exactly
    the same ids — no invented or missing entries).
 3. Section grouping covers every story category in both editions.
 4. Every MCQ has options A-D and a correct key inside them.
 5. Word-card derivations used by the Dart code work on the real data:
    synonyms/antonyms present, word-family stem, related phrases,
    spelling misspellings generatable, practice-question pools big
    enough (synonym/antonym/spelling/analogy).
 6. The verified exam-pattern words exist in the data; no other word
    claims a previous-exam reference.
 7. Lightweight Dart hygiene: balanced braces/parens per file and every
    relative import resolves to a file that exists.

Exit code 0 = all checks pass.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SRC = APP.parent / "editions"
ASSETS = APP / "assets" / "editions"

failures = []
warnings = []


def check(cond, msg):
    print(("  PASS " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


print("== 1. App edition assets match the canonical source editions ==")
# The canonical editions/index.json carries counts and filenames. The
# app index is intentionally compact (edition_date + status only), so
# compare its date/status registry rather than requiring byte identity.
source_index = load(SRC / "index.json")
asset_index = load(ASSETS / "index.json")
source_entries = source_index.get("editions", [])
asset_entries = asset_index.get("editions", [])
check(
    [(e.get("edition_date"), e.get("status")) for e in source_entries] ==
    [(e.get("edition_date"), e.get("status")) for e in asset_entries],
    "app index dates/statuses match canonical index")
_asset_names = [e["file"] for e in source_entries]
for name in _asset_names:
    check(md5(SRC / name) == md5(ASSETS / name), f"{name} identical")
# bn overlays live only in assets (no source copy): just check presence.
for e in source_entries:
    bn = "bn-" + e["edition_date"] + ".json"
    check((ASSETS / bn).exists(), f"{bn} present in assets")

print("== 2. Editions parse; counts match canonical index.json ==")
index = source_index
editions = {}
for entry in index["editions"]:
    d = load(ASSETS / entry["file"])
    editions[entry["edition_date"]] = d
    check(len(d["stories"]) == entry["stories"], f"{entry['edition_date']} stories={entry['stories']}")
    check(len(d["words"]) == entry["words"], f"{entry['edition_date']} words={entry['words']}")
    check(len(d["phrases"]) == entry["phrases"], f"{entry['edition_date']} phrases={entry['phrases']}")
    check(len(d["mcqs"]) == entry["mcqs"], f"{entry['edition_date']} mcqs={entry['mcqs']}")
    check(len(d["revision_words"]) == entry["revision_words"], f"{entry['edition_date']} revision={entry['revision_words']}")
    check(len(d["sources"]) == entry["sources"], f"{entry['edition_date']} sources={entry['sources']}")
    check(d["counts"]["stories"] == len(d["stories"]), f"{entry['edition_date']} counts.stories consistent")

print("== 3. Story ids / headwords / MCQ numbers ==")
for date, d in editions.items():
    ids = [s["id"] for s in d["stories"]]
    check(ids == sorted(set(ids)) and len(ids) == len(d["stories"]), f"{date}: story ids unique ({len(ids)})")
    check(all(re.fullmatch(r"CA\d+", i) for i in ids), f"{date}: story id format CA##")
    heads = [w["Headword / phrase"] for w in d["words"]]
    check(len(heads) == len(set(heads)), f"{date}: word headwords unique")
    check(all(h for h in heads), f"{date}: headwords non-empty")
    nos = [m["no"] for m in d["mcqs"]]
    check(nos == list(range(1, 26)), f"{date}: MCQ numbers 1..25")
    rev = [w["Headword / phrase"] for w in d["revision_words"]]
    check(len(rev) == 5, f"{date}: 5 revision words")
    for s in d["stories"]:
        check(bool(s.get("exam_relevance")), f"{date} {s['id']}: exam_relevance present")
        check(bool(s.get("summary")) and bool(s.get("headline")), f"{date} {s['id']}: headline+summary present")
        check(len(s.get("sources", [])) >= 1, f"{date} {s['id']}: >=1 source")

print("== 4. Bengali overlays cover exactly the source ids ==")
for date, d in editions.items():
    bn = load(ASSETS / f"bn-{date}.json")
    check(bn["edition_date"] == date, f"bn-{date}: edition_date matches")
    src_ids = {s["id"] for s in d["stories"]}
    check(set(bn["stories"]) == src_ids, f"bn-{date}: story keys == source ids ({len(bn['stories'])})")
    check(set(bn["mcqs"]) == {str(m["no"]) for m in d["mcqs"]}, f"bn-{date}: mcq keys == 1..25")
    for sid, bs in bn["stories"].items():
        for k in ["headline", "summary", "why_it_matters", "exam_facts", "figures"]:
            check(bool(bs.get(k)), f"bn-{date} {sid}: {k} translated")
    for n, bm in bn["mcqs"].items():
        check(bool(bm.get("question")) and len(bm.get("options", {})) == 4 and bool(bm.get("explanation")),
              f"bn-{date} MCQ {n}: question+4 options+explanation translated")
    # figures/dates must survive translation: every number token in the
    # English summary must also appear in the Bengali summary.
    # Phase 4: the Bengali text uses Bangla digits, so normalise them
    # back to Latin (and en/em dashes to hyphens) before comparing.
    # Two deliberate exceptions, both by design:
    #  - money re-expressed, not digit-swapped (Tk 13.5 billion ->
    #    ১,৩৫০ কোটি টাকা; US$113.4378 billion -> ১১৩.৪ বিলিয়ন ডলার):
    #    tokens inside a Tk/US$/$ amount are skipped here — the value
    #    conversion is covered by the Bengali validator + widget tests.
    #  - fiscal years (FY2025 -> ২০২৪-২৫ অর্থবছর): the FY token is
    #    skipped; any other 2025 token must still match.
    # The HSC date strings ("1 December", corrected 2026-11-12) are untouched
    # by the converter, so they still match literally and need no exception.
    _bn_digits = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

    def _to_latin(s):
        return s.translate(_bn_digits).replace("–", "-").replace("—", "-")

    _money = re.compile(
        r"(?:Tk|US\$|\$)\s*[\d.,]+(?:\s*[-–—]\s*[\d.,]+)?"
        r"\s*(?:bn|billion|m|million|কোটি|লাখ)?"
    )
    num = re.compile(r"\d[\d.,]*")
    bad = []
    for s in d["stories"]:
        bn_summary = _to_latin(bn["stories"][s["id"]]["summary"])
        money_spans = [(m.start(), m.end()) for m in _money.finditer(s["summary"])]
        for m in num.finditer(s["summary"]):
            tok = m.group(0).rstrip(".,")
            if not tok:
                continue
            if any(a <= m.start() < b for a, b in money_spans):
                continue
            if m.start() >= 2 and s["summary"][m.start() - 2 : m.start()] == "FY":
                continue
            if tok not in bn_summary:
                bad.append((s["id"], tok))
    check(not bad, f"bn-{date}: all summary numbers preserved in translation ({bad[:3] if bad else 'none missing'})")

print("== 5. MCQ options A-D, correct key valid ==")
for date, d in editions.items():
    ok = True
    for m in d["mcqs"]:
        if set(m["options"]) != {"A", "B", "C", "D"} or m["correct"] not in m["options"]:
            ok = False
    check(ok, f"{date}: all MCQs have A-D options and a valid correct key")
    for m in d["mcqs"]:
        bn = load(ASSETS / f"bn-{date}.json")["mcqs"][str(m["no"])]
        check(set(bn["options"]) == {"A", "B", "C", "D"}, f"{date} MCQ {m['no']}: bn options A-D")

print("== 6. Section grouping covers every category ==")
SIX = ["Bangladesh", "Economy & Banking", "World", "Politics", "Technology", "Jobs & Education"]


def section_for(cat):
    if cat in SIX:
        return cat
    c = cat.lower()
    if "banking" in c:
        return "Economy & Banking"
    if "international" in c:
        return "World"
    if "technology" in c or "science" in c:
        return "Technology"
    if any(k in c for k in ["economy", "trade", "finance", "tax", "industrial", "infrastructure"]):
        return "Economy & Banking"
    if "labour" in c or "migration" in c:
        return "Jobs & Education"
    if "renewable" in c or "climate" in c:
        return "Bangladesh"
    if "history" in c or "governance" in c:
        return "Bangladesh"
    return "Bangladesh"


for date, d in editions.items():
    groups = {}
    for s in d["stories"]:
        groups.setdefault(section_for(s["category"]), []).append(s["id"])
    print(f"  {date}: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(groups.items())))
    check(all(g in SIX for g in groups), f"{date}: all groups are among the six sections")
    check(sum(len(v) for v in groups.values()) == len(d["stories"]), f"{date}: every story grouped")

print("== 7. Word-card derivations work on the real data ==")
for date, d in editions.items():
    phrases = [p["Phrase"] for p in d["phrases"]]
    n_syn = n_ant = n_fam = n_col = n_rel = n_stem = 0
    for w in d["words"]:
        h = (w.get("Headword / phrase") or "")
        if w.get("Synonyms"):
            n_syn += 1
        ant = (w.get("Antonyms") or "").strip().lower()
        if ant and ant != "no direct antonym":
            n_ant += 1
        fam = [x.strip() for x in (w.get("Word family / derivatives") or "").split(";") if x.strip()]
        if fam:
            n_fam += 1
        if w.get("Collocations / patterns"):
            n_col += 1
        if any(h.lower() in p.lower() for p in phrases if h):
            n_rel += 1
        # common stem >= 3 letters shared with a derivative
        for f in fam:
            i = 0
            a, b = h.lower(), f.lower().strip()
            while i < len(a) and i < len(b) and a[i] == b[i]:
                i += 1
            if i >= 3:
                n_stem += 1
                break
    print(f"  {date}: synonyms {n_syn}/20, antonyms {n_ant}/20, family {n_fam}/20, collocations {n_col}/20, related-phrase {n_rel}/20, stem {n_stem}/20")
    check(n_syn >= 15, f"{date}: synonym pool usable")
    check(n_ant >= 10, f"{date}: antonym pool usable")
    check(n_col >= 15, f"{date}: collocation field present")

print("== 8. Practice-question pools (synonym/antonym/spelling/analogy) ==")
for date, d in editions.items():
    syn_pool = {w["Headword / phrase"]: w["Synonyms"].split(";")[0].strip()
                for w in d["words"] if w.get("Synonyms")}
    ant_pool = {w["Headword / phrase"]: w["Antonyms"].split(";")[0].strip()
                for w in d["words"] if (w.get("Antonyms") or "").strip().lower() not in ("", "no direct antonym")}
    spellable = [w["Headword / phrase"] for w in d["words"] if len(w["Headword / phrase"]) >= 5]
    check(len(syn_pool) >= 4, f"{date}: synonym distractor pool >= 4 ({len(syn_pool)})")
    check(len(ant_pool) >= 4, f"{date}: antonym distractor pool >= 4 ({len(ant_pool)})")
    check(len(spellable) >= 10, f"{date}: spellable words >= 10 ({len(spellable)})")
    check(len(syn_pool) >= 2, f"{date}: analogy needs >= 2 synonym pairs")

print("== 9. Verified exam-pattern words exist in the data ==")
dart = (APP / "lib" / "data" / "exam_patterns.dart").read_text(encoding="utf-8")
# Phase 1: the user-visible pattern strings no longer carry the raw
# "PAST_QUESTION_PATTERNS" code name, so detect the verified words from
# the verifiedExamPatterns map keys instead of from the string contents.
_map = re.search(r"verifiedExamPatterns = \{(.*?)\n\};", dart, re.S)
claimed = sorted(set(re.findall(r"'([a-z]+)':", _map.group(1)))) if _map else []
all_words = set()
for d in editions.values():
    all_words |= {w["Headword / phrase"].lower() for w in d["words"]}
    all_words |= {w["Headword / phrase"].lower() for w in d["revision_words"]}
print(f"  claimed verified-pattern words: {claimed}")
for w in claimed:
    check(w in all_words, f"pattern word '{w}' exists in edition data")
check(claimed == ["adaptation", "bilateral", "bureaucratic", "mitigation", "sanction"],
      "exactly the 5 verified words, no invented exam references")

print("== 10. Dart hygiene: balanced delimiters + imports resolve ==")
for f in sorted((APP / "lib").rglob("*.dart")):
    src = f.read_text(encoding="utf-8")
    for a, b, name in [("{", "}", "braces"), ("(", ")", "parens"), ("[", "]", "brackets")]:
        check(src.count(a) == src.count(b), f"{f.relative_to(APP)}: {name} balanced ({src.count(a)}/{src.count(b)})")
    for m in re.finditer(r"import '([^']+)';", src):
        imp = m.group(1)
        if imp.startswith("package:") or imp.startswith("dart:"):
            continue
        target = (f.parent / imp).resolve()
        check(target.exists(), f"{f.relative_to(APP)}: import {imp} resolves")
    for m in re.finditer(r"import \"([^\"]+)\";", src):
        check(False, f"{f.relative_to(APP)}: double-quoted import {m.group(1)}")
    # Extension methods .t() / .strings live in widgets/app_theme.dart:
    # any file using them must import it.
    uses_ext = (".t(" in src or ".strings" in src) and f.name != "app_theme.dart"
    imports_theme = "app_theme.dart" in src
    check(not uses_ext or imports_theme,
          f"{f.relative_to(APP)}: uses .t()/.strings only with app_theme import")

print("== 11. Phase 5 data rules: schema, shuffle, new story fields ==")
# Phase 5 (see ../phase5-data.py and ../tools/validate_editions.py):
# one schema (status, 6 categories, 3 MCQ sections, CA-id MCQ sources,
# ISO dates), seeded MCQ shuffle (each letter 20-30%), no '[example]'
# markers, word examples contain their headwords, authored story fields
# present with the right shapes. Longest-option-correct is reported here
# as information only: it is invariant under shuffling (the correct
# texts are inherently the longest in 7 of 8 editions), so it cannot be
# a pass/fail data check -- see tools/validate_editions_allowlist.json.
_SIX = {"Bangladesh", "Economy & Banking", "World", "Politics",
        "Technology", "Jobs & Education", "Editorial & Opinion"}
_SECTIONS = {"Vocabulary", "Phrases", "Current Affairs"}
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REV_Q = {"paradox", "sovereign", "refinancing", "remuneration",
          "mitigation"}
for date, d in editions.items():
    check(d.get("status") == "published",
          f"{date}: status field published")
    check("revision_words" in d.get("counts", {}),
          f"{date}: counts uses revision_words")
    check(all(s.get("category") in _SIX for s in d["stories"]),
          f"{date}: all categories in the 7 fixed")
    check(all(m.get("section") in _SECTIONS for m in d["mcqs"]),
          f"{date}: all MCQ sections in the 3 fixed")
    _ids = {s["id"] for s in d["stories"]}
    check(all(m.get("source") in _ids for m in d["mcqs"]),
          f"{date}: all MCQ sources are story ids")
    for s in d["stories"]:
        check(_ISO.match(str(s.get("event_date") or "")) and
              _ISO.match(str(s.get("article_date") or "")),
              f"{date} {s['id']}: dates ISO")
        for _k in ("one_liner", "key_facts", "what_happened", "exam_qa",
                   "recall_cards", "keywords"):
            check(_k in s, f"{date} {s['id']}: {_k} present")
        if not (date == "2026-11-02" and s["id"] == "CA04"):
            check(bool(s.get("detail")), f"{date} {s['id']}: detail present")
            check(len(s.get("one_liner", "").split()) <= 20,
                  f"{date} {s['id']}: one_liner <= 20 words")
        check(isinstance(s.get("key_facts"), list) and
              len(s.get("key_facts", [])) <= 4,
              f"{date} {s['id']}: key_facts <= 4")
    _dist = {L: sum(1 for m in d["mcqs"] if m["correct"] == L)
             for L in "ABCD"}
    check(all(5 <= v <= 8 for v in _dist.values()),
          f"{date}: MCQ letters 5-8 each {_dist}")

    def _longest(_m):
        _best, _bl = "A", -1
        for _L in "ABCD":
            _n = len(str(_m["options"][_L]))
            if _n > _bl:
                _best, _bl = _L, _n
        return _best

    _lc = sum(1 for m in d["mcqs"] if _longest(m) == m["correct"])
    print(f"  {date}: longest-correct {_lc}/25 (info only; see section 11)")
    _text = json.dumps(d, ensure_ascii=False)
    check("[example]" not in _text, f"{date}: no '[example]' markers")
    for _w in d["words"] + d["revision_words"]:
        _hw = (_w.get("Headword / phrase") or "").strip()
        _ex = _w.get("Original example") or ""
        if (_w.get("Record type") == "Revision" and
                _hw.lower() in _REV_Q and _ex.strip().startswith("What")):
            continue  # known-format quiz question (see allowlist)
        check(_hw.lower() in _ex.lower(),
              f"{date} '{_hw}': example contains headword")
    if date == "2026-11-02":
        _m16 = [m for m in d["mcqs"] if m["no"] == 16][0]
        check(_m16["options"] == {
            "A": "1 November 2026", "B": "1 December 2026",
            "C": "31 December 2026", "D": "10 October 2026"}
            and _m16["correct"] == "B",
            f"{date}: MCQ 16 corrected (HSC fix 2026-11-12)")
    _bn = load(ASSETS / f"bn-{date}.json")
    check(_bn.get("status") == "published", f"{date}: BN status published")
    for _sid, _bs in _bn["stories"].items():
        for _k in ("one_liner", "key_facts", "what_happened", "exam_qa",
                   "recall_cards", "keywords"):
            check(_k in _bs, f"{date} BN {_sid}: {_k} present")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f_ in failures:
        print(" - " + f_)
    sys.exit(1)
print("ALL CHECKS PASSED")
