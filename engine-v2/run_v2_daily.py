#!/usr/bin/env python3
"""run_v2_daily — Sarangsho Plus engine v2 daily orchestrator.

Thin orchestrator for one v2 edition day. It runs the v2 pipeline,
converts the result to app format, runs the v2 publish gate, and
then STOPS at the human gate. It never publishes on its own.

Run order (each step stops the run on failure; nothing after a
failed step runs):
  1. Paste check — read engine/paste/paste-<date>.md if present
     (07:30 deadline, optional-only, never required). Records
     paste_file_found + paste_count in the run report.
  2. v2 run — run_v2.run(date, fresh=True). Always fresh; never
     reuse a stale articles file.
  3. Convert — convert_to_app.py --date <date>
     (staging = runs/<date>/app-format).
  4. Export — export_app_format.py --date (XLSX + PDF beside the
     staged data file).
  5. Gate — publish_v2.py --check --date <date> (subprocess ONLY;
     never imported). Below 15/15: STOP, print the failing checks,
     exit 1, publish nothing. At 15/15: STOP at the human gate —
     print "ready for review", exit 0.
  6. Publish — ONLY with --publish AND an approval file
     runs/<date>/approval-<date>.json saying approved: true.
     Then publish_v2.py --publish --date <date> runs as a
     subprocess. Without an approval file the script always stops
     at the human gate. There is NO auto-publish path.

Browser sync is a SEPARATE step: this script never syncs anything
to GitHub. Sync happens via the browser route after publish
(SWITCH_PLAN.md §6).

Tracker: the publish step (publish_v2.py --publish) writes
runs/<date>/tracker-record-<date>.json and updates the v2 tracker
(engine-v2/runs/tracker.md), and sets correct_consecutive_editions
/ correct_rule in both index.json files: 1 at the first v2 edition
(Edition 11 = v2 Day 1; the v1 run closed at 7/7, reset to 0 —
Rudro's rule 2026-11-15), +1 per later v2 edition. The v1 tracker
(engine/runs/tracker.md) is never touched by a v2 publish.
tracker.db recording is still MANUAL until engine/db.py gains a v2
record path — v1's db.py --record reads v1 run files (articles-,
events-, import-report-, review- in engine/runs/) that a v2 run
never produces, so it cannot consume v2 run files.

The script never edits a converted file by hand to make a check
pass, never pads a thin page, never invents stories, figures or
URLs. v1 (engine/) is frozen and is never touched or imported.

Usage:
  python3 run_v2_daily.py [--date YYYY-MM-DD] [--dry-run]
  python3 run_v2_daily.py [--date YYYY-MM-DD] --publish
  python3 run_v2_daily.py --reuse-run YYYY-MM-DD [--run-dir DIR]
                          [--dry-run | --publish]
--date defaults to today (Asia/Dhaka). --dry-run is the same as the
default stop-at-gate behaviour, made explicit. --reuse-run skips
steps 1-4 and gates an existing run dir (how a past dry run is
exercised without a fresh ~6-minute fetch); --run-dir points it at
a scratch copy instead of the live runs/<date>/ dir.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EDITIONS_DIR = ROOT / "editions"
RUNS_DIR = HERE / "runs"
PUBLISH_SCRIPT = HERE / "publish_v2.py"
CONVERT_SCRIPT = HERE / "convert_to_app.py"
EXPORT_SCRIPT = HERE / "export_app_format.py"

GATE_TOTAL = 15
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def today_dhaka():
    """Today as YYYY-MM-DD in Asia/Dhaka."""
    sys.path.insert(0, str(HERE))
    import common
    return common.today_dhaka()


def paste_check(date):
    """Step 1: optional paste file. Returns (found, count).

    Uses v2's own read_paste_file (engine-v2/step1_collect.py):
    engine/paste/paste-<date>.md in the v1 format, merged by
    collect() before dedup with found_via "paste". A missing file
    is normal — paste is optional-only, never required.
    """
    sys.path.insert(0, str(HERE))
    from step1_collect import read_paste_file
    articles, found = read_paste_file(date)
    return found, len(articles)


def run_cmd(argv, label):
    """Run a subprocess, echoing its output. Returns (rc, output)."""
    print(f"[daily] {label}: {' '.join(str(a) for a in argv)}")
    proc = subprocess.run(argv, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    if out.strip():
        print(out.rstrip())
    return proc.returncode, out


def gate_supports_run_dir():
    """True if publish_v2.py accepts --run-dir (probe --help).

    The gate is only ever pointed at a scratch run dir through
    --run-dir when the script says it supports it; otherwise the
    orchestrator refuses to gate a scratch dir rather than risk
    touching the live runs/<date>/ dir.
    """
    if not PUBLISH_SCRIPT.exists():
        return False
    try:
        proc = subprocess.run(
            [sys.executable, str(PUBLISH_SCRIPT), "--help"],
            capture_output=True, text=True, timeout=30)
        return "--run-dir" in (proc.stdout or "") + (proc.stderr or "")
    except Exception:
        return False


def gate_argv(date, run_dir):
    """argv for publish_v2.py --check, or None + reason if the gate
    cannot be run safely against this run dir."""
    if not PUBLISH_SCRIPT.exists():
        return None, ("publish_v2.py does not exist yet — the v2 gate "
                      "script has not been delivered, so the gate "
                      "cannot run and the edition stops here.")
    default_dir = RUNS_DIR / date
    if run_dir.resolve() != default_dir.resolve():
        if not gate_supports_run_dir():
            return None, ("publish_v2.py does not accept --run-dir, so "
                          "the gate cannot be pointed at the scratch "
                          f"run dir {run_dir} — refusing to run it "
                          "against the live runs/<date>/ dir instead.")
        return ([sys.executable, str(PUBLISH_SCRIPT), "--check",
                 "--date", date, "--run-dir", str(run_dir)], "")
    return [sys.executable, str(PUBLISH_SCRIPT), "--check",
            "--date", date], ""


def publish_argv(date, run_dir):
    """argv for publish_v2.py --publish, mirroring gate_argv."""
    if not PUBLISH_SCRIPT.exists():
        return None, "publish_v2.py does not exist yet."
    default_dir = RUNS_DIR / date
    if run_dir.resolve() != default_dir.resolve():
        if not gate_supports_run_dir():
            return None, ("publish_v2.py does not accept --run-dir, so "
                          "the publish step cannot be pointed at the "
                          f"scratch run dir {run_dir}.")
        return ([sys.executable, str(PUBLISH_SCRIPT), "--publish",
                 "--date", date, "--run-dir", str(run_dir)], "")
    return [sys.executable, str(PUBLISH_SCRIPT), "--publish",
            "--date", date], ""


def read_gate_review(run_dir, date):
    """Parse runs/<date>/review-v2-<date>.json.

    Returns a dict with passed/failed/unresolved check numbers,
    the tally string, and the check-8 (longest-correct) detail —
    or None when the gate wrote no review file.
    """
    path = Path(run_dir) / f"review-v2-{date}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"review file unreadable: {e}"}
    checks = data.get("checks", [])
    passed, failed, unresolved = [], [], []
    longest_detail = ""
    for c in checks:
        n = c.get("n")
        if c.get("pass") is True:
            passed.append(n)
        elif c.get("pass") is False:
            failed.append(n)
        else:
            unresolved.append(n)
        if n == 8:
            longest_detail = c.get("detail", "")
    total = len(checks) or GATE_TOTAL
    return {"passed": passed, "failed": failed,
            "unresolved": unresolved, "total": total,
            "tally": data.get("tally", f"{len(passed)}/{total} pass"),
            "verdict": data.get("verdict", ""),
            "longest_detail": longest_detail,
            "path": str(path)}


def read_approval(run_dir, date):
    """Read runs/<date>/approval-<date>.json.

    Returns (approved_bool, reason). Only approved: true counts.
    """
    path = Path(run_dir) / f"approval-{date}.json"
    if not path.exists():
        return False, f"no approval file ({path.name} missing)"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"approval file unreadable: {e}"
    if data.get("approved") is True:
        reviewer = data.get("reviewer", "unknown reviewer")
        return True, f"approved by {reviewer}"
    return False, "approval file says approved: false"


def edition_stats(run_dir, date):
    """Counts from runs/<date>/edition-<date>.json, or {}."""
    path = Path(run_dir) / f"edition-{date}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("stats", {})
    except Exception:
        return {}


def print_gate_result(review):
    """Print the gate result plainly (failing checks by number)."""
    if review is None:
        print("[daily] GATE: no review file was written — "
              "gate result unknown, stopping.")
        return
    if "error" in review:
        print(f"[daily] GATE: {review['error']} — stopping.")
        return
    print(f"[daily] GATE: {review['tally']} "
          f"({len(review['passed'])}/{review['total']} passed)")
    if review["failed"]:
        print(f"[daily] GATE FAILING checks: "
              f"{', '.join(str(n) for n in review['failed'])}")
    if review["unresolved"]:
        print(f"[daily] GATE UNRESOLVED checks (need Rudro's call): "
              f"{', '.join(str(n) for n in review['unresolved'])}")
    if review["longest_detail"]:
        print(f"[daily] GATE check 8 (longest-correct): "
              f"{review['longest_detail']}")
    if review["verdict"]:
        print(f"[daily] GATE verdict: {review['verdict']}")


def print_report(date, *, paste_found, paste_count, stats, gate,
                 published, stopped_at, missing, next_steps):
    """The run report: counts, gate, publish state, what is missing,
    what Rudro needs to do. Always states the tracker status and
    that browser sync is a separate step."""
    print("")
    print(f"===== Sarangsho Plus v2 run report — {date} =====")
    print(f"Paste file: {'found' if paste_found else 'not found'}"
          + (f" ({paste_count} article(s))" if paste_found else
             " (optional-only; no paste file is normal)")
          + f" — engine/paste/paste-{date}.md, 07:30 deadline")
    if stats:
        dec = stats.get("decisions", {})
        print(f"Collected: {stats.get('collected', '?')} articles; "
              f"keep {dec.get('keep', '?')} / maybe {dec.get('maybe', '?')} "
              f"/ reject {dec.get('reject', '?')}")
        print(f"Page items: {stats.get('page_items', '?')} "
              f"(floor 12, ceiling 15); "
              f"Q&A {stats.get('qa', '?')}, MCQ {stats.get('mcq', '?')} raw, "
              f"analytical {stats.get('analytical', '?')}, "
              f"SRS cards {stats.get('srs_cards', '?')}")
        vocab = stats.get("vocab", {})
        print(f"Vocabulary: {vocab.get('words', '?')} words / "
              f"{vocab.get('phrases', '?')} phrases / "
              f"{vocab.get('revision_words', '?')} revision "
              f"(target 20/10/5)")
        ed = stats.get("editorial", {})
        print(f"Editorial slot: "
              + ("filled" if ed.get("filled") else
                 f"empty ({ed.get('reason', '')})"))
    else:
        print("Run stats: unavailable (no edition file for this date)")
    if gate is not None:
        print(f"Gate: {gate.get('tally', '?')} "
              f"(failing: {gate.get('failed') or 'none'}; "
              f"unresolved: {gate.get('unresolved') or 'none'})")
    else:
        print("Gate: did not run")
    print(f"Published: {'YES' if published else 'NO — NOT published: ' + stopped_at}")
    print("Tracker: tracker.md is updated by the publish step "
          "(publish_v2.py --publish writes "
          f"runs/<date>/tracker-record-<date>.json and updates "
          "runs/tracker.md). tracker.db recording is still MANUAL "
          "until engine/db.py gains a v2 record path — v1's "
          "db.py --record reads v1 run files (articles-, events-, "
          "import-report-, review-) that a v2 run never produces. "
          "correct_consecutive_editions / correct_rule were NOT "
          "changed by this run (tracker reset is Rudro's call, "
          "still pending).")
    print("Sync: browser sync is a SEPARATE step — this script does "
          "NOT sync anything to GitHub. After publish, sync via the "
          "browser route (SWITCH_PLAN.md §6) and verify the live index.")
    if missing:
        print("Missing: " + "; ".join(missing))
    if next_steps:
        print("Rudro needs to: " + "; ".join(next_steps))
    print(f"===== end of report — {date} =====")


def run_gate(date, run_dir):
    """Run the gate subprocess and parse its review file.

    Returns (gate_ok, review, error). gate_ok is True only when the
    review file says every check passed.
    """
    argv, reason = gate_argv(date, run_dir)
    if argv is None:
        return False, None, reason
    rc, _out = run_cmd(argv, "gate (publish_v2.py --check)")
    review = read_gate_review(run_dir, date)
    if review is None:
        return False, None, (f"gate exited {rc} but wrote no review "
                             f"file {run_dir}/review-v2-{date}.json")
    if "error" in review:
        return False, review, review["error"]
    ok = (not review["failed"] and not review["unresolved"]
          and len(review["passed"]) == review["total"])
    return ok, review, ""


def try_publish(date, run_dir):
    """Publish only with an approval file saying approved: true.

    Returns (published_bool, reason).
    """
    approved, why = read_approval(run_dir, date)
    if not approved:
        return False, f"refusing to publish: {why}"
    argv, reason = publish_argv(date, run_dir)
    if argv is None:
        return False, f"cannot publish: {reason}"
    rc, _out = run_cmd(argv, "publish (publish_v2.py --publish)")
    if rc != 0:
        return False, f"publish_v2.py --publish exited {rc}"
    return True, why


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Sarangsho Plus engine v2 daily orchestrator "
                    "(stops at the human gate; never auto-publishes)")
    ap.add_argument("--date", default=None,
                    help="edition date YYYY-MM-DD (default: today Asia/Dhaka)")
    ap.add_argument("--publish", action="store_true",
                    help="publish only with an approval file "
                         "(runs/<date>/approval-<date>.json, approved: true)")
    ap.add_argument("--reuse-run", default=None, metavar="YYYY-MM-DD",
                    help="gate an existing run dir instead of a fresh "
                         "run (skips paste check, v2 run, convert, export)")
    ap.add_argument("--run-dir", default=None,
                    help="run dir to gate (only with --reuse-run; "
                         "default runs/<date>). Use a scratch copy to "
                         "exercise a past dry run without touching live files.")
    ap.add_argument("--dry-run", action="store_true",
                    help="explicit stop-at-gate behaviour (the default "
                         "already stops at the gate; this just says so)")
    args = ap.parse_args(argv)

    date = args.date or today_dhaka()
    if not DATE_RE.match(date):
        print(f"[daily] bad --date {date!r}: use YYYY-MM-DD")
        return 2
    if args.reuse_run and not DATE_RE.match(args.reuse_run):
        print(f"[daily] bad --reuse-run {args.reuse_run!r}: use YYYY-MM-DD")
        return 2
    if args.run_dir and not args.reuse_run:
        print("[daily] --run-dir is only for --reuse-run")
        return 2

    reuse_date = args.reuse_run or date
    if args.reuse_run:
        run_dir = Path(args.run_dir) if args.run_dir else RUNS_DIR / reuse_date
        staging = run_dir / "app-format"
    else:
        run_dir = RUNS_DIR / date
        staging = run_dir / "app-format"
    date = reuse_date if args.reuse_run else date

    paste_found, paste_count = False, 0
    stats = {}
    missing = []
    published = False

    if args.publish:
        # Fail fast: publishing needs an approval file saying
        # approved: true. Refusing here (before the gate, let alone
        # a 6-minute fresh run) names the blocker plainly instead
        # of letting a gate failure mask it. The gate must still
        # pass before anything publishes — this check adds a
        # refusal, it never bypasses one.
        approved, why = read_approval(run_dir, date)
        if not approved:
            print(f"[daily] refusing to publish: {why} — NOT "
                  "published, NOT synced.")
            print_report(date, paste_found=paste_found,
                         paste_count=paste_count, stats=stats,
                         gate=None, published=False,
                         stopped_at=f"publish refused ({why})",
                         missing=[why],
                         next_steps=["write "
                                     f"runs/{date}/approval-{date}.json "
                                     "with approved: true (reviewer + "
                                     "notes), then re-run with --publish"])
            return 1

    if args.reuse_run:
        # --reuse-run: skip steps 1-4; gate the existing run only.
        if not (run_dir / f"edition-{reuse_date}.json").exists():
            print(f"[daily] no edition file in {run_dir} — "
                  "nothing to gate; run the full flow first.")
            return 1
        if not staging.exists():
            missing.append("no app-format staging in the run dir — "
                           "convert first (convert_to_app.py)")
            print(f"[daily] no staging dir {staging} — the gate needs "
                  "the converted file. Convert first, then re-run.")
            return 1
        stats = edition_stats(run_dir, reuse_date)
        # Paste state for the report only (read-only check).
        try:
            paste_found, paste_count = paste_check(reuse_date)
        except Exception as e:
            print(f"[daily] paste check failed (non-fatal): {e}")
    else:
        # ---- Step 1: paste check (optional-only, never required) ----
        try:
            paste_found, paste_count = paste_check(date)
        except Exception as e:
            print(f"[daily] paste check failed (non-fatal): {e}")
            paste_found, paste_count = False, 0
        print(f"[daily] paste: {'found' if paste_found else 'no file'}"
              + (f", {paste_count} article(s)" if paste_found else ""))

        # ---- Step 2: v2 run, always fresh ---------------------------
        sys.path.insert(0, str(HERE))
        try:
            import run_v2
            stats = run_v2.run(date, fresh=True)
        except Exception as e:
            print(f"[daily] v2 run FAILED: {e}")
            print_report(date, paste_found=paste_found,
                         paste_count=paste_count, stats={},
                         gate=None, published=False,
                         stopped_at="v2 run failed",
                         missing=[f"v2 run failed: {e}"],
                         next_steps=["check the v2 run output above; "
                                     "Edition 11 fallback decision by "
                                     "10:00 Asia/Dhaka (SWITCH_PLAN.md §7)"])
            return 1
        print(f"[daily] v2 run done: collected "
              f"{stats.get('collected')}, page "
              f"{stats.get('page_items')} items")

        # ---- Step 3: convert to app format (staging only) -----------
        rc, _ = run_cmd([sys.executable, str(CONVERT_SCRIPT),
                         "--date", date, "--run-dir", str(run_dir),
                         "--staging", str(staging)],
                        "convert (convert_to_app.py)")
        if rc != 0:
            print_report(date, paste_found=paste_found,
                         paste_count=paste_count, stats=stats,
                         gate=None, published=False,
                         stopped_at="convert failed",
                         missing=["convert_to_app.py failed — no "
                                  "converted file, no gate"],
                         next_steps=["fix the converter and re-run; "
                                     "fallback decision by 10:00 "
                                     "Asia/Dhaka if not fixable"])
            return 1

        # ---- Step 4: XLSX + PDF exports ------------------------------
        rc, _ = run_cmd([sys.executable, str(EXPORT_SCRIPT),
                         "--date", date], "export (export_app_format.py)")
        if rc != 0:
            print_report(date, paste_found=paste_found,
                         paste_count=paste_count, stats=stats,
                         gate=None, published=False,
                         stopped_at="export failed",
                         missing=["export_app_format.py failed — XLSX/PDF "
                                  "exports missing"],
                         next_steps=["fix the export step and re-run"])
            return 1

    # ---- Step 5: gate (never overridden, never hand-fixed) ----------
    gate_ok, review, gate_error = run_gate(date, run_dir)
    if gate_error:
        print(f"[daily] GATE could not run: {gate_error}")
        print_report(date, paste_found=paste_found,
                     paste_count=paste_count, stats=stats,
                     gate=review, published=False,
                     stopped_at="gate could not run",
                     missing=[gate_error],
                     next_steps=["deliver publish_v2.py (gate script) "
                                 "and re-run"])
        return 1
    print_gate_result(review)
    if not gate_ok:
        print("[daily] STOPPED at the gate — NOT published, NOT synced.")
        print_report(date, paste_found=paste_found,
                     paste_count=paste_count, stats=stats,
                     gate=review, published=False,
                     stopped_at="gate below 15/15 (or unresolved checks)",
                     missing=["gate did not pass — see failing/unresolved "
                              "checks above; fix the engine/converter "
                              "input and re-run, never hand-edit the "
                              "converted file"],
                     next_steps=["review the failing checks; fix upstream "
                                 "and re-run (fallback decision by 10:00 "
                                 "Asia/Dhaka if not fixable)"])
        return 1

    # Gate passed. Default (and --dry-run): STOP at the human gate.
    if not args.publish:
        print("[daily] Gate 15/15 — READY FOR REVIEW. Stopping at the "
              "human gate: NOT published, NOT synced.")
        print_report(date, paste_found=paste_found,
                     paste_count=paste_count, stats=stats,
                     gate=review, published=False,
                     stopped_at="human gate (ready for review)",
                     missing=[],
                     next_steps=["Rudro reviews the converted edition "
                                 "(spot-check MCQs against sources — the "
                                 "Edition 7 lesson) and writes "
                                 f"runs/{date}/approval-{date}.json with "
                                 "approved: true to publish"])
        return 0

    # ---- Step 6: publish — approval file only, no auto-publish ------
    published, why = try_publish(date, run_dir)
    if not published:
        print(f"[daily] {why} — NOT published, NOT synced.")
        print_report(date, paste_found=paste_found,
                     paste_count=paste_count, stats=stats,
                     gate=review, published=False,
                     stopped_at=f"human gate ({why})",
                     missing=[why],
                     next_steps=["write "
                                 f"runs/{date}/approval-{date}.json with "
                                 "approved: true (reviewer + notes), then "
                                 "re-run with --publish"])
        return 1
    print(f"[daily] PUBLISHED ({why}).")
    print_report(date, paste_found=paste_found,
                 paste_count=paste_count, stats=stats,
                 gate=review, published=True,
                 stopped_at="",
                 missing=["browser sync not done by this script — "
                          "sync is a separate step"],
                 next_steps=["sync via the browser route "
                             "(editions/data, bn, index.json) and verify "
                             "the live index; record the tracker.db row "
                             "by hand until db.py gains a v2 path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
