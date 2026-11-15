"""Regenerate the XLSX + PDF exports for a converted v2 edition.

Reads the staged app-format data file (runs/<date>/app-format/
data-<date>.json) and writes edition-<date>.xlsx / .pdf beside it,
using v1's export_xlsx()/export_pdf() imported unmodified from
engine/publish.py -- the same exporters that produce the v1 run
exports. This script is separate from convert_to_app.py on purpose:
the converter stays stdlib-only and never imports v1; exports are
a post-conversion step. Run after every conversion -- the files in
app-format/ are staging only, never published or synced.

Usage: python3 export_app_format.py --date 2026-11-15
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine"
sys.path.insert(0, str(ENGINE))

from publish import export_pdf, export_xlsx  # noqa: E402  (v1, unmodified)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="edition date YYYY-MM-DD")
    args = ap.parse_args()
    staging = HERE / "runs" / args.date / "app-format"
    data_path = staging / f"data-{args.date}.json"
    draft = json.loads(data_path.read_text(encoding="utf-8"))
    xlsx = export_xlsx(draft, staging / f"edition-{args.date}.xlsx")
    pdf = export_pdf(draft, staging / f"edition-{args.date}.pdf")
    print(f"[export] wrote {xlsx} ({xlsx.stat().st_size} B)")
    print(f"[export] wrote {pdf} ({pdf.stat().st_size} B)")


if __name__ == "__main__":
    main()
