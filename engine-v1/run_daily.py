#!/usr/bin/env python3
"""run_daily.py — Phase 2 daily runner (ENGINE_DESIGN §5, Modules 1-6).

One command, end to end, up to the human review gate:
  1. tools/collector/collect.py (Sarangsho Plus Collector — Bing News
     RSS + Google News RSS + Prothom Alo feed; fully automated, free,
     no paste needed; paste file is optional only)
  2. clean_rank.py (event grouping + 0-100 ranking, borderline list)
  3. summarise_exam.py --prompt (Claude Project prompt for Rudro)
Then it STOPS. It never writes a draft, never approves, never
publishes — those need the Claude pack (step 4) and Rudro's review
(step 5). The full day is:
  python3 run_daily.py --date YYYY-MM-DD --bodies
  # paste claude-prompt-<date>.md into the Claude Project, save the
  # JSON reply as runs/<date>/reviewed-pack-<date>.json
  python3 summarise_exam.py --date YYYY-MM-DD --import-pack runs/<date>/reviewed-pack-<date>.json
  python3 publish.py --date YYYY-MM-DD --check
  # Rudro writes runs/<date>/approval-<date>.json, then:
  python3 publish.py --date YYYY-MM-DD --publish
  python3 db.py --record runs/<date>
Usage: python3 run_daily.py [--date YYYY-MM-DD] [--bodies]
Only stdlib here; sub-steps import openpyxl/reportlab lazily.
"""
import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
ROOT = ENGINE.parent
COLLECTOR = ROOT / "tools" / "collector" / "collect.py"


def run(cmd, label):
    print(f"[run_daily] --- {label} ---")
    r = subprocess.run([sys.executable, str(cmd[0]), *cmd[1:]])
    if r.returncode != 0:
        print(f"[run_daily] {label} exited {r.returncode} (see above)")
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--bodies", action="store_true")
    args = ap.parse_args()
    day = args.date
    rundir = ENGINE / "runs" / day
    print(f"[run_daily] Sarangsho Plus — Phase 2 daily run for {day}")
    print("[run_daily] Collection is fully automated (Sarangsho Plus "
          "Collector: Bing + Google News RSS + Prothom Alo feed). "
          "Paste file is optional only — nobody has to paste anything.")
    rc = 0
    rc |= run([COLLECTOR, "--date", day,
               *(
                   ["--bodies"] if args.bodies else []),
               "--out", str(rundir)], "1. Collect (Sarangsho Plus Collector)")
    rc |= run([ENGINE / "clean_rank.py", "--date", day,
               "--in", str(rundir)], "2-3. Clean + Rank")
    rc |= run([ENGINE / "summarise_exam.py", "--date", day, "--prompt",
               "--in", str(rundir)], "4-5. Claude prompt (Summarise + Exam)")
    print("[run_daily] STOPPED at the human gate — as designed.")
    print(f"[run_daily] Next: paste runs/{day}/claude-prompt-{day}.md into "
          "the Claude Project, save the JSON reply as "
          f"runs/{day}/reviewed-pack-{day}.json, then run --import-pack.")
    print("[run_daily] Nothing was published. No edition is correct until "
          "Rudro reviews and approves it.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
