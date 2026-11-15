#!/usr/bin/env python3
"""Step 3 tests (engine v2) — runnable as: python3 tests/test_step3.py

1. The 6 script examples from CONTRACTS.md (acceptance test): the
   [blanks] are filled with plausible values and decision + score +
   topic are asserted EXACTLY.
2. A real batch of ~30 headlines: engine-v2/runs/2026-11-14/
   articles-2026-11-14.json if Step 1 produced it, else a live Bing
   News RSS sample ("Bangladesh", format=rss) fetched with urllib.
   Every decision is printed with its quote for human eyeballing, plus
   PASS/FAIL invariant counts.
Invariants asserted on every batch item:
  - keep -> non-empty evidence_quote, verbatim substring of input text
  - reject -> empty topic_primary
  - decision/score consistency (keep=2/3, maybe=1, reject=0)
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from step3_decide import decide, decide_batch  # noqa: E402

HERE = Path(__file__).resolve().parent
ENGINE_V2 = HERE.parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "Chrome/120 Safari/537.36 SarangshoPlus/2.0")
BING_RSS = "https://www.bing.com/news/search?q=Bangladesh&format=rss"

FAILURES = []


def check(cond, label):
    print(("  PASS " if cond else "  FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def art(aid, title, summary, **kw):
    d = {"id": aid, "title": title, "summary": summary,
         "url": kw.get("url", ""), "source": kw.get("source", "Test"),
         "section": kw.get("section", ""),
         "published": kw.get("published", "2026-11-14T05:30:00+00:00")}
    d.update(kw)
    return d


def test_examples():
    print("== 6 script examples (acceptance test) ==")
    # 1. Cabinet approves draft ordinance on [subject]
    d = decide(art(
        "ex1", "Cabinet approves draft ordinance on public procurement",
        "The cabinet approved the draft ordinance on public procurement "
        "at a meeting on Thursday."))
    check(d["decision"] == "keep" and d["score"] == 3
          and d["topic_primary"] == "BD-GOV", "1 keep/3/BD-GOV -> %s" % d)
    check("approved the draft ordinance" in d["evidence_quote"],
          "1 quote contains 'approved the draft ordinance' -> %r"
          % d["evidence_quote"])

    # 2. IMF board approves [amount] tranche for Bangladesh
    d = decide(art(
        "ex2", "IMF board approves USD 500 million tranche for Bangladesh",
        "The International Monetary Fund board approved a USD 500 million "
        "tranche for Bangladesh under its loan programme."))
    check(d["decision"] == "keep" and d["score"] == 3
          and d["topic_primary"] == "INT-ORG", "2 keep/3/INT-ORG -> %s" % d)

    # 3. Minister says economy will improve soon
    d = decide(art(
        "ex3", "Minister says economy will improve soon",
        "The finance minister said the economy will improve soon and "
        "people should remain hopeful."))
    check(d["decision"] == "reject" and d["score"] == 0
          and d["topic_primary"] == "", "3 reject/0 -> %s" % d)

    # 4. Bank robbery in [district]
    d = decide(art(
        "ex4", "Bank robbery in Chattogram",
        "Robbers looted a bank branch in Chattogram early on Friday, "
        "police said."))
    check(d["decision"] == "reject" and d["score"] == 0
          and d["topic_primary"] == "", "4 reject/0 -> %s" % d)

    # 5. After [violent crime], High Court issues [N] directives on [subject]
    d = decide(art(
        "ex5", "After a violent crime, High Court issues 5 directives "
               "on land records",
        "After a violent crime that shocked the country, the High Court "
        "issued 5 directives on land records to protect citizens."))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "BD-GOV", "5 keep/2/BD-GOV -> %s" % d)
    check("instrument only" in d["reason"],
          "5 reason notes 'instrument only' -> %r" % d["reason"])

    # 6a. Bangladesh win one match in a bilateral series
    d = decide(art(
        "ex6a", "Bangladesh win one match in a bilateral series",
        "Bangladesh won one match in the bilateral series against the "
        "visitors on Sunday."))
    check(d["decision"] == "maybe" and d["score"] == 1,
          "6a maybe/1 -> %s" % d)

    # 6b. Bangladesh win a major tournament final
    d = decide(art(
        "ex6b", "Bangladesh win a major tournament final",
        "Bangladesh won a major tournament final, lifting the trophy "
        "after a thrilling match."))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "SPORT", "6b keep/2/SPORT -> %s" % d)


def test_robustness():
    print("== robustness ==")
    for label, bad in [
            ("missing title", {"id": "bad1", "summary": "Cabinet approves ordinance"}),
            ("empty dict", {}),
            ("not a dict", "hello"),
            ("None", None),
            ("empty title", {"id": "bad5", "title": "", "summary": "x"})]:
        try:
            d = decide(bad)
            check(d["decision"] == "maybe" and d["score"] == 1,
                  "%s -> maybe/1, no crash (%s)" % (label, d["decision"]))
        except Exception as e:  # decide() must NEVER raise
            check(False, "%s raised %r" % (label, e))
    # Too old -> reject "too old"; no date -> no age rejection.
    d = decide(art("old", "Cabinet approves draft ordinance on procurement",
                   "The cabinet approved the draft ordinance.",
                   published="2020-01-01T00:00:00+00:00"))
    check(d["decision"] == "reject" and d["reason"] == "too old",
          "too old (2020) -> reject 'too old' (%s)" % d)
    d = decide(art("nodate", "Cabinet approves draft ordinance on procurement",
                   "The cabinet approved the draft ordinance.",
                   published=""))
    check(d["decision"] == "keep", "no date -> not rejected on age (%s)" % d)
    # Opinion column -> reject.
    d = decide(art("op", "Budget will change everything",
                   "The budget is the biggest story of the year.",
                   section="editorial"))
    check(d["decision"] == "reject" and d["reason"] == "opinion",
          "editorial section -> reject (%s)" % d)


def test_decisions_2026_11_15():
    """Decision 4 (Support-only cap for ALL topics) and Decision 2
    (editorial scoring for the মতামত slot). Decision 3 (BD-EDU) was
    reversed by Rudro on 2026-11-14 ("No Need") — the topic was removed,
    so the DU/JU/BUET admissions story must not keep."""
    print("== 2026-11-15 decisions (Support-only cap, editorial) ==")
    # BD-EDU removed (Rudro, 2026-11-14): the DU/JU/BUET admissions
    # story must not keep as news.
    d = decide(art(
        "edu1", "DU, JU, BUET shut doors on HSC supplementary candidates",
        "Dhaka University, Jahangirnagar University and BUET will not "
        "admit HSC supplementary candidates this year, officials said."))
    check(d["decision"] != "keep",
          "admissions story -> not kept without BD-EDU (%s)" % d)

    # Support-only cap, all topics: the 14 Nov US flight-delay miss.
    d = decide(art(
        "cap1", "US flight delays and cancellations continue as FAA "
                "services resume",
        "Flight delays and cancellations continued across the United "
        "States on Friday as FAA services resumed, with 1,200 flights "
        "cancelled."))
    check(d["decision"] == "maybe" and d["score"] == 1,
          "flight-delay Support-only -> maybe/1 (%s)" % d)
    # Support-only + digit no longer rescues a keep. (The summary
    # deliberately contains no Strong term anywhere: "exports" would
    # be a Strong BD-ECO hit and the story would rightly keep.)
    d = decide(art(
        "cap2", "United States and Bangladesh hold trade talks",
        "The United States and Bangladesh held trade talks on Friday, "
        "discussing future cooperation with 500 delegates attending."))
    check(d["decision"] == "maybe" and d["score"] == 1,
          "Support-only + number -> still maybe/1 (%s)" % d)
    # Strong hit still keeps (cap does not touch Strong matches).
    d = decide(art(
        "cap3", "Bangladesh Bank cuts policy rate to 9 percent",
        "Bangladesh Bank cut the policy rate to 9 percent on Sunday."))
    check(d["decision"] == "keep" and d["score"] >= 2
          and d["topic_primary"] == "BD-BANK",
          "Strong match still keeps (%s)" % d)
    # Crime + instrument rescue is exempt from the cap.
    d = decide(art(
        "cap4", "After murder, commission formed to probe killings",
        "After a murder that shocked the country, a commission was "
        "formed to probe the killings."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "instrument rescue exempt from cap (%s)" % d)

    # Editorial slot scoring (Decision 2): opinion with a topic
    # scores for the slot; opinion with no topic does not.
    from step3_decide import score_editorial  # noqa: E402
    d = score_editorial(art(
        "ed1", "Budget must protect the poor",
        "The national budget should protect the poor as inflation rises "
        "to 9 percent, writes an economist.",
        section="editorial"))
    check(d["decision"] == "keep" and d["score"] >= 2,
          "editorial with topic scores for slot (%s)" % d)
    d = score_editorial(art(
        "ed2", "Why I love rainy days",
        "Rainy days remind me of childhood and mangoes.",
        section="editorial"))
    check(d["decision"] != "keep",
          "editorial with no topic does not score (%s)" % d)
    # News path still rejects opinion.
    d = decide(art(
        "ed3", "Budget must protect the poor",
        "The national budget should protect the poor as inflation rises "
        "to 9 percent, writes an economist.",
        section="editorial"))
    check(d["decision"] == "reject" and d["reason"] == "opinion",
          "news path still rejects opinion (%s)" % d)


def test_syllabus_proposals():
    """Syllabus proposals 1-6 (2026-11-15, all approved by Rudro)."""
    print("== syllabus proposals 1-6 ==")
    # P1: first / record with a number and a date -> score 3.
    d = decide(art(
        "p1a", "Bangladesh records highest-ever remittance of $2.5 billion in October 2026",
        "Bangladesh recorded its highest-ever monthly remittance of $2.5 billion in October 2026, central bank data showed."))
    check(d["decision"] == "keep" and d["score"] == 3
          and d["topic_primary"] == "BD-ECO",
          "P1 remittance record -> keep/3/BD-ECO (%s)" % d)
    d = decide(art(
        "p1b", "Bangladesh launches first-ever satellite in November 2026",
        "Bangladesh launched its first-ever satellite on 14 November 2026, officials said."))
    check(d["decision"] == "keep" and d["score"] == 3
          and d["topic_primary"] == "SCI",
          "P1 first-ever satellite -> keep/3/SCI (%s)" % d)
    # P1: a first WITHOUT a number and a date is not score 3.
    d = decide(art(
        "p1c", "Bangladesh launches first satellite",
        "Bangladesh launched its first satellite, officials said."))
    check(d["decision"] == "keep" and d["score"] == 2,
          "P1 first without number/date -> keep/2, not 3 (%s)" % d)
    # P1: "first phase" is a schedule, not an achievement.
    d = decide(art(
        "p1d", "First phase of the five year plan begins on 14 November 2026",
        "The first phase of the five year plan begins on 14 November 2026, officials said."))
    check(d["decision"] == "keep" and d["score"] == 2,
          "P1 'first phase' is not a score-3 first (%s)" % d)

    # P2: ranking WITH Bangladesh's position keeps; WITHOUT stays maybe.
    d = decide(art(
        "p2a", "Global Hunger Index: Bangladesh improves its position",
        "Bangladesh improved its position in the Global Hunger Index, with hunger levels falling across the country."))
    check(d["decision"] == "keep" and d["score"] == 2,
          "P2 ranking with BD position -> keep/2 (%s)" % d)
    d = decide(art(
        "p2b", "Global Hunger Index 2026: Bangladesh ranks 88th",
        "Bangladesh ranks 88th out of 125 countries in the Global Hunger Index 2026."))
    check(d["decision"] == "keep" and d["score"] == 3,
          "P2 ranking with BD position + number/date -> keep/3 (%s)" % d)
    d = decide(art(
        "p2c", "Global Hunger Index 2026 released",
        "The Global Hunger Index 2026 was released on Friday, showing progress in South Asia."))
    check(d["decision"] == "maybe" and d["score"] == 1,
          "P2 ranking with no BD position -> maybe/1 (%s)" % d)
    # P2: awards keep the old rule (BD person involved -> keep 2).
    d = decide(art(
        "p2d", "Bangladeshi filmmaker wins award at Cannes",
        "A Bangladeshi filmmaker won an award at the Cannes film festival on Friday."))
    check(d["decision"] == "keep" and d["score"] == 2,
          "P2 award with BD person -> keep/2 (%s)" % d)
    # P2: a substantive story that merely cites an index keeps on merits.
    d = decide(art(
        "p2e", "'Debt by design': Bangladesh's climate debt estimated at $80 per person, new index finds",
        "The country received $2.54 billion in climate finance between 2002 and 2023, but 92% came as loans, the index findings show."))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "ENV",
          "P2 index story with strong substance keeps on merits (%s)" % d)

    # P3: gender & development terms (BD-NATL Strong).
    d = decide(art(
        "p3a", "Government launches women empowerment programme",
        "The government launched a women empowerment programme for rural women on Sunday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-NATL",
          "P3 women empowerment -> keep/BD-NATL (%s)" % d)
    d = decide(art(
        "p3b", "Gender gap in Bangladesh narrows to 0.68, report says",
        "The gender gap in Bangladesh narrowed to 0.68 this year, a new report says."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-NATL",
          "P3 gender gap -> keep/BD-NATL (%s)" % d)

    # P4: climate-diplomacy / climate-finance terms (ENV Strong).
    d = decide(art(
        "p4a", "COP31 agrees $300 billion climate finance deal",
        "COP31 agreed a $300 billion climate finance deal on Saturday after two weeks of talks."))
    check(d["decision"] == "keep" and d["topic_primary"] == "ENV",
          "P4 climate finance -> keep/ENV (%s)" % d)
    d = decide(art(
        "p4b", "Loss and damage fund disburses first payments",
        "The loss and damage fund disbursed its first payments to vulnerable countries this week."))
    check(d["decision"] == "keep" and d["topic_primary"] == "ENV",
          "P4 loss and damage -> keep/ENV (%s)" % d)

    # P5: election-law terms (BD-GOV Strong).
    d = decide(art(
        "p5a", "Election Commission issues guidelines under Representation of the People Order",
        "The Election Commission issued guidelines under the Representation of the People Order on Monday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "P5 RPO -> keep/BD-GOV (%s)" % d)

    # P6: development-plan terms (BD-ECO Strong).
    d = decide(art(
        "p6a", "Vision 2041: government unveils Delta Plan for climate resilience",
        "The government unveiled the Delta Plan under Vision 2041 for climate resilience on Tuesday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-ECO",
          "P6 Vision 2041 / Delta Plan -> keep/BD-ECO (%s)" % d)
    d = decide(art(
        "p6b", "Smart Bangladesh initiative to digitise public services",
        "The Smart Bangladesh initiative will digitise public services across the country, officials said."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-ECO",
          "P6 Smart Bangladesh -> keep/BD-ECO (%s)" % d)


def test_mislabels_2026_11_15():
    """Two confirmed mislabels from the live 15 Nov v2 page (CAT
    verified 09:00), fixed as part of the v2 switch. Each case is
    asserted on the real article plus positive controls: a genuine
    Bangladesh court story must still keep as BD-GOV, and a genuine
    sports record must still keep as SPORT."""
    print("== 2026-11-15 mislabels (foreign court / sports record) ==")
    # MISLABEL 1 — the real article a349: US story, was keep/2/BD-GOV.
    d = decide(art(
        "a349", "At the Supreme Court, Trump aims to cut the power "
                "of judges again", "",
        url="https://www.tbsnews.net/worldbiz/usa/supreme-court-trump-"
            "aims-cut-power-judges-again-1602676",
        source="The Business Standard",
        published="2026-11-15T00:53:48+06:00"))
    check(d["decision"] == "reject" and d["score"] == 0
          and d["topic_primary"] == "",
          "a349 US Supreme Court/Trump -> reject, not BD-GOV (%s)" % d)
    # Same guard, other foreign courts.
    d = decide(art(
        "m1a", "US Attorney General sues tech giants over monopoly",
        "The US Attorney General sued tech giants over monopoly "
        "on Friday."))
    check(d["decision"] == "reject" and d["topic_primary"] == "",
          "US Attorney General -> reject, not BD-GOV (%s)" % d)
    d = decide(art(
        "m1b", "US Supreme Court rules on tariffs",
        "The US Supreme Court ruled on tariffs on Friday."))
    check(d["decision"] == "reject" and d["topic_primary"] == "",
          "US Supreme Court -> reject, not BD-GOV (%s)" % d)
    d = decide(art(
        "m1c", "India's Supreme Court bans single-use plastic nationwide",
        "India's Supreme Court banned single-use plastic nationwide "
        "on Friday."))
    check(d["topic_primary"] != "BD-GOV",
          "India's Supreme Court -> not BD-GOV (%s)" % d)
    d = decide(art(
        "m1d", "মার্কিন সুপ্রিম কোর্ট ট্রাম্পের পক্ষে রায় দিয়েছে",
        "মার্কিন সুপ্রিম কোর্ট ট্রাম্পের পক্ষে রায় দিয়েছে।"))
    check(d["decision"] == "reject" and d["topic_primary"] == "",
          "Bangla US Supreme Court -> reject, not BD-GOV (%s)" % d)
    # Appointment guard: no BD-GOV fallback for a foreign appointment.
    d = decide(art(
        "m1e", "Trump appoints new Supreme Court justice",
        "Trump appointed a new Supreme Court justice on Friday."))
    check(d["topic_primary"] != "BD-GOV",
          "Trump appoints Supreme Court justice -> not BD-GOV (%s)" % d)
    # POSITIVE CONTROL — genuine Bangladesh court stories still keep.
    d = decide(art(
        "m1f", "Supreme Court directs government to publish land "
               "survey report in 30 days",
        "The Supreme Court directed the government to publish the "
        "land survey report within 30 days."))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "BD-GOV",
          "genuine BD Supreme Court (no BD marker) -> keep/2/BD-GOV "
          "(%s)" % d)
    d = decide(art(
        "m1g", "High Court orders Dhaka authorities to clear "
               "Buriganga encroachments",
        "The High Court ordered Dhaka authorities to clear "
        "encroachments on the Buriganga river."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "genuine BD High Court + Dhaka -> keep/BD-GOV (%s)" % d)
    d = decide(art(
        "m1h", "Trump praises Bangladesh Supreme Court verdict",
        "Trump praised the Bangladesh Supreme Court verdict on Friday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "BD marker disables the guard (%s)" % d)

    # MISLABEL 2 — the real article a282: was keep/2/SPORT.
    d = decide(art(
        "a282", "Packing the Blue Zone: Bangladesh registers record "
                "361 delegates at COP31", "",
        url="https://www.tbsnews.net/bangladesh/packing-blue-zone-"
            "bangladesh-registers-record-361-delegates-cop31-1602051",
        source="The Business Standard",
        published="2026-11-14T19:34:37+06:00"))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "INT-ORG"
          and d["topic_secondary"] == "ENV",
          "a282 COP31 delegates record -> keep/2/INT-ORG, ENV second "
          "(%s)" % d)
    # Same guard: a record climate deal is not sport either (a139).
    d = decide(art(
        "a139", "COP31 host Turkey, AIIB strike record $1.6 billion "
                "climate policy deal", "",
        url="https://www.tbsnews.net/worldbiz/europe/cop31-host-turkey-"
            "aiib-strike-record-16-billion-climate-policy-deal-1601231",
        source="The Business Standard",
        published="2026-11-13T10:21:18+06:00"))
    check(d["decision"] == "keep" and d["topic_primary"] == "INT-ORG",
          "a139 record climate deal -> keep/INT-ORG, not SPORT (%s)" % d)
    # The Proposal-1 record signal still works — on the right topic.
    d = decide(art(
        "m2a", "Bangladesh registers record 361 delegates at COP31",
        "Bangladesh registered a record 361 delegates at COP31 in "
        "Antalya on 14 November 2026."))
    check(d["decision"] == "keep" and d["score"] == 3
          and d["topic_primary"] == "INT-ORG",
          "COP31 record + number/date -> keep/3/INT-ORG (%s)" % d)
    d = decide(art(
        "m2b", "কপ৩১-এ বাংলাদেশের রেকর্ড ৩৬১ প্রতিনিধি",
        "কপ৩১-এ বাংলাদেশের রেকর্ড ৩৬১ প্রতিনিধি নিবন্ধিত হয়েছে।"))
    check(d["decision"] == "keep" and d["topic_primary"] == "INT-ORG",
          "Bangla COP31 record -> keep/INT-ORG, not SPORT (%s)" % d)
    # POSITIVE CONTROL — genuine sports records still keep as SPORT.
    d = decide(art(
        "m2c", "Bangladesh set new world record in T20 match against India",
        "Bangladesh set a new world record in the T20 match against "
        "India on Friday."))
    check(d["decision"] == "keep" and d["score"] == 2
          and d["topic_primary"] == "SPORT",
          "T20 world record -> keep/2/SPORT (%s)" % d)
    d = decide(art(
        "m2d", "Tamim breaks record with fastest century in Dhaka Test",
        "Tamim broke the record with the fastest century in the Dhaka "
        "Test on Friday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "SPORT",
          "record century -> keep/SPORT (%s)" % d)
    d = decide(art(
        "m2e", "Bangladesh win SAFF final, set new record",
        "Bangladesh won the SAFF final and set a new record on Friday."))
    check(d["decision"] == "keep" and d["topic_primary"] == "SPORT",
          "final win + record -> keep/SPORT (%s)" % d)


def test_bangla_crime_terms():
    print("== Bangla crime terms (Level 1 wiring, 2026-11-15) ==")
    # a951 (15 Nov, PA Bangla sitemap): a case against an MP's father
    # for vandalism, assault, looting and land-grab — pure crime, no
    # instrument. The old _CRIME_TERMS had no Bangla case/crime words,
    # so the "সংসদ" Strong match kept it as BD-GOV/2 and it reached
    # the page as CA11.
    d = decide(art(
        "c1", "নুসরাতের বাবার বিরুদ্ধে মামলা : তিন সাক্ষীর দুজনই "
        "বললেন, তাঁরা কিছুই জানেন না",
        "জাতীয় নাগরিক পার্টির যুগ্ম আহ্বায়ক ও সংরক্ষিত নারী আসনের "
        "সংসদ সদস্য নুসরাত তাবাসসুমের বাবা আবদুল হালিমের বিরুদ্ধে "
        "বাড়িঘর ভাঙচুর, মারধর, মালামাল লুট ও জমি দখলের অভিযোগে করা "
        "মামলার তিন সাক্ষীর দুজনই দাবি করেছেন, এ বিষয়ে তাঁরা কিছুই "
        "জানেন না।"))
    check(d["decision"] == "reject" and d["score"] == 0,
          "MP's father case (crime, no instrument) -> reject/0 (%s)" % d)
    # a720 (15 Nov, Jugantor): compensation suit over a boat collision.
    d = decide(art(
        "c2", "প্রমোদতরিতে ট্যাংকারের ধাক্কা, ১০ লাখ ডলারের ক্ষতিপূরণ "
        "চেয়ে মামলা",
        "প্রমোদতরিতে ট্যাংকারের ধাক্কায় ক্ষতি হওয়ায় ১০ লাখ ডলারের "
        "ক্ষতিপূরণ চেয়ে মামলা করা হয়েছে।"))
    check(d["decision"] == "reject" and d["score"] == 0,
          "compensation suit over collision -> reject/0 (%s)" % d)
    # a966 (15 Nov, PA Bangla): parliament debate over handcuffs in a
    # war-crimes case. মামলা is present, but "আইনমন্ত্রী" carries the
    # আইন instrument term, so the crime rule must not reject it.
    d = decide(art(
        "c3", "জিয়াউলের হাতে হাতকড়া না থাকায় সংসদে ক্ষোভ, আইনমন্ত্রী "
        "বললেন পুনরাবৃত্তি হবে না",
        "মানবতাবিরোধী অপরাধের মামলায় আদালতে হাজির করার সময় সাবেক "
        "সেনা কর্মকর্তা জিয়াউল আহসানকে হাতকড়া না পরানোয় ক্ষোভ প্রকাশ "
        "করেছেন বিএনপির সংসদ সদস্য তাহসিনা রুশদী।"))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "parliament debate + law-minister instrument -> keep/BD-GOV "
          "(%s)" % d)
    # POSITIVE CONTROL — crime WITH a real instrument keeps.
    d = decide(art(
        "c4", "ধর্ষণ মামলায় হাইকোর্টের নির্দেশনা",
        "ধর্ষণ মামলার বিচারে হাইকোর্ট ৩টি নির্দেশনা দিয়েছেন। আদালত "
        "বলেছেন, ভুক্তভোগীর পরিচয় গোপন রাখতে হবে।"))
    check(d["decision"] == "keep" and d["topic_primary"] == "BD-GOV",
          "crime + court directive (instrument) -> keep/BD-GOV (%s)" % d)
    # POSITIVE CONTROL — the narrowed disaster carve-out still rescues
    # a genuine disaster that carries a crime word ("দুর্ঘটনা").
    # Topic is PEOPLE (মৃত্যু is a PEOPLE Strong term) with ENV
    # secondary; what matters is the keep, not which topic wins.
    d = decide(art(
        "c5", "বন্যায় নৌকা দুর্ঘটনায় ৫ জনের মৃত্যু",
        "বন্যার পানিতে নৌকা দুর্ঘটনায় ৫ জনের মৃত্যু হয়েছে। জেলায় "
        "বন্যা পরিস্থিতির অবনতি হয়েছে।"))
    check(d["decision"] == "keep"
          and "ENV" in (d["topic_primary"], d["topic_secondary"]),
          "flood + accident word -> keep, ENV recognised (%s)" % d)


def _load_step1_batch():
    p = ENGINE_V2 / "runs" / "2026-11-14" / "articles-2026-11-14.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        arts = data.get("articles", []) if isinstance(data, dict) else data
        print("batch source: Step 1 file %s (%d articles)" % (p, len(arts)))
        return arts[:30], "step1-file"
    return None, None


def _fetch_bing_batch(n=30):
    req = urllib.request.Request(BING_RSS, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    root = ET.fromstring(raw)
    arts = []
    for i, item in enumerate(root.iter("item")):
        if len(arts) >= n:
            break
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        desc = html.unescape(re.sub(r"<[^>]+>", " ", desc))
        desc = re.sub(r"\s+", " ", desc).strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        arts.append({"id": "a%03d" % (len(arts) + 1), "title": title,
                     "summary": desc[:600], "url": link, "source": "Bing News",
                     "section": "", "published": pub, "found_via": "bing"})
    print("batch source: live Bing News RSS (%d articles)" % len(arts))
    return arts


def test_real_batch():
    print("== real batch (~30 headlines) ==")
    arts, src = _load_step1_batch()
    if arts is None:
        try:
            arts = _fetch_bing_batch(30)
            src = "bing-rss"
        except Exception as e:
            print("  !! live fetch failed: %r — batch test skipped" % e)
            print("  (6 examples + robustness above still ran)")
            return
    decisions = decide_batch(arts)
    dist = Counter(d["decision"] for d in decisions)
    topics = Counter(d["topic_primary"] for d in decisions if d["topic_primary"])
    n_pass = n_fail = 0
    for a, d in zip(arts, decisions):
        text = (a.get("title", "") + " " + a.get("summary", "")).strip()
        ok = True
        msgs = []
        if d["decision"] == "keep":
            if not d["evidence_quote"]:
                ok, msgs = False, msgs + ["empty quote"]
            elif d["evidence_quote"] not in text:
                ok, msgs = False, msgs + ["quote not verbatim"]
            if d["score"] not in (2, 3):
                ok, msgs = False, msgs + ["keep but score %s" % d["score"]]
            if not d["topic_primary"]:
                ok, msgs = False, msgs + ["keep but no topic"]
        elif d["decision"] == "maybe":
            if d["score"] != 1:
                ok, msgs = False, msgs + ["maybe but score %s" % d["score"]]
        elif d["decision"] == "reject":
            if d["score"] != 0:
                ok, msgs = False, msgs + ["reject but score %s" % d["score"]]
            if d["topic_primary"]:
                ok, msgs = False, msgs + ["reject but topic set"]
        else:
            ok, msgs = False, msgs + ["bad decision %r" % d["decision"]]
        if ok:
            n_pass += 1
        else:
            n_fail += 1
        print("[%s] %s/%d %-7s | %s"
              % ("ok " if ok else "BAD", d["id"], d["score"],
                 d["topic_primary"] or "-", a["title"][:72]))
        print("      quote: %r | reason: %s%s"
              % (d["evidence_quote"], d["reason"],
                 (" | " + "; ".join(msgs)) if msgs else ""))
    print("batch invariants: PASS=%d FAIL=%d (of %d)"
          % (n_pass, n_fail, len(decisions)))
    print("distribution: keep=%d maybe=%d reject=%d"
          % (dist.get("keep", 0), dist.get("maybe", 0), dist.get("reject", 0)))
    print("top topics: %s" % dict(topics.most_common(8)))
    if n_fail:
        FAILURES.append("real batch: %d invariant failures" % n_fail)


def main():
    test_examples()
    test_robustness()
    test_decisions_2026_11_15()
    test_syllabus_proposals()
    test_mislabels_2026_11_15()
    test_bangla_crime_terms()
    test_real_batch()
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
