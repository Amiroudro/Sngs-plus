#!/usr/bin/env python3
"""run_v2_daily tests — orchestrator stop-at-gate / refuse-to-publish.

Run: python3 tests/test_run_v2_daily.py
Stdlib only. All CLI tests run against a SCRATCH COPY of the
2026-11-15 run dir (temp dir); the live runs/2026-11-15/ dir and
the live editions/ tree are never written to — hashes of the live
files are taken before and after and must be unchanged. No fresh
v2 fetch is ever run here (too slow/flaky); the reuse-run tests
cover the orchestrator logic.

publish_v2.py is built by a parallel worker and may not exist yet.
The CLI tests therefore branch honestly:
  * if it exists and accepts --run-dir: the gate runs for real on
    the scratch copy and must report 15/15 (the 2026-11-15 gate
    fixes: check 12 Bangla-digit normalisation, check 8 excl
    definition). At 15/15 the orchestrator STOPS at the human gate
    -- "ready for review", exit 0, nothing published.
  * if it is missing (or has no --run-dir): the orchestrator must
    refuse to gate, exit non-zero, publish nothing, and say so.
Either branch publishes nothing and writes nothing live. The branch
taken is printed.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_v2_daily as daily

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
RUN_2026_11_15 = HERE / "runs" / "2026-11-15"
LIVE_GUARDS = [
    ROOT / "editions" / "index.json",
    ROOT / "editions" / "data-2026-11-15.json",
    ROOT / "engine" / "runs" / "tracker.md",
    RUN_2026_11_15 / "review-v2-2026-11-15.json",
]

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def file_hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(paths):
    return {str(p): file_hash(p) for p in paths if Path(p).exists()}


def run_cli(args):
    return subprocess.run(
        [sys.executable, str(HERE / "run_v2_daily.py")] + args,
        capture_output=True, text=True, timeout=120)


def main():
    print("== paste check (v2 read_paste_file) ==")
    found, count = daily.paste_check("2026-11-08")
    check("paste file 2026-11-08 found", found is True, f"got {found}")
    check("paste count 2026-11-08 is 13", count == 13, f"got {count}")
    found15, count15 = daily.paste_check("2026-11-15")
    check("no paste file 2026-11-15", found15 is False, f"got {found15}")
    check("paste count 2026-11-15 is 0", count15 == 0, f"got {count15}")

    print("== approval file parsing ==")
    with tempfile.TemporaryDirectory() as td:
        rd = Path(td)
        ok, why = daily.read_approval(rd, "2026-11-15")
        check("no approval file -> not approved", ok is False, why)
        check("no approval file reason names the file",
              "approval" in why.lower(), why)
        (rd / "approval-2026-11-15.json").write_text(
            json.dumps({"approved": False, "reviewer": "x"}),
            encoding="utf-8")
        ok, why = daily.read_approval(rd, "2026-11-15")
        check("approved:false -> not approved", ok is False, why)
        (rd / "approval-2026-11-15.json").write_text(
            json.dumps({"approved": True, "reviewer": "Rudro",
                        "notes": "spot-checked"}),
            encoding="utf-8")
        ok, why = daily.read_approval(rd, "2026-11-15")
        check("approved:true -> approved", ok is True, why)
        (rd / "approval-2026-11-15.json").write_text(
            "{not json", encoding="utf-8")
        ok, why = daily.read_approval(rd, "2026-11-15")
        check("malformed approval file -> not approved", ok is False, why)

    print("== gate review parsing (scratch copy of the 15 Nov review) ==")
    gate_exists = daily.PUBLISH_SCRIPT.exists()
    gate_run_dir = gate_exists and daily.gate_supports_run_dir()
    print(f"  [info] publish_v2.py exists: {gate_exists}; "
          f"accepts --run-dir: {gate_run_dir}")
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "2026-11-15"
        shutil.copytree(RUN_2026_11_15, scratch)
        review = daily.read_gate_review(scratch, "2026-11-15")
        check("review file parses", review is not None
              and "error" not in review, str(review)[:200])
        check("gate tally is 15/15 pass",
              review and len(review["passed"]) == 15
              and review["total"] == 15,
              f"got {review['passed'] if review else None}/{review['total'] if review else '?'}")
        check("gate has no failing check",
              review and review["failed"] == [],
              f"got {review['failed'] if review else None}")
        check("gate has no unresolved check",
              review and review["unresolved"] == [],
              f"got {review['unresolved'] if review else None}")
        check("check 8 detail names the longest-correct question",
              review and "14/25" in review["longest_detail"],
              (review or {}).get("longest_detail", "")[:120])
        check("review file has no approval side effect",
              not (scratch / "approval-2026-11-15.json").exists())

    print("== CLI: --reuse-run on a scratch copy stops at the gate ==")
    before = snapshot(LIVE_GUARDS)
    before_listing = sorted(p.name for p in RUN_2026_11_15.iterdir())
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "2026-11-15"
        shutil.copytree(RUN_2026_11_15, scratch)
        proc = run_cli(["--reuse-run", "2026-11-15",
                        "--run-dir", str(scratch)])
        out = proc.stdout + proc.stderr
        print("  --- orchestrator output (reuse-run) ---")
        print(out.rstrip())
        print("  --- end output ---")
        check("reuse-run stops at the human gate at 15/15 (exit 0, "
              "ready for review)", proc.returncode == 0
              and "ready for review" in out.lower(),
              f"exit {proc.returncode}")
        check("reuse-run publishes nothing",
              "NOT published" in out and "[daily] PUBLISHED" not in out,
              out[-300:])
        if gate_run_dir:
            check("real gate ran on scratch copy: 15/15 in output",
                  "15/15" in out, out[-500:])
            check("real gate names check 8 excl count (1/25)",
                  "1/25" in out, out[-500:])
        else:
            check("missing/unsupported gate script is reported plainly",
                  "publish_v2.py" in out, out[-500:])
        check("no tracker-record file created in scratch",
              not (scratch / "tracker-record-2026-11-15.json").exists())
        check("no published file created in scratch",
              not (scratch / "published-2026-11-15.json").exists())
        # --check's contract is to (re)write the review file: the
        # gate must freshly evaluate the scratch copy and reach the
        # same verdict (15/15, no fail, no unresolved). A stale or
        # missing review would mean the gate did not run.
        fresh = daily.read_gate_review(scratch, "2026-11-15")
        check("scratch review freshly written by the gate (15/15)",
              fresh is not None and "error" not in fresh
              and len(fresh["passed"]) == 15 and fresh["total"] == 15
              and fresh["failed"] == []
              and fresh["unresolved"] == [],
              f"got {fresh}")
        check("browser sync stated as a separate step",
              "browser sync is a SEPARATE step" in out
              or "Sync: browser sync is a SEPARATE step" in out)
        check("tracker status stated (tracker.db manual)",
              "tracker.db" in out and "MANUAL" in out)
        check("report does not change correct_consecutive",
              "correct_consecutive_editions" in out
              and "NOT changed" in out)

    print("== CLI: --dry-run with --reuse-run, same stop-at-gate ==")
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "2026-11-15"
        shutil.copytree(RUN_2026_11_15, scratch)
        proc = run_cli(["--reuse-run", "2026-11-15",
                        "--run-dir", str(scratch), "--dry-run"])
        out = proc.stdout + proc.stderr
        check("dry-run reuse-run stops at the human gate at 15/15 "
              "(exit 0, ready for review)",
              proc.returncode == 0 and "ready for review" in out.lower(),
              f"exit {proc.returncode}")
        check("dry-run publishes nothing", "NOT published" in out)
        check("dry-run creates no tracker-record",
              not (scratch / "tracker-record-2026-11-15.json").exists())

    print("== CLI: --publish without an approval file refuses ==")
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "2026-11-15"
        shutil.copytree(RUN_2026_11_15, scratch)
        assert not (scratch / "approval-2026-11-15.json").exists()
        proc = run_cli(["--reuse-run", "2026-11-15",
                        "--run-dir", str(scratch), "--publish"])
        out = proc.stdout + proc.stderr
        print("  --- orchestrator output (publish, no approval) ---")
        print(out.rstrip())
        print("  --- end output ---")
        check("publish without approval exits non-zero",
              proc.returncode != 0, f"exit {proc.returncode}")
        check("publish without approval publishes nothing",
              "NOT published" in out)
        check("no tracker-record file created",
              not (scratch / "tracker-record-2026-11-15.json").exists())
        check("no published file created",
              not (scratch / "published-2026-11-15.json").exists())
        if gate_run_dir:
            check("refusal names the missing approval file",
                  "no approval file" in out, out[-500:])

    print("== CLI: usage errors ==")
    proc = run_cli(["--date", "15-11-2026", "--reuse-run", "2026-11-15"])
    check("bad --date exits non-zero", proc.returncode != 0)
    proc = run_cli(["--run-dir", "/tmp/x"])
    check("--run-dir without --reuse-run exits non-zero",
          proc.returncode != 0)
    check("today (Asia/Dhaka) is a valid date",
          bool(daily.DATE_RE.match(daily.today_dhaka())),
          daily.today_dhaka())

    print("== live files untouched ==")
    after = snapshot(LIVE_GUARDS)
    check("live guarded files unchanged", before == after,
          f"changed: {[k for k in before if before.get(k) != after.get(k)]}")
    after_listing = sorted(p.name for p in RUN_2026_11_15.iterdir())
    check("live 15 Nov run dir listing unchanged",
          before_listing == after_listing,
          f"before {before_listing} after {after_listing}")

    print(f"== {PASS} passed, {FAIL} failed ==")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
