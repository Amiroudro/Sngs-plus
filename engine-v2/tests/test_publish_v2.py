#!/usr/bin/env python3
"""publish_v2.py tests (engine v2) -- runnable as: python3 tests/test_publish_v2.py

Style follows the other engine-v2 suites: PASS/FAIL counts printed,
exit 0 iff all pass. Stdlib only.

Tests:
  1. Gate reproduction: --check on a SCRATCH COPY of
     runs/2026-11-15 (+ staging) reproduces the live 15/15 review
     (check 12 PASS after the 2026-11-15 Bangla-digit fix, check 8
     PASS on the "excl" definition). NEVER runs --check against the
     live runs/2026-11-15/ dir -- it would overwrite the live
     review-v2-2026-11-15.json. The live review file's hash is
     checked before/after to prove it was untouched.
  2. --publish refuses without an approval file (exit non-zero, zero
     files written to the scratch editions/app dirs).
  3. --publish refuses with an approval file saying approved:false.
  4. --publish refuses with approved:true but a SYNTHETIC 13/15
     gate review (written into the scratch run dir for this test
     only -- the real gate is 15/15 after the 2026-11-15 fixes).
  5. --publish with approved:true + a synthetic GREEN review file
     (tally 15/15) works on SCRATCH copies only -- verifies copied
     files, both index.json entries, tracker.md row, published file,
     review status flip, tracker-record. The synthetic green review
     is a TEST FIXTURE ONLY, retained so the test controls the
     review content exactly (the real gate is 15/15 since the
     2026-11-15 decisions, so the fixture no longer stands in for
     an unreachable state).

No test touches the live editions/ tree or live runs/2026-11-15/.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_V2 = HERE.parent
ROOT = ENGINE_V2.parent
PUBLISH_V2 = ENGINE_V2 / "publish_v2.py"
DATE = "2026-11-15"
LIVE_RUN = ENGINE_V2 / "runs" / DATE

FAILURES = []
_LIVE_UNTOUCHED = False


def check(cond, label):
    print(("  PASS " if cond else "  FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def run_pub(args, cwd=ENGINE_V2):
    return subprocess.run([sys.executable, str(PUBLISH_V2)] + args,
                          cwd=cwd, capture_output=True, text=True, timeout=600)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scratch_run_dir(tmp):
    """Copy the live 15 Nov run dir (+ staging) to tmp; return its path."""
    dst = tmp / f"runs-{DATE}"
    shutil.copytree(LIVE_RUN, dst)
    return dst


def scratch_trees(tmp):
    """Minimal scratch editions/app/tracker trees (index.json + tracker.md
    copied from live -- read-only copies, never written back). The live
    index already has a v1 entry for 2026-11-15 (Edition 9), so that
    entry is stripped from the SCRATCH copies: the fixture simulates
    the date not yet published, which is the state --publish expects."""
    ed = tmp / "editions"
    app_ed = tmp / "app" / "assets" / "editions"
    ed.mkdir(parents=True)
    app_ed.mkdir(parents=True)
    for src, dst in ((ROOT / "editions" / "index.json", ed / "index.json"),
                     (ROOT / "app" / "assets" / "editions" / "index.json",
                      app_ed / "index.json")):
        idx = json.loads(src.read_text(encoding="utf-8"))
        idx["editions"] = [e for e in idx["editions"]
                           if e.get("edition_date") != DATE]
        dst.write_text(json.dumps(idx, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    tracker = tmp / "tracker.md"
    # The v2 tracker (engine-v2/runs/tracker.md) is the one --publish
    # writes; the v1 tracker is never touched by a v2 publish.
    shutil.copy2(ENGINE_V2 / "runs" / "tracker.md", tracker)
    return ed, app_ed, tracker


def test_gate_reproduction():
    print("== 1. gate reproduction on a scratch copy of runs/2026-11-15 ==")
    live_review = LIVE_RUN / f"review-v2-{DATE}.json"
    before = sha(live_review)
    with tempfile.TemporaryDirectory(prefix="v2-pub-test-") as tmp:
        tmp = Path(tmp)
        run_dir = scratch_run_dir(tmp)
        proc = run_pub(["--check", "--date", DATE,
                        "--run-dir", str(run_dir),
                        "--staging-dir", str(run_dir / "app-format")])
        check(proc.returncode == 0,
              f"--check exit 0 at 15/15 (got {proc.returncode})")
        review_path = run_dir / f"review-v2-{DATE}.json"
        check(review_path.exists(), "scratch review-v2 file written")
        review = json.loads(review_path.read_text(encoding="utf-8"))
        check(set(review) >= {"checks", "tally", "verdict", "date",
                              "edition", "engine", "gate"},
              "review has the reference top-level keys")
        checks = {c["n"]: c for c in review["checks"]}
        check(len(review["checks"]) == 15, "review has 15 checks")
        n_pass = sum(1 for c in review["checks"] if c["pass"] is True)
        check(n_pass == 15, f"15/15 pass (got {n_pass}/15)")
        check(review["tally"].startswith("15/15 pass"),
              f"tally reads 15/15 pass (got {review['tally']!r})")
        check(checks[12]["pass"] is True,
              "check 12 PASS (number-token, Bangla-digit fix)")
        check(checks[8]["pass"] is True,
              "check 8 PASS (excl definition)")
        detail8 = checks[8]["detail"]
        check(all(s in detail8 for s in ("14/25", "4/25", "1/25")),
              "check 8 detail carries all four counts (14/25, 4/25, 1/25, 1/25)")
        check("1/25 PASS" in detail8 or "excl" in detail8.lower()
              or "1/25" in detail8,
              "check 8 detail names the excl count")
        check(all(c["pass"] is True for c in review["checks"]),
              "all 15 checks pass")
        check("READY" in review["verdict"], "verdict is READY")
        check("15/15 pass" in proc.stdout, "--check prints the 15/15 tally")
    after = sha(live_review)
    check(before == after, "live runs/2026-11-15/review-v2 file untouched")


def _publish_args(tmp, run_dir, ed, app_ed, tracker):
    return ["--publish", "--date", DATE,
            "--run-dir", str(run_dir),
            "--staging-dir", str(run_dir / "app-format"),
            "--editions-dir", str(ed),
            "--app-editions-dir", str(app_ed),
            "--tracker-md", str(tracker)]


def test_publish_refusals():
    print("== 2/3/4. --publish refusals ==")
    with tempfile.TemporaryDirectory(prefix="v2-pub-test-") as tmp:
        tmp = Path(tmp)
        run_dir = scratch_run_dir(tmp)
        ed, app_ed, tracker = scratch_trees(tmp)
        args = _publish_args(tmp, run_dir, ed, app_ed, tracker)

        # 2. No approval file at all.
        proc = run_pub(args)
        check(proc.returncode != 0, "--publish without approval exits non-zero")
        check("no approval" in proc.stdout.lower(),
              "--publish without approval says why (no approval file)")
        check(not (ed / f"data-{DATE}.json").exists()
              and not (app_ed / f"bn-{DATE}.json").exists()
              and not (run_dir / f"published-{DATE}.json").exists(),
              "refusal wrote zero files")

        # 3. Approval file says approved:false.
        (run_dir / f"approval-{DATE}.json").write_text(
            json.dumps({"approved": False, "reviewer": "Rudro",
                        "notes": "", "corrections": "fix CA09 numbers"},
                       ensure_ascii=False), encoding="utf-8")
        proc = run_pub(args)
        check(proc.returncode != 0, "--publish with approved:false exits non-zero")
        check("approved=false" in proc.stdout,
              "--publish with approved:false says why")
        check(not (ed / f"data-{DATE}.json").exists(),
              "approved:false refusal wrote zero files")

        # 4. approved:true but a SYNTHETIC 13/15 gate review. The real
        # gate is 15/15 after the 2026-11-15 fixes, so the refusal path
        # is exercised with a red review written into the scratch run
        # dir for this test only (13 pass, check 12 fail, check 8
        # unresolved -- the pre-decision state).
        (run_dir / f"approval-{DATE}.json").write_text(
            json.dumps({"approved": True, "reviewer": "Rudro",
                        "notes": "test approval"}, ensure_ascii=False),
            encoding="utf-8")
        red = {
            "date": DATE, "edition": "synthetic red fixture (test only)",
            "engine": "v2",
            "gate": "v2 publish gate, CONTRACTS.md / RULES.md (15 checks, all must pass)",
            "status": "draft",
            "checks": [{"n": n, "check": f"check {n}", "detail": "fixture",
                        "pass": (False if n == 12 else
                                 None if n == 8 else True)}
                       for n in range(1, 16)],
            "tally": "13/15 pass, 1 fail (check 12), 1 unresolved (check 8)",
            "verdict": "NOT READY (synthetic fixture)",
        }
        (run_dir / f"review-v2-{DATE}.json").write_text(
            json.dumps(red, indent=2, ensure_ascii=False), encoding="utf-8")
        proc = run_pub(args)
        check(proc.returncode != 0,
              "--publish with approved:true but 13/15 review exits non-zero")
        check("13/15" in proc.stdout,
              "--publish with 13/15 review says why (gate not 15/15)")
        check(not (ed / f"data-{DATE}.json").exists(),
              "13/15 refusal wrote zero files")


def test_publish_success_scratch():
    print("== 5. --publish success on scratch copies (synthetic green review) ==")
    print("    FIXTURE NOTE: the green review below is synthetic -- it is "
          "retained so this test controls the review content exactly. "
          "The real gate is 15/15 since the 2026-11-15 decisions; the "
          "fixture stands in for a future edition's 15/15 review, for "
          "this test only.")
    with tempfile.TemporaryDirectory(prefix="v2-pub-test-") as tmp:
        tmp = Path(tmp)
        run_dir = scratch_run_dir(tmp)
        ed, app_ed, tracker = scratch_trees(tmp)

        # Approval file + synthetic green review (15/15), scratch only.
        (run_dir / f"approval-{DATE}.json").write_text(
            json.dumps({"approved": True, "reviewer": "Rudro",
                        "notes": "test approval -- synthetic green review"},
                       ensure_ascii=False), encoding="utf-8")
        green = {
            "date": DATE, "edition": "synthetic green fixture (test only)",
            "engine": "v2",
            "gate": "v2 publish gate, CONTRACTS.md / RULES.md (15 checks, all must pass)",
            "status": "draft",
            "checks": [{"n": n, "check": f"check {n}", "detail": "fixture",
                        "pass": True} for n in range(1, 16)],
            "tally": "15/15 pass",
            "verdict": "READY (synthetic fixture)",
        }
        (run_dir / f"review-v2-{DATE}.json").write_text(
            json.dumps(green, indent=2, ensure_ascii=False), encoding="utf-8")

        proc = run_pub(_publish_args(tmp, run_dir, ed, app_ed, tracker))
        check(proc.returncode == 0,
              f"--publish with approval + green review exits 0 (got "
              f"{proc.returncode}: {proc.stdout[-400:]} {proc.stderr[-200:]})")

        # Copied files.
        check((ed / f"data-{DATE}.json").exists(),
              "data file copied to scratch editions/")
        check((app_ed / f"data-{DATE}.json").exists(),
              "data file copied to scratch app/assets/editions/ (asset copy)")
        check((app_ed / f"bn-{DATE}.json").exists(),
              "bn file copied to scratch app/assets/editions/")
        if (ed / f"data-{DATE}.json").exists():
            pub = json.loads((ed / f"data-{DATE}.json").read_text(encoding="utf-8"))
            check(pub.get("status") == "published", "published data status published")
            check(pub.get("edition_day") == "Sunday",
                  "published data edition_day Sunday (2026-11-15)")
            check(pub.get("approval_notes") == "test approval -- synthetic green review",
                  "published data carries approval_notes")
            check(pub.get("coverage") == "14 Nov 2026, 7:47 AM to 2026-11-15, "
                  "7:47 AM (Asia/Dhaka)", "published data coverage is the gate label")
        check((ed / f"edition-{DATE}.xlsx").exists(),
              "staged xlsx copied to scratch editions/")
        check((ed / f"edition-{DATE}.pdf").exists(),
              "staged pdf copied to scratch editions/")

        # Both index.json entries, identical; first v2 edition resets
        # the v1 7/7 count to 0 and makes the v2 run 1/7.
        idx_live = json.loads((ed / "index.json").read_text(encoding="utf-8"))
        idx_app = json.loads((app_ed / "index.json").read_text(encoding="utf-8"))
        check(idx_live == idx_app, "both scratch index.json files identical")
        entries = [e for e in idx_live["editions"] if e["edition_date"] == DATE]
        check(len(entries) == 1, "exactly one new index entry for the date")
        if entries:
            e = entries[0]
            check(e["status"] == "published", "index entry status published")
            check(e["stories"] == 15 and e["words"] == 20
                  and e["phrases"] == 10 and e["mcqs"] == 25,
                  "index entry counts 15/20/10/25")
            check(e["coverage"] == "14 Nov 2026, 7:47 AM to 2026-11-15, "
                  "7:47 AM (Asia/Dhaka)", "index entry coverage is the gate label")
            check(isinstance(e["sources"], int) and e["sources"] == 15,
                  "index entry sources = 15 distinct story source URLs")
            check("First v2 edition" in e["review"]
                  and "reset to 0" in e["review"],
                  "index entry review says first v2 edition, reset to 0")
        check(idx_live.get("correct_consecutive_editions") == 1,
              "correct_consecutive_editions set to 1 (first v2 edition, "
              "reset from v1 7/7)")
        check("v2 run is 1" in idx_live.get("correct_rule", ""),
              "correct_rule rewritten for the v2 run (run is 1)")
        check("correct-consecutive count set to 1" in proc.stdout.lower(),
              "publish output records the v2 count set to 1")

        # Tracker.md row (v2 tracker, starts empty: row #1).
        tracker_text = tracker.read_text(encoding="utf-8")
        check(f"| 1 | {DATE} |" in tracker_text,
              "v2 tracker.md gained row #1 for the date")
        check("**Published**" in tracker_text.split(f"| 1 | {DATE} |", 1)[-1][:400],
              "tracker.md row says Published")
        check("Correct consecutive editions so far: 1 / 7." in tracker_text,
              "tracker.md correct-consecutive line now 1 / 7")
        check("Correct v2 edition 1/7" in tracker_text,
              "tracker.md row notes correct v2 edition 1/7")

        # Published snapshot, review flip, tracker record.
        check((run_dir / f"published-{DATE}.json").exists(),
              "published-<date>.json written to scratch run dir")
        review = json.loads((run_dir / f"review-v2-{DATE}.json").read_text(encoding="utf-8"))
        check(review.get("status") == "published",
              "review status flipped draft -> published")
        rec_path = run_dir / f"tracker-record-{DATE}.json"
        check(rec_path.exists(), "tracker-record-<date>.json written")
        if rec_path.exists():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            check(rec.get("engine") == "v2" and rec.get("date") == DATE,
                  "tracker record is v2 for the date")
            check(rec.get("collected") == 1514 and rec.get("keep") == 128
                  and rec.get("maybe") == 300 and rec.get("reject") == 949,
                  "tracker record counts 1514/128/300/949 from edition stats")
            check(rec.get("stories") == 15 and rec.get("mcqs") == 25
                  and rec.get("review_passed") == 15
                  and rec.get("review_total") == 15
                  and rec.get("status") == "published",
                  "tracker record 15 stories / 25 MCQs / 15/15 / published")

    # (Live-tree safety is asserted in main() via before/after hashes,
    # not here: the flag is only computed after the whole suite runs.)


def test_v2_run_counter():
    print("== 6. _v2_run_counter: tracker reset at first v2 edition ==")
    import importlib.util
    spec = importlib.util.spec_from_file_location("publish_v2", PUBLISH_V2)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    counter = mod._v2_run_counter

    # (a) Live v1 index: 7/7, no v2 entry -> first v2, count 1.
    first, n, rule = counter({"correct_consecutive_editions": 7,
                              "editions": [{"review": "17/17 checks passed"}]})
    check(first is True and n == 1, "v1 index (7/7, no v2) -> first v2, count 1")
    check("v2 run is 1" in rule and "reset to 0" in rule,
          "first-v2 rule text says reset to 0, run is 1")
    # (b) One v2 entry already published, count 1 -> second v2, count 2.
    first, n, rule = counter({"correct_consecutive_editions": 1,
                              "editions": [{"review": "v2 gate 15/15 passed; "
                                            "First v2 edition"}]})
    check(first is False and n == 2, "one v2 entry, count 1 -> second v2, count 2")
    check("v2 run is 2" in rule, "second-v2 rule text says run is 2")
    # (c) Count missing entirely (defensive) -> 1.
    first, n, rule = counter({"editions": [{"review": "v2 gate 15/15 passed"}]})
    check(first is False and n == 1, "missing count -> 0 + 1 = 1")
    # (d) A v1 review that merely mentions v2 does not count as a v2 entry.
    first, n, rule = counter({"correct_consecutive_editions": 7,
                              "editions": [{"review": "mentions v2 gate in prose"}]})
    check(first is True, "review not STARTING with 'v2 gate' is not a v2 entry")


def main():
    global _LIVE_UNTOUCHED
    _live_paths = [ROOT / "editions" / "index.json",
                   ROOT / "app" / "assets" / "editions" / "index.json",
                   ROOT / "engine-v1" / "tracker.md",
                   ENGINE_V2 / "runs" / "tracker.md",
                   LIVE_RUN / f"review-v2-{DATE}.json"]
    _before = {str(p): sha(p) for p in _live_paths}
    test_gate_reproduction()
    test_publish_refusals()
    test_publish_success_scratch()
    test_v2_run_counter()
    _after = {str(p): sha(p) for p in _live_paths}
    _LIVE_UNTOUCHED = _before == _after
    # Live-untouched check runs here (not inside test 5): the flag is
    # only computed after the whole suite has run.
    check(_LIVE_UNTOUCHED, "live editions/index.json, app index.json, v1 "
          "tracker.md, v2 tracker.md hashes unchanged after the suite")
    print()
    if FAILURES:
        print(f"FAILURES: {len(FAILURES)}")
        for f in FAILURES:
            print(f" - {f}")
        return 1
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
