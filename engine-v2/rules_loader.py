#!/usr/bin/env python3
"""Parse engine-v2/rules/RULES.md into structured data.

RULES.md is the canonical, human-editable rules file. This parser is
deliberately forgiving about whitespace but strict about headings:
topic blocks start with "### TOPIC <ID>", glossary lines are
"<bangla> = <english>" under "## GLOSSARY", the section order and
mapping live under "## STEP 7". If a section is missing, the parser
returns empty data for it (never raises) so a half-edited RULES.md
degrades instead of crashing a run.
"""
import re
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "rules" / "RULES.md"
APP_MIRROR = (Path(__file__).resolve().parent.parent / "app" / "assets"
              / "engine-rules" / "rules.md")


def _read_rules(path=None):
    p = Path(path) if path else RULES_PATH
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _section(text, heading):
    """Text under a '## <heading...>' block (up to the next '## ' heading).
    Matches the heading as a prefix so '## GLOSSARY (fixed terms ...)'
    still matches 'GLOSSARY'."""
    m = re.search(r"^## " + re.escape(heading) + r"[^\n]*$",
                  text, re.M)
    if not m:
        return ""
    start = m.end()
    m2 = re.search(r"^## ", text[start:], re.M)
    end = start + m2.start() if m2 else len(text)
    return text[start:end]


def parse_topics(text=None):
    """Return {topic_id: {"what": str, "not": str,
    "strong": [terms], "support": [terms]}} preserving file order."""
    text = text if text is not None else _read_rules()
    topics = {}
    for m in re.finditer(r"^### TOPIC (\S+)\s*$", text, re.M):
        tid = m.group(1)
        start = m.end()
        m2 = re.search(r"^#{2,3} ", text[start:], re.M)
        end = start + m2.start() if m2 else len(text)
        block = text[start:end]
        what = ""
        not_this = ""
        wm = re.search(r"What counts:\s*(.*?)(?:\nNOT this:|\nStrong:|\Z)",
                       block, re.S)
        if wm:
            what = " ".join(wm.group(1).split())
        nm = re.search(r"NOT this:\s*(.*?)(?:\nStrong:|\Z)", block, re.S)
        if nm:
            not_this = " ".join(nm.group(1).split())

        def _terms(kind):
            # Strong: runs until Support: (or end of block); Support:
            # runs to end of block. Entries wrap across lines, so join
            # lines with a space and split on commas.
            if kind == "Strong":
                mm = re.search(r"^Strong:\s*(.*?)(?=^Support:|\Z)", block,
                               re.M | re.S)
            else:
                mm = re.search(r"^Support:\s*(.*)", block, re.M | re.S)
            if not mm:
                return []
            raw = mm.group(1).replace("\n", " ")
            return [t.strip().lower() for t in raw.split(",")
                    if t.strip()]
        topics[tid] = {"what": what, "not": not_this,
                       "strong": _terms("Strong"),
                       "support": _terms("Support")}
    return topics


def parse_let_through_keywords(text=None):
    """The 10 always-let-through keywords (Step 2)."""
    text = text if text is not None else _read_rules()
    sec = _section(text, "STEP 2 — PRE-FILTER")
    m = re.search(r"these 10 keywords[^:]*:\s*(.*?)(?:\.\s*\n|\n\n|\Z)", sec, re.S)
    if not m:
        return []
    raw = m.group(1).replace("\n", " ")
    return [t.strip().rstrip(".") for t in raw.split(",") if t.strip()]


def parse_deprioritise_terms(text=None):
    """Crime/accident/entertainment terms (Step 2)."""
    text = text if text is not None else _read_rules()
    sec = _section(text, "STEP 2 — PRE-FILTER")
    m = re.search(r"Deprioritise terms[^:]*:\n(.*?)(?:\n\n|\Z)", sec, re.S)
    if not m:
        return []
    return [t.strip().lower() for t in m.group(1).replace("\n", ",").split(",")
            if t.strip()]


def parse_glossary(text=None):
    """{bangla_term: english} from the GLOSSARY section.

    RULES.md packs several "bangla = english;" pairs on one line, so
    split each line on ";" first, then on "=" per pair.
    """
    text = text if text is not None else _read_rules()
    sec = _section(text, "GLOSSARY")
    out = {}
    for line in sec.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for chunk in line.split(";"):
            chunk = chunk.strip()
            if "=" not in chunk:
                continue
            bangla, eng = chunk.split("=", 1)
            bangla = bangla.strip()
            eng = eng.strip()
            if bangla and eng:
                out[bangla] = eng
    return out


def parse_section_order(text=None):
    """Daily-page sections in order (Step 7)."""
    text = text if text is not None else _read_rules()
    sec = _section(text, "STEP 7 — DAILY PAGE")
    m = re.search(r"Sections in order:\s*(.*?)(?:\n3\.|\Z)", sec, re.S)
    if not m:
        return []
    raw = m.group(1).replace("\n", " ")
    parts = [p.strip() for p in raw.split("→")]
    out = []
    for p in parts:
        # The last part carries a trailing sentence ("Skip empty ones.")
        p = p.split(". ")[0].rstrip(".").strip()
        if p:
            out.append(p)
    return out


def parse_section_mapping(text=None):
    """{topic_id: section_name} from the Step 7 mapping."""
    text = text if text is not None else _read_rules()
    sec = _section(text, "STEP 7 — DAILY PAGE")
    out = {}
    for line in sec.splitlines():
        m = re.match(r"^([A-Z\-]+(?:,\s*[A-Z\-]+)*)\s*→\s*(.+)$", line.strip())
        if m:
            for tid in m.group(1).split(","):
                out[tid.strip()] = m.group(2).strip()
    return out


def load_rules(path=None):
    """Everything the engine needs from RULES.md, in one dict."""
    text = _read_rules(path)
    return {
        "topics": parse_topics(text),
        "topic_order": list(parse_topics(text).keys()),
        "let_through": parse_let_through_keywords(text),
        "deprioritise": parse_deprioritise_terms(text),
        "glossary": parse_glossary(text),
        "section_order": parse_section_order(text),
        "section_mapping": parse_section_mapping(text),
        "raw": text,
    }


if __name__ == "__main__":
    import json
    r = load_rules()
    print(f"topics: {list(r['topics'])}")
    for tid, t in r["topics"].items():
        print(f"  {tid}: {len(t['strong'])} strong, "
              f"{len(t['support'])} support")
    print(f"let-through keywords: {r['let_through']}")
    print(f"deprioritise terms: {len(r['deprioritise'])}")
    print(f"glossary entries: {len(r['glossary'])}")
    print(f"sections: {r['section_order']}")
    print(f"mapping: {r['section_mapping']}")
