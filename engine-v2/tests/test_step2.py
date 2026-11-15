#!/usr/bin/env python3
"""Step 2 test — pre-filter logic + real-batch run (when available).

Run: python3 tests/test_step2.py
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from step2_prefilter import prefilter, prefilter_batch

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def main():
    print("== Step 2 unit tests (hand-built articles) ==")
    cases = [
        ({"id": "t1", "title": "Murder in Dhaka flat, one arrested",
          "summary": "", "source": "X", "section": "", "url": ""},
         "low", "crime lowered"),
        ({"id": "t2", "title": "নতুন সিনেমায় অভিনেতার গান",
          "summary": "", "source": "X", "section": "", "url": ""},
         "low", "entertainment lowered"),
        ({"id": "t3", "title": "সড়ক দুর্ঘটনায় ৩ জন নিহত",
          "summary": "", "source": "X", "section": "", "url": ""},
         "low", "accident lowered"),
        # Keyword let-through beats the deprioritise term.
        ({"id": "t4", "title": "হত্যা মামলায় নতুন আইন পাস করল সংসদ",
          "summary": "", "source": "X", "section": "", "url": ""},
         "normal", "আইন keyword lets a crime-worded item through"),
        ({"id": "t5", "title": "Bangladesh Bank keeps policy rate unchanged",
          "summary": "Bangladesh Bank announced the monetary policy.",
          "source": "TBS", "section": "", "url": ""},
         "normal", "বাংলাদেশ ব্যাংক keyword lets through"),
        ({"id": "t6", "title": "IMF board approves tranche for Bangladesh",
          "summary": "", "source": "X", "section": "", "url": ""},
         "normal", "ordinary exam item stays normal"),
        ({"id": "t7", "title": "মন্ত্রণালয় নতুন অধ্যাদেশ জারি করেছে",
          "summary": "", "source": "X", "section": "", "url": ""},
         "normal", "মন্ত্রণালয় keyword lets through"),
    ]
    for art, want, name in cases:
        out, _ = prefilter(art)
        check(name, out["priority"] == want,
              f"(got {out['priority']}, reason {out['prefilter_reason']})")
    # Nothing is deleted: batch length is preserved.
    arts = [c[0] for c in cases]
    out, log = prefilter_batch(arts)
    check("batch preserves every article (never hard-deletes)",
          len(out) == len(arts))
    check("log has exactly the low-priority items",
          len(log) == sum(1 for a in out if a["priority"] == "low"))

    print("== Step 2 real-batch test ==")
    found = sorted(glob.glob(str(Path(__file__).resolve().parent.parent
                               / "runs" / "2026-11-14" / "articles-*.json")))
    if not found:
        print("  SKIP real batch: no Step 1 output yet "
              "(runs/2026-11-14/articles-*.json missing) — rerun after Step 1.")
    else:
        data = json.loads(Path(found[0]).read_text(encoding="utf-8"))
        arts = data["articles"]
        out, log = prefilter_batch(arts)
        low = [a for a in out if a["priority"] == "low"]
        print(f"  real batch: {len(arts)} articles, {len(low)} deprioritised")
        for a in low[:10]:
            print(f"    LOW [{a['id']}] {a['title'][:80]} "
                  f"({a['prefilter_reason']})")
        check("real batch: no article dropped", len(out) == len(arts))
        check("real batch: every low item has a log entry",
              len(log) == len(low))
    print(f"\nStep 2: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
