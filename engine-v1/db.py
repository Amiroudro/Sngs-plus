#!/usr/bin/env python3
"""Phase 2 tracker — SQLite record of every daily run.

Tables: editions (one row per edition date: counts at each stage,
review result, published or not) and runs (free-form log lines).
Usage: python3 db.py --record runs/2026-11-08 (reads that run's
summary files)  |  python3 db.py --status  (prints the 7-day table)
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_json

DB = Path(__file__).resolve().parent / "tracker.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS editions (
  date TEXT PRIMARY KEY,
  collected INTEGER, events INTEGER, kept INTEGER, borderline INTEGER,
  stories INTEGER, words INTEGER, phrases INTEGER, mcqs INTEGER,
  review_passed INTEGER, review_total INTEGER,
  status TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT, stage TEXT, message TEXT, created_at TEXT DEFAULT (datetime('now')));
"""


def connect():
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    return con


def record(run_dir: Path):
    day = run_dir.name
    def read(name):
        p = run_dir / name
        return load_json(p) if p.exists() else {}
    arts = read(f"articles-{day}.json")
    evs = read(f"events-{day}.json")
    imp = read(f"import-report-{day}.json")
    rev = read(f"review-{day}.json")
    counts = imp.get("counts", {})
    # Fix 5 (audit): record who wrote the pack — 'claude' (the Claude
    # Project as designed) or 'agent' (the operator acting as it).
    # The import report carries pack_author; the notes field carries
    # it into the tracker so the honesty is visible in one place.
    notes = "; ".join(imp.get("problems", []))[:500]
    author = imp.get("pack_author")
    if author and author != "unknown":
        notes = (f"pack: {author}" + ("; " + notes if notes else ""))[:500]
    con = connect()
    con.execute(
        "INSERT OR REPLACE INTO editions (date, collected, events, kept, borderline,"
        " stories, words, phrases, mcqs, review_passed, review_total, status, notes)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (day, len(arts.get("articles", [])), evs.get("events_collected", 0),
         len(evs.get("kept", [])), len(evs.get("borderline", [])),
         counts.get("stories", 0), counts.get("words", 0),
         counts.get("phrases", 0), counts.get("mcqs", 0),
         rev.get("passed", 0), rev.get("total", 0),
         rev.get("status", "draft"),
         notes))
    con.commit()
    con.close()
    print(f"[db] recorded {day}")


def status():
    con = connect()
    rows = con.execute(
        "SELECT date, collected, events, kept, borderline, stories, words,"
        " phrases, mcqs, review_passed, review_total, status FROM editions"
        " ORDER BY date").fetchall()
    con.close()
    print("date        coll evts kept bord | stor wrds phrs mcqs | review  status")
    for r in rows:
        print(f"{r[0]}  {r[1]:4d} {r[2]:4d} {r[3]:4d} {r[4]:4d} |"
              f" {r[5]:4d} {r[6]:4d} {r[7]:4d} {r[8]:4d} |"
              f" {r[9]}/{r[10]:<2d}    {r[11]}")
    print(f"Correct consecutive editions so far: "
          f"{sum(1 for r in rows if r[11] == 'published' and r[9] == r[10])} "
          "(target: 7 before any charge — ENGINE_DESIGN §10)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", default=None)
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.record:
        record(Path(args.record))
        return 0
    if args.status:
        return status()
    ap.error("need --record <run dir> or --status")


if __name__ == "__main__":
    raise SystemExit(main())
