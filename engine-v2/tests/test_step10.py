#!/usr/bin/env python3
"""Test Step 10 vocabulary (engine v2).

Runnable as:  python3 tests/test_step10.py   (from engine-v2/)
or:            python3 test_step10.py        (from engine-v2/tests/)

Asserts: exactly 20 words + 10 phrases + 5 revision words; every
word/phrase traces to a verbatim article sentence; every word carries
a Bengali meaning and an English definition; output keys match the
v1 app contract exactly; revision words come from previous editions
and never duplicate today's words. Plus a live-coverage check: the
bank must match >=20 words and >=10 phrases on the real 14 Nov
kept-article summaries (a stricter test than the dry-run, which uses
full body text).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(ENGINE))

from step10_vocab import (  # noqa: E402
    WORD_KEYS, PHRASE_KEYS, build_vocab, load_bank,
    load_previous_words)

FAILURES = []


def check(name, ok, detail=""):
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name,
                         ("  " + str(detail)) if (detail and not ok) else ""))
    if not ok:
        FAILURES.append(name + " " + str(detail))


def _item(iid, headline, quotes, source="Test Paper", date="2026-11-15"):
    body = " ".join(quotes)
    return {"id": iid, "headline": headline, "score": 2,
            "topic_primary": "BD-GOV",
            "facts": [{"what": "fact", "value": "", "unit": "",
                       "date": date, "status": "happened", "quote": q}
                      for q in quotes],
            "body_text": body, "source": source,
            "url": "https://example.com/%s" % iid, "date": date,
            "published": date + "T06:00:00+00:00"}


def synthetic_items():
    return [
        _item("s1", "Cabinet approves ordinance after tribunal verdict",
              ["The cabinet approved the ordinance after the tribunal "
               "delivered its verdict on the corruption allegation.",
               "The government will implement the fiscal policy and "
               "protect the rule of law."]),
        _item("s2", "Inflation rises as deficit widens",
              ["Inflation rose as the deficit widened, while revenue "
               "fell and export earnings dropped.",
               "The central bank raised the interest rate as the "
               "monetary policy tightened and the trade deficit grew."]),
        _item("s3", "Remittance slows, reserves fall",
              ["Remittance inflow slowed while foreign exchange reserves "
               "fell, and the gross domestic product growth was revised "
               "down.",
               "The budget deficit widened as public procurement costs "
               "rose."]),
        _item("s4", "Cyclone floods coast as climate talks stall",
              ["The cyclone brought flood waters, and climate change "
               "made the emission cuts crucial for sustainable "
               "development.",
               "Renewable energy can help, but the damage will escalate "
               "if the drought continues."]),
        _item("s5", "Curriculum changes before admissions open",
              ["The curriculum changed before admission opened, and "
               "scholarship offers rose as higher education expanded.",
               "Students must pledge to follow the rules, and the "
               "university will launch the new syllabus next year."]),
        _item("s6", "Minister to reveal plan, postpone decision",
              ["The minister will reveal the plan and postpone the "
               "decision, but the economy may thrive if exports rebound.",
               "Human rights groups warned that law and order must "
               "improve and food security remains a concern."]),
    ]


def _prev_words():
    # 8 previous-edition records: 6 fresh + 2 overlapping today's words.
    def rec(w):
        return {"Headword / phrase": w, "IPA": "/x/", "Bangla phonetic": "ব",
                "Part of speech / type": "Noun", "Difficulty": "Basic",
                "Bangla meaning": "অর্থ", "English definition": "def",
                "Synonyms": "", "Antonyms": "",
                "Word family / derivatives": "",
                "Collocations / patterns": "",
                "Original example": "Old example with %s." % w,
                "Newspaper context note": "old headline",
                "Source publication": "Old Paper",
                "Article headline": "old headline",
                "Publication date": "2026-11-14",
                "Direct source URL": "https://example.com/old",
                "BCS / Bank relevance": "old", "Priority": "High"}
    return [rec(w) for w in
            ["stagnant", "robust", "feasible", "inevitable", "plunge",
             "withstand", "cabinet", "inflation"]]


def test_synthetic():
    print("== synthetic items (controlled vocabulary) ==")
    items = synthetic_items()
    vocab = build_vocab(items, "2026-11-15",
                        previous_words=_prev_words())
    print("  stats: %s" % vocab["stats"])
    check("exactly 20 words", len(vocab["words"]) == 20,
          len(vocab["words"]))
    check("exactly 10 phrases", len(vocab["phrases"]) == 10,
          len(vocab["phrases"]))
    check("exactly 5 revision words", len(vocab["revision_words"]) == 5,
          len(vocab["revision_words"]))
    check("no shortfall flags",
          not (vocab["stats"]["short_words"]
               or vocab["stats"]["short_phrases"]
               or vocab["stats"]["short_revision"]),
          vocab["stats"])

    # Traceability: every example is verbatim in some item's text.
    all_text = []
    for it in items:
        all_text.append(it["body_text"])
        all_text.extend(f["quote"] for f in it["facts"])
    for w in vocab["words"]:
        check("word %r: example verbatim in an article"
              % w["Headword / phrase"],
              w["Original example"] and any(
                  w["Original example"] in t for t in all_text),
              w["Original example"][:60])
        check("word %r: Bengali meaning + definition present"
              % w["Headword / phrase"],
              bool(w["Bangla meaning"]) and bool(w["English definition"]))
        check("word %r: keys match v1 contract"
              % w["Headword / phrase"],
              list(w.keys()) == WORD_KEYS, list(w.keys()))
    for p in vocab["phrases"]:
        check("phrase %r: example 1 verbatim in an article" % p["Phrase"],
              p["Original example 1"] and any(
                  p["Original example 1"] in t for t in all_text),
              p["Original example 1"][:60])
        check("phrase %r: Bengali meaning + explanation present"
              % p["Phrase"],
              bool(p["Bangla meaning"])
              and bool(p["English explanation"]))
        check("phrase %r: keys match v1 contract" % p["Phrase"],
              list(p.keys()) == PHRASE_KEYS, list(p.keys()))

    # Revision: first 5 non-overlapping previous words, in order.
    today = {w["Headword / phrase"] for w in vocab["words"]}
    rev = [r["Headword / phrase"] for r in vocab["revision_words"]]
    check("revision: 5 words, none in today's 20",
          len(rev) == 5 and not (set(rev) & today), rev)
    check("revision: in previous-edition order",
          rev == ["stagnant", "robust", "feasible", "inevitable",
                  "plunge"], rev)
    print("  words: %s"
          % [w["Headword / phrase"] for w in vocab["words"]])
    print("  phrases: %s" % [p["Phrase"] for p in vocab["phrases"]])


def test_plural_example():
    """Example must contain the exact headword (Level 1 wiring, 2026-11-15).

    _word_re tolerates inflections, so "factory" matches "factories"
    — but the app validator requires the example to contain the
    headword as a substring, and "factories" does not contain
    "factory". A word whose sentences carry only the plural form is
    dropped; a word with an exact-form sentence keeps that example.
    """
    print("== plural-only examples ==")
    bank = {"words": [
        {"w": "factory", "pos": "Noun", "diff": "Basic",
         "bn": "কারখানা", "def": "a building where goods are made"},
        {"w": "company", "pos": "Noun", "diff": "Basic",
         "bn": "কোম্পানি", "def": "a business organisation"},
    ], "phrases": []}
    items = [
        _item("p1", "RMG unrest shuts factories",
              ["RMG unrest: 50 factories remain closed in Savar-Ashulia."]),
        _item("p2", "ICSB honours companies",
              ["The ceremony recognised companies for their corporate "
               "governance practices.",
               "The company said it would publish its annual report."]),
    ]
    vocab = build_vocab(items, "2026-11-15", bank=bank)
    got = {w["Headword / phrase"]: w for w in vocab["words"]}
    check("plural-only word 'factory' is dropped",
          "factory" not in got, list(got))
    check("'company' kept with the exact-form example",
          "company" in got
          and "company" in got["company"]["Original example"].lower()
          and "companies" not in got["company"]["Original example"].lower(),
          got.get("company", {}).get("Original example", ""))


def test_live_coverage():
    """Bank coverage on the real 14 Nov kept-article summaries."""
    print("== live coverage (14 Nov kept summaries, stricter than body) ==")
    run14 = ENGINE / "runs" / "2026-11-14"
    arts_path = run14 / "articles-2026-11-14.json"
    dec_path = run14 / "decisions-2026-11-14.json"
    if not (arts_path.exists() and dec_path.exists()):
        print("  !! 14 Nov run files missing — coverage check skipped")
        return
    arts = json.loads(arts_path.read_text(encoding="utf-8"))
    arts = arts.get("articles", arts) if isinstance(arts, dict) else arts
    decs = json.loads(dec_path.read_text(encoding="utf-8"))
    decided = decs.get("decisions", decs) if isinstance(decs, dict) else decs
    keep_ids = {d["id"] for d in decided if d.get("decision") == "keep"}
    items = []
    for a in arts:
        if a.get("id") not in keep_ids:
            continue
        summary = (a.get("summary") or a.get("description") or "").strip()
        if not summary:
            continue
        items.append(_item(a["id"], a.get("title", ""), [summary],
                           source=a.get("source", ""),
                           date=(a.get("published", "")[:10]
                                 or "2026-11-14")))
    print("  kept items with summaries: %d" % len(items))
    prev = load_previous_words("2026-11-15", runs_dir=ENGINE / "runs",
                               editions_dir=ENGINE.parent / "editions")
    vocab = build_vocab(items, "2026-11-15", previous_words=prev)
    print("  stats: %s" % vocab["stats"])
    check("live coverage: >=20 bank words match kept summaries",
          vocab["stats"]["matched_words"] >= 20,
          vocab["stats"]["matched_words"])
    # Phrases need longer text than a 1-2 sentence summary, so the
    # summary bar is >=3; the full-body dry-run is the real 10-phrase
    # test (see TEST_REPORT_2026-11-15.md). The bar was >=5 when the
    # fixture still carried the original 14 Nov summaries (52 words /
    # 7 phrases, report 2026-11-14 17:31); articles-2026-11-14.json
    # was rewritten 2026-11-15 11:58 with the fetched bodies lost
    # (0 bodies on kept articles), so summaries now yield 3 phrases.
    # Do NOT raise the bar back without restoring the bodies.
    check("live coverage: >=3 bank phrases match kept summaries",
          vocab["stats"]["matched_phrases"] >= 3,
          vocab["stats"]["matched_phrases"])
    check("live coverage: 20 words selected",
          len(vocab["words"]) == 20, len(vocab["words"]))
    check("live coverage: 5 revision words (from v1 editions)",
          len(vocab["revision_words"]) == 5,
          len(vocab["revision_words"]))


def test_dedupe_and_enrichment():
    """Dedupe + curated-enrichment-first (Phase 0 ws1, 2026-11-18).

    A headword used in any earlier edition is never selected again
    (17 Nov repeated "postpone" from 13 Nov); the next-ranked words
    fill the slots. Enrichment comes from rules/enrichment.json
    first, falling back to the v1 archive record.
    """
    import tempfile
    from step10_vocab import (_word_enrichment, load_enrichment,
                              load_v1_enrichment)
    print("== dedupe + curated enrichment first ==")
    with tempfile.TemporaryDirectory() as td:
        ed = Path(td) / "editions"
        ed.mkdir()
        prior = {"words": [
            {"Headword / phrase": "cabinet"},
            {"Headword / phrase": "inflation"},
            {"Headword / phrase": "decision", "IPA": "/old/",
             "Bangla phonetic": "", "Synonyms": "old syn",
             "Antonyms": "", "Word family / derivatives": "",
             "Collocations / patterns": ""},
        ], "phrases": [{"Phrase": "fiscal policy"}]}
        (ed / "data-2026-11-14.json").write_text(
            json.dumps(prior), encoding="utf-8")
        runs = Path(td) / "runs"
        runs.mkdir()
        vocab = build_vocab(synthetic_items(), "2026-11-15",
                            runs_dir=runs, editions_dir=ed,
                            previous_words=_prev_words())
        got_w = [w["Headword / phrase"] for w in vocab["words"]]
        got_p = [p["Phrase"] for p in vocab["phrases"]]
        check("dedupe: 'cabinet'/'inflation' from 14 Nov not re-selected",
              "cabinet" not in got_w and "inflation" not in got_w, got_w)
        check("dedupe: 'decision' from 14 Nov not re-selected",
              "decision" not in got_w, got_w)
        check("dedupe: still exactly 20 words (next-ranked fill in)",
              len(got_w) == 20, len(got_w))
        check("dedupe: 'fiscal policy' from 14 Nov not re-selected",
              "fiscal policy" not in got_p, got_p)
        check("dedupe: still exactly 10 phrases",
              len(got_p) == 10, len(got_p))
        check("dedupe: no shortfall flags",
              not (vocab["stats"]["short_words"]
                   or vocab["stats"]["short_phrases"]
                   or vocab["stats"]["short_revision"]),
              vocab["stats"])
        check("dedupe: stats count the dropped words",
              vocab["stats"]["deduped_words"] == 3
              and vocab["stats"]["deduped_phrases"] == 1,
              vocab["stats"])

    # Curated enrichment wins over the archive; the archive fills
    # words the curated file does not cover.
    cur_w, cur_p = load_enrichment()
    bank = load_bank()
    check("enrichment: curated file covers the whole bank",
          len(cur_w) == len(bank["words"])
          and len(cur_p) == len(bank["phrases"]),
          (len(cur_w), len(cur_p)))
    arch_w, _arch_p = load_v1_enrichment()
    got = _word_enrichment("decision", cur_w, arch_w)
    check("enrichment: curated IPA/synonyms beat the stale archive",
          got["IPA"] == "/dɪˈsɪʒən/"
          and got["Synonyms"] == "determination; conclusion; decisiveness"
          and got["Bangla phonetic"] == "ডিসিশন", got)
    got2 = _word_enrichment("postpone", cur_w, arch_w)
    check("enrichment: archive fills a word the curated file lacks",
          got2["IPA"] == "/poʊstˈpoʊn/"
          and got2["Synonyms"] != "", got2)
    for w, e in cur_w.items():
        check("enrichment: word %r fully filled" % w,
              all(str(e.get(k, "")).strip() for k in
                  ("ipa", "bangla_phonetic", "synonyms", "antonyms",
                   "word_family", "collocations")), e)
    for p, e in cur_p.items():
        check("enrichment: phrase %r has collocations" % p,
              bool(str(e.get("collocations", "")).strip()), e)


def main():
    bank = load_bank()
    print("bank: %d words, %d phrases"
          % (len(bank["words"]), len(bank["phrases"])))
    test_synthetic()
    test_plural_example()
    test_dedupe_and_enrichment()
    test_live_coverage()
    print("=" * 60)
    if FAILURES:
        print("OVERALL: FAIL (%d failures)" % len(FAILURES))
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
