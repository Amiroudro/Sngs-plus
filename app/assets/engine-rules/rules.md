# Sarangsho Plus Engine v2 — RULES

**Canonical copy.** This file is the engine's rules: rubric, topic list, decider
lexicon, glossary and style rules. The engine reads it at runtime, so a rule
can change without rebuilding anything. A mirror copy lives in the app at
`app/assets/engine-rules/rules.md` — the mirror is for display inside the app
only; **this file (`engine-v2/rules/RULES.md`) is canonical**. If the two ever
disagree, this file wins; re-copy it to the app after any edit.

**How to edit.** Plain text. Keep the section headings exactly as they are —
the engine parses them. Inside a topic block, lines starting with `Strong:`
and `Support:` are comma-separated match terms (English and Bangla, lowercased
by the engine; Bangla terms are matched after NFC normalisation and digit
normalisation). Add or remove terms freely; do not rename topic IDs.

**Digit style (Step 6, Rudro to confirm):** Bengali digits in Bengali text,
Western digits in English text. Amounts exactly as printed — never convert,
round, or write "প্রায়".

---

## TOPICS

Each topic: ID, what counts, what does NOT count. The decider assigns
`topic_primary` (and `topic_secondary` when a second topic clearly applies).

### TOPIC BD-GOV
What counts: constitution, parliament, laws/ordinances, president/PM/cabinet,
judiciary, Election Commission, reform commissions, local government, RTI,
e-governance.
NOT this: party quarrels, statements without a decision.
Strong: ordinance, অধ্যাদেশ, constitution, সংবিধান, parliament, সংসদ,
election commission, নির্বাচন কমিশন, reform commission, সংস্কার কমিশন,
supreme court, সুপ্রিম কোর্ট, high court, হাইকোর্ট, chief justice,
প্রধান বিচারপতি, cabinet, মন্ত্রিসভা, gazette, গেজেট, bill passed,
আইন পাস, local government, স্থানীয় সরকার, right to information,
তথ্য অধিকার, e-governance, ই-গভর্ন্যান্স, referendum, গণভোট,
attorney general, অ্যাটর্নি জেনারেল, tribunal, ট্রাইব্যুনাল,
ordinance promulgated, অধ্যাদেশ জারি, representation of the people
order, rpo, election observation, নির্বাচন পর্যবেক্ষণ, electoral law,
নির্বাচনী আইন
Support: president, রাষ্ট্রপতি, prime minister, প্রধানমন্ত্রী,
chief adviser, প্রধান উপদেষ্টা, adviser, উপদেষ্টা, ministry,
মন্ত্রণালয়, minister, মন্ত্রী, law, আইন, judiciary, বিচার বিভাগ,
court directive, আদালতের নির্দেশ, election, নির্বাচন, voter,
ভোটার, polling, ভোটগ্রহণ, commission, কমিশন, secretary, সচিব,
appointment, নিয়োগ, policy, নীতি, directive, নির্দেশনা

### TOPIC BD-ECO
What counts: budget, GDP, inflation, reserves, remittance, export-import,
poverty, ADP/projects, industry, garments, agriculture, census.
NOT this: price of a single item in one market.
Strong: budget, বাজেট, gdp, জিডিপি, inflation, মূল্যস্ফীতি, reserves,
রিজার্ভ, remittance, রেমিট্যান্স, export, রপ্তানি, import, আমদানি,
poverty rate, দারিদ্র্যের হার, adp, এডিপি, census, আদমশুমারি,
per capita income, মাথাপিছু আয়, trade deficit, বাণিজ্য ঘাটতি,
foreign exchange, বৈদেশিক মুদ্রা, economic growth, অর্থনৈতিক প্রবৃদ্ধি,
vision 2041, ভিশন ২০৪১, delta plan, ডেল্টা প্ল্যান, smart bangladesh,
স্মার্ট বাংলাদেশ, five year plan, পঞ্চবার্ষিক পরিকল্পনা,
adp implementation, এডিপি বাস্তবায়ন
Support: economy, অর্থনীতি, garment, পোশাক, rmg, তৈরি পোশাক,
agriculture, কৃষি, industry, শিল্প, project, প্রকল্প, price,
মূল্য, market, বাজার, investment, বিনিয়োগ, tax, কর, revenue,
রাজস্ব, employment, কর্মসংস্থান, unemployment, বেকারত্ব, wage,
মজুরি, food price, খাদ্যের দাম, production, উৎপাদন

### TOPIC BD-BANK
What counts: Bangladesh Bank policy, interest rates, bank mergers, NPL,
digital finance, financial cyber security.
NOT this: a bank robbery or one branch event.
Strong: bangladesh bank, বাংলাদেশ ব্যাংক, interest rate, সুদের হার,
policy rate, নীতি সুদহার, bank merger, ব্যাংক একীকরণ, non-performing loan,
খেলাপি ঋণ, npl, monetary policy, মুদ্রানীতি, reserve requirement,
banking reform, ব্যাংকিং সংস্কার, digital payment, ডিজিটাল পেমেন্ট,
mobile financial service, মোবাইল ব্যাংকিং, central bank, কেন্দ্রীয় ব্যাংক
Support: bank, ব্যাংক, loan, ঋণ, deposit, আমানত, credit, ঋণদান,
financial, আর্থিক, branch, শাখা, atm, booming, islamic bank,
ইসলামী ব্যাংক, microfinance, ক্ষুদ্রঋণ, financial inclusion,
আর্থিক অন্তর্ভুক্তি, cyber security, সাইবার নিরাপত্তা

### TOPIC BD-NATL
What counts: national awards, institutions, culture, NGOs, women's development.
NOT this: local events or gossip.
Strong: national award, জাতীয় পুরস্কার, ekushey padak, একুশে পদক,
swadhinata padak, স্বাধীনতা পুরস্কার, bangla academy, বাংলা একাডেমি,
national museum, জাতীয় জাদুঘর, women's development, নারী উন্নয়ন,
ngo affairs bureau, এনজিও বিষয়ক ব্যুরো, gender equality, নারী অধিকার,
women empowerment, নারীর ক্ষমতায়ন, gender gap, লিঙ্গ বৈষম্য
Support: culture, সংস্কৃতি, heritage, ঐতিহ্য, institution, প্রতিষ্ঠান,
award, পুরস্কার, festival, উৎসব, language, ভাষা, literature,
সাহিত্য, museum, জাদুঘর, women, নারী, youth, যুব, development,
উন্নয়ন, social welfare, সমাজকল্যাণ

### TOPIC INT-ORG
What counts: UN, peacekeeping, ICJ, World Bank, IMF, ADB, WTO, G7/G20,
BRICS, SAARC, BIMSTEC, ASEAN, EU, NATO, OIC, AU, COP.
NOT this: routine visits with no outcome.
Strong: united nations, জাতিসংঘ, un security council, নিরাপত্তা পরিষদ,
peacekeeping, শান্তিরক্ষা, international court of justice, আইসিজে,
world bank, বিশ্বব্যাংক, imf, আইএমএফ, asian development bank, এডিবি,
wto, বিশ্ব বাণিজ্য সংস্থা, brics, ব্রিকস, saarc, সার্ক, bimstec, বিমসটেক,
asean, আসিয়ান, european union, ইউরোপীয় ইউনিয়ন, nato, ন্যাটো, oic,
ওআইসি, african union, আফ্রিকান ইউনিয়ন, cop, কপ, g7, g20,
international monetary fund, আন্তর্জাতিক মুদ্রা তহবিল
Support: international organisation, আন্তর্জাতিক সংস্থা, summit, সম্মেলন,
treaty, চুক্তি, convention, কনভেনশন, protocol, প্রটোকল, member state,
সদস্য রাষ্ট্র, resolution, প্রস্তাব, assembly, অধিবেশন

### TOPIC INT-REL
What counts: relations of USA, China, Russia, India, Japan, UK, EU;
Bangladesh-India (water, border), Rohingya; wars, conflicts, peace deals;
new heads of state.
NOT this: opinion.
Strong: rohingya, রোহিঙ্গা, peace deal, শান্তি চুক্তি, ceasefire,
যুদ্ধবিরতি, border killing, সীমান্ত হত্যা, water sharing, পানি বণ্টন,
teesta, তিস্তা, head of state, রাষ্ট্রপ্রধান, new president,
নতুন রাষ্ট্রপতি, new prime minister, নতুন প্রধানমন্ত্রী, war,
যুদ্ধ, conflict, সংঘাত, invasion, আগ্রাসন, sanctions, নিষেধাজ্ঞা,
airstrike, air strike, বিমান হামলা, bombing, বোমা হামলা,
missile strike, ক্ষেপণাস্ত্র হামলা, shelling, গোলাবর্ষণ,
military offensive, সামরিক অভিযান
Support: united states, যুক্তরাষ্ট্র, china, চীন, russia, রাশিয়া,
india, ভারত, japan, জাপান, united kingdom, যুক্তরাজ্য, bilateral,
দ্বিপাক্ষিক, diplomatic, কূটনৈতিক, foreign minister, পররাষ্ট্রমন্ত্রী,
embassy, দূতাবাস, visit, সফর, relations, সম্পর্ক, deal, চুক্তি,
talks, আলোচনা, border, সীমান্ত

### TOPIC ENV
What counts: climate change, major disasters (name, date, size, deaths).
Strong: climate change, জলবায়ু পরিবর্তন, cyclone, ঘূর্ণিঝড়,
flood, বন্যা, earthquake, ভূমিকম্প, disaster, দুর্যোগ, death toll,
মৃতের সংখ্যা, global warming, বৈশ্বিক উষ্ণায়ন, carbon emission,
কার্বন নিঃসরণ, sea level, সমুদ্রপৃষ্ঠ, drought, খরা,
climate diplomacy, জলবায়ু কূটনীতি, loss and damage, ক্ষতিপূরণ,
climate finance, জলবায়ু অর্থায়ন, climate adaptation, জলবায়ু অভিযোজন,
cop29, cop30, cop31
Support: environment, পরিবেশ, weather, আবহাওয়া, rain, বৃষ্টি,
river erosion, নদীভাঙন, pollution, দূষণ, forest, বন, wildlife,
বন্যপ্রাণী, sundarbans, সুন্দরবন

### TOPIC SCI
What counts: space missions, discoveries, vaccines/diseases (dengue,
cancer, HIV), biotech, energy, ICT, AI, cyber security.
Strong: space mission, মহাকাশ অভিযান, satellite, উপগ্রহ, vaccine,
টিকা, dengue, ডেঙ্গু, cancer, ক্যানসার, hiv, এইচআইভি, discovery,
আবিষ্কার, artificial intelligence, কৃত্রিম বুদ্ধিমত্তা, ai, এআই,
cyber attack, সাইবার হামলা, nuclear, পারমাণবিক, renewable energy,
নবায়নযোগ্য জ্বালানি, solar, সৌর, hydrogen, হাইড্রোজেন
Support: science, বিজ্ঞান, technology, প্রযুক্তি, research, গবেষণা,
disease, রোগ, health, স্বাস্থ্য, medicine, ওষুধ, energy, জ্বালানি,
electricity, বিদ্যুৎ, ict, আইসিটি, digital, ডিজিটাল, computer,
কম্পিউটার, internet, ইন্টারনেট, innovation, উদ্ভাবন

### TOPIC SPORT
What counts: major tournaments, records, winners, schedules.
NOT this: ordinary bilateral match results.
Strong: world cup, বিশ্বকাপ, olympics, অলিম্পিক, asian games,
এশিয়ান গেমস, tournament final, টুর্নামেন্ট ফাইনাল, champion,
চ্যাম্পিয়ন, record, রেকর্ড, gold medal, স্বর্ণপদক
Support: cricket, ক্রিকেট, football, ফুটবল, hockey, হকি, match,
ম্যাচ, series, সিরিজ, player, খেলোয়াড়, team, দল, win, জয়,
tournament, টুর্নামেন্ট, fifa, ফিফা, icc, আইসিসি

### TOPIC PEOPLE
What counts: major awards (Nobel etc.), top appointments, deaths of
notable people, international days with their themes.
Strong: nobel, নোবেল, nobel prize, নোবেল পুরস্কার, died, মারা গেছেন,
passed away, মৃত্যু, appointed, নিযুক্ত, international day,
আন্তর্জাতিক দিবস, world day, বিশ্ব দিবস, theme, প্রতিপাদ্য
Support: award, পুরস্কার, appointment, নিয়োগ, birthday, জন্মদিন,
anniversary, বার্ষিকী, celebrity, তারকা, leader, নেতা, scientist,
বিজ্ঞানী, writer, লেখক, artist, শিল্পী

---

## RUBRIC (Step 3)

Score the article on headline + first 200 words only.

- **0 = unrelated.** No named topic is supported. Reject.
- **1 = same broad area, no named topic.** Maybe.
- **2 = clearly supports a named topic.** Keep (brief format in Step 7).
- **3 = directly on a topic AND likely to be asked.** New law/ordinance/
  commission, treaty, appointment to a constitutional or major economic
  body, official statistic, development involving a named international
  organisation, or a first / record / ranking with a number and a date.
  (A ranking scores 3 only when it states Bangladesh's position — see
  the awards/rankings rule below.) Keep (longer format in Step 7).

Decisions: keep = 2 or 3. maybe = 1. reject = 0.

**Every keep needs a topic ID and an exact quote from the article; no
quote = reject.** The quote must be a substring of the headline or the
first-200-words text the decider was given.

**Tie-breaks** (in order): (1) the topic of the headline's main subject;
(2) the more specific topic; (3) the earlier-listed topic in the TOPICS
section above.

**If evidence is weak, REJECT.** Do not guess a topic.

**Support-only cap:** a hit on Support terms only (no Strong term
matched in any topic) scores at most 1 (maybe), for ALL topics.
Exception: a crime/accident story rescued by an instrument
(law/ordinance/commission/directive/policy) keeps whatever score its
concrete signals (action verb, number, 2+ terms) give it.

**Minor stories:** also keep a minor story if it touches an established
institution, treaty or concept — NATO, BRICS, UN, IMF, WTO, Green Climate
Fund, hydrogen, space missions — because exams ask these with a news hook.
(Score 2, topic of the institution/concept.)

**Awards, world indexes and rankings = "maybe"** by default. An award
keeps (score 2, topic PEOPLE or the relevant topic) when a Bangladeshi
institution or person is involved. A ranking/index keeps (score 2) when
the article states Bangladesh's rank/position; a ranking that states
Bangladesh's position AND carries a number and a date scores 3 (the
first/record/ranking signal above). A ranking with no Bangladesh
position stays "maybe".

**Time window:** keep items from the last 24–36 months; show the last
12–18 months first. Items older than 36 months are rejected (score 0,
reason "too old").

**Status labels (every kept item gets one):** happened / scheduled /
proposed / forecast. Never write a scheduled event as if it already
happened. Scheduled = a dated future event. Proposed = announced but not
decided. Forecast = a prediction or projection. Otherwise happened.

---

## EDGE RULES

- A story that began as a crime or accident is kept ONLY if it produced a
  law, ordinance, commission, court directive or policy. Then summarise
  only that instrument, not the incident.
- Different papers give different numbers: never merge or average. Show
  each number with its source and date, mark the item "বিতর্কিত", and keep
  it out of quizzes until resolved. Prefer the official source for
  official figures.
- Opinion columns: reject, unless they only repeat an official figure;
  then use the original report. (The মতামত slot in Step 7 is the only
  place opinion appears — see "7. মতামত slot" under STEP 7.)
- A bank robbery, a single branch event, or one market's price of one
  item is NOT BD-BANK / BD-ECO, even though it shares the word "bank"
  or "price".
- A minister saying the economy "will improve soon" (no number, no
  decision) is reject, 0.
- Bangladesh winning one match in a bilateral series is maybe, 1.
  Bangladesh winning a major tournament final is keep, 2, SPORT.
- Foreign-court guard: a bare court term (Supreme Court, High Court,
  Chief Justice, Attorney General, tribunal) counts as BD-GOV only
  when the story is anchored to Bangladesh. If the headline names a
  foreign leader or country and nothing in the article mentions
  Bangladesh/Dhaka, the term does not count — a US Supreme Court story
  is not BD-GOV, and appointing a foreign Supreme Court justice is not
  a Bangladeshi appointment. (2026-11-15: "At the Supreme Court, Trump
  aims to cut the power of judges again" was wrongly kept 2 as BD-GOV.)
- Sports-record guard: "record" / "রেকর্ড" counts as a SPORT Strong
  term only when the article carries a sports anchor (another sports
  term, or a word like century/wicket/goal/championship/medal). A
  record number of delegates, a record deal or a record loss is not a
  sports record. (2026-11-15: "Bangladesh registers record 361
  delegates at COP31" was wrongly filed as SPORT; it is climate
  diplomacy — INT-ORG/ENV.)

---

## STEP 2 — PRE-FILTER

Never hard-delete. Lower the priority of items from crime, accident and
entertainment sections. **Always let through** any item containing one of
these 10 keywords (Bangla or English): মন্ত্রণালয়, অধ্যাদেশ, আইন, বাজেট,
চুক্তি, জিডিপি, মূল্যস্ফীতি, বাংলাদেশ ব্যাংক, নির্বাচন কমিশন, জাতিসংঘ.
Every deprioritised headline is written to the weekly-scannable log
(`runs/<date>/prefilter-log-<date>.md`).

Deprioritise terms (crime / accident / entertainment):
murder, হত্যা, robbery, ডাকাতি, rape, ধর্ষণ, accident, দুর্ঘটনা,
crash, সংঘর্ষ, fire, আগুন, suicide, আত্মহত্যা, arrested, গ্রেপ্তার,
entertainment, বিনোদন, film, সিনেমা, actor, অভিনেতা, actress,
অভিনেত্রী, singer, গায়ক, cricket match, ক্রিকেট ম্যাচ (ordinary),
gossip, গসিপ, scandal, কেলেঙ্কারি.

---

## STEP 4 — FACT LIST

From the article only, list each fact as: what | value | unit | date |
status | exact supporting quote. If something is not stated, write
"উল্লেখ নেই". Then write at most 3–5 short fact lines ONLY from this
list, plus one line "কেন গুরুত্বপূর্ণ" (this line may be background;
mark it as such, e.g. prefix "[পটভূমি]").

Rules: copy numbers, units and currency exactly (টাকা, কোটি, লাখ, USD);
never convert, round or say "প্রায়". Use names and titles exactly as
printed; never add a name or post the article does not contain, even if
you know it. Keep the article's tense and hedges. Attribute opinions to
the speaker. Use only absolute dates from the article's date line (the
app passes the date in); never write "আজ", "গতকাল", "এ বছর".

**`facts_en` (translation / precis practice):** for every kept story
the edition also carries an English fact list, same shape as the facts
above. For English-language articles it is the same facts (already
English). For Bangla-language articles it is the translator's
rendering of the same verified facts: same value, unit, date and
status, same verbatim quote, with the "what" rendered in English via
the glossary. Step 5 rules apply to the numbers and names in it — they
must appear in the article.

---

## STEP 5 — CHECK BY CODE

(a) Every quote must appear exactly inside the article text.
(b) Every number in the summary (after mapping Bangla digits to English
and removing commas) must appear in the article.
(c) Every proper name must appear in the article.
Any failure: delete that fact, or mark the item "যাচাই করুন". If fewer
than 2 facts remain, drop the item.
The optional "new chat" claim check (give the AI the article and ONE
claim and ask "Does the text state this? Quote it.") is MANUAL-ONLY —
never automate it.

---

## STEP 6 — BANGLA STYLE

- Standard cholito news Bangla, not sadhu; no word-for-word translation.
- English name in brackets on first mention of foreign names/organisations.
- One fixed style for digits and amounts (see the digit style at the top
  of this file).
- Use the glossary below for fixed terms.
- If unsure how to spell a name, copy it from the article.
- For English-language papers: extract the facts in English first, then
  write Bangla from the fact list.

---

## GLOSSARY (fixed terms — use exactly these)

মন্ত্রণালয় = ministry; অধ্যাদেশ = ordinance; উপদেষ্টা = adviser;
রিজার্ভ = reserves; বাংলাদেশ ব্যাংক = Bangladesh Bank;
নির্বাচন কমিশন = Election Commission; জাতিসংঘ = United Nations;
বাজেট = budget; জিডিপি = GDP; মূল্যস্ফীতি = inflation;
চুক্তি = agreement / treaty; আইন = law / act; সংসদ = parliament;
সংবিধান = constitution; সুপ্রিম কোর্ট = Supreme Court;
হাইকোর্ট = High Court; প্রধান বিচারপতি = Chief Justice;
মন্ত্রিসভা = cabinet; গেজেট = gazette; রেমিট্যান্স = remittance;
রপ্তানি = export; আমদানি = import; মুদ্রানীতি = monetary policy;
সুদের হার = interest rate; খেলাপি ঋণ = non-performing loan;
শান্তিরক্ষা = peacekeeping; বিশ্বব্যাংক = World Bank;
আইএমএফ = IMF; এডিবি = ADB; বিশ্ব বাণিজ্য সংস্থা = WTO;
ব্রিকস = BRICS; সার্ক = SAARC; বিমসটেক = BIMSTEC; আসিয়ান = ASEAN;
ইউরোপীয় ইউনিয়ন = European Union; ন্যাটো = NATO; ওআইসি = OIC;
জলবায়ু পরিবর্তন = climate change; কৃত্রিম বুদ্ধিমত্তা = artificial
intelligence; নোবেল পুরস্কার = Nobel Prize; প্রতিপাদ্য = theme;
নিযুক্ত = appointed; মৃত্যু = death; যুদ্ধবিরতি = ceasefire;
রোহিঙ্গা = Rohingya; তিস্তা = Teesta; ডেঙ্গু = dengue;
পারমাণবিক = nuclear; নবায়নযোগ্য জ্বালানি = renewable energy.

---

## STEP 7 — DAILY PAGE

1. "আজকের এক নজরে": table of top items (event | date | key fact | status).
2. Sections in order: বাংলাদেশ (রাজনীতি, আইন, প্রশাসন) →
   অর্থনীতি ও ব্যাংকিং → আন্তর্জাতিক → বিজ্ঞান, প্রযুক্তি ও পরিবেশ →
   খেলাধুলা, পুরস্কার, দিবস ও নিয়োগ. Skip empty ones.
3. Each item: one-line headline (subject + action), 1–3 fact lines with
   date and source tag, status label, "কেন গুরুত্বপূর্ণ", source links.
   Short brief format for score-2 items, longer for score-3.
4. "আজকের পরিবর্তনগুলো মনে রাখুন": a short list of what changed today.
5. "maybe" items appear as headline + link only, in a collapsed list.
6. Max 15 full items a day.
7. মতামত slot: ONE editorial/opinion of the day, scored separately
   from the news rubric (same topic scoring, but the opinion-reject
   does not apply). Best editorial of the day only, and only if it
   scores 2 or higher; otherwise the slot stays empty and the page
   says why. Rendered in its own labelled মতামত (opinion) slot,
   OUTSIDE the 15 news items and never counted in the 15. Clearly
   labelled opinion; show headline, source, link and the feed
   summary only — never full opinion text.
8. `focus_paragraph` (optional, score-3 items only): 3–4 sentences
   built ONLY from the item's verified fact list + its [পটভূমি] line,
   in the shape প্রসঙ্গ → তথ্য → বিশ্লেষণ → উপসংহার. No new facts:
   the context sentence is the headline, the fact sentences are the
   item's own fact lines, the analysis sentence is the [পটভূমি] line,
   and the closing sentence repeats the key fact as a memory hook.
   Omit the field when the fact list cannot support 3 sentences
   (fewer than 1 fact, or no [পটভূমি] line). Every number in it must
   pass the Step 5 check: headline numbers that do not appear in the
   article body are dropped (slug-derived headlines sometimes express
   a figure in a different unit than the body, e.g. "Tk159 Crore"
   vs "1.59 billion") — the headline words stay, the untraceable
   number goes.

Section mapping (topic → daily-page section):
BD-GOV, BD-NATL → বাংলাদেশ (রাজনীতি, আইন, প্রশাসন)
BD-ECO, BD-BANK → অর্থনীতি ও ব্যাংকিং
INT-ORG, INT-REL → আন্তর্জাতিক
ENV, SCI → বিজ্ঞান, প্রযুক্তি ও পরিবেশ
SPORT, PEOPLE → খেলাধুলা, পুরস্কার, দিবস ও নিয়োগ

Style-guide additions (from the current-affairs study): ranking triple
(top + bottom + Bangladesh position) for every report/index story; a
Top News box (the edition's ~10 best items, one dated line each);
days+themes as a standing fixture; appointments as their own slot
(post : name; date); a GK footer (one static fact per edition); every
number carries a unit and a date.

---

## STEP 8 — QUESTIONS

Q&A: one fact per question; the answer must come from the fact list.
MCQ: stem + options ক খ গ ঘ + key + the quoted source sentence + one
line on why each wrong option fails. Reject any MCQ whose quote fails
the Step 5 check. Wrong options must be the same type and grammar as
the key (all names, all dates, all organisations); for numbers use close
values; for names use real related bodies. No "সবগুলো" / "কোনোটিই নয়"
options and no negative stems. Put the year or "as of" date in the stem
for time-sensitive facts. **The app, not the engine, shuffles the key
position** — the engine outputs the key in canonical order and never
shuffles. Mostly recall questions, a few analytical ones.

Analytical questions (syllabus Proposal 9): at most 2 per edition,
only from score-3 items. The stem asks for an implication or a
solution ("এই সিদ্ধান্তের বাংলাদেশের জন্য প্রভাব কী?" / "সমাধানে কী
করা উচিত?"). The answer is grounded ONLY in the item's verified fact
list + its [পটভূমি] line and is explicitly marked as analysis, not
fact ("বিশ্লেষণ" prefix, kind "analytical"). Any analytical question
whose answer would need a fact not in the list is rejected (no
question is emitted). Analytical questions are not SRS cards — they
train analysis, not recall.

---

## STEP 9 — STUDY FEATURES (engine data contract)

Quiz yesterday's facts first, with immediate feedback on every answer.
Bring back missed questions after 1, 3, 7, then 14 days. A "ভুল রিপোর্ট
করুন" report on a card removes the card until review. All Step 5 checks
run before any fact enters the quiz. The engine keeps the SRS state as
JSON: each card has fact_id, question, next_review (date), interval_days,
repetitions, reported (true/false). The app renders the quiz UI from
this state; the engine only produces and updates the state.

## STEP 10 — VOCABULARY (deterministic, no LLM)

From the kept articles' fact lists, the engine picks 20 words + 10
phrases + 5 revision words — in the v1 app's word/phrase contract
shape (same field names the app already reads).

- Source: a curated, editable word/phrase bank in
  `rules/vocab_bank.json` (each entry carries a Bengali meaning and an
  English definition). A bank word/phrase is selected ONLY if it occurs
  verbatim in a kept article (fact quote first, else a sentence of the
  article body). Nothing is invented: every word/phrase traces to an
  article sentence, which is used as its example.
- Matching tolerates ordinary inflections (announced / announcing,
  ministers / policies) but the headword shown is always the base form.
- Ranking: in the most articles first, then longer word/phrase, then
  A–Z. Priority is High when a word occurs in 2+ articles, else Medium.
- Revision: the first 5 words from the previous editions' word lists
  (last v2 dry-run vocab, else the v1 editions dir) that are NOT in
  today's 20, copied verbatim with their original example and fields.
- Enrichment: a word/phrase that appeared in an earlier v1 edition
  reuses that edition's IPA, Bangla phonetic, synonyms, antonyms, word
  family and collocations. New words leave those fields empty — the
  engine never guesses a pronunciation or a synonym.
- If fewer than 20 words or 10 phrases match on a day, the edition
  reports a shortfall in its stats instead of inventing entries.

---

## V2 PUBLISH GATE (summary — canonical text in CONTRACTS.md)

The publish gate is defined in `engine-v2/CONTRACTS.md` ("V2 publish
gate"), not in this rubric file, and it does not change the rubric
above. Two rubric-adjacent points are recorded here so a rules edit
cannot silently break them:

- **Step 5 at publish time is stricter than Step 5 in the pipeline.**
  The pipeline lets an item marked "যাচাই করুন" (`action "verify"`)
  or with a dropped fact (`action "drop_fact"`) onto the page; the
  publish gate does not — every page item must have Step 5 `action
  "keep"` with zero quote/number/name failures. A rule change that
  weakens a Step 5 check therefore weakens the gate, and must be
  called out as such.
- **MCQ counts are judged after conversion, never on raw engine
  output.** The engine outputs every MCQ key in canonical order
  (`ক`); longest-correct (≤10/25, ties count) and letter balance
  (5–8 per letter) are computed by the gate script from the
  converted 25 MCQs in `editions/data-<date>.json` after the
  converter shuffles the keys.

**First-edition rule:** Edition 10 (2026-11-16) stops at the human
gate for Rudro's eyes even if it passes every gate check. Auto-publish
under the v2 gate for later editions needs a separate grant from
Rudro; the gate defines the checks, it does not grant auto-publish.
