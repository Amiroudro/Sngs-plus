#!/usr/bin/env python3
"""Verify the v1 -> v2 conversion (re-run from the converted files).

Usage: python3 renovation/conversion-verify.py <converted-dir> <v1-backup-dir>
Checks:
 1. 225 stories; every story has all 11 learning_module keys in order;
    no exam_notes anywhere; renovation_format == learning-module-v2.
 2. Per-story counts: mcq 4 (correct int 0-3 + explanation), vocab 5,
    revision 3-5 flashcards + 2 next-revision, deep_prep 4-6.
 3. Byte-identity vs v1 backup: every story field except learning_module
    identical; verified_facts identical; news_summary text identical;
    hero/topic_gk identical; top-level keys identical except
    renovation_format / renovation_date.
 4. Nothing dropped: every content word of every v1 exam_notes point
    (minus copula/stopwords) appears in the converted story's
    institutions + extra_knowledge text.
 5. news_summary.source is {publication, date, url} with Latin ISO date.
 6. The 6 marker stories keep the marker in topic_gk, institutions and
    extra_knowledge.
Exit 0 = all checks pass.
"""
import json, re, sys
from pathlib import Path

CONV = Path(sys.argv[1])
V1 = Path(sys.argv[2])
KEYS = ["hero", "news_summary", "verified_facts", "topic_gk",
        "institutions", "extra_knowledge", "mcq_practice", "written_prep",
        "vocabulary", "revision", "deep_prep"]
MARKER = "যাচাই করা যায়নি — ফাঁকা রাখা হয়েছে"
STOP = {"মানে", "হলো", "হচ্ছে", "হল", "এবং", "ও", "এর", "এ", "যে", "কি",
        "কী", "অনুযায়ী", "অনুসারে", "থেকে", "দিয়ে", "নিয়ে", "কাছে",
        "জন্য", "মতো", "সঙ্গে", "ছাড়া", "বিনা", "প্রতি", "উপর", "উপরে",
        "মধ্যে", "ভেতরে", "বাইরে", "আগে", "পরে", "পাশে", "হিসেবে",
        "হিসাবে", "অর্থাৎ", "অর্থ", "যেমন", "যদি", "তবে", "কিন্তু",
        "আর", "বা", "নয়", "না", "কে", "কার", "কোনো", "কোন", "এটি",
        "এটা", "সেটি", "সেটা", "তারা", "তাদের", "তার", "আমরা", "আমাদের",
        "the", "a", "an", "of", "to", "in", "on", "and", "or", "for",
        "by", "with", "as", "is", "are", "was", "were", "be", "been"}
fails = []
n_stories = 0

def fail(msg):
    fails.append(msg)
    print("FAIL " + msg)

def words(text):
    toks = re.split(r"[\s,;:()\"'’‘“”।—–\-/=]+", text or "")
    return [t for t in toks if t and t not in STOP]

for path in sorted(CONV.glob("data-*.json")):
    name = path.name
    v1 = json.loads((V1 / name).read_text(encoding="utf-8"))
    cv = json.loads(path.read_text(encoding="utf-8"))
    if cv.get("renovation_format") != "learning-module-v2":
        fail(f"{name}: renovation_format != learning-module-v2")
    if cv.get("renovation_date") != "2026-11-18":
        fail(f"{name}: renovation_date != 2026-11-18")
    # top-level keys identical except the two renovation keys
    for k in v1:
        if k in ("renovation_format", "renovation_date"):
            continue
        if v1[k] != cv.get(k) and k != "stories":
            fail(f"{name}: top-level key {k} changed")
    if len(v1["stories"]) != len(cv["stories"]):
        fail(f"{name}: story count changed")
    for s1, s2 in zip(v1["stories"], cv["stories"]):
        n_stories += 1
        sid = s1["id"]
        for k in s1:
            if k == "learning_module":
                continue
            if s1[k] != s2.get(k):
                fail(f"{name} {sid}: story field {k} changed")
        lm1, lm2 = s1["learning_module"], s2["learning_module"]
        if list(lm2.keys()) != KEYS:
            fail(f"{name} {sid}: LM keys/order {list(lm2.keys())}")
        if "exam_notes" in lm2:
            fail(f"{name} {sid}: exam_notes still present")
        if lm2["hero"] != lm1["hero"]:
            fail(f"{name} {sid}: hero changed")
        if lm2["verified_facts"] != lm1["verified_facts"]:
            fail(f"{name} {sid}: verified_facts changed")
        if lm2["topic_gk"] != lm1["topic_gk"]:
            fail(f"{name} {sid}: topic_gk changed")
        if lm2["deep_prep"] != lm1["deep_prep"]:
            fail(f"{name} {sid}: deep_prep changed")
        ns1, ns2 = lm1["news_summary"], lm2["news_summary"]
        t1 = ns1["text"] if isinstance(ns1, dict) else ns1
        if ns2.get("text") != t1:
            fail(f"{name} {sid}: news_summary text changed")
        src = ns2.get("source", {})
        if set(src) != {"publication", "date", "url"}:
            fail(f"{name} {sid}: news_summary.source keys {set(src)}")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", src["date"]):
            fail(f"{name} {sid}: source date not Latin ISO: {src['date']!r}")
        elif not src["publication"] or not src["url"].startswith("http"):
            fail(f"{name} {sid}: source publication/url bad: {src}")
        if len(lm2["mcq_practice"]) != 4:
            fail(f"{name} {sid}: mcq != 4")
        for m in lm2["mcq_practice"]:
            if not isinstance(m.get("correct"), int) or \
                    not 0 <= m["correct"] <= 3:
                fail(f"{name} {sid}: mcq correct not 0-3: {m.get('correct')!r}")
            if len(m.get("options", [])) != 4 or not m.get("explanation"):
                fail(f"{name} {sid}: mcq options/explanation bad")
        if len(lm2["vocabulary"]) != 5:
            fail(f"{name} {sid}: vocab != 5")
        for v in lm2["vocabulary"]:
            if set(v) != {"word", "meaning_bn", "example", "synonyms",
                          "antonyms"}:
                fail(f"{name} {sid}: vocab entry keys {set(v)}")
            if not isinstance(v["synonyms"], list) or \
                    not isinstance(v["antonyms"], list):
                fail(f"{name} {sid}: vocab synonyms/antonyms not lists")
        if not 3 <= len(lm2["revision"]["flashcards"]) <= 5:
            fail(f"{name} {sid}: flashcards not 3-5")
        for fc in lm2["revision"]["flashcards"]:
            if set(fc) != {"q", "a"}:
                fail(f"{name} {sid}: flashcard keys {set(fc)}")
        if len(lm2["revision"]["next_revision"]) != 2:
            fail(f"{name} {sid}: next_revision != 2")
        if not 4 <= len(lm2["deep_prep"]) <= 6:
            fail(f"{name} {sid}: deep_prep not 4-6")
        wp = lm2["written_prep"]
        if set(wp) != {"short", "analytical"}:
            fail(f"{name} {sid}: written_prep keys {set(wp)}")
        else:
            for part in ("short", "analytical"):
                if set(wp[part]) != {"question", "outline"}:
                    fail(f"{name} {sid}: written_prep.{part} keys")
        # marker stories
        if isinstance(lm1["topic_gk"], str):
            if lm1["topic_gk"] != MARKER:
                fail(f"{name} {sid}: unexpected topic_gk marker")
            if lm2["institutions"] != MARKER or \
                    lm2["extra_knowledge"] != MARKER:
                fail(f"{name} {sid}: marker not carried to new sections")
        # nothing dropped: content words of v1 exam_notes points
        en = lm1["exam_notes"]
        if isinstance(en, dict):
            conv_text = ""
            for sec in (lm2["institutions"], lm2["extra_knowledge"]):
                if isinstance(sec, list):
                    for e in sec:
                        conv_text += " " + " ".join(
                            str(v) for v in e.values())
            points = []
            for f in ("points", "notes", "key_points"):
                points.extend(en.get(f, []))
            points.extend(en.get("institutions", [])
                          if isinstance(en.get("institutions"), list)
                          else [])
            if en.get("text"):
                points.append(en["text"])
            for p in points:
                if isinstance(p, dict):
                    p = p.get("name", "") + " " + p.get("role", "")
                missing = [w for w in words(p) if w not in conv_text]
                if missing:
                    fail(f"{name} {sid}: words lost from exam_notes: "
                         f"{missing[:6]} :: {p[:80]}")

print(f"stories checked: {n_stories}")
if n_stories != 225:
    fail(f"total stories {n_stories} != 225")
if fails:
    print(f"\nFAILED: {len(fails)} check(s)")
    sys.exit(1)
print("\nVERIFY: ALL CHECKS PASS")
