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
sentence, which is used as its example. Words/phrases are enriched
from rules/enrichment.json FIRST (curated IPA, Bangla phonetic,
synonyms, antonyms, word family, collocations — checked against the
Free Dictionary API and Datamuse), falling back to an earlier
edition's record via load_v1_enrichment().

A headword/phrase used in any earlier edition is never selected
again (load_previous_headwords): the 17 Nov edition repeated
"postpone" from 13 Nov, which the repo validator flagged.

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
ENRICHMENT_PATH = HERE / "rules" / "enrichment.json"
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


def load_enrichment(enrichment_path=ENRICHMENT_PATH):
    """Curated enrichment {"words": {...}, "phrases": {...}}.

    Keys are lowercased headwords/phrases. Word entries carry
    ipa / bangla_phonetic / synonyms / antonyms / word_family /
    collocations (+ provenance); phrase entries carry collocations /
    usage / exam_value (+ provenance). Returns ({}, {}) when the
    file is absent, so the archive fallback still works.
    """
    p = Path(enrichment_path)
    if not p.is_file():
        return {}, {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}, {}
    words = {str(k).strip().lower(): v
             for k, v in (data.get("words", {}) or {}).items()}
    phrases = {str(k).strip().lower(): v
               for k, v in (data.get("phrases", {}) or {}).items()}
    return words, phrases


def load_previous_headwords(date, runs_dir=None,
                            editions_dir=EDITIONS_DIR):
    """Headwords/phrases used by editions strictly before `date`.

    Scans v2 dry-run vocab files (runs/<d>/vocab-<d>.json) and the v1
    editions dir (data-<d>.json). Returns (words, phrases) as sets of
    lowercased headwords. Used to dedupe: a headword never repeats
    across editions (17 Nov repeated "postpone" from 13 Nov).
    """
    words, phrases = set(), set()
    if runs_dir is not None:
        rd = Path(runs_dir)
        if rd.is_dir():
            for f in sorted(rd.glob("*/vocab-*.json")):
                m = re.search(r"vocab-(\d{4}-\d{2}-\d{2})\.json$",
                              f.name)
                if not m or m.group(1) >= date:
                    continue
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                for rec in data.get("words", []) or []:
                    k = str(rec.get("Headword / phrase", "")).strip().lower()
                    if k:
                        words.add(k)
                for rec in data.get("phrases", []) or []:
                    k = str(rec.get("Phrase", "")).strip().lower()
                    if k:
                        phrases.add(k)
    d = Path(editions_dir)
    if d.is_dir():
        for f in sorted(d.glob("data-*.json")):
            m = re.search(r"data-(\d{4}-\d{2}-\d{2})\.json$", f.name)
            if not m or m.group(1) >= date:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for rec in data.get("words", []) or []:
                k = str(rec.get("Headword / phrase", "")).strip().lower()
                if k:
                    words.add(k)
            for rec in data.get("phrases", []) or []:
                k = str(rec.get("Phrase", "")).strip().lower()
                if k:
                    phrases.add(k)
    return words, phrases


def _word_enrichment(w, curated_words, enr_words):
    """Merged enrichment for one word, app field names.

    Curated rules/enrichment.json wins; the v1 archive record fills
    any field the curated entry leaves empty.
    """
    arch = enr_words.get(w.lower(), {}) or {}
    cur = curated_words.get(w.lower(), {}) or {}
    return {
        "IPA": cur.get("ipa") or arch.get("IPA", ""),
        "Bangla phonetic": (cur.get("bangla_phonetic")
                            or arch.get("Bangla phonetic", "")),
        "Synonyms": cur.get("synonyms") or arch.get("Synonyms", ""),
        "Antonyms": cur.get("antonyms") or arch.get("Antonyms", ""),
        "Word family / derivatives": (cur.get("word_family")
                                      or arch.get(
                                          "Word family / derivatives", "")),
        "Collocations / patterns": (cur.get("collocations")
                                    or arch.get(
                                        "Collocations / patterns", "")),
        "BCS / Bank relevance": arch.get("BCS / Bank relevance",
                                         DEFAULT_BCS),
    }


def _phrase_enrichment(p, curated_phrases, enr_phrases):
    """Merged enrichment for one phrase, app field names.

    Curated rules/enrichment.json wins; the v1 archive record fills
    any field the curated entry leaves empty.
    """
    arch = enr_phrases.get(p.lower(), {}) or {}
    cur = curated_phrases.get(p.lower(), {}) or {}
    return {
        "Usage / register": (cur.get("usage")
                             or arch.get("Usage / register", "")
                             or DEFAULT_USAGE),
        "Common collocations / grammar pattern": (
            cur.get("collocations")
            or arch.get("Common collocations / grammar pattern", "")),
        "Exam value": (cur.get("exam_value")
                       or arch.get("Exam value", "")
                       or DEFAULT_EXAM_VALUE),
    }


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


def _find_example(word, word_re, quotes, body):
    """First sentence containing the word: fact quote, else body.

    Prefer a sentence containing the EXACT headword: the app validator
    requires the example to contain the headword as a substring, and
    an inflected form ("factories") does not contain it ("factory").
    Only if no sentence carries the exact form do we fall back to an
    inflected-form sentence — and build_vocab drops the word then,
    because the validator would reject it (2026-11-15).
    """
    exact = word.lower()
    for q in quotes:
        if exact in q.lower():
            return q
    for s in body:
        if exact in s.lower():
            return s
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
    curated_words, curated_phrases = load_enrichment()
    enr_words, enr_phrases = load_v1_enrichment(editions_dir)
    prev_words, prev_phrases = load_previous_headwords(
        date, runs_dir=runs_dir, editions_dir=editions_dir)

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
                ex = _find_example(w, w_re, quotes, body)
                hits.append((it, ex))
        if not hits:
            continue
        # The app validator (and the converter's self-check) requires
        # the example to contain the headword as a substring. The
        # match regex tolerates inflections ("factories" matches
        # "factory"), so the first hit's example may only carry the
        # plural form — keep the first hit whose example contains the
        # exact headword, and drop the word entirely if no hit does
        # (2026-11-15: 'factory'/'company' failed the check on
        # plural-only examples). The next-ranked word fills the slot.
        hits = [(it, ex) for it, ex in hits
                if w.lower() in (ex or "").lower()]
        if not hits:
            continue
        # Rank: in the most articles first, then longer word, then A-Z.
        matched.append((-len(hits), -len(w), w, entry, hits))
    matched.sort(key=lambda t: (t[0], t[1], t[2]))

    # Dedupe: a headword used in any earlier edition never repeats.
    # Filter BEFORE taking the top 20 so the next-ranked words fill
    # the slots (2026-11-18: 17 Nov repeated "postpone" from 13 Nov).
    deduped_words = [t for t in matched if t[2].lower() not in prev_words]

    words = []
    for _neg_n, _neg_l, w, entry, hits in deduped_words[:N_WORDS]:
        it, example = hits[0]
        enr = _word_enrichment(w, curated_words, enr_words)
        words.append({
            "Headword / phrase": w,
            "IPA": enr["IPA"],
            "Bangla phonetic": enr["Bangla phonetic"],
            "Part of speech / type": entry.get("pos", ""),
            "Difficulty": entry.get("diff", ""),
            "Bangla meaning": entry.get("bn", ""),
            "English definition": entry.get("def", ""),
            "Synonyms": enr["Synonyms"],
            "Antonyms": enr["Antonyms"],
            "Word family / derivatives": enr["Word family / derivatives"],
            "Collocations / patterns": enr["Collocations / patterns"],
            "Original example": example,
            "Newspaper context note": it.get("headline", ""),
            "Source publication": it.get("source", ""),
            "Article headline": it.get("headline", ""),
            "Publication date": it.get("date", ""),
            "Direct source URL": it.get("url", ""),
            "BCS / Bank relevance": enr["BCS / Bank relevance"],
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

    # Dedupe phrases the same way as words (see above).
    deduped_phrases = [t for t in matched_ph
                       if t[2].lower() not in prev_phrases]

    phrases = []
    for _neg_n, _neg_l, p, entry, hits in deduped_phrases[:N_PHRASES]:
        it, exs = hits[0]
        enr = _phrase_enrichment(p, curated_phrases, enr_phrases)
        phrases.append({
            "Phrase": p,
            "Type": entry.get("type", ""),
            "Bangla meaning": entry.get("bn", ""),
            "English explanation": entry.get("explanation", ""),
            "Usage / register": enr["Usage / register"],
            "Original example 1": exs[0] if exs else "",
            "Original example 2": exs[1] if len(exs) > 1 else "",
            "Common collocations / grammar pattern":
                enr["Common collocations / grammar pattern"],
            "Source publication": it.get("source", ""),
            "Article headline": it.get("headline", ""),
            "Publication date": it.get("date", ""),
            "Direct source URL": it.get("url", ""),
            "Exam value": enr["Exam value"],
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
             "deduped_words": len(matched) - len(deduped_words),
             "deduped_phrases": len(matched_ph) - len(deduped_phrases),
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
