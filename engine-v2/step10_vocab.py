#!/usr/bin/env python3
"""Step 10 — vocabulary (engine v2).

Deterministic extraction from the kept articles' fact lists.
NO LLM, no paid APIs, stdlib only.

Method
------
A curated, editable word/phrase bank lives in rules/vocab_bank.json
(each entry carries a Bengali meaning and an English definition).
Step 10 selects from the bank ONLY the words/phrases that occur
verbatim in a kept article (fact quote first, else a sentence of the
article body). Every selected item therefore traces to an article
sentence, which is used as its example. Words/phrases that already
appeared in a v1 edition are enriched with that edition's IPA,
phonetics, synonyms, antonyms and collocations.

Revision words come from the previous editions' word lists: the most
recent v2 dry-run vocab file if one exists, else the v1 editions dir.
The first 5 words not already in today's 20 are copied verbatim.

Output matches the v1 app contract exactly (see
editions/data-2026-11-14.json): 20 words + 10 phrases + 5 revision
words, with the same field names the app reads.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK_PATH = HERE / "rules" / "vocab_bank.json"
EDITIONS_DIR = HERE.parent / "editions"

N_WORDS = 20
N_PHRASES = 10
N_REVISION = 5

DEFAULT_BCS = ("BCS/Bank English vocabulary — common in newspaper "
               "reporting and exam passages.")
DEFAULT_USAGE = "News and formal writing"
DEFAULT_EXAM_VALUE = ("Common in BCS/Bank English and newspaper "
                      "vocabulary.")

WORD_KEYS = ["Headword / phrase", "IPA", "Bangla phonetic",
             "Part of speech / type", "Difficulty", "Bangla meaning",
             "English definition", "Synonyms", "Antonyms",
             "Word family / derivatives", "Collocations / patterns",
             "Original example", "Newspaper context note",
             "Source publication", "Article headline",
             "Publication date", "Direct source URL",
             "BCS / Bank relevance", "Priority"]
PHRASE_KEYS = ["Phrase", "Type", "Bangla meaning",
               "English explanation", "Usage / register",
               "Original example 1", "Original example 2",
               "Common collocations / grammar pattern",
               "Source publication", "Article headline",
               "Publication date", "Direct source URL", "Exam value"]


def load_bank(bank_path=BANK_PATH):
    """Return the vocab bank {"words": [...], "phrases": [...]}."""
    return json.loads(Path(bank_path).read_text(encoding="utf-8"))


def load_v1_enrichment(editions_dir=EDITIONS_DIR):
    """Map headword/phrase (lowercased) -> full v1 record, newest first.

    Used to fill IPA, phonetics, synonyms, antonyms, word family and
    collocations for words/phrases that appeared in an earlier edition.
    """
    words, phrases = {}, {}
    d = Path(editions_dir)
    if not d.is_dir():
        return words, phrases
    for f in sorted(d.glob("data-*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for rec in data.get("words", []) or []:
            k = str(rec.get("Headword / phrase", "")).strip().lower()
            if k and k not in words:
                words[k] = rec
        for rec in data.get("phrases", []) or []:
            k = str(rec.get("Phrase", "")).strip().lower()
            if k and k not in phrases:
                phrases[k] = rec
    return words, phrases


def load_previous_words(date, runs_dir=None, editions_dir=EDITIONS_DIR):
    """Previous editions' word lists, newest edition first.

    Prefers v2 dry-run vocab files (runs/<date>/vocab-<date>.json),
    falls back to the v1 editions dir (data-<date>.json). Returns a
    flat list of v1-shaped word records, deduped by headword, newest
    occurrence kept. Only editions dated before `date` are used.
    """
    out, seen = [], set()
    # v2 dry-run vocab files first.
    if runs_dir is not None:
        rd = Path(runs_dir)
        if rd.is_dir():
            for f in sorted(rd.glob("*/vocab-*.json"), reverse=True):
                m = re.search(r"vocab-(\d{4}-\d{2}-\d{2})\.json$", f.name)
                if not m or m.group(1) >= date:
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                for rec in data.get("words", []) or []:
                    k = str(rec.get("Headword / phrase", "")).strip().lower()
                    if k and k not in seen:
                        seen.add(k)
                        out.append(rec)
                if out:
                    return out
    # v1 editions dir.
    d = Path(editions_dir)
    if d.is_dir():
        for f in sorted(d.glob("data-*.json"), reverse=True):
            m = re.search(r"data-(\d{4}-\d{2}-\d{2})\.json$", f.name)
            if not m or m.group(1) >= date:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for rec in data.get("words", []) or []:
                k = str(rec.get("Headword / phrase", "")).strip().lower()
                if k and k not in seen:
                    seen.add(k)
                    out.append(rec)
            if out:
                return out
    return out


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text):
    """Split article text into sentences (kept verbatim)."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def _item_text(item):
    """(search_text, quote_sentences, body_sentences) for one item.

    quote_sentences are the Step 5 fact quotes (preferred for
    examples); body_sentences are the article body split up.
    """
    quotes = []
    for f in item.get("facts", []) or []:
        q = (f.get("quote") or "").strip()
        if q:
            quotes.append(q)
    body = _sentences(item.get("body_text", ""))
    search = " ".join([item.get("headline", "")] + quotes + body)
    return search, quotes, body


def _word_re(word, pos=""):
    """Match a bank word with its ordinary inflections.

    News text rarely uses the base form: verbs appear as announced /
    announcing, nouns as ministers / policies. The headword shown to
    the learner stays the base form; the match tolerates the regular
    inflections only (irregular forms such as sought / children are
    simply not matched).
    """
    w = word.lower()
    if pos == "Verb":
        if w.endswith("e"):
            return re.compile(r"\b" + re.escape(w[:-1])
                              + r"(?:e|ed|es|ing)\b", re.IGNORECASE)
        if len(w) > 1 and w[-1] == "y" and w[-2] not in "aeiou":
            return re.compile(r"\b" + re.escape(w[:-1])
                              + r"(?:y|ies|ied|ying)\b", re.IGNORECASE)
        return re.compile(r"\b" + re.escape(w)
                          + r"(?:s|d|ed|ing)?\b", re.IGNORECASE)
    if pos == "Noun":
        if len(w) > 1 and w[-1] == "y" and w[-2] not in "aeiou":
            return re.compile(r"\b" + re.escape(w[:-1])
                              + r"(?:y|ies)\b", re.IGNORECASE)
        if w.endswith(("s", "x", "ch", "sh")):
            return re.compile(r"\b" + re.escape(w) + r"(?:es)?\b",
                              re.IGNORECASE)
        return re.compile(r"\b" + re.escape(w) + r"s?\b", re.IGNORECASE)
    return re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)


def _phrase_re(phrase):
    """Match a bank phrase, tolerating a plural on its last word."""
    return re.compile(r"\b" + re.escape(phrase.lower()) + r"s?\b",
                      re.IGNORECASE)


def _find_example(word_re, quotes, body):
    """First sentence containing the word: fact quote, else body."""
    for q in quotes:
        if word_re.search(q):
            return q
    for s in body:
        if word_re.search(s):
            return s
    return ""


def _find_examples(phrase_re, quotes, body, n=2):
    """Up to n distinct sentences containing the phrase, quotes first."""
    found = []
    for q in quotes + body:
        if phrase_re.search(q) and q not in found:
            found.append(q)
            if len(found) == n:
                break
    return found


def build_vocab(items, date, runs_dir=None, editions_dir=EDITIONS_DIR,
                bank=None, previous_words=None):
    """Build the vocabulary lists from kept (final) items.

    items: Step 5/6 final_items — each with facts[{quote}], body_text,
    headline, source, url, date. Returns {"date", "words", "phrases",
    "revision_words", "stats"} in the v1 app contract shape.
    """
    bank = bank or load_bank()
    enr_words, enr_phrases = load_v1_enrichment(editions_dir)

    # Per-item text, computed once.
    per_item = []
    for it in items:
        search, quotes, body = _item_text(it)
        per_item.append((it, search, quotes, body))

    # ---- words -------------------------------------------------------
    matched = []
    for entry in bank.get("words", []):
        w = entry["w"]
        w_re = _word_re(w, entry.get("pos", ""))
        hits = []  # (item, example sentence)
        for it, search, quotes, body in per_item:
            if w_re.search(search):
                ex = _find_example(w_re, quotes, body)
                hits.append((it, ex))
        if not hits:
            continue
        # Rank: in the most articles first, then longer word, then A-Z.
        matched.append((-len(hits), -len(w), w, entry, hits))
    matched.sort(key=lambda t: (t[0], t[1], t[2]))

    words = []
    for _neg_n, _neg_l, w, entry, hits in matched[:N_WORDS]:
        it, example = hits[0]
        enr = enr_words.get(w.lower(), {})
        words.append({
            "Headword / phrase": w,
            "IPA": enr.get("IPA", ""),
            "Bangla phonetic": enr.get("Bangla phonetic", ""),
            "Part of speech / type": entry.get("pos", ""),
            "Difficulty": entry.get("diff", ""),
            "Bangla meaning": entry.get("bn", ""),
            "English definition": entry.get("def", ""),
            "Synonyms": enr.get("Synonyms", ""),
            "Antonyms": enr.get("Antonyms", ""),
            "Word family / derivatives": enr.get(
                "Word family / derivatives", ""),
            "Collocations / patterns": enr.get(
                "Collocations / patterns", ""),
            "Original example": example,
            "Newspaper context note": it.get("headline", ""),
            "Source publication": it.get("source", ""),
            "Article headline": it.get("headline", ""),
            "Publication date": it.get("date", ""),
            "Direct source URL": it.get("url", ""),
            "BCS / Bank relevance": enr.get("BCS / Bank relevance",
                                            DEFAULT_BCS),
            "Priority": "High" if len(hits) >= 2 else "Medium",
        })

    # ---- phrases -----------------------------------------------------
    matched_ph = []
    for entry in bank.get("phrases", []):
        p = entry["p"]
        p_re = _phrase_re(p)
        hits = []  # (item, [example sentences])
        for it, search, quotes, body in per_item:
            if p_re.search(search):
                exs = _find_examples(p_re, quotes, body, n=2)
                hits.append((it, exs))
        if not hits:
            continue
        matched_ph.append((-len(hits), -len(p), p, entry, hits))
    matched_ph.sort(key=lambda t: (t[0], t[1], t[2]))

    phrases = []
    for _neg_n, _neg_l, p, entry, hits in matched_ph[:N_PHRASES]:
        it, exs = hits[0]
        enr = enr_phrases.get(p.lower(), {})
        phrases.append({
            "Phrase": p,
            "Type": entry.get("type", ""),
            "Bangla meaning": entry.get("bn", ""),
            "English explanation": entry.get("explanation", ""),
            "Usage / register": enr.get("Usage / register",
                                        DEFAULT_USAGE),
            "Original example 1": exs[0] if exs else "",
            "Original example 2": exs[1] if len(exs) > 1 else "",
            "Common collocations / grammar pattern": enr.get(
                "Common collocations / grammar pattern", ""),
            "Source publication": it.get("source", ""),
            "Article headline": it.get("headline", ""),
            "Publication date": it.get("date", ""),
            "Direct source URL": it.get("url", ""),
            "Exam value": enr.get("Exam value", DEFAULT_EXAM_VALUE),
        })

    # ---- revision ----------------------------------------------------
    if previous_words is None:
        previous_words = load_previous_words(date, runs_dir=runs_dir,
                                            editions_dir=editions_dir)
    today = {w["Headword / phrase"].lower() for w in words}
    revision = []
    for rec in previous_words:
        k = str(rec.get("Headword / phrase", "")).strip().lower()
        if not k or k in today:
            continue
        if k in {r["Headword / phrase"].lower() for r in revision}:
            continue
        revision.append({k2: rec.get(k2, "") for k2 in WORD_KEYS})
        if len(revision) == N_REVISION:
            break

    stats = {"bank_words": len(bank.get("words", [])),
             "bank_phrases": len(bank.get("phrases", [])),
             "matched_words": len(matched),
             "matched_phrases": len(matched_ph),
             "words": len(words),
             "phrases": len(phrases),
             "revision_words": len(revision),
             "short_words": len(words) < N_WORDS,
             "short_phrases": len(phrases) < N_PHRASES,
             "short_revision": len(revision) < N_REVISION}
    return {"date": date, "words": words, "phrases": phrases,
            "revision_words": revision, "stats": stats}


if __name__ == "__main__":
    # Quick manual check: python3 step10_vocab.py runs/2026-11-14
    print("bank: %s" % load_bank())
    sys.exit(0)
