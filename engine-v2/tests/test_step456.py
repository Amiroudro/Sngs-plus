#!/usr/bin/env python3
"""Tests for engine v2 Steps 4, 5 and 6 (fact list, check by code,
Bangla style). Runnable as: python3 tests/test_step456.py
(from engine-v2/, or from anywhere — paths derive from __file__).

- Fetches 3 real kept-style articles live (tbsnews.net /
  thedailystar.net / en.prothomalo.com, urllib + browser User-Agent,
  HTML stripped to text). If runs/2026-11-14/decisions-*.json already
  exists, its kept items are preferred instead.
- For each: prints extracted facts, the Step 5 check result and the
  Bangla lines.
- Step 5 is proven with one deliberately broken fact per check type:
  (a) fake quote, (b) wrong number, (c) invented proper name — each
  must be caught (fact dropped / item marked "যাচাই করুন"), while a
  correct fact passes all three checks.
- Asserts: no fact value contains "প্রায়"; no fact date is a relative
  date ("আজ"/"গতকাল"/"এ বছর"); every kept fact's quote is a verbatim
  substring of the article text; fewer-than-2-facts drops the item.
- Prints PASS/FAIL counts at the end; exit code 0 only if all pass.
"""
import glob
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_V2 = HERE.parent
sys.path.insert(0, str(ENGINE_V2))

from step4_facts import (extract_facts, detect_topic, norm_bangla,
                         render_facts_en)  # noqa: E402
from step5_check import check, check_batch, numbers_in, quote_in_text  # noqa: E402
from step6_style import render_bangla  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
                   "SarangshoPlus/2.0"}
TODAY = datetime.now(timezone.utc).date().isoformat()
PUBLISHED = datetime.now(timezone.utc).isoformat()

RESULTS = []  # (name, passed, detail)


def record(name, passed, detail=""):
    RESULTS.append((name, bool(passed), detail))
    print(("PASS " if passed else "FAIL ") + name
          + ((" — " + detail) if detail else ""))


# ---------------------------------------------------------------------------
# Fetching (live; Step 1's job is the clean body — the test strips HTML
# and drops obvious footer/nav paragraphs, Step 4 filters the rest)
# ---------------------------------------------------------------------------
CHROME_PARA = ("EMAIL US", "FOLLOW US", "MOST VIEWED", "Related News",
               "Copyright", "About Us", "TBS NEWS AT", "Privacy Policy",
               "Comment Policy", "Technical Partner")


def fetch_page(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def body_text(page):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page,
                  flags=re.S | re.I)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", page, flags=re.S | re.I)
    out = []
    for p in paras:
        t = re.sub(r"<[^>]+>", " ", p)
        t = html.unescape(t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 60:
            continue
        if any(m in t for m in CHROME_PARA):
            continue
        out.append(t)
    return " ".join(out)


def title_of(page):
    m = re.search(r"<title>(.*?)</title>", page, flags=re.S | re.I)
    if not m:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


KEYWORDS = ["bank", "imf", "budget", "court", "election", "reserve",
            "remittance", "export", "ordinance", "cabinet", "parliament",
            "treaty", "climate", "gdp", "inflation", "loan", "trade",
            "energy", "dengue", "award", "economy"]


def is_article_url(u):
    path = re.sub(r"^https?://[^/]+", "", u).strip("/")
    parts = path.split("/")
    if len(parts) < 2 or not re.search(r"\d", parts[-1]):
        return False
    return not any(s in path for s in ("/tag/", "/author/", "/search"))


def fetch_live_articles(n=3):
    """Fresh article URLs from the three papers' homepages."""
    homes = [("https://www.tbsnews.net", "https://www.tbsnews.net"),
             ("https://www.thedailystar.net", "https://www.thedailystar.net"),
             ("https://en.prothomalo.com", "https://en.prothomalo.com")]
    picked, tried = [], []
    for home, base in homes:
        if len(picked) >= n:
            break
        try:
            hrefs = []
            for x in re.findall(r'href="([^"]+)"', fetch_page(home)):
                if x.startswith("/"):
                    x = base + x
                if x.startswith(base) and x not in hrefs:
                    hrefs.append(x)
        except Exception as e:  # noqa: BLE001 - note and move on
            print("  [fetch] homepage failed %s: %s" % (home, e))
            continue
        for u in hrefs:
            if len(picked) >= n:
                break
            if not is_article_url(u):
                continue
            if not any(k in u.lower() for k in KEYWORDS):
                continue
            if u in tried:
                continue
            tried.append(u)
            try:
                page = fetch_page(u)
                body = body_text(page)
            except Exception as e:  # noqa: BLE001
                print("  [fetch] article failed %s: %s" % (u, e))
                continue
            if len(body) < 1200:
                continue
            picked.append({"url": u, "title": title_of(page), "body": body})
            print("  [fetch] picked %s (%d chars)" % (u, len(body)))
    return picked


def load_articles():
    """Prefer a Step 3 decisions file if one exists, else fetch live."""
    today_dir = ENGINE_V2 / "runs" / TODAY
    for path in sorted(glob.glob(str(today_dir / "decisions-*.json"))):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print("  [decisions] unreadable %s: %s" % (path, e))
            continue
        kept = [a for a in data.get("articles", [])
                if a.get("decision") == "keep" and a.get("body_text")]
        if kept:
            print("  [decisions] using kept items from %s" % path)
            return [{"url": a.get("url", ""), "title": a.get("title", ""),
                     "body": a["body_text"],
                     "published": a.get("published", PUBLISHED)}
                    for a in kept[:3]]
    print("  [decisions] no decisions file for %s — fetching live" % TODAY)
    arts = fetch_live_articles(3)
    for a in arts:
        a.setdefault("published", PUBLISHED)
    return arts


# ---------------------------------------------------------------------------
# Helpers for the broken-fact tests
# ---------------------------------------------------------------------------
def first_numbers_with_sentences(body, count=3):
    """(number, sentence) pairs for the first `count` distinct numbers
    in the article, from sentences that actually contain them."""
    from step4_facts import split_sentences, _number_matches
    out, seen = [], set()
    for sent in split_sentences(body):
        for m in _number_matches(sent):
            num = m.group(0)
            if num not in seen:
                seen.add(num)
                out.append((num, sent))
                if len(out) >= count:
                    return out
    return out


def break_number(value, article_text):
    """Change one digit of `value` so the result is NOT in the article."""
    norm_art = norm_bangla(article_text).replace(",", "")
    for i in range(len(value) - 1, -1, -1):
        if value[i].isdigit():
            for repl in ("9", "8", "7", "5", "3", "1"):
                if repl == value[i]:
                    continue
                cand = value[:i] + repl + value[i + 1:]
                if norm_bangla(cand) not in norm_art:
                    return cand
    return None


# ---------------------------------------------------------------------------
# Proposal 8 (syllabus): facts_en for every story — fixed fixtures,
# no network, so these run even when the live fetch fails.
# ---------------------------------------------------------------------------
def test_facts_en():
    print("\n== facts_en (Proposal 8) — fixed fixtures ==")
    # English article: facts_en is the same facts.
    en_body = (
        "The International Monetary Fund board has approved a $442 million "
        "tranche for Bangladesh under its loan programme. The approval came "
        "on 13 November 2026 after a review of the country's economic "
        "reforms. Bangladesh's foreign exchange reserves stood at "
        "$26 billion in October 2026.")
    en_facts = [
        {"what": "IMF board approves tranche for Bangladesh", "value": "442",
         "unit": "million", "date": "2026-11-13", "status": "happened",
         "quote": "The International Monetary Fund board has approved a "
                  "$442 million tranche for Bangladesh under its loan programme."},
        {"what": "foreign exchange reserves", "value": "26",
         "unit": "billion", "date": "2026-10-31", "status": "happened",
         "quote": "Bangladesh's foreign exchange reserves stood at "
                  "$26 billion in October 2026."},
    ]
    got = render_facts_en(en_facts, en_body)
    record("facts_en: English article keeps the same facts",
           len(got) == 2 and got[0]["what"] == en_facts[0]["what"]
           and got[0]["value"] == "442" and got[1]["value"] == "26")
    record("facts_en: quotes stay verbatim",
           all(quote_in_text(f["quote"], en_body) for f in got))
    record("facts_en: every number appears in the article",
           all(n in numbers_in(en_body)
               for f in got for n in numbers_in(f["value"] + " "
                                                + f["what"])))
    # Bangla article: glossary rendering, same values/dates/quotes.
    bn_body = (
        "বাংলাদেশ ব্যাংক সুদের হার ৯ শতাংশে কমিয়েছে। রিজার্ভ ২৬ বিলিয়ন "
        "ডলারে দাঁড়িয়েছে।")
    bn_facts = [
        {"what": "বাংলাদেশ ব্যাংক সুদের হার কমিয়েছে", "value": "৯",
         "unit": "শতাংশ", "date": "2026-11-14", "status": "happened",
         "quote": "বাংলাদেশ ব্যাংক সুদের হার ৯ শতাংশে কমিয়েছে।"},
        {"what": "রিজার্ভ", "value": "২৬", "unit": "বিলিয়ন",
         "date": "উল্লেখ নেই", "status": "happened",
         "quote": "রিজার্ভ ২৬ বিলিয়ন ডলারে দাঁড়িয়েছে।"},
    ]
    got = render_facts_en(bn_facts, bn_body)
    record("facts_en: Bangla article renders 'what' in English",
           "Bangladesh Bank" in got[0]["what"] and "interest rate" in got[0]["what"],
           got[0]["what"])
    record("facts_en: Bangla digits normalised to English values",
           got[0]["value"] == "9" and got[1]["value"] == "26",
           str([(f["value"], f["unit"]) for f in got]))
    record("facts_en: units mapped to English",
           got[0]["unit"] == "percent" and got[1]["unit"] == "billion",
           str([f["unit"] for f in got]))
    record("facts_en: 'উল্লেখ নেই' dates become 'not stated'",
           got[1]["date"] == "not stated")
    record("facts_en: same quotes, same statuses",
           all(g["quote"] == f["quote"] and g["status"] == f["status"]
               for g, f in zip(got, bn_facts)))
    record("facts_en: every number appears in the article (normalised)",
           all(n in numbers_in(bn_body)
               for f in got for n in numbers_in(f["value"] + " "
                                                + f["what"])))


def test_indian_grouping():
    """Indian-grouped figures ("Tk22,06,462 crore") must tokenise as ONE
    number. Found 2026-11-15 in the live Step 4/5/6 suite: the old
    NUM_RE matched only "22", leaving ",06,462" in the fact text, which
    Step 5 rightly rejected ("number 06462 not in article")."""
    print("\n== Indian grouping (2026-11-15 fix) — fixed fixture ==")
    body = (
        "On 12 July, the finance minister told parliament that the "
        "government's total outstanding debt stood at Tk22,06,462 crore, "
        "including Tk9,59,311 crore in foreign debt. The Finance Division "
        "said the debt strategy would be reviewed by the Asian Development "
        "Bank.")
    art = {"id": "grp1", "title": "Bangladesh seeks new debt strategy",
           "url": "", "published": "2026-11-14T05:30:00+00:00",
           "body_text": body}
    res = extract_facts(art)
    debt = [f for f in res["facts"]
            if (f.get("value") or "") == "22,06,462"]
    record("Indian grouping: debt fact keeps the full figure",
           len(debt) == 1 and debt[0]["value"] == "22,06,462",
           str([(f["value"], f["what"][:45]) for f in res["facts"]]))
    chk = check({"id": "grp1", "facts": res["facts"]}, body)
    record("Indian grouping: Step 5 passes the extracted facts",
           chk["ok"] and chk["action"] == "keep",
           "action=%s kept=%d" % (chk["action"], chk["facts_kept"]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("== Step 4/5/6 tests — %s ==" % TODAY)
    test_facts_en()
    test_indian_grouping()
    articles = load_articles()
    record("fetched 3 real articles", len(articles) >= 3,
           "%d fetched" % len(articles))
    if len(articles) < 3:
        print("Cannot run the real-article checks without 3 articles.")
        return finish()

    items, bodies = [], {}
    for i, a in enumerate(articles):
        art = {"id": "a%03d" % (i + 1), "title": a["title"],
               "url": a["url"], "published": a.get("published", PUBLISHED),
               "body_text": a["body"]}
        res = extract_facts(art)
        topic = detect_topic(a["title"] + " " + a["body"][:2000])
        item = {"id": art["id"], "facts": res["facts"]}
        items.append(item)
        bodies[art["id"]] = a["body"]
        print("\n" + "=" * 100)
        print("[%s] %s" % (art["id"], a["url"]))
        print("title: %s | topic: %s" % (a["title"], topic))
        print("facts (%d):" % len(res["facts"]))
        for f in res["facts"]:
            print("  - " + json.dumps(f, ensure_ascii=False))
        print("why_important: %s" % res["why_important"])
        chk = check(item, a["body"])
        print("check: " + json.dumps(chk, ensure_ascii=False))
        bn = render_bangla(res["facts"], topic)
        print("bangla_lines:")
        for line in bn["bangla_lines"]:
            print("  - " + line)
        print("why_important_bn: %s" % bn["why_important_bn"])

        record("%s extracted >=2 facts" % art["id"],
               len(res["facts"]) >= 2, "%d facts" % len(res["facts"]))
        record("%s why_important is marked background" % art["id"],
               res["why_important"].startswith("[পটভূমি]"))
        record("%s Step 5 passes its own facts" % art["id"],
               chk["ok"] and chk["action"] in ("keep", "drop_fact"),
               "action=%s kept=%d" % (chk["action"], chk["facts_kept"]))
        record("%s Bangla lines rendered (1-5)" % art["id"],
               1 <= len(bn["bangla_lines"]) <= 5,
               "%d lines" % len(bn["bangla_lines"]))
        record("%s Bangla lines end with ।" % art["id"],
               all(l.endswith("।") for l in bn["bangla_lines"]))
        for f in res["facts"]:
            record("%s value has no 'প্রায়'" % art["id"],
                   "প্রায়" not in (f.get("value") or ""),
                   "value=%r" % f.get("value"))
            record("%s date is absolute, not relative" % art["id"],
                   f.get("date") not in ("আজ", "গতকাল", "এ বছর"),
                   "date=%r" % f.get("date"))
            record("%s quote is a verbatim substring" % art["id"],
                   f.get("quote") and f["quote"] in a["body"],
                   (f.get("quote") or "")[:60])

    # check_batch over the real items
    batch = check_batch(items, bodies)
    record("check_batch returns one result per item",
           len(batch) == len(items)
           and all(b["ok"] for b in batch),
           str([(b["item_id"], b["action"]) for b in batch]))

    # --- Step 5 broken-fact proofs (built from article 1) -------------
    print("\n" + "=" * 100)
    print("Step 5 broken-fact proofs (article a001)")
    body1 = bodies["a001"]
    pairs = first_numbers_with_sentences(body1, 3)
    record("found >=3 numbered sentences for proof facts",
           len(pairs) >= 3, "%d found" % len(pairs))
    if len(pairs) < 3:
        return finish()

    def good_fact(num, sent):
        return {"what": "reported figure", "value": num, "unit": "",
                "date": "2026-11-14", "status": "happened", "quote": sent}

    good_facts = [good_fact(n, s) for n, s in pairs]
    good_item = {"id": "a001", "facts": [dict(f) for f in good_facts]}
    good = check(good_item, body1)
    record("correct facts pass all three checks",
           good["ok"] and good["action"] == "keep"
           and good["facts_kept"] == 3,
           json.dumps(good, ensure_ascii=False))

    # (a) fake quote
    broken = [dict(f) for f in good_facts]
    broken[0]["quote"] = "This sentence was never published in the article."
    res_a = check({"id": "a001", "facts": broken}, body1)
    record("(a) fake quote is caught",
           (not res_a["ok"]) and res_a["facts_kept"] == 2
           and res_a["action"] in ("drop_fact", "verify", "drop")
           and any(f["check"] == "quote" for f in res_a["failures"]),
           json.dumps(res_a["failures"], ensure_ascii=False))

    # (b) wrong number
    broken = [dict(f) for f in good_facts]
    wrong = break_number(broken[1]["value"], body1)
    record("(b) test setup: wrong number differs from article",
           wrong is not None, "value %r -> %r"
           % (broken[1]["value"], wrong))
    if wrong:
        broken[1]["value"] = wrong
        res_b = check({"id": "a001", "facts": broken}, body1)
        record("(b) wrong number is caught",
               (not res_b["ok"]) and res_b["facts_kept"] == 2
               and res_b["action"] in ("drop_fact", "verify", "drop")
               and any(f["check"] == "number" for f in res_b["failures"]),
               json.dumps(res_b["failures"], ensure_ascii=False))

    # (c) invented proper name
    broken = [dict(f) for f in good_facts]
    broken[2]["what"] = "statement by Zorblax Quimble"
    res_c = check({"id": "a001", "facts": broken}, body1)
    record("(c) invented proper name is caught",
           (not res_c["ok"]) and res_c["facts_kept"] == 2
           and res_c["action"] in ("drop_fact", "verify", "drop")
           and any(f["check"] == "name" for f in res_c["failures"]),
           json.dumps(res_c["failures"], ensure_ascii=False))

    # Fewer than 2 facts -> drop
    one = check({"id": "a001", "facts": [dict(good_facts[0])]}, body1)
    record("1-fact item is dropped",
           one["action"] == "drop" and one["facts_kept"] == 1,
           json.dumps(one, ensure_ascii=False))

    # --- Step 6 glossary / bracket proof on fixed demo facts ----------
    print("\nStep 6 glossary proof (fixed demo facts)")
    demo = render_bangla([
        {"what": "IMF board approves tranche for Bangladesh",
         "value": "442", "unit": "million", "date": "2026-11-13",
         "status": "happened", "quote": "x"},
        {"what": "World Bank approves loan for Bangladesh",
         "value": "500", "unit": "million", "date": "2026-11-13",
         "status": "happened", "quote": "y"}], "INT-ORG")
    joined = " ".join(demo["bangla_lines"])
    record("glossary: IMF rendered as আইএমএফ (IMF)",
           "আইএমএফ (IMF)" in joined, joined)
    record("glossary: World Bank rendered as বিশ্বব্যাংক (World Bank)",
           "বিশ্বব্যাংক (World Bank)" in joined, joined)
    record("glossary: common nouns not bracketed (রিজার্ভ plain)",
           "রিজার্ভ (reserves)" not in render_bangla(
               [{"what": "foreign exchange reserves rise", "value": "30",
                 "unit": "billion", "date": "2026-11-13",
                 "status": "happened", "quote": "z"}], "BD-ECO")
           ["bangla_lines"][0])
    record("Bangla lines use Bengali digits",
           any(ch in joined for ch in "০১২৩৪৫৬৭৮৯")
           and "442" not in joined and "500" not in joined, joined)
    record("why_important_bn carries the [পটভূমি] mark",
           demo["why_important_bn"].startswith("[পটভূমি]"))
    return finish()


def finish():
    passed = sum(1 for _n, ok, _d in RESULTS if ok)
    failed = len(RESULTS) - passed
    print("\n" + "=" * 100)
    print("RESULT: %d PASS, %d FAIL (of %d checks)"
          % (passed, failed, len(RESULTS)))
    for name, ok, detail in RESULTS:
        if not ok:
            print("  FAILED: %s — %s" % (name, detail))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
