# Sarangsho Plus Engine v2 — Rebuild Plan

**Goal (Rudro, 14 Nov 2026):** rebuild the news engine for Bangladeshi job-exam candidates (BCS, bank, other govt jobs), free tools only, one step at a time, each step tested before the next. The rubric, glossary and rules live in an editable text file inside the app so they can change without rebuilding.

**Assumption (one line):** Step 3's "one article per call" is implemented as deterministic rubric code, not an LLM call, because the free-only constraint rules out paid APIs and there is no free LLM endpoint in the pipeline.

## Plan (short)

1. **Freeze v1.** `engine/` and the 08:00 daily cron keep running untouched — Edition 9 (15 Nov) is the 7/7 decider. v2 is built in parallel in `engine-v2/` and never touches a live edition until Rudro approves the switch.
2. **One editable rules file.** `engine-v2/rules/RULES.md` holds the rubric, topic list, glossary and style rules; the engine reads it at runtime (no rebuild to change a rule). A mirror copy goes into the app at `app/assets/engine-rules/rules.md` so the rules live inside the app too; the engine copy is canonical.
3. **Build Steps 1–9 in order, one at a time, each tested on real data before the next starts.** The 6 examples in the script are the Step 3 test suite — the decider must classify all 6 correctly.
4. **Where the script is silent, use the style guide** (`~/workspace/current-affairs-study/CURRENT_AFFAIRS_STYLE_GUIDE.md`): ranking triple (top + bottom + Bangladesh position) for report stories, Top News box, days+themes fixture, appointments as their own slot, GK footer, number+unit+date always, and MCQ key shuffling done by the app (never by the judge).
5. **Dry-run a full v2 edition** from real feeds and compare it with a v1 edition on the same day; fix the gaps; hand Rudro the v2 edition + test report. **Switch only on his word.**
6. **Manual-only:** Step 5's optional "new chat" claim check is a human check, not part of the automated pipeline.

## Steps

- Step 1 — Collect (RSS → sitemap → section links; per-source last-success time; dead sources shown in settings; robots.txt; duplicates by 3–5-gram overlap within 48h; cluster size never affects keep/reject)
- Step 2 — Light pre-filter (never hard-delete; lower priority for crime/accident/entertainment; always let through the 10 keywords; rejected headlines logged for weekly scan)
- Step 3 — Decide (headline + first 200 words; JSON keep/maybe/reject + topic + evidence quote; rubric 0–3; tie-breaks; edge rules; 24–36 month window)
- Step 4 — Fact list first (what | value | unit | date | status | exact quote; "উল্লেখ নেই" if unstated; max 3–5 fact lines + one marked "কেন গুরুত্বপূর্ণ")
- Step 5 — Check by app code (quotes verbatim; numbers present; names present; drop or mark "যাচাই করুন"; fewer than 2 facts = drop)
- Step 6 — Bangla style (cholito, glossary terms, English name in brackets on first mention, fixed digit/amount style, facts in English first for English papers)
- Step 7 — Daily page (এক নজরে table; sections in order; brief vs long by score; "আজকের পরিবর্তনগুলো"; maybe-items collapsed; max 15 full items)
- Step 8 — Questions (Q&A from fact list; MCQ with same-type distractors, no "সবগুলো"/"কোনোটিই নয়", no negative stems, year/"as of" in stem, app shuffles key position)
- Step 9 — Study features (yesterday's facts first; missed questions after 1/3/7/14 days; "ভুল রিপোর্ট করুন" button; all Step 5 checks before a fact enters the quiz)

## Files

- `engine-v2/PLAN.md` (this file)
- `engine-v2/rules/RULES.md` (rubric, topics, glossary, style — editable)
- `engine-v2/<step modules>` + `engine-v2/tests/` (one test file per step, run on real data)
- `engine-v2/runs/` (dry-run editions + test reports)
