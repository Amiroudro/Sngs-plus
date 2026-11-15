#!/usr/bin/env python3
"""run_v2 — full v2 pipeline dry run (Steps 1-10) for one edition date.

Reads the Step 1 batch for <date> (or collects fresh with --fresh),
then runs every step in order and writes the edition JSON + per-step
outputs to engine-v2/runs/<date>/.

Pipeline:
  Step 1 articles -> Step 2 prefilter -> Step 3 decide (cluster mains
  ONLY) -> Step 4 fetch bodies for kept + extract facts -> Step 5
  check (drop/mark) -> Step 6 Bangla lines -> Step 7 daily page ->
  Step 8 questions -> Step 9 SRS cards -> Step 10 vocabulary.

Nothing is published. v1 is never touched. Run:
  python3 run_v2.py --date 2026-11-14 [--fresh]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from step2_prefilter import prefilter_batch, write_log
from step3_decide import decide_batch, score_editorial
from step1_collect import fetch_bodies_for_kept, pick_main, resolve_slug_titles
import common  # noqa: E402  (parse_pubdate for editorial tie-breaks)
from step4_facts import extract_facts, render_facts_en
from step5_check import check as step5_check
from step6_style import render_bangla
from step7_page import build_page
from step8_questions import questions_for_item, analytical_for_items
from step9_study import build_cards
from step10_vocab import build_vocab

# One static GK fact for the footer (style-guide device). The app
# should rotate this per edition; the engine only needs one true,
# evergreen fact here.
GK_FACT = ("বাংলাদেশের জাতীয় সংগীত 'আমার সোনার বাংলা' — "
           "রচয়িতা রবীন্দ্রনাথ ঠাকুর।")


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


def _item_status(facts):
    """Item status from its facts: the first non-happened status wins,
    else happened (the script: every kept item gets exactly one label)."""
    for f in facts:
        if f.get("status") and f["status"] != "happened":
            return f["status"]
    return "happened"


def _metadata_only_record(decision, article):
    """Preserve a kept story's accessible metadata when body text is unavailable.

    This record is an archive entry, not a verified study note. It deliberately
    contains no body text, extracted facts, generated translation or questions.
    """
    error = (article.get("body_error") or "").strip()
    if error.startswith("rights registry:"):
        status = "metadata_only_body_not_licensed"
    elif error == "robots.txt disallows":
        status = "body_blocked_by_robots"
    elif error == "no direct URL":
        status = "no_direct_article_url"
    else:
        status = "body_fetch_failed"
    return {
        "id": decision.get("id", article.get("id", "")),
        "headline": (article.get("title") or "").strip(),
        "source": (article.get("source") or "").strip(),
        "url": (article.get("url") or "").strip(),
        "published": article.get("published") or "",
        "rss_summary": (article.get("summary") or "")[:600],
        "archive_status": status,
        "study_note_status": "not_generated",
        "body_error": error,
    }


def _pub_date(raw):
    """Article date as YYYY-MM-DD from any pub-date format.

    The old code sliced the first 10 characters, which is only
    correct for ISO dates — an RFC-2822 date ("Sat, 14 Nov 2026
    02:00:00 GMT", as The Financial Express publishes) came out as
    "Sat, 14 No" and leaked into page dates, at-a-glance lines and
    focus paragraphs. Parse properly; "" when unparseable.
    """
    dt = common.parse_pubdate(raw or "")
    return dt.strftime("%Y-%m-%d") if dt is not None else ""


def pick_editorial(editorial_articles, date):
    """Best editorial of the day for the মতামত slot (Decision 2):
    scored with the news rubric except the opinion-reject does not
    apply; needs score >= 2. Highest score wins; ties go to the
    earliest published. Returns {"item": {...}|None, "empty_reason"}.
    The item carries headline/source/url/summary only — never full
    opinion text."""
    if not editorial_articles:
        return {"item": None,
                "empty_reason": "আজ কোনো সম্পাদকীয় পাওয়া যায়নি।"}
    scored = []
    for art in editorial_articles:
        dec = score_editorial(art)
        if dec["decision"] != "keep" or dec["score"] < 2:
            continue
        pub = common.parse_pubdate(art.get("published") or "")
        scored.append((dec, art, pub))
    if not scored:
        return {"item": None,
                "empty_reason":
                    "আজ কোনো সম্পাদকীয় নির্ধারিত মান পূরণ করেনি।"}
    # Highest score first; earliest published breaks ties (undated last).
    scored.sort(key=lambda t: (-t[0]["score"],
                               t[2] or datetime_max()))
    dec, art, _ = scored[0]
    return {"item": {"headline": (art.get("title") or "").strip(),
                     "source": art.get("source", ""),
                     "url": art.get("url", ""),
                     "summary": (art.get("summary") or "").strip(),
                     "score": dec["score"],
                     "topic_primary": dec["topic_primary"]},
            "empty_reason": ""}


def datetime_max():
    from datetime import datetime, timezone
    return datetime.max.replace(tzinfo=timezone.utc)


def run(date, fresh=False):
    outdir = HERE / "runs" / date
    outdir.mkdir(parents=True, exist_ok=True)
    stats = {}

    # ---- Step 1 ------------------------------------------------------
    articles_path = outdir / f"articles-{date}.json"
    fresh_clusters = None
    if fresh or not articles_path.exists():
        from step1_collect import collect as step1_collect
        kept, report, fresh_clusters, meta = step1_collect(date, bodies=False)
        _save_json(articles_path, {"date": date, "collected": len(kept),
                                   "articles": kept})
        _save_json(outdir / f"clusters-{date}.json",
                   {"date": date, "clusters": fresh_clusters})
        _save_json(outdir / f"sources-{date}.json",
                   {"date": date, "sources": report})
        print(f"[run] step1 fresh collect: {len(kept)} articles")
    data = _load_json(articles_path)
    articles = data["articles"]
    stats["collected"] = len(articles)

    # ---- Editorial split (Decision 2) --------------------------------
    # Opinion/editorial items never enter the news flow: they are
    # scored separately for the মতামত slot and excluded from
    # clusters, prefilter and Step 3.
    editorial_articles = [a for a in articles
                          if (a.get("section") or "").lower() == "editorial"
                          or a.get("found_via") == "editorial"]
    editorial_ids = {a["id"] for a in editorial_articles}
    articles = [a for a in articles if a["id"] not in editorial_ids]
    stats["editorial_collected"] = len(editorial_articles)

    # Clusters: prefer the file Step 1 wrote; else every article is its own main.
    clusters_path = outdir / f"clusters-{date}.json"
    if fresh_clusters is not None:
        clusters = fresh_clusters
    elif clusters_path.exists():
        clusters = _load_json(clusters_path)["clusters"]
    else:
        clusters = [{"members": [a["id"]], "main_id": a["id"], "size": 1}
                    for a in articles]
    # Filter clusters to news members only (an editorial member must
    # never become a Step 3 main); re-pick the main where the old
    # main was editorial.
    by_id = {a["id"]: a for a in articles}
    news_clusters = []
    for c in clusters:
        members = [m for m in c.get("members", [])
                   if m not in editorial_ids and m in by_id]
        if not members:
            continue
        main_id = c.get("main_id")
        if main_id not in members:
            main_id = pick_main([by_id[m] for m in members])["id"]
        news_clusters.append({"members": members, "main_id": main_id,
                              "size": len(members)})
    clusters = news_clusters
    mains = {c["main_id"] for c in clusters}
    stats["clusters"] = len(clusters)
    main_articles = [by_id[m] for m in sorted(mains) if m in by_id]
    # Safety net: a re-picked main (the old main was editorial) may
    # still carry a slug title — resolve it now, before Step 3
    # decides. Normally a no-op: collect() already resolved every
    # main, so this fetches nothing.
    _r_res, _r_fail, _r_secs = resolve_slug_titles(main_articles, clusters)
    if _r_res or _r_fail:
        print(f"[run] title safety net: {_r_res} resolved, "
              f"{_r_fail} kept slug ({_r_secs:.1f}s)")
    print(f"[run] step1: {len(articles)} news articles in "
          f"{len(clusters)} clusters; "
          f"{len(editorial_articles)} editorial articles set aside")

    # ---- Step 2 ------------------------------------------------------
    prefiltered, log = prefilter_batch(articles)
    _save_json(outdir / f"prefiltered-{date}.json",
               {"date": date, "articles": prefiltered,
                "deprioritised": len(log)})
    write_log(log, date, outdir)
    stats["deprioritised"] = len(log)
    print(f"[run] step2: {len(log)} deprioritised (logged, none deleted)")

    # ---- Step 3 (cluster mains only) ---------------------------------
    decisions = decide_batch(main_articles)
    _save_json(outdir / f"decisions-{date}.json",
               {"date": date, "decided": len(decisions),
                "decisions": decisions})
    dist = Counter(d["decision"] for d in decisions)
    stats["decisions"] = dict(dist)
    print(f"[run] step3: decided {len(decisions)} mains -> {dict(dist)}")
    kept = [d for d in decisions if d["decision"] == "keep"]
    maybe = [d for d in decisions if d["decision"] == "maybe"]
    print(f"[run] step3: keep={len(kept)} maybe={len(maybe)} "
          f"reject={dist.get('reject', 0)}")

    # ---- Step 4 (bodies for kept only, then facts) -------------------
    kept_articles = [dict(by_id[d["id"]]) for d in kept]
    ok, tried = fetch_bodies_for_kept(kept_articles)
    stats["bodies"] = {"ok": ok, "tried": tried}
    print(f"[run] step4: bodies fetched {ok}/{tried} kept articles")
    items = []
    metadata_only_items = []
    no_body = 0
    for dec, art in zip(kept, kept_articles):
        if not art.get("body_text"):
            no_body += 1
            metadata_only_items.append(_metadata_only_record(dec, art))
            continue
        art = dict(art)
        art["topic_primary"] = dec["topic_primary"]
        extracted = extract_facts(art)
        items.append({"id": dec["id"], "headline": art["title"],
                      "score": dec["score"],
                      "topic_primary": dec["topic_primary"],
                      "topic_secondary": dec.get("topic_secondary", ""),
                      "decision": dec, "article": art,
                      "facts_raw": extracted["facts"],
                      "why_important": extracted["why_important"]})
    stats["no_body_dropped"] = no_body\n    stats["metadata_only_items"] = len(metadata_only_items)\n    print(f"[run] step4: {len(items)} items with facts "
          f"({no_body} preserved in metadata-only archive; no body text)")

    # ---- Step 5 (check) + Step 6 (Bangla) ----------------------------
    final_items = []
    step5_records = []
    dropped_few_facts = 0
    marked_verify = 0
    for it in items:
        res = step5_check({"id": it["id"], "facts": it["facts_raw"]},
                          it["article"]["body_text"])
        if res["action"] == "drop":
            step5_records.append({"item_id": it["id"], "action": "drop",
                                  "failures": res["failures"],
                                  "facts_kept": res["facts_kept"]})
            dropped_few_facts += 1
            continue
        if res["action"] == "verify":
            marked_verify += 1
        kept_facts = it["facts_raw"][:res["facts_kept"]] \
            if res["facts_kept"] < len(it["facts_raw"]) else it["facts_raw"]
        # The checker drops specific failed facts (named in failures),
        # not necessarily trailing ones — rebuild the kept set exactly.
        dropped_whats = {f["fact"] for f in res["failures"]}
        kept_facts = [f for f in it["facts_raw"]
                      if f["what"] not in dropped_whats]
        if len(kept_facts) < 2:
            step5_records.append({"item_id": it["id"], "action": "drop",
                                  "failures": res["failures"],
                                  "facts_kept": len(kept_facts)})
            dropped_few_facts += 1
            continue
        rendered = render_bangla(kept_facts, it["topic_primary"])
        final_items.append({
            "id": it["id"],
            "headline": it["headline"],
            "score": it["score"],
            "topic_primary": it["topic_primary"],
            "topic_secondary": it["topic_secondary"],
            "status": _item_status(kept_facts),
            "facts": kept_facts,
            # Proposal 8: English fact list for every story — same
            # verified facts, rendered in English (glossary-based for
            # Bangla-language articles), quote-checked the same way.
            "facts_en": render_facts_en(kept_facts,
                                         it["article"]["body_text"]),
            "fact_lines": rendered["bangla_lines"],
            "why_important": it["why_important"],
            "why_important_bn": rendered["why_important_bn"],
            "sources": [{"name": it["article"]["source"],
                         "url": it["article"]["url"]}],
            "url": it["article"]["url"],
            "source": it["article"]["source"],
            "date": _pub_date(it["article"].get("published", "")),
            "published": it["article"].get("published", ""),
            "body_text": it["article"]["body_text"],
            "check": res["action"],
        })
        step5_records.append({"item_id": it["id"], "action": res["action"],
                              "failures": res["failures"],
                              "facts_kept": len(kept_facts)})
    # Persisted Step 5 evidence (v2 publish gate check 3 reads this
    # file; a missing file is a FAIL). Re-running Step 5 from
    # re-fetched bodies is not a substitute — it would check
    # different text than the edition was built from.
    _save_json(outdir / f"step5-{date}.json",
               {"date": date, "items": step5_records})
    stats["step5_dropped"] = dropped_few_facts
    stats["step5_verify"] = marked_verify
    stats["final_items"] = len(final_items)
    print(f"[run] step5: {dropped_few_facts} dropped (<2 facts), "
          f"{marked_verify} marked যাচাই করুন, {len(final_items)} items kept")
    print(f"[run] step6: Bangla lines rendered for {len(final_items)} items")

    # ---- Editorial slot (Decision 2) ---------------------------------
    editorial_slot = pick_editorial(editorial_articles, date)
    stats["editorial"] = {
        "filled": editorial_slot["item"] is not None,
        "headline": (editorial_slot["item"] or {}).get("headline", ""),
        "reason": editorial_slot["empty_reason"],
    }
    print(f"[run] editorial slot: "
          f"{'filled: ' + stats['editorial']['headline'] if stats['editorial']['filled'] else 'empty (' + stats['editorial']['reason'] + ')'}")

    # ---- Step 7 (daily page, max 15) ---------------------------------
    maybe_items = [{"title": by_id[d["id"]]["title"],
                    "url": by_id[d["id"]]["url"],
                    "source": by_id[d["id"]]["source"]} for d in maybe]
    page = build_page(date, final_items, maybe_items, gk_fact=GK_FACT,
                      editorial=editorial_slot)
    _save_json(outdir / f"page-{date}.json", page)
    stats["page_items"] = sum(len(v) for v in page["sections"].values())
    stats["page_maybe"] = len(page.get("maybe_items", []))
    print(f"[run] step7: page has {stats['page_items']} full items, "
          f"{stats['page_maybe']} maybe items")

    # ---- Step 8 (questions) ------------------------------------------
    all_qa, all_mcq = [], []
    for it in final_items:
        q = questions_for_item({**it, "checked": True,
                                "source_text": it["body_text"]})
        all_qa.extend(q.get("qa", []))
        all_mcq.extend(q.get("mcq", []))
    # Proposal 9: analytical questions, max 2 per edition, only from
    # score-3 items, in page order (score desc, then newest first —
    # the same order build_page uses). They are NOT SRS cards.
    ranked_items = sorted(final_items,
                          key=lambda it: it.get("published", ""),
                          reverse=True)
    ranked_items = sorted(ranked_items, key=lambda it: -it["score"])
    all_analytical = analytical_for_items(ranked_items)
    _save_json(outdir / f"questions-{date}.json",
               {"date": date, "qa": all_qa, "mcq": all_mcq,
                "analytical": all_analytical})
    stats["qa"] = len(all_qa)
    stats["mcq"] = len(all_mcq)
    stats["analytical"] = len(all_analytical)
    stats["facts_en_items"] = sum(
        1 for sec in page["sections"].values() for it in sec
        if it.get("facts_en"))
    print(f"[run] step8: {len(all_qa)} Q&A, {len(all_mcq)} MCQ, "
          f"{len(all_analytical)} analytical; "
          f"facts_en on {stats['facts_en_items']}/{stats['page_items']} "
          f"page items")

    # ---- Step 9 (SRS cards) ------------------------------------------
    # The returned QA/MCQ dicts already carry "checked": true (Step 8
    # sets it only when the source quote is verified verbatim).
    cards = build_cards(all_qa + all_mcq, date)
    _save_json(outdir / f"srs-{date}.json", cards)
    stats["srs_cards"] = len(cards.get("cards", []))
    print(f"[run] step9: {stats['srs_cards']} SRS cards")

    # ---- Step 10 (vocabulary) ----------------------------------------
    # Deterministic extraction from the kept articles' fact lists;
    # revision words come from the previous editions' word lists
    # (last v2 dry-run vocab, else the v1 editions dir).
    vocab = build_vocab(final_items, date, runs_dir=HERE / "runs",
                        editions_dir=HERE.parent / "editions")
    _save_json(outdir / f"vocab-{date}.json", vocab)
    stats["vocab"] = vocab["stats"]
    print(f"[run] step10: {len(vocab['words'])} words, "
          f"{len(vocab['phrases'])} phrases, "
          f"{len(vocab['revision_words'])} revision words"
          + (" (SHORT: %s)" % vocab["stats"] if vocab["stats"]["short_words"]
             or vocab["stats"]["short_phrases"]
             or vocab["stats"]["short_revision"] else ""))

    # ---- Persist final items (2026-11-15, converter support) ------------
    # convert_to_app.py reads this file for Bangla structured facts,
    # why_important_bn and body text (e.g. a second phrase-example
    # sentence). The converter works without it (fallbacks), but the
    # 15 Nov run predates this line, so that run has no items file.
    _save_json(outdir / f"items-{date}.json",
               {"date": date, "items": final_items})
    _save_json(outdir / f"metadata-only-{date}.json",
               {"date": date, "items": metadata_only_items})
    print(f"[run] final items written: {outdir}/items-{date}.json "
          f"({len(final_items)} items)")

    # ---- Edition file --------------------------------------------------
    edition = {"date": date, "engine": "v2", "stats": stats,
               "page": page, "qa": all_qa, "mcq": all_mcq,
               "analytical": all_analytical,
               "srs_cards": stats["srs_cards"], "vocab": vocab,\n               "metadata_only_items": metadata_only_items}\n    _save_json(outdir / f"edition-{date}.json", edition)
    print(f"[run] edition written: {outdir}/edition-{date}.json")
    return stats


def main():
    ap = argparse.ArgumentParser(description="Sarangsho Plus engine v2 dry run")
    ap.add_argument("--date", required=True, help="edition date YYYY-MM-DD")
    ap.add_argument("--fresh", action="store_true",
                    help="re-collect Step 1 instead of reusing the batch")
    args = ap.parse_args()
    stats = run(args.date, fresh=args.fresh)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
