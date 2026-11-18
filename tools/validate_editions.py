#!/usr/bin/env python3
"""Sarangsho Plus edition validator (Phase 5).

Run:  python3 tools/validate_editions.py

Rejects a bad edition: exit 0 = all editions pass, non-zero = fail, with a
per-edition, per-rule failure list. Checks (EN canonical editions,
EN asset copies, Bengali overlays, index.json):
  1. JSON validity; EN asset copies byte-identical to canonical editions.
  2. Required top-level keys + status field (must match index.json).
  3. Stories: id / headline / category (one of the 7 fixed: the 6 + Editorial & Opinion) / summary /
     >=1 source; new story fields present with the right shapes
     (one_liner, key_facts, what_happened, exam_qa, recall_cards,
     keywords, detail).
  4. MCQs: options A-D, correct key inside them, source is a real story
     id in the same edition, section in the 3 fixed names; letter
     distribution 20-30% per letter (5-8 of 25).
  5. No '[example]' markers (fixed-string search).
  6. Every word example contains its headword; headwords are base form
     (explicit allowlist, not a stemmer); phrase examples contain their
     complement.
  7. Dates in ISO format + weekday matches the date.
  8. No duplicate source URLs within one story's source list or within
     the top-level sources list.
  9. Bengali overlay covers exactly the same story ids and MCQ numbers
     as the English edition; BN MCQ option values correspond to the
     English options (unit-normalised numeric comparison).
 10. The 2 Nov HSC date is corrected (fix applied 2026-11-12 on Rudro's
     order 'fix all and update all'): the corrected '1 December' occurrence
     counts are enforced as the baseline, and MCQ 16 option B is
     '1 December 2026' (correct stays B).

Deliberately NOT failures (see tools/validate_editions_allowlist.json):
  * The 2 Nov HSC date strings are corrected to 1 December (2026-11-12);
    their corrected occurrence counts are enforced as the baseline -- any
    change to the counts IS a failure.
  * Longest-option-correct > 40% is reported as a FLAG: shuffling cannot
    change which answer text is longest, so it needs option-text
    rewrites (a content decision), not a data fix.
  * Story<->word URL reuse is provenance by design (see allowlist).

Works ALONGSIDE app/tools/validate_bangla.dart (run both; this script
does not modify it or its allowlist) and app/tools/check_data.py.
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EDITIONS = BASE / "editions"
ASSETS = BASE / "app" / "assets" / "editions"
ALLOWLIST = json.loads(
    (Path(__file__).resolve().parent
     / "validate_editions_allowlist.json").read_text(encoding="utf-8"))

FIXED_CATEGORIES = {
    "Economy & Banking", "Bangladesh", "Jobs & Education",
    "World", "Politics", "Technology", "Editorial & Opinion",
}
FIXED_SECTIONS = {"Vocabulary", "Phrases", "Current Affairs"}
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADWORD_ALLOW = ALLOWLIST["headwords"]
REVISION_QUESTIONS = {
    "paradox", "sovereign", "refinancing", "remuneration", "mitigation",
}
DESCRIPTIVE_DATES = {
    "Current official conference information",
    "International Debt Report 2026; reference year 2025",
    "Reference year 2025",
    "World Bank International Debt Report 2026, reference year 2025",
    "Reference year for finance flows: 2024; needs estimated to 2035",
    "36-hour review window",
    "Earlier feed entry",  # 7 Nov Revision records' Publication date
}
# Re-baselined 2026-11-17 with the learning-module renovation: the 2 Nov
# edition gained two CORRECT "1 December" occurrences — the restored
# exam_qa answer "1 December 2026." (CA04) and the learning-module
# vocabulary example "will begin on 1 December." (CA04). Both state the
# correct supplementary-exam date (never "2 December"); the gate still
# fails if a "2 December" appears or a "1 December" goes missing.
HSC_BASELINE_EN = {"1 December": 8, "1-31 December": 1, "1 December 2026": 2}
HSC_BASELINE_BN = {"1 December": 5, "1-31 December": 1, "1 December 2026": 1}
HSC_MCQ16_EN = {
    "A": "1 November 2026", "B": "1 December 2026",
    "C": "31 December 2026", "D": "10 October 2026",
}
HSC_MCQ16_BN = {
    "A": "\u09e7 \u09a8\u09ad\u09c7\u09ae\u09cd\u09ac\u09b0 \u09e8\u09e6\u09e8\u09ec",
    "B": "1 December 2026",
    "C": "\u09e9\u09e7 \u09a1\u09bf\u09b8\u09c7\u09ae\u09cd\u09ac\u09b0 \u09e8\u09e6\u09e8\u09ec",
    "D": "\u09e7\u09e6 \u0985\u0995\u09cd\u099f\u09cb\u09ac\u09b0 \u09e8\u09e6\u09e8\u09ec",
}

failures = []
flags = []


def check(cond, msg):
    print(("  PASS " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def flag(msg):
    print("  FLAG " + msg)
    flags.append(msg)


def info(msg):
    print("  .... " + msg)


def word_count(text):
    return len([w for w in re.split(r"\s+", (text or "").strip()) if w])


def longest_letter(mcq):
    best_len, best = -1, "A"
    for letter in "ABCD":
        n = len(str(mcq["options"][letter]))
        if n > best_len:
            best_len, best = n, letter
    return best


_BN_DIGITS = str.maketrans(
    "\u09e6\u09e7\u09e8\u09e9\u09ea\u09eb\u09ec\u09ed\u09ee\u09ef", "0123456789")
_UNIT_TO_MILLIONS = {
    "billion": 1000.0, "bn": 1000.0, "million": 1.0, "mn": 1.0,
    "thousand": 0.001, "lakh": 0.1, "crore": 10.0, "percent": 1.0,
    "\u09ac\u09bf\u09b2\u09bf\u09df\u09a8": 1000.0,
    "\u09ae\u09bf\u09b2\u09bf\u09df\u09a8": 1.0,
    "\u0995\u09cb\u099f\u09bf": 10.0, "\u09b2\u09be\u0996": 0.1,
    "\u09b9\u09be\u099c\u09be\u09b0": 0.001,
    "\u09b6\u09a4\u09be\u0982\u09b6": 1.0,
}
_UNIT_WORDS = sorted(_UNIT_TO_MILLIONS, key=len, reverse=True)


def option_values(text):
    """Numeric values of one MCQ option, in millions (unit-normalised),
    as a sorted list of UNIQUE values. [] when the option has no
    numbers. A range ('2-3 billion') gives both endpoints with the
    shared unit; a parenthetical restatement ('10 million (1 crore)')
    collapses to one value. Bengali য় is normalised first: the data
    writes it decomposed (য + nukta), not as U+09DF."""
    t = (text or "").translate(_BN_DIGITS).replace("\u09af\u09bc", "\u09df")
    matches = list(re.finditer(r"\d[\d,]*(?:\.\d+)?", t))

    def unit_after(pos):
        rest = t[pos:].lstrip().lower()
        for u in _UNIT_WORDS:
            if rest.startswith(u):
                return _UNIT_TO_MILLIONS[u]
        return 1.0

    out = set()
    for m in matches:
        num = float(m.group(0).replace(",", ""))
        rest = t[m.end():].lstrip()
        rm = re.match(r"[-–—]\s*\d[\d,]*(?:\.\d+)?", rest)
        if rm:
            # Range: the unit after the second number applies to both.
            out.add(num * unit_after(m.end() + rm.end()))
        else:
            out.add(num * unit_after(m.end()))
    return sorted(out)


def values_match(a, b):
    if len(a) != len(b):
        return False
    return all(abs(x - y) <= 0.01 * max(abs(x), abs(y), 1.0)
               for x, y in zip(a, b))


IRREG = {
    "take": ["took", "taking", "taken"], "bring": ["brought"],
    "come": ["came"], "lay": ["laid"], "break": ["broke"],
    "fall": ["fell", "falling", "fallen"], "weigh": ["weighed"],
    "carry": ["carried"], "hit": ["hit"], "walk": ["walked"],
    "set": ["set"], "turn": ["turned"], "resume": ["resumes", "resumed"],
    "give": ["gave"], "keep": ["kept"], "run": ["ran"],
    "go": ["went", "gone"], "speak": ["spoke"], "write": ["wrote"],
}


def main():
    index = json.loads((EDITIONS / "index.json").read_text(encoding="utf-8"))
    index_asset = json.loads(
        (ASSETS / "index.json").read_text(encoding="utf-8"))
    check(index == index_asset, "index.json canonical == asset")
    dates = [e["edition_date"] for e in index["editions"]]
    by_date = {e["edition_date"]: e for e in index["editions"]}

    for day in dates:
        print(f"== {day} ==")
        try:
            en = json.loads(
                (EDITIONS / f"data-{day}.json").read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report and continue
            check(False, f"{day}: EN JSON parses ({exc})")
            continue
        try:
            bn = json.loads(
                (ASSETS / f"bn-{day}.json").read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            check(False, f"{day}: BN JSON parses ({exc})")
            continue
        check((EDITIONS / f"data-{day}.json").read_bytes() ==
              (ASSETS / f"data-{day}.json").read_bytes(),
              f"{day}: EN asset byte-identical to canonical")

        # --- top-level keys + status ------------------------------------
        for key in ("edition_date", "edition_day", "coverage", "counts",
                    "stories", "words", "revision_words", "phrases",
                    "mcqs", "sources", "status"):
            check(key in en, f"{day}: top-level key '{key}' present")
        check(en.get("status") == by_date[day]["status"],
              f"{day}: status == index status "
              f"({en.get('status')} vs {by_date[day]['status']})")
        check(bn.get("status") == "published",
              f"{day}: BN status published")
        check("revision_words" in en.get("counts", {}) and
              "revision" not in en.get("counts", {}),
              f"{day}: counts uses 'revision_words'")
        check(en.get("edition_day") ==
              datetime.strptime(day, "%Y-%m-%d").strftime("%A"),
              f"{day}: weekday matches date")
        check(len(en["stories"]) == by_date[day]["stories"] and
              len(en["words"]) == by_date[day]["words"] and
              len(en["phrases"]) == by_date[day]["phrases"] and
              len(en["mcqs"]) == by_date[day]["mcqs"] and
              len(en["revision_words"]) == by_date[day]["revision_words"] and
              len(en["sources"]) == by_date[day]["sources"],
              f"{day}: counts match index.json")

        # --- HSC pending strings: baseline enforced, never a failure ----
        if day == "2026-11-02":
            # "1 December" is a substring of "31 December" (5x in EN, 1x in
            # BN), so a plain count inflates it; exclude the "31" prefix.
            def hsc_count(text, sub):
                if sub.startswith("1 December"):
                    return len(re.findall(r"(?<!3)" + re.escape(sub), text))
                return text.count(sub)
            en_text = (EDITIONS / f"data-{day}.json").read_text(
                encoding="utf-8")
            bn_text = (ASSETS / f"bn-{day}.json").read_text(encoding="utf-8")
            for sub, want in HSC_BASELINE_EN.items():
                check(hsc_count(en_text, sub) == want,
                      f"{day}: EN HSC baseline '{sub}' x{want}")
            for sub, want in HSC_BASELINE_BN.items():
                check(hsc_count(bn_text, sub) == want,
                      f"{day}: BN HSC baseline '{sub}' x{want}")
            flag(f"{day}: HSC strings corrected to '1 December' "
                 f"(fix applied 2026-11-12); baseline counts enforced")
        else:
            # The HSC error was the supplementary exams BEGINNING on
            # 2 December (correct: 1 December). Scope the check to
            # that claim: a paper legitimately held ON 2 December
            # inside a routine that starts 1 December (13 Nov CA07)
            # is not the error, and "12/22 December" dates are not
            # "2 December" at all (the word boundary excludes them).
            # The "2-31 December" exam window stays banned outright
            # (correct window: "1-31 December").
            for name, path in (("EN", EDITIONS / f"data-{day}.json"),
                               ("BN", ASSETS / f"bn-{day}.json")):
                t = path.read_text(encoding="utf-8")
                wrong_start = re.search(
                    r"(?i)\b(begin|begins|beginning|start|starts|"
                    r"starting|commence|commences)\b[^.;]{0,60}?"
                    r"\b2 December\b", t)
                check(wrong_start is None,
                      f"{day} {name}: HSC exams do not begin on "
                      f"2 December")
                check(not re.search(r"(?<!\d)2-31 December", t),
                      f"{day} {name}: no '2-31 December' window")
            en_text = (EDITIONS / f"data-{day}.json").read_text(
                encoding="utf-8")
            check("rice, wheat," not in en_text,
                  f"{day}: no 'rice, wheat,' as a separate item "
                  f"(wheat wording corrected to 'wheat and flour')")

        # --- no '[example]' anywhere ------------------------------------
        for name, data in (("EN", en), ("BN", bn)):
            text = json.dumps(data, ensure_ascii=False)
            check("[example]" not in text, f"{day} {name}: no '[example]'")

        story_ids = {s["id"] for s in en["stories"]}

        # --- stories ------------------------------------------------------
        for s in en["stories"]:
            sid = s["id"]
            check(bool(s.get("headline")) and bool(s.get("summary")),
                  f"{day} {sid}: headline + summary")
            check(s.get("category") in FIXED_CATEGORIES,
                  f"{day} {sid}: category in the 7 fixed")
            for key in ("event_date", "article_date"):
                check(ISO_RE.match(str(s.get(key) or "")),
                      f"{day} {sid}: {key} ISO ({s.get(key)})")
            check(isinstance(s.get("sources"), list) and
                  len(s.get("sources", [])) >= 1,
                  f"{day} {sid}: >=1 source")
            urls = [x.get("url") for x in s.get("sources", [])
                    if isinstance(x, dict)]
            check(len(urls) == len(set(urls)),
                  f"{day} {sid}: no dup URLs in story sources")
            for key in ("one_liner", "key_facts", "what_happened",
                        "exam_qa", "recall_cards", "keywords"):
                check(key in s, f"{day} {sid}: new field '{key}' present")
            frozen_story = (day == "2026-11-02" and sid == "CA04")
            if frozen_story:
                # Re-frozen 2026-11-17 with the renovation: the other new
                # fields stay empty (as fixed 2026-11-12), but exam_qa is
                # the restored live version — exactly 2 items, both
                # verified against the story (supplementary exams begin
                # 1 December 2026; 646,685 passed of 1,240,798 = 52.12%).
                # The empty-exam_qa freeze conflicted with the live
                # feed's validator (which requires exactly 2 Q&A per
                # story); the frozen values below are the correct ones.
                check(s.get("one_liner") == "" and
                      s.get("key_facts") == [] and
                      s.get("what_happened") == [] and
                      s.get("exam_qa") == [
                          {"q": "When were the HSC supplementary "
                                "examinations scheduled to begin?",
                           "a": "1 December 2026."},
                          {"q": "How many candidates passed the HSC and "
                                "equivalent examinations out of 1,240,798?",
                           "a": "646,685 candidates, or 52.12%."},
                      ] and
                      s.get("recall_cards") == [] and
                      s.get("keywords") == ["jobs & education"] and
                      "detail" not in s,
                      f"{day} {sid}: frozen new fields (HSC protection)")
            else:
                check(isinstance(s.get("one_liner"), str) and
                      s.get("one_liner") and
                      word_count(s["one_liner"]) <= 20,
                      f"{day} {sid}: one_liner non-empty, <=20 words")
                check(isinstance(s.get("detail"), str) and s.get("detail"),
                      f"{day} {sid}: detail present")
                check(isinstance(s.get("key_facts"), list) and
                      1 <= len(s["key_facts"]) <= 4,
                      f"{day} {sid}: 1-4 key_facts")
                check(isinstance(s.get("what_happened"), list) and
                      len(s["what_happened"]) >= 1,
                      f"{day} {sid}: >=1 what_happened bullet")
            for kf in s.get("key_facts", []):
                check(isinstance(kf, dict) and
                      set(kf) == {"label", "value", "original"} and
                      isinstance(kf["label"], str) and
                      isinstance(kf["value"], str) and
                      (kf["original"] is None or
                       isinstance(kf["original"], str)),
                      f"{day} {sid}: key_fact shape")
            for kf in bn["stories"][sid].get("key_facts", []):
                # BN 'original' is the raw BN figure text: it must stay
                # free of Latin digits / 'Tk' / English months, or
                # tools/validate_bangla.dart (which scans every string
                # in bn-*.json) would flag it. The English figure lives
                # in the EN story's key_facts for runtime use.
                orig = kf.get("original") or ""
                # NOTE: [0-9], not \d -- \d matches Bangla digits too.
                check(not re.search(r"[0-9]", orig) and "Tk" not in orig
                      and not re.search(
                          r"\b(?:January|February|March|April|May|June|"
                          r"July|August|September|October|November|"
                          r"December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|"
                          r"Sept|Oct|Nov|Dec)\b", orig),
                      f"{day} BN {sid}: key_fact original has no Latin "
                      f"digits/Tk/English months")
            for qa in s.get("exam_qa", []):
                check(isinstance(qa, dict) and set(qa) == {"q", "a"},
                      f"{day} {sid}: exam_qa shape")
            for rc in s.get("recall_cards", []):
                check(isinstance(rc, dict) and set(rc) == {"cloze", "answer"}
                      and "______" in rc["cloze"],
                      f"{day} {sid}: recall_card shape + blank")

        # --- words / phrases ----------------------------------------------
        for coll in ("words", "revision_words"):
            for w in en[coll]:
                hw = (w.get("Headword / phrase") or "").strip()
                ex = w.get("Original example") or ""
                if not hw:
                    check(False, f"{day} {coll}: empty headword")
                    continue
                if hw.lower() in ex.lower():
                    continue
                if (w.get("Record type") == "Revision" and
                        hw.lower() in REVISION_QUESTIONS and
                        ex.strip().startswith("What")):
                    continue  # known-format exemption (see allowlist)
                check(False, f"{day} {coll} '{hw}': example lacks headword")
            # dates + headword form are checked for every record below
            for w in en[coll]:
                pub = w.get("Publication date")
                if pub is not None:
                    check(ISO_RE.match(str(pub)) or
                          pub in DESCRIPTIVE_DATES,
                          f"{day} '{w.get('Headword / phrase')}': "
                          f"Publication date ISO or descriptive ({pub})")
                # Revision records from the external feed (7 Nov) carry
                # the descriptive 'Earlier feed entry' instead of a date;
                # that is their known shape, not a missing date.
                # Revision records from the external feed (7 Nov) carry
                # no Publication date at all; that is their known shape,
                # not a missing date.
                low = (w.get("Headword / phrase") or "").strip().lower()
                if not low or " " in low:
                    continue
                suspicious = (
                    (low.endswith("ed") and len(low) > 4)
                    or (low.endswith("ing") and len(low) > 5)
                    or (low.endswith("s") and not low.endswith("ss")
                        and len(low) > 3))
                if suspicious and low not in HEADWORD_ALLOW:
                    check(False, f"{day} '{low}': inflected-looking "
                          f"headword not in allowlist")
        for p in en["phrases"]:
            ph = p.get("Phrase", "")
            words = [w for w in re.findall(r"[a-z']+", ph.lower())
                     if len(w) >= 3]
            for key in ("Original example 1", "Original example 2"):
                ex = (p.get(key) or "").lower()
                for w in words[1:]:
                    if w in ex or w[:4] in ex:
                        continue
                    if any(f in ex for f in IRREG.get(w, [])):
                        continue
                    check(False, f"{day} phrase '{ph}' {key}: "
                          f"complement word '{w}' missing")
            if p.get("Publication date"):
                check(ISO_RE.match(str(p["Publication date"])),
                      f"{day} phrase '{ph}': Publication date ISO")

        # --- MCQs -----------------------------------------------------------
        dist = Counter(m["correct"] for m in en["mcqs"])
        check(all(5 <= dist.get(L, 0) <= 8 for L in "ABCD"),
              f"{day}: letter distribution 5-8 each {dict(dist)}")
        lc = sum(1 for m in en["mcqs"]
                 if longest_letter(m) == m["correct"])
        if lc <= 10:
            info(f"{day}: longest-correct {lc}/25 (<= 10)")
        else:
            flag(f"{day}: longest-correct {lc}/25 (> 10) -- KNOWN "
                 f"CONTENT LIMIT (see allowlist); shuffling cannot fix it")
        for m in en["mcqs"]:
            check(set(m["options"]) == set("ABCD"),
                  f"{day} MCQ {m['no']}: options A-D")
            check(m["correct"] in m["options"],
                  f"{day} MCQ {m['no']}: correct valid")
            check(m["section"] in FIXED_SECTIONS,
                  f"{day} MCQ {m['no']}: section in the 3 fixed")
            check(m["source"] in story_ids,
                  f"{day} MCQ {m['no']}: source is a story id "
                  f"({m['source']})")
        if day == "2026-11-02":
            m16 = next(m for m in en["mcqs"] if m["no"] == 16)
            check(m16["options"] == HSC_MCQ16_EN and
                  m16["correct"] == "B",
                  f"{day}: MCQ 16 EN corrected (HSC fix 2026-11-12)")
            check(bn["mcqs"]["16"]["options"] == HSC_MCQ16_BN,
                  f"{day}: MCQ 16 BN corrected (HSC fix 2026-11-12)")

        # --- top-level sources: dates + dup URLs --------------------------
        for src in en.get("sources", []):
            pub = src.get("Publication date")
            if pub is not None:
                check(ISO_RE.match(str(pub)) or pub in DESCRIPTIVE_DATES,
                      f"{day} source {src.get('Source ID')}: "
                      f"Publication date ISO or descriptive ({pub})")
            ref = src.get("Event / reference date")
            if ref is not None:
                check(ISO_RE.match(str(ref)) or ref in DESCRIPTIVE_DATES,
                      f"{day} source {src.get('Source ID')}: "
                      f"Event/reference date ISO or descriptive ({ref})")
        urls = [x.get("Direct URL") for x in en.get("sources", [])]
        check(len(urls) == len(set(urls)),
              f"{day}: no dup URLs in top-level sources")
        # Story<->word URL reuse is by design; report the scale as info.
        story_urls = {x.get("url") for s in en["stories"]
                      for x in s.get("sources", []) if isinstance(x, dict)}
        word_urls = [w.get("Direct source URL")
                     for w in en["words"] + en["phrases"] if w.get(
                         "Direct source URL")]
        reuse = sum(1 for u in word_urls if u in story_urls)
        info(f"{day}: {reuse}/{len(word_urls)} word/phrase URLs reuse "
             f"their story's source (by design, see allowlist)")

        # --- Bengali overlay ----------------------------------------------
        check(bn.get("edition_date") == day,
              f"{day}: BN edition_date matches")
        check(set(bn["stories"]) == story_ids,
              f"{day}: BN story ids == EN")
        check(set(bn["mcqs"]) == {str(m["no"]) for m in en["mcqs"]},
              f"{day}: BN MCQ numbers == EN 1..25")
        for sid, bs in bn["stories"].items():
            for key in ("headline", "summary", "why_it_matters",
                        "exam_facts", "figures"):
                check(bool(bs.get(key)),
                      f"{day} BN {sid}: {key} translated")
            for key in ("one_liner", "key_facts", "what_happened",
                        "exam_qa", "recall_cards", "keywords"):
                check(key in bs, f"{day} BN {sid}: new field '{key}'")
            if not (day == "2026-11-02" and sid == "CA04"):
                check(isinstance(bs.get("detail"), str) and bs.get("detail"),
                      f"{day} BN {sid}: detail present")
        for m in en["mcqs"]:
            b = bn["mcqs"][str(m["no"])]
            check(bool(b.get("question")) and
                  set(b.get("options", {})) == set("ABCD") and
                  bool(b.get("explanation")),
                  f"{day} BN MCQ {m['no']}: question + 4 options + "
                  f"explanation")
            # Numeric-option correspondence (unit-normalised).
            mismatch = []
            for letter in "ABCD":
                ev = option_values(m["options"][letter])
                bv = option_values(b["options"][letter])
                if ev and bv and not values_match(ev, bv):
                    mismatch.append(letter)
            check(not mismatch,
                  f"{day} BN MCQ {m['no']}: numeric options correspond "
                  f"to EN{f' (mismatch: {mismatch})' if mismatch else ''}")

    print()
    print(f"FLAGS (known, non-failing): {len(flags)}")
    for f_ in flags:
        print(" - " + f_)
    if failures:
        print(f"\nFAILED: {len(failures)} check(s)")
        for f_ in failures:
            print(" - " + f_)
        return 1
    print("\nALL EDITIONS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
