#!/usr/bin/env python3
"""Step 5 — Check by code (engine v2).

Deterministic, stdlib-only. No LLM, no v1 imports.

check(item, article_text) -> check result per CONTRACTS.md::

    {"item_id": ..., "ok": bool,
     "failures": [{"fact": ..., "check": "quote|number|name", "detail": ...}],
     "action": "keep|drop_fact|verify|drop", "facts_kept": N}

Implements exactly:
  (a) every quote appears verbatim inside the article text (compared
      after Bangla normalisation — NFC, Bangla digits -> English,
      zero-width removed — the SAME norm_bangla() as Step 4, imported
      from step4_facts so the two can never drift apart);
  (b) every number in the fact (value / what / unit, after mapping
      Bangla digits to English and removing commas) appears in the
      article. The fact's ``date`` field is NOT number-checked: it may
      legitimately be the article's date line, which need not appear
      in the body text;
  (c) every proper name in the fact appears in the article. Proper
      names = capitalised tokens in English text, and the Bangla name
      tokens the fact carries. Candidates are taken from the fact's
      what/value AND from its quote (never from thin air) and checked
      against the article text.

Any failure: that fact is dropped. A failure that cannot be attributed
to a single fact (e.g. a number in an item-level summary line) marks
the item "যাচাই করুন" (action "verify"). If fewer than 2 facts remain,
the item is dropped (action "drop").

The optional "new chat" claim check is MANUAL-ONLY and is not part of
this module.
"""
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from step4_facts import norm_bangla
except Exception:  # pragma: no cover - fallback, identical definition
    import unicodedata
    _BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

    def norm_bangla(text):
        if not text:
            return ""
        text = unicodedata.normalize("NFC", str(text))
        text = text.translate(_BN_TO_EN)
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# (a) quotes — also exposed standalone so Step 8 can reuse the exact
# same check (it looks for a `quote_in_text(quote, text)` function).
# ---------------------------------------------------------------------------
def quote_in_text(quote, text):
    """Step 5(a): is this quote verbatim inside the article text?"""
    q, t = norm_bangla(quote), norm_bangla(text)
    return bool(q) and q in t


# ---------------------------------------------------------------------------
# (b) numbers
# ---------------------------------------------------------------------------
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def numbers_in(text):
    """Numbers in text after digit normalisation, commas removed."""
    if not text:
        return set()
    return set(_NUM_RE.findall(norm_bangla(text).replace(",", "")))


def article_numbers(article_text):
    return numbers_in(article_text)


# ---------------------------------------------------------------------------
# (c) proper names
# ---------------------------------------------------------------------------
# Words that may be capitalised without being names.
_CAP_STOP = {
    "the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "but",
    "with", "from", "by", "as", "it", "its", "this", "that", "these",
    "those", "is", "are", "was", "were", "has", "have", "had", "will",
    "would", "can", "could", "after", "before", "during", "between",
    "over", "under", "new", "more", "most", "first", "last", "one",
    "two", "also", "not", "no", "per", "i",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept",
    "oct", "nov", "dec",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
}
# Common Bangla words that are not names (stoplist for name extraction).
_BN_STOP = {
    "এবং", "বা", "যে", "যা", "এই", "ওই", "সেই", "তার", "তাদের", "এর",
    "থেকে", "সঙ্গে", "জন্য", "করে", "করা", "হয়", "হয়েছে", "হবে",
    "ছিল", "আছে", "নেই", "বলে", "বলেন", "অনুযায়ী", "পর", "আগে",
    "মধ্যে", "উপর", "নতুন", "বড়", "প্রথম", "দ্বিতীয়", "বছর", "মাস",
    "দিন", "টাকা", "কোটি", "লাখ", "হাজার", "শতাংশ", "হার", "বাজেট",
    "আইন", "সরকার", "মন্ত্রণালয়", "মন্ত্রী", "প্রধানমন্ত্রী",
    "রাষ্ট্রপতি", "সচিব", "আদালত", "ব্যাংক", "অর্থনীতি", "দেশ",
    "জাতীয়", "আন্তর্জাতিক", "সিদ্ধান্ত", "ঘোষণা", "প্রস্তাব",
    "বৈঠক", "সভা", "কমিটি", "কমিশন", "সংসদ", "সংবিধান",
}
_BN_UNIT_WORDS = {"টাকা", "কোটি", "লাখ", "হাজার", "শতাংশ", "ডলার"}

_CAP_SEQ = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
_BN_WORD = re.compile(r"[\u0980-\u09FF]+")
# Bangla name after a title/honorific in the quote.
_BN_TITLE = re.compile(
    r"(?:প্রধানমন্ত্রী|মন্ত্রী|সচিব|চেয়ারম্যান|গভর্নর|অধ্যাপক|ড\.|মো\.|"
    r"রাষ্ট্রপতি|উপদেষ্টা)\s+([\u0980-\u09FF]+(?:\s+[\u0980-\u09FF]+)?)")


def english_names(text):
    """Capitalised English words/phrases, excluding sentence starts,
    months, weekdays and other non-name capitals."""
    out = set()
    if not text:
        return out
    for m in _CAP_SEQ.finditer(text):
        phrase = m.group(0)
        # Skip a capitalised word that only opens the sentence.
        start = m.start()
        before = text[:start].rstrip()
        if not before or before[-1] in ".!?।":
            # Sentence-initial: keep only multi-word phrases (a real
            # name rarely stands alone as the first word).
            if " " not in phrase:
                continue
        for word in phrase.split():
            if word.lower() in _CAP_STOP or len(word) < 3:
                continue
            out.add(word)
        if " " in phrase:
            out.add(phrase)
    return out


def bangla_names(fact):
    """Bangla name tokens the fact carries.

    From what/value: Bangla tokens that are not common words, units or
    dates. From the quote: tokens following a title/honorific. A token
    taken from the quote is by construction in the article; the check
    bites on names invented in what/value.
    """
    out = set()
    for field in ("what", "value"):
        for tok in _BN_WORD.findall(fact.get(field) or ""):
            if (tok not in _BN_STOP and tok not in _BN_UNIT_WORDS
                    and len(tok) >= 2):
                out.add(tok)
    for m in _BN_TITLE.finditer(fact.get("quote") or ""):
        for tok in m.group(1).split():
            if tok not in _BN_STOP:
                out.add(tok)
    return out


def proper_names(fact):
    """All proper-name candidates for one fact (English + Bangla)."""
    names = english_names((fact.get("what") or "") + " "
                          + (fact.get("value") or ""))
    names |= english_names(fact.get("quote") or "")
    names |= bangla_names(fact)
    return names


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------
def _check_fact(fact, norm_article, art_numbers):
    """Failures for one fact: list of {"fact","check","detail"}."""
    failures = []
    label = (fact.get("what") or fact.get("quote") or "?")[:80]
    quote = fact.get("quote") or ""
    if not quote:
        failures.append({"fact": label, "check": "quote",
                         "detail": "fact has no supporting quote"})
    elif norm_bangla(quote) not in norm_article:
        failures.append({"fact": label, "check": "quote",
                         "detail": "quote not found verbatim in article"})
    # (b) numbers in what/value/unit (date field excluded — see docstring)
    for num in sorted(numbers_in((fact.get("what") or "") + " "
                                 + (fact.get("value") or "") + " "
                                 + (fact.get("unit") or ""))):
        if num not in art_numbers:
            failures.append({"fact": label, "check": "number",
                             "detail": "number %s not in article" % num})
    # (c) proper names
    for name in sorted(proper_names(fact)):
        if norm_bangla(name) not in norm_article:
            failures.append({"fact": label, "check": "name",
                             "detail": "name %r not in article" % name})
    return failures


def check(item, article_text):
    """Check one item ({"id"/"item_id", "facts": [...]}) against the
    article text. Returns the CONTRACTS.md check result."""
    item_id = (item or {}).get("id") or (item or {}).get("item_id") or ""
    facts = list((item or {}).get("facts") or [])
    norm_article = norm_bangla(article_text or "")
    art_numbers = article_numbers(article_text or "")

    failures = []
    kept = []
    for fact in facts:
        fact_failures = _check_fact(fact, norm_article, art_numbers)
        if fact_failures:
            failures.extend(fact_failures)
        else:
            kept.append(fact)

    # Item-level numbers (summary lines that belong to no single fact):
    # a failure here cannot be dropped cleanly -> "যাচাই করুন".
    verify = False
    for field in ("summary_lines", "bangla_lines", "summary"):
        lines = (item or {}).get(field)
        if isinstance(lines, str):
            lines = [lines]
        if not lines:
            continue
        for line in lines:
            for num in sorted(numbers_in(line)):
                if num not in art_numbers:
                    verify = True
                    failures.append({
                        "fact": "(item-level %s)" % field,
                        "check": "number",
                        "detail": "number %s in %s not in article" % (num, field),
                    })

    facts_kept = len(kept)
    if facts_kept < 2:
        action = "drop"
    elif verify:
        action = "verify"
    elif failures:
        action = "drop_fact"
    else:
        action = "keep"
    return {
        "item_id": item_id,
        "ok": not failures,
        "failures": failures,
        "action": action,
        "facts_kept": facts_kept,
    }


def _article_text_for(article):
    """Accept a plain string, an article dict, or None."""
    if article is None:
        return ""
    if isinstance(article, str):
        return article
    if isinstance(article, dict):
        return article.get("body_text") or article.get("text") or ""
    return ""


def check_batch(items, articles):
    """Check many items. ``articles`` may be:
    - {id: text} or {id: article-dict}, or
    - a list of article dicts (matched by "id").
    Returns a list of check results in item order."""
    if isinstance(articles, list):
        lookup = {a.get("id"): a for a in articles
                  if isinstance(a, dict) and a.get("id")}
    elif isinstance(articles, dict):
        lookup = articles
    else:
        lookup = {}
    results = []
    for item in items or []:
        item_id = (item or {}).get("id") or (item or {}).get("item_id") or ""
        if item_id in lookup:
            text = _article_text_for(lookup[item_id])
            results.append(check(item, text))
        else:
            results.append({
                "item_id": item_id,
                "ok": False,
                "failures": [{"fact": "", "check": "quote",
                              "detail": "article text not supplied for item"}],
                "action": "verify",
                "facts_kept": len((item or {}).get("facts") or []),
            })
    return results


if __name__ == "__main__":
    import json
    article = (
        "The International Monetary Fund board has approved a $442 million "
        "tranche for Bangladesh under its loan programme. The approval came "
        "on 13 November 2026 after a review of the country's economic "
        "reforms. Bangladesh's foreign exchange reserves stood at "
        "$26 billion in October 2026."
    )
    good = {"id": "a001", "facts": [{
        "what": "IMF board approves tranche for Bangladesh",
        "value": "442", "unit": "million",
        "date": "2026-11-13", "status": "happened",
        "quote": "The International Monetary Fund board has approved a "
                 "$442 million tranche for Bangladesh under its loan programme."}]}
    bad = {"id": "a001", "facts": [{
        "what": "IMF board approves tranche for Bangladesh",
        "value": "445", "unit": "million",
        "date": "2026-11-13", "status": "happened",
        "quote": "The International Monetary Fund board has approved a "
                 "$442 million tranche for Bangladesh under its loan programme."}]}
    print(json.dumps(check(good, article), ensure_ascii=False, indent=2))
    print(json.dumps(check(bad, article), ensure_ascii=False, indent=2))
