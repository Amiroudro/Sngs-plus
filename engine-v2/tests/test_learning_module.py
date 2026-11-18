#!/usr/bin/env python3
"""learning_module.py tests (engine v2) -- runnable as:
python3 tests/test_learning_module.py

Style follows the other engine-v2 suites: PASS/FAIL counts printed,
exit 0 iff all pass. Stdlib only. Read-only on the live run dirs:
the CA03 golden test builds the module from runs/2026-11-17 in
memory and never writes into it.

Tests:
  1. Bangla helpers: bn_date, bn_value (units + Tk/$ currency).
  2. GK knowledge file loads; the ADP entry matches ADP headlines
     only (CA03/CA10) and nothing else in the 17 Nov edition.
  3. CA03 golden build (real 17 Nov run data): hero ৬.৫৩%, GK
     sections are content (not markers), 4 MCQs with traced answers,
     validate_module clean.
  4. A non-ADP story gets the per-section marker on all three GK
     sections and still validates clean.
  5. Editorial module: 4 mechanical MCQs, hero 'মতামত', validates.
  6. validate_module rejects: wrong key order, 3 MCQs, a non-marker
     GK string, a vocabulary word that is not an edition word, an
     untraced correct answer.
  7. Vocabulary: only edition words, matched by headline or source
     URL (CA14 gets 7 on 17 Nov; CA03 gets 0).
  8. Degenerate MCQs are rejected: answer inside the question,
     answer's number inside the question, near-duplicate
     question/answer — and CA11/CA12/CA13 still reach 4 MCQs on
     the honest metadata floor.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_V2 = HERE.parent
ROOT = ENGINE_V2.parent
sys.path.insert(0, str(ENGINE_V2))

import learning_module as lm  # noqa: E402

DATE = "2026-11-17"
RUN = ENGINE_V2 / "runs" / DATE

FAILURES = []


def check(cond, label):
    print(("  PASS " if cond else "  FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def build_ctx(date_str=DATE):
    page = load(f"page-{date_str}.json")
    questions = load(f"questions-{date_str}.json")
    vocab = load(f"vocab-{date_str}.json")
    articles = load(f"articles-{date_str}.json").get("articles", [])
    data = load(Path("app-format") / f"data-{date_str}.json")
    flat = [it for sec in page["sections"].values() for it in sec]
    by_hl = {it["headline"]: it for it in flat}
    ordered = []
    for row in page.get("at_a_glance", []):
        it = by_hl.get(row.get("event", ""))
        if it is not None and it not in ordered:
            ordered.append(it)
    for it in flat:
        if it not in ordered:
            ordered.append(it)
    news_items = ordered[:-1]
    return {
        "page": page, "questions": questions, "vocab": vocab,
        "articles": articles, "data": data, "ordered": ordered,
        "news_items": news_items,
        "gk_entries": lm.load_gk_entries(),
        "enrichment": lm.load_enrichment(),
    }


def ctx_for(ctx, ca_id, is_editorial=False):
    base = {
        "questions": ctx["questions"],
        "vocab_words": ctx["vocab"]["words"],
        "enrichment": ctx["enrichment"],
        "gk_entries": ctx["gk_entries"],
        "page_items": ctx["news_items"],
        "articles": ctx["articles"],
        "edition_stories": ctx["data"]["stories"],
        "date": DATE,
        "ca_id": ca_id,
        "is_editorial": is_editorial,
    }
    return base


def test_helpers():
    check(lm.bn_date("2026-11-15") == "১৫ নভেম্বর ২০২৬",
          "bn_date 2026-11-15 -> ১৫ নভেম্বর ২০২৬")
    check(lm.bn_date("not-a-date") == "", "bn_date garbage -> ''")
    check(lm.bn_value("20,160", "crore",
                       "spent Tk20,160 crore between July and October")
          == "২০,১৬০ কোটি টাকা", "bn_value Tk crore")
    check(lm.bn_value("6.53", "%", "fell to 6.53%") == "৬.৫৩ %",
          "bn_value percent")
    check(lm.bn_value("100", "million", "sold $100 million")
          == "১০০ মিলিয়ন ডলার", "bn_value $ million")
    check(lm.bn_value("72", "", "from 72 countries") == "৭২",
          "bn_value bare number")
    check(lm.bn_value("20,160 crore", "", "spent Tk20,160 crore")
          == "২০,১৬০ কোটি টাকা", "bn_value unit inside value string")


def test_gk_file(ctx):
    entries = ctx["gk_entries"]
    check(len(entries) == 1 and entries[0]["id"] == "adp",
          f"GK file: 1 entry (adp), got {[e.get('id') for e in entries]}")
    adp = entries[0]
    check(len(adp["institutions"]) == 5,
          "ADP entry: 5 institutions (Planning Commission, NEC, "
          "ECNEC, IMED, DPP)")
    check(all(i.get("source") for i in adp["institutions"]),
          "ADP institutions all carry a source")
    check(len(adp["extra_knowledge"]) == 4,
          "ADP entry: 4 extra-knowledge terms")
    check(all(t.get("source") for t in adp["extra_knowledge"]),
          "ADP extra-knowledge terms all carry a source")
    check(len(adp["topic_gk"]["sources"]) >= 2,
          "ADP topic_gk carries >=2 named sources with URLs")
    check(all(s.get("url", "").startswith("http")
              for s in adp["topic_gk"]["sources"]),
          "ADP topic_gk source URLs are http(s)")
    matched = [s["id"] for s in ctx["data"]["stories"]
               if lm.find_gk_entry(s["headline"], s["category"], entries)]
    check(matched == ["CA03", "CA10"],
          f"ADP entry matches only CA03+CA10, got {matched}")


def test_ca03_golden(ctx):
    data = ctx["data"]
    ca03 = next(s for s in data["stories"] if s["id"] == "CA03")
    bn = load(Path("app-format") / f"bn-{DATE}.json")
    item = next(it for it in ctx["news_items"]
                if it["headline"] == ca03["headline"])
    module, notes = lm.build_module(ca03, bn["stories"]["CA03"], item,
                                    ctx_for(ctx, "CA03"))
    check(list(module.keys()) == list(lm.SECTION_KEYS),
          "CA03: 11 keys in v2 order")
    check(module["hero"]["figure"] == "৬.৫৩%",
          f"CA03 hero figure ৬.৫৩%, got {module['hero']['figure']!r}")
    check("ADP" in module["hero"]["label"],
          f"CA03 hero label names ADP: {module['hero']['label']!r}")
    check(module["news_summary"]["source"]["publication"] ==
          "The Business Standard",
          "CA03 news_summary.source.publication is TBS")
    check(module["news_summary"]["source"]["url"].startswith("https://"),
          "CA03 news_summary.source.url is the TBS article URL")
    check(module["news_summary"]["source"]["date"] == "2026-11-16",
          "CA03 news_summary.source.date is the article date")
    check(isinstance(module["topic_gk"], dict),
          "CA03 topic_gk is content, not the marker")
    check(isinstance(module["institutions"], list) and
          len(module["institutions"]) == 5,
          "CA03 institutions: 5 entries")
    check(isinstance(module["extra_knowledge"], list) and
          len(module["extra_knowledge"]) == 4,
          "CA03 extra_knowledge: 4 entries")
    check(len(module["verified_facts"]) == 4,
          f"CA03 verified_facts: 4 rows, got {len(module['verified_facts'])}")
    check(module["verified_facts"][1]["value"] == "৬.৫৩ %",
          "CA03 verified_facts[1] is the 6.53% rate in Bangla")
    mcqs = module["mcq_practice"]
    check(len(mcqs) == 4, f"CA03 mcq_practice: 4, got {len(mcqs)}")
    check(all(m["correct"] in (0, 1, 2, 3) for m in mcqs),
          "CA03 MCQ correct indices are 0-3")
    check(len({m["correct"] for m in mcqs}) == 4,
          "CA03 MCQ correct positions are all distinct")
    check(all(m.get("explanation") for m in mcqs),
          "CA03 MCQs all carry explanations")
    check(all(len(m["options"]) == 4 for m in mcqs),
          "CA03 MCQ options are lists of 4")
    headwords = [w.get("Headword / phrase", "")
                 for w in ctx["vocab"]["words"]]
    problems = lm.validate_module(module, ca03, headwords)
    check(not problems, f"CA03 validate_module clean (got {problems[:3]})")
    check(module["vocabulary"] == [],
          "CA03 vocabulary empty: no edition word matches the ADP story")
    check(len(module["revision"]["flashcards"]) == 4,
          "CA03 revision: 4 flashcards")
    check(len(module["revision"]["next_revision"]) == 2,
          "CA03 revision: 2 next-revision questions")
    check(len(module["deep_prep"]) == 6,
          "CA03 deep_prep: 6 topics from the GK entry")
    check("সংশোধিত" in json.dumps(module["topic_gk"],
                                   ensure_ascii=False),
          "CA03 topic_gk covers the RADP distinction")


def test_marker_story(ctx):
    data = ctx["data"]
    ca01 = next(s for s in data["stories"] if s["id"] == "CA01")
    bn = load(Path("app-format") / f"bn-{DATE}.json")
    item = next(it for it in ctx["news_items"]
                if it["headline"] == ca01["headline"])
    module, _notes = lm.build_module(ca01, bn["stories"]["CA01"], item,
                                     ctx_for(ctx, "CA01"))
    check(module["topic_gk"] == lm.MARKER,
          "CA01 topic_gk is the exact marker (no GK entry)")
    check(module["institutions"] == lm.MARKER,
          "CA01 institutions is the exact marker")
    check(module["extra_knowledge"] == lm.MARKER,
          "CA01 extra_knowledge is the exact marker")
    headwords = [w.get("Headword / phrase", "")
                 for w in ctx["vocab"]["words"]]
    problems = lm.validate_module(module, ca01, headwords)
    check(not problems, f"CA01 validate_module clean (got {problems[:3]})")
    check(len(module["mcq_practice"]) == 4,
          "CA01 mcq_practice: 4 (Step 8 reuse + synthesis)")


def test_editorial(ctx):
    data = ctx["data"]
    ca15 = next(s for s in data["stories"] if s["id"] == "CA15")
    bn = load(Path("app-format") / f"bn-{DATE}.json")
    page = ctx["page"]
    ed_item = dict(page["editorial"]["item"])
    module, _notes = lm.build_module(
        ca15, bn["stories"]["CA15"], ed_item,
        ctx_for(ctx, "CA15", is_editorial=True))
    check(module["hero"]["figure"] == "মতামত",
          "editorial hero figure is 'মতামত' (no numeric fact)")
    check(len(module["mcq_practice"]) == 4,
          f"editorial mcq_practice: 4 mechanical, "
          f"got {len(module['mcq_practice'])}")
    headwords = [w.get("Headword / phrase", "")
                 for w in ctx["vocab"]["words"]]
    problems = lm.validate_module(module, ca15, headwords,
                                  is_editorial=True)
    check(not problems, f"editorial validate_module clean (got {problems[:3]})")
    check(module["topic_gk"] == lm.MARKER,
          "editorial topic_gk is the marker")


def test_vocabulary_matching(ctx):
    data = ctx["data"]
    bn = load(Path("app-format") / f"bn-{DATE}.json")
    ca14 = next(s for s in data["stories"] if s["id"] == "CA14")
    item = next(it for it in ctx["news_items"]
                if it["headline"] == ca14["headline"])
    module, _notes = lm.build_module(ca14, bn["stories"]["CA14"], item,
                                     ctx_for(ctx, "CA14"))
    words = [w["word"] for w in module["vocabulary"]]
    check(len(words) == 5,
          f"CA14 vocabulary: 5 of the 7 matched words (cap 5), got {words}")
    check(all(w in ("garment", "worker", "data", "official", "market",
                    "increase", "demand") for w in words),
          "CA14 vocabulary words are all headline-matched edition words")
    check(all(w.get("synonyms") for w in module["vocabulary"]),
          "CA14 vocabulary synonyms come from the enrichment bank")
    headwords = [w.get("Headword / phrase", "")
                 for w in ctx["vocab"]["words"]]
    problems = lm.validate_module(module, ca14, headwords)
    check(not problems, f"CA14 validate_module clean (got {problems[:3]})")


def test_validate_rejects(ctx):
    data = ctx["data"]
    ca03 = next(s for s in data["stories"] if s["id"] == "CA03")
    bn = load(Path("app-format") / f"bn-{DATE}.json")
    item = next(it for it in ctx["news_items"]
                if it["headline"] == ca03["headline"])
    module, _notes = lm.build_module(ca03, bn["stories"]["CA03"], item,
                                     ctx_for(ctx, "CA03"))
    headwords = [w.get("Headword / phrase", "")
                 for w in ctx["vocab"]["words"]]

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    bad["mcq_practice"] = bad["mcq_practice"][:3]
    check(any("mcq_practice" in p
              for p in lm.validate_module(bad, ca03, headwords)),
          "validator rejects 3 MCQs")

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    bad["topic_gk"] = "some unverified guess"
    check(any("topic_gk" in p
              for p in lm.validate_module(bad, ca03, headwords)),
          "validator rejects a non-marker GK string")

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    bad["vocabulary"] = [{"word": "invented", "meaning_bn": "x",
                          "example": "invented word here",
                          "synonyms": [], "antonyms": []}]
    check(any("vocabulary" in p
              for p in lm.validate_module(bad, ca03, headwords)),
          "validator rejects a vocabulary word outside the edition")

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    keys = list(bad.keys())
    keys[0], keys[1] = keys[1], keys[0]
    reordered = {k: bad[k] for k in keys}
    check(any("keys" in p
              for p in lm.validate_module(reordered, ca03, headwords)),
          "validator rejects out-of-order section keys")

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    bad["mcq_practice"][0]["options"][bad["mcq_practice"][0]["correct"]] = \
        "৯৯,৯৯৯ কোটি টাকা"
    check(any("mcq_practice[0]" in p and "trace" in p
              for p in lm.validate_module(bad, ca03, headwords)),
          "validator rejects an MCQ answer that does not trace to "
          "the story")

    bad = json.loads(json.dumps(module, ensure_ascii=False))
    bad["topic_gk"] = ""
    check(any("topic_gk" in p
              for p in lm.validate_module(bad, ca03, headwords)),
          "validator rejects an empty-string GK section")


def test_degenerate_mcqs(ctx):
    # (1) Q&A answer that IS the headline the question quotes.
    check(lm._is_degenerate(
        "Reclaiming religious authority: What Bangladesh can learn "
        "from Indonesia's women ulama movement কী (2026-11-17 "
        "অনুযায়ী)?",
        "Reclaiming religious authority: What Bangladesh can learn "
        "from Indonesia's women ulama movement"),
        "degenerate: answer is the question's headline")
    # (2) Recall answer '31' when the question says 'COP31'.
    check(lm._is_degenerate(
        "COP31 SUMMIT: Draft deal calls for faster ‘action’ to exit "
        "fossil fuels কী (2026-11-16 অনুযায়ী)?", "৩১"),
        "degenerate: answer 31 given away by COP31 in the question")
    # (3) Near-duplicate: answer is the question minus its last word.
    check(lm._is_degenerate(
        "বাংলাদেশ ব্যাংক বলছে, ই-মেইল ও অন্যান্য ডিজিটাল মাধ্যমে "
        "ক্রেতা-বিক্রেতার মধ্যে তথ্য ও নথি আদান-প্রদানের কী "
        "(2026-11-16 অনুযায়ী)?",
        "বাংলাদেশ ব্যাংক বলছে, ই-মেইল ও অন্যান্য ডিজিটাল মাধ্যমে "
        "ক্রেতা-বিক্রেতার মধ্যে তথ্য ও নথি আদান-প্রদানের ক্ষেত্রে "
        "সতর্ক থাকতে হবে।"),
        "degenerate: answer is the question with one word changed")
    # (4) Answer's number inside an English stem (Bangla answer).
    check(lm._is_degenerate(
        "The government spent 20,160 crore between July and "
        "October কত (2026-11-15 অনুযায়ী)?", "২০,১৬০ কোটি টাকা"),
        "degenerate: answer's number 20,160 sits in the stem")
    # Real negatives: legitimate questions must NOT be rejected.
    check(not lm._is_degenerate(
        "implementation rate of the government's Annual Development "
        "Programme (ADP) fell to a record low কত (১৬ নভেম্বর ২০২৬ "
        "অনুযায়ী)?", "৬.৫৩ %"),
        "not degenerate: CA03 synthesised MCQ survives")
    check(not lm._is_degenerate(
        "এই খবরটি কোন প্রকাশনায় ছাপা হয়েছে?", "The Daily Star"),
        "not degenerate: metadata publication MCQ survives")
    check(not lm._is_degenerate(
        "এই খবরের শিরোনাম কী?",
        "COP31 SUMMIT: Draft deal calls for faster ‘action’ to exit "
        "fossil fuels"),
        "not degenerate: metadata headline MCQ survives")
    # A stem holding a DIFFERENT number must not be flagged: the
    # answer's number is 6.53, the stem holds 20.74 and 33,374.
    check(not lm._is_degenerate(
        "Local Government Division recorded the highest "
        "implementation rate, spending, or 20.74% of its Tk33,374 "
        "কত (১৬ নভেম্বর ২০২৬ অনুযায়ী)?", "৬,৯২৪ কোটি টাকা"),
        "not degenerate: other numbers in the stem do not leak")
    # And the whole-edition effect: the three headline-QA stories
    # fall through to the honest metadata floor, still 4 MCQs.
    # (Match items by POSITION, as the converter does: the CA13
    # headline differs by one Bangla spelling variant between the
    # page item — 'জালিয়াতির' with য় — and the converted file —
    # 'জালিয়াতির' with য + nukta — so a headline lookup misses.)
    for ca_id in ("CA11", "CA12", "CA13"):
        data = ctx["data"]
        story = next(s for s in data["stories"] if s["id"] == ca_id)
        bn = load(Path("app-format") / f"bn-{DATE}.json")
        item = ctx["news_items"][int(ca_id[2:]) - 1]
        module, notes = lm.build_module(
            story, bn["stories"][ca_id], item, ctx_for(ctx, ca_id))
        check(len(module["mcq_practice"]) == 4,
              f"{ca_id} still reaches 4 MCQs after degenerate "
              "rejection")
        check(any("rejected" in n for n in notes),
              f"{ca_id} notes record the degenerate rejection")
        check(all(not lm._is_degenerate(m["question"],
                                         m["options"][m["correct"]])
                  for m in module["mcq_practice"]),
              f"{ca_id} emitted MCQs contain no degenerate question")
        # The metadata floor is a full 4: publication, date,
        # section, headline. The date question's wrong options are
        # other stories' dates, then neighbouring calendar dates.
        date_q = [m for m in module["mcq_practice"]
                  if "তারিখে" in m["question"]]
        check(len(date_q) == 1 and len(date_q[0]["options"]) == 4,
              f"{ca_id} metadata floor includes the date question")


def main():
    ctx = build_ctx()
    test_helpers()
    test_gk_file(ctx)
    test_ca03_golden(ctx)
    test_marker_story(ctx)
    test_editorial(ctx)
    test_vocabulary_matching(ctx)
    test_validate_rejects(ctx)
    test_degenerate_mcqs(ctx)
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s)")
        for f in FAILURES:
            print(" - " + f)
        return 1
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
