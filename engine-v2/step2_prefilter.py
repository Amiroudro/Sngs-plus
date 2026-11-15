#!/usr/bin/env python3
"""Step 2 — Light pre-filter (engine v2).

Never hard-deletes: it only lowers priority. An item is deprioritised
when its title/summary/section matches a crime, accident or
entertainment term from RULES.md — UNLESS it contains one of the 10
always-let-through keywords, which always keep normal priority.
Every deprioritised headline is written to a weekly-scannable log
(runs/<date>/prefilter-log-<date>.md) so the operator can scan what
was lowered.

Priority is advisory only: Step 3 still decides every item, and
cluster size / priority never affect keep/reject.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rules_loader import load_rules

RULES = load_rules()


def _norm(text):
    return (text or "").lower()


def prefilter(article, rules=None):
    """Return (article_copy, log_entry_or_None).

    article_copy gains "priority" ("normal"|"low") and
    "prefilter_reason". log_entry is a dict for the weekly log when
    the item was deprioritised, else None.
    """
    rules = rules or RULES
    a = dict(article)
    text = _norm(f"{a.get('title', '')} {a.get('summary', '')} "
                 f"{a.get('section', '')}")
    # Always let through: any of the 10 keywords wins over everything.
    for kw in rules["let_through"]:
        if kw.lower() in text or kw in (a.get("title", "") +
                                        a.get("summary", "")):
            a["priority"] = "normal"
            a["prefilter_reason"] = "keyword-let-through"
            return a, None
    hit = None
    for term in rules["deprioritise"]:
        if not term:
            continue
        if term.isascii():
            # English terms must match on word boundaries: "actor" must
            # not fire inside "factory".
            if re.search(r"\b" + re.escape(term) + r"\b", text):
                hit = term
                break
        elif term in text:
            hit = term
            break
    if hit:
        a["priority"] = "low"
        a["prefilter_reason"] = f"deprioritised: {hit}"
        entry = {"id": a.get("id", ""), "title": a.get("title", ""),
                 "source": a.get("source", ""), "reason": hit,
                 "url": a.get("url", "")}
        return a, entry
    a["priority"] = "normal"
    a["prefilter_reason"] = ""
    return a, None


def prefilter_batch(articles, rules=None):
    """Return (articles_with_priority, log_entries)."""
    out, log = [], []
    for a in articles:
        b, entry = prefilter(a, rules)
        out.append(b)
        if entry:
            log.append(entry)
    return out, log


def write_log(log, date, outdir):
    """Weekly-scannable markdown log of deprioritised headlines."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"prefilter-log-{date}.md"
    lines = [f"# Pre-filter log — {date}",
             "",
             f"Deprioritised headlines: {len(log)} (low priority only; "
             "nothing was deleted, Step 3 still decides each one).",
             ""]
    for e in log:
        lines.append(f"- [{e['id']}] {e['title']} — {e['source']} "
                     f"(matched: {e['reason']})")
        lines.append(f"  {e['url']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True,
                    help="articles JSON file (Step 1 output)")
    ap.add_argument("--out", default=None, help="output dir")
    args = ap.parse_args()
    data = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    articles = data["articles"] if isinstance(data, dict) else data
    date = data.get("date", "") if isinstance(data, dict) else ""
    out, log = prefilter_batch(articles)
    outdir = Path(args.out) if args.out else (
        Path(__file__).resolve().parent / "runs" / date)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"prefiltered-{date}.json").write_text(
        json.dumps({"date": date, "articles": out,
                    "deprioritised": len(log)}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    log_path = write_log(log, date, outdir)
    low = sum(1 for a in out if a["priority"] == "low")
    print(f"[step2] {date}: {len(out)} articles, {low} deprioritised "
          f"(log: {log_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
