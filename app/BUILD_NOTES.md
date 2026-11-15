# BUILD_NOTES — Sarangsho Plus Flutter app

APK বিল্ডার যাচাই করার জন্য: এখানে প্রতিটি অনুমান (assumption) লেখা
আছে। কিছু ভুল মনে হলে কোড বদলানোর আগে এই তালিকা দেখুন।

## ১. ভাষার নিয়ম (Rudro-র পরিবর্তন, ২০২৬-১১-০৭)

- **সবকিছু বাংলায়।** UI, নেভিগেশন, বিভাগ, খবর, কুইজ, সেটিংস —
  বাংলা ডিফল্ট। English টগল আছে (প্রোফাইল → ভাষা) কিন্তু ডিফল্ট
  বাংলা; টগল করলে ইংরেজি উৎস-পাঠ্য দেখায়।
- **একমাত্র ইংরেজি: শব্দগুলো নিজে**, তাদের অর্থের বিভাগে —
  headword ইংরেজিতে থাকে, সঙ্গে বাংলা অর্থ, উচ্চারণ ও উদাহরণ।
  headword কখনো বাংলায় অনুবাদ করা হয় না।
- **সংখ্যা, তারিখ, উৎসের নাম/লিংক ও নাম (proper noun) হুবহু।**
  অনুবাদে সব সংখ্যা পশ্চিমা অঙ্কে রাখা হয়েছে (যেমন 355, 18,
  Tk4,068 কোটি, US$113.4378 বিলিয়ন) যাতে উৎসের সঙ্গে মিলিয়ে
  যাচাই করা যায়। ব্যক্তি/সংস্থার নাম বাংলা লিপিতে লেখা হয়েছে
  (যেমন জিয়াউর রহমান, বাংলাদেশ ব্যাংক) কিন্তু নাম বদলানো হয়নি;
  প্রকাশনার নাম (The Business Standard, Prothom Alo English)
  ও সংস্থার সংক্ষিপ্ত নাম (BSEC, DCCI, NBR, BGB, IDA) ইংরেজিতেই
  রাখা হয়েছে।
- শব্দ/শব্দবন্ধের **বাংলা অর্থ উৎসের তথ্য থেকে হুবহু** নেওয়া —
  নতুন করে অনুবাদ করা হয়নি।
- খবরের বাংলা অনুবাদ `assets/editions/bn-*.json` overlay-তে আছে।
  অনুবাদে তথ্য বদলানো হয়নি — শুধু সংযোগকারী ভাষা বাংলায় করা
  হয়েছে। `tools/check_data.py` যাচাই করে: overlay-র key গুলো
  উৎসের id-র সঙ্গে হুবহু মেলে, এবং ইংরেজি সারসংক্ষেপের প্রতিটি
  সংখ্যা বাংলা সারসংক্ষেপেও আছে।

### যেখানে বাংলায় করা যায়নি (এবং কেন)

1. **শব্দের শেখার উপাদান ইংরেজিতে থাকে:** ইংরেজি সংজ্ঞা,
   প্রতিশব্দ, বিপরীত শব্দ, শব্দরূপ, শব্দবন্ধ, মূল উদাহরণ,
   সংবাদ প্রসঙ্গ, BCS/Bank প্রাসঙ্গিকতা — এগুলো শেখার ইংরেজি
   উপাদান। প্রতিশব্দ বাংলায় করলে তার উদ্দেশ্য নষ্ট হয়;
   ইংরেজি সংজ্ঞা বাংলায় করলে তা বাংলা অর্থের পুনরাবৃত্তি হয়।
   কার্ডের সব লেবেল বাংলায়, তথ্য ইংরেজিতে।
2. **IPA** আন্তর্জাতিক ধ্বনিলিপি — বাংলায় রূপান্তর করা হয় না
   (পাশে বাংলা ধ্বনি আছে)।
3. **প্রকাশনা/সংস্থার নাম ও URL** হুবহু ইংরেজিতে (উৎসের নাম)।
4. **তারিখের মাসের নাম** বাংলায় (৭ নভেম্বর ২০২৬), কিন্তু
   খবরের ভেতরের তারিখের লেখা (যেমন "6 November") উৎসের মতোই
   রাখা হয়েছে।
5. **অনুবাদের মান:** বাংলা অনুবাদ এই বিল্ডে হাতে করা হয়েছে;
   কোনো মেশিন অনুবাদ বা যাচাইকৃত বাংলা উৎস ব্যবহার করা হয়নি।
   Rudro/পর্যালোচক চাইলে `bn-*.json` ফাইল দুটি সরাসরি সম্পাদনা
   করতে পারেন — অ্যাপের কোড বদলাতে হয় না।

## ২. পরীক্ষার গুরুত্বের ব্যাজ — ০–১০০ স্কোর নেই

মূল কাজের বিবরণে ধরা হয়েছিল `exam_relevance` একটি ০–১০০ স্কোর।
**আসল তথ্যে তা নেই।** `exam_relevance` একটি ফ্রি-টেক্সট লেবেল:
সংস্করণ ১-এ "High"/"Medium"; সংস্করণ ২-এ "High — ICT, public
spending, governance." ধরনের লেখা। ব্যাজ সেই লেবেলের মাত্রাটি
দেখায় (উচ্চ/মাধ্যমিক) — কোনো সংখ্যা হিসাব করা বা বানানো হয়নি।
কোনো খবরে লেবেল না থাকলে ব্যাজে "—" দেখায়। কোড:
`lib/models.dart` → `Story.relevanceLevel`।

## ৩. বিভাগের ভাগ (সংস্করণ ১-এর লম্বা বিভাগ → ছয় বিভাগ)

সংস্করণ ২-এর বিভাগের নাম সরাসরি ছয় বিভাগের নাম। সংস্করণ ১-এর
বিভাগ কীওয়ার্ড নিয়মে ভাগ করা হয়েছে (`lib/data/sections.dart`,
নিয়মের ক্রম গুরুত্বপূর্ণ):

| সংস্করণ ১-এর বিভাগ | ছয় বিভাগে ফলাফল |
|---|---|
| Bangladesh history / governance | বাংলাদেশ |
| Bangladesh economy / investment climate, Bangladesh economy / external debt | অর্থনীতি ও ব্যাংকিং |
| Banking / capital market regulation, Banking / corporate finance, Banking / industrial finance, Banking / fintech / international trade | অর্থনীতি ও ব্যাংকিং |
| Energy / diplomacy / banking | অর্থনীতি ও ব্যাংকিং |
| Infrastructure / trade / regional development | অর্থনীতি ও ব্যাংকিং |
| Science / technology / economy | প্রযুক্তি |
| Migration / labour market | চাকরি ও শিক্ষা |
| Labour / RMG / tax administration | অর্থনীতি ও ব্যাংকিং |
| Renewable energy / industry / climate | বাংলাদেশ |
| International affairs / climate / environment, International affairs / governance / anti-corruption | বিশ্ব |

ফলাফল (যাচাইকৃত): বাংলাদেশ ২, অর্থনীতি ও ব্যাংকিং ৯, বিশ্ব ২,
প্রযুক্তি ১, চাকরি ও শিক্ষা ১, রাজনীতি ০। সংস্করণ ১-এ রাজনীতি
বিভাগে কোনো খবর নেই — এটি তথ্যের ফল, কোডের ভুল নয়।

## ৪. সম্পাদকীয় ট্যাব

দুটি সংস্করণের কোনো খবরের বিভাগ/শিরোনামে opinion/editorial/
analysis/commentary চিহ্ন নেই (যাচাই করা হয়েছে) — তাই ট্যাবটি
সৎ খালি অবস্থা দেখায়। ভবিষ্যৎ সংস্করণে মতামত-ধরনের খবর এলে
`isEditorial()` (`lib/screens/editorial_screen.dart`) সেটি
নিজে থেকেই দেখাবে। কোনো সম্পাদকীয় লেখা বানানো হয়নি।

## ৫. শব্দ কার্ড — কোন ক্ষেত্র তথ্য থেকে, কোনটি হিসাব (derived)

| # | ক্ষেত্র | উৎস |
|---|---|---|
| 1 | headword + বাংলা অর্থ | তথ্য (`Headword / phrase`, `Bangla meaning` হুবহু) |
| 2 | উচ্চারণ / IPA | তথ্য (`IPA`, `Bangla phonetic`) |
| 3 | পদ + শব্দরূপ | তথ্য (`Part of speech / type`, `Word family / derivatives`) |
| 4 | প্রতিশব্দ | তথ্য (`Synonyms`) |
| 5 | বিপরীত শব্দ | তথ্য (`Antonyms`); "No direct antonym" = অনুপস্থিত |
| 6 | সঠিক বানান | **হিসাব:** headword থেকে; জোড়া অক্ষর যান্ত্রিকভাবে রঙ করা হয় (যেমন suppress-এর ss)। নীরব অক্ষর বা অন্য বানান-ফাঁদ নিয়ে কোনো দাবি করা হয় না — তথ্যে তা নেই। |
| 7 | সংবাদপত্রের উদাহরণ | তথ্য (`Original example`) |
| 8 | উপযুক্ত শব্দবন্ধ / preposition | তথ্য (`Collocations / patterns` হুবহু); preposition আলাদা করে বানানো হয় না — শব্দবন্ধের ভেতরে যা আছে তাই দেখায়। |
| 9 | সংশ্লিষ্ট idiom/phrase/group verb | **হিসাব:** একই সংস্করণের শব্দবন্ধের মধ্যে headword থাকলে তবেই দেখায় (যেমন turnaround → "turnaround time", blanket → "blanket extension")। না থাকলে "এই শব্দের জন্য তথ্য নেই"। |
| 10 | মূল অংশ ও গঠন | **হিসাব:** headword ও তার শব্দরূপগুলোর দীর্ঘতম সাধারণ উপসর্গ (কমপক্ষে ৩ অক্ষর)। এটি যান্ত্রিক গঠন-বিশ্লেষণ, যাচাইকৃত ব্যুৎপত্তি (etymology) নয়। কোনো সাধারণ মূল না থাকলে "তথ্য নেই"। |
| 11 | পরীক্ষায় যেভাবে আসে | **হিসাব:** প্রশ্নের ধরনের তালিকা (`PAST_QUESTION_PATTERNS.md`) + শব্দের নিজের তথ্য (প্রতিশব্দ থাকলে প্রতিশব্দের প্রশ্ন, বিপরীত শব্দ থাকলে বিপরীত শব্দের প্রশ্ন, শব্দরূপ ≥২ হলে বিভিন্ন পদ হিসেবে ব্যবহার, শব্দবন্ধ থাকলে শূন্যস্থান পূরণ, সংশ্লিষ্ট phrase থাকলে idiom/phrase; অর্থ/বানান/পদ/এক শব্দে প্রকাশ সব শব্দে)। পূর্ববর্তী পরীক্ষার তথ্য **শুধু ৫টি শব্দে** — যেগুলো `PAST_QUESTION_PATTERNS.md`-এ যাচাইকৃত পরিবারে আছে (নিচে দেখুন)। বাকি সব শব্দে সৎভাবে "নির্দিষ্ট পূর্ববর্তী পরীক্ষার তথ্য নেই"। |

### যাচাইকৃত পূর্ববর্তী-পরীক্ষার তথ্য (শুধু এই ৫টি — আর কিছু নয়)

উৎস: `~/workspace/english-daily-ai/claude-project/PAST_QUESTION_PATTERNS.md`।
কোনো "৪৩তম BCS-এ এসেছিল" ধরনের দাবি কোথাও করা হয়নি।

- `bureaucratic` — Governance শব্দ-পরিবার (bureaucracy)
- `bilateral` — International শব্দ-পরিবার (bilateral)
- `sanction` — International শব্দ-পরিবার (sanction)
- `adaptation` — Environment শব্দ-পরিবার (adaptation)
- `mitigation` — Bank previous-question family (mitigate/mitigation)

### যেসব ক্ষেত্র তথ্যে নেই — কার্ডে "তথ্য নেই" দেখায়

- সংস্করণ ১-এর ৫টি পুনরালোচনা শব্দের IPA, বাংলা ধ্বনি, প্রতিশব্দ,
  বিপরীত শব্দ, শব্দরূপ, শব্দবন্ধ — উৎসের তথ্যেই খালি।
- ১০টি শব্দের সরাসরি বিপরীত শব্দ নেই (সংস্করণ ১: bureaucratic,
  prerequisite, turnaround, maturity, heritage, roadmap,
  adaptation; সংস্করণ ২: gratuity, coordinator, accomplice —
  তথ্যে "No direct antonym" বা খালি)।
- বেশিরভাগ শব্দের কোনো সংশ্লিষ্ট idiom/phrase নেই (শুধু ৪টি শব্দে
  আছে: turnaround, liquidity, blanket, resume/recruitment)।
- কোনো শব্দেরই আলাদা "appropriate preposition" ক্ষেত্র তথ্যে নেই —
  শুধু শব্দবন্ধ আছে।

## ৬. কুইজ অনুশীলন (Practice) — কীভাবে তৈরি

- সংস্করণের ২৫টি MCQ আলাদা; অনুশীলন প্রশ্ন **তৈরি** করা হয়
  (`lib/data/exam_patterns.dart` → `buildPracticeQuestions`)।
- প্রতিশব্দ: সঠিক উত্তর = শব্দের প্রথম প্রতিশব্দ; ভুল বিকল্প =
  অন্য শব্দগুলোর প্রথম প্রতিশব্দ।
- বিপরীত শব্দ: একইভাবে, বিপরীত শব্দের তথ্য থেকে।
- বানান: সঠিক headword + ৩টি যান্ত্রিক ভুল বানান (পাশের দুটি
  অক্ষর বদল / একটি অক্ষর বাদ / একটি অক্ষর জোড়া করা)।
- উপমা (Analogy): `A : প্রতিশব্দ(A) :: B : ?` — শুধু তথ্যে থাকা
  শব্দ:প্রতিশব্দ জোড়া থেকে।
- সব অনুশীলন প্রশ্নে "অনুশীলন — সংস্করণের শব্দ থেকে তৈরি" লেখা
  থাকে; ভুল উত্তর "আমার ভুলগুলো"-তে জমা হয় (অনুশীলন চিহ্নসহ)।
- প্রশ্নের সেট deterministic (সংস্করণের তারিখ দিয়ে seed করা) —
  একই সংস্করণে সবসময় একই সেট আসে।

## ৭. অন্যান্য অনুমান

- **MCQ বিকল্পের আকার:** কাজের বিবরণে "options (list)" বলা
  হয়েছিল; আসল তথ্যে options একটি map (`{"A": ..., "B": ...}`)।
  কোড map পড়ে, list পেলে সেটিও সামলায় (`lib/models.dart` →
  `Mcq.fromJson`)।
- **MCQ `source` ক্ষেত্র** ("S01", "CA10") UI-তে দেখানো হয় না —
  এটি অভ্যন্তরীণ তথ্যসূত্র; সূত্রের নাম খবরের কার্ড/বিস্তারিতেই
  দেখা যায়।
- **খবরের `event_date` / `article_date`** হুবহু দেখানো হয়
  (যেমন "2026-11-06 (updated 2026-11-07)") — তারিখ নতুন করে
  লেখা হয় না।
- **সময়রেখা (Timeline):** `event_date` দিয়ে সাজানো হয়
  (নতুন থেকে পুরনো); তারিখ ছাড়া খবর শেষে যায়।
- **রিভিশন শব্দের "আজকের পড়া":** প্রতি সংস্করণের ৫টি শব্দই
  "Due today" তালিকায় থাকে; "পড়া হয়েছে" চিহ্ন
  shared_preferences-এ জমা থাকে (পূর্ণ SRS সময়সূচি 1-3-7-14-30-60
  দিনের হিসাব এই অ্যাপে নেই — ইংরেজি-দৈনিক সিস্টেমের SQLite DB-তে
  আছে)।
- **ভাষা টগল:** English বেছে নিলে UI ও খবর ইংরেজি উৎস-পাঠ্যে
  দেখায়; কিন্তু শব্দের বাংলা অর্থ তখনও বাংলা অর্থ হিসেবেই থাকে
  (অর্থের ভাষা বাংলা — এটাই নিয়ম)।
- **থিম:** ডিফল্ট লাইট; ডার্ক মোড টগল প্রোফাইলে।
- **অনুমতি:** শুধু INTERNET (url_launcher দিয়ে সূত্রের লিংক
  বাইরের ব্রাউজারে খুলতে)। অ্যাপ নিজে কোনো নেটওয়ার্ক ব্যবহার
  করে না। কোনো FLAG_SECURE নেই — স্ক্রিনশট নেওয়া যায়।
- **iOS:** এই প্রজেক্টে `ios/` ফোল্ডার নেই — `flutter create .`
  চালালে Flutter তা তৈরি করে দেবে। Android-ই মূল লক্ষ্য।
- **স্বাক্ষর (signing):** রিলিজ বিল্ড ডিবাগ-সই দিয়ে হয়
  (`android/app/build.gradle`)। Play Store-এ দেওয়ার আগে নিজের
  keystore + signingConfigs যোগ করুন।
- **৭ দিনের ট্র্যাকার:** `index.json`-এ `correct_consecutive_editions`
  = 0; নিয়ম: পূর্ণ ১২-ধাপের যাচাইয়ে উত্তীর্ণ হয়ে প্রকাশিত
  সংস্করণই "সঠিক" ধরা হয়।

## ৮. যাচাই (Verification) — ২০২৬-১১-০৭, আপডেট

```bash
python3 tools/check_data.py   # সব চেক পাস (৫৫২টি)
flutter analyze               # No issues found
flutter build apk --release   # ✓ app-release.apk, 48.1 MB
```

APK যাচাই (`aapt2 dump badging`): package `com.sarangsho.plus`,
version 1.0.0 (code 1), label `সারাংশ প্লাস`, launchable
`MainActivity`; APK-তে `libflutter.so` (arm64) ও পাঁচটি edition
asset bundle করা আছে। রিলিজ APK:
`build/app/outputs/flutter-apk/app-release.apk`। বিল্ডে শুধু
৩টি নিরীহ javac সতর্কতা (Java 8 source/target obsolete) — কোডের
কোনো সতর্কতা নেই।

### এখনও যাচাই হয়নি (সৎ সীমা)

- আসল Android ডিভাইসে চালানো হয়নি — এই VM-এ কোনো ডিভাইস/
  এমুলেটর নেই। Rudro নিজের ফোনে APK ইনস্টল করে দেখবেন।
- হাতে করা বাংলা অনুবাদের ভাষাগত মান — মানুষের পর্যালোচনা
  দরকার (`bn-*.json` সরাসরি সম্পাদনাযোগ্য)।

## ৯. পলিশ পাস — ২০২৬-১১-০৭ (Rudro: "be the best, make it legendary")

- **লঞ্চার আইকন:** আগে `android:icon="@mipmap/ic_launcher"` ছিল
  কিন্তু কোনো mipmap আইকনই ছিল না — APK বিল্ড
  `processReleaseResources`-এ ব্যর্থ হতো। এখন নিজস্ব আইকন আছে:
  গাঢ়-সবুজ পটভূমিতে সাদা "সা" + কমলা-লাল বার (Noto Sans Bengali
  Black দিয়ে আঁকা)। সব density-তে legacy + round PNG,
  adaptive-icon foreground/background (`mipmap-anydpi-v26`),
  এবং ব্র্যান্ডেড launch screen (`drawable/launch_background.xml`
  — গাঢ়-সবুজ + মাঝখানে আইকন)। প্রোফাইলের অবতারেও একই "সা" চিহ্ন।
- **Lint শূন্য:** `flutter analyze` — ৪টি সমস্যা ছিল (২টি
  অব্যবহৃত import, ২টি শৈলী) — সব ঠিক করা হয়েছে।
- **কপি-ভুল ঠিক:** খবরের বিস্তারিত পাতায় সূত্র না থাকলে আগে
  "এই শব্দের জন্য তথ্য নেই" দেখাত — এখন সঠিক `noSources`
  লেখা ("এই খবরের কোনো সূত্রের তথ্য নেই")।
- **সংস্করণের অবস্থা:** হোমের switcher "প্রকাশিত" দেখাত না,
  কারণ `Edition.status` কখনো ভরা হতো না — এখন loader
  `index.json`-এর `status` পৌঁছে দেয়।
- **পুনরালোচনার গণনা:** সংস্করণ ২-এর counts key `revision_words`,
  সংস্করণ ১-এর `revision` — `revisionCount` এখন দুটোই ধরে।
- **CMake 3.31.6:** AGP-র ডিফল্ট CMake 3.22.1-এর Linux প্যাকেজ
  Google আর হোস্ট করে না (404)। CMake 3.31.6 ইনস্টল করে
  `android/app/build.gradle`-এ `cmake { version "3.31.6" }`
  দিয়ে পিন করা হয়েছে — `android.cmake.version` gradle property
  একা কাজ করেনি।

### এই VM-এ বিল্ড করতে যা লেগেছে (শুধু এই মেশিনের কাজ, Rudro-র নয়)

সাধারণ মেশিনে শুধু `flutter build apk --release` চালালেই হয়।
এই VM-এর নেটওয়ার্কে Java-র সরাসরি TLS ভাঙা (transparent
proxy) বলে লেগেছে: `~/tools/proxy-bridge.py` (127.0.0.1:8899),
`~/tools/hatch-ca.jks` truststore, `JDK_JAVA_OPTIONS` +
`GRADLE_OPTS`/`JAVA_OPTS`-এ `-Djava.net.preferIPv4Stack=true`,
Gradle 8.11.1 + AGP 8.9.2 + Kotlin 2.1.0, NDK 27, build-tools
34/35/36, CMake 3.31.6 — সব `~/Android/sdk/`-এ হাতে ইনস্টল
(direct curl + unzip; sdkmanager proxy দিয়ে কাজ করে না)।
`gradle-wrapper.properties`-এর distributionUrl আবার https-এ
ফেরানো হয়েছে (VM-এ সাময়িকভাবে `file://` ছিল)। বিস্তারিত টুলচেইন
ইতিহাস মূল এজেন্টের কাছে আছে; প্রজেক্টের কোডে VM-নির্ভর কিছু নেই।

## ১০. প্রিমিয়াম পলিশ পাস — ২০২৬-১১-০৮ (v1.1.0+2)

Rudro-র নির্দেশ: elegant/premium, হালকা (~২০ MB), শব্দের তালিকা
collapsed, রং বদলানো যাবে, অপ্রয়োজনীয় লেখা ছাঁটা, আর UI যেন
"amazing" হয় — clean হলো ভিত্তি, wow হলো লক্ষ্য।

### রং — একটাই accent (বদলেছে)

- কমলা-লাল UI থেকে পুরোপুরি সরানো হয়েছে — ওটাই ছিল চোখে লাগা
  উপাদান। এখন একটাই brand রং: গাঢ় পান্না-সবুজ `#0B5D3B`
  (আগের `#0E6B3A` থেকে গাঢ়, সাদা কাগজে AAA contrast), dark-এ
  হালকা পান্না `#6FC79B`। Amber শুধু system warning (Medium),
  লাল শুধু system error।
- লঞ্চার আইকন নতুন করে আঁকা (emerald-only, সাদা "সা", কমলা বার
  নেই) — Noto Sans Bengali Black + PIL দিয়ে সব density-তে;
  `colors.xml`-এ `ic_launcher_background` এখন `#0B5D3B`।
- প্রোফাইল অবতার ও সব বোতাম/নেভিগেশন এখন পান্না-সবুজ।

### ডিজাইন সিস্টেম (`lib/widgets/app_theme.dart`)

- 8pt গ্রিড, section gap 24, card radius 20, sheet 28, button 14।
- Type scale একটাই: display 32/1.1 w900, title 22/1.25, body
  16/1.6 (বাংলা body সর্বনিম্ন 14), caption 12/1.4।
- একটাই motion ভাষা: curve Cubic(0.16, 1, 0.3, 1), 180/320/360ms;
  page transition fade + 3% slide; staggered list entry (fade + 12px,
  45ms/item, সর্বোচ্চ 8); hero on story open; skeleton (pulsing
  block) লোডিংয়ে — spinner নেই।
- কার্ড: hairline border + নরম ছায়া (`PremiumCard`)। অ্যাপ বার
  শান্ত paper + ink শিরোনাম; রং শুধু Home hero ও primary বোতামে।
- Dark mode নতুন করে ভাবা: off-white `#F2EFE9` on `#131311`, হালকা
  surface দিয়ে depth — শুধু invert নয়।

### নতুন ফিচার

- Home hero: পান্না gradient + বিশাল ফিকে "সা" watermark, পুরো
  তারিখ, অফলাইন পিল, stats strip (খবর/শব্দ/প্রশ্ন — আসল সংখ্যা),
  প্রধান খবরের cover কার্ড; pull-to-refresh।
- শব্দের তালিকা collapsed: compact row (headword + বাংলা অর্থ);
  ট্যাপে inline expand — পুরো ১১-আইটেম কার্ড, একবারে একটাই খোলা;
  "পুরো পাতা" বোতামে আলাদা পাতা।
- ফ্ল্যাশকার্ড: 3D flip (সামনে headword + IPA, পেছনে বাংলা অর্থ +
  প্রতিশব্দ + উদাহরণ), "জানি / জানি না" গণনাসহ।
- কুইজ ফলাফল: animated score ring (count-up) + এক শব্দের verdict।
- গল্প শেয়ার: branded image card (preview দেখিয়ে) → PNG →
  system share sheet; কোনো নতুন dependency নেই — ন্যূনতম
  MethodChannel (`com.sarangsho.plus/share`) + FileProvider।
- পড়ার progress bar (গল্পের বিস্তারিতে), সূত্র bottom sheet-এ,
  thumb-first নিচের বার (Share + Bookmark)।
- খোঁজ: সাম্প্রতিক খোঁজ সংরক্ষিত (সর্বোচ্চ ৮), মিল highlight।
- ফন্টের আকার সেটিং (০.৯/১.০/১.১৫/১.৩, system size-এর গুণিতক —
  accessibility বজায় থাকে), সংরক্ষিত।
- Profile-এ কুইজ streak (টানা দিন) + সেরা/গড়/মোট + শেষ ৫টি
  ফলাফল; সংস্করণের download অবস্থা ("ডাউনলোড করা" পিল)।
- Timeline-এ rail (dot + লাইন), Library/Editorial-এ পরিশীলিত
  empty state (নরম বৃত্তে আইকন + এক লাইন)।

### লেখা ছাঁটা (v2 copy rule)

- মুছে ফেলা/ছোট করা: `englishSubtitle`, `timelineNote`,
  `dataNote`, `shareNote` (শেয়ার বোতাম এসেছে), `eventDate`,
  `meaning`, `yourScore` কী-গুলো; editorial empty body →
  "ভবিষ্যৎ সংস্করণে এলে এখানে দেখাবে।"; GK → "পরের সংস্করণে
  আসছে।"; about → এক লাইন; noMistakes → "এখনও কোনো ভুল নেই।";
  practiceNote, dueTodayNote, examRefNone, noDataForWord ("তথ্য
  নেই"), spellingNote — সব এক লাইনে।

### হালকা করা (size) — চূড়ান্ত ফলাফল (২০২৬-১১-০৮ ০১:৩০)

- `--split-per-abi` + R8 `minifyEnabled` + `shrinkResources`
  (`android/app/build.gradle`)। কোনো নতুন dependency যোগ হয়নি
  (share_plus নেওয়া হয়নি — method channel-ই যথেষ্ট)।
- Edition JSON মোট ~২৯৬ KB — চাপার মতো কিছু নয়; compress করা
  হয়নি। কোনো বাড়তি font/locale bundle করা হয়নি।
- **আসল আকার** (bytes, `build/app/outputs/flutter-apk/`):
  - `app-arm64-v8a-release.apk` — **17,457,750 (17.5 MB)** ← headline
  - `app-armeabi-v7a-release.apk` — 14,904,628 (14.9 MB)
  - `app-x86_64-release.apk` — 18,630,005 (18.6 MB)
  - `app-release.apk` (fat, সব ABI) — 48,973,639 (49.0 MB);
    v1 fat ছিল 48,124,735 (48.1 MB) — fat সামান্য বড় হয়েছে
    (নতুন ফিচারের কোড R8-এর সাশ্রয় ছাপিয়ে গেছে), কিন্তু
    ইনস্টল হয় **একটাই** APK — Rudro-র ফোনে সেটা arm64-র
    17.5 MB, v1-এর 48.1 MB-র বদলে (−৬৪%)।
- `--analyze-size` breakdown (arm64, `--target-platform
  android-arm64` দিয়ে আলাদা বিল্ড): `lib/arm64-v8a` 16 MB
  (Flutter engine + Dart AOT; Dart AOT symbols 5 MB decompressed,
  তার মধ্যে `package:flutter` 3 MB, আমাদের কোড 225 KB),
  `flutter_assets` 148 KB, `classes.dex` 445 KB। অর্থাৎ
  আকারের প্রায় সবটাই Flutter engine — অ্যাপের নিজের কোড/ডেটা
  সামান্য। ২০ MB-র নিচে যাওয়ার আর কোনো সহজ উপায় নেই
  (engine-ই ১৬ MB)।
- **পাঠ:** `--analyze-size` একসাথে `--split-per-abi`-র সঙ্গে
  চলে না — "Cannot perform code size analysis when building
  for multiple ABIs" — একটা ABI (`--target-platform
  android-arm64`) দিয়ে আলাদা বিল্ড লাগে।

### এই পাসে পাওয়া ও ঠিক করা ত্রুটি

1. `TextScaler.scale()` font size scale করে, scaler নয় —
   `baseScaler.scale(1.0) * fontScale` দিয়ে গুণ করা হয়েছে।
2. শেয়ার capture ডায়ালগ বন্ধ হওয়ার পরে করা যেত না —
   capture এখন ডায়ালগের ভেতরেই হয়, ফাইলের path ফেরত আসে।
3. কুইজ "আবার দিন" আগে মোড তালিকায় ফিরত — এখন একই কুইজ
   নতুন করে শুরু হয়।
4. `FadeSlideIn`-এর fade delay-এর আগেই চলত — এখন stateful
   controller delay-এর পরে শুরু হয়।
5. `flutter analyze`-এ আসা সব নাম/import/const lint ঠিক করা
   হয়েছে; `flutter test`-এ ৪টি widget test যোগ হয়েছে।
6. **Button theme-এ `Size.fromHeight(48)` = infinite width** —
   Row-এ থাকা যেকোনো বোতাম crash করত (English স্ক্রিনের
   Flashcards বোতাম — আসল ফোনে crash হতো)। ৪টি theme entry-ই
   `Size(0, 48)` করা হয়েছে।
7. **Home-র Hero Row 200% text scale-এ 23px overflow** —
   greeting + offline pill দুটোই `Flexible` + ellipsis করা হয়েছে।
8. **Dark mode contrast** — গাঢ় সবুজ লেখা/আইকন অন্ধকার
   surface-এ পড়া যেত না (WordCard, English, Flashcard, Quiz,
   Profile, StoryCard/Detail, HighlightText, ScoreBadge) —
   `AppColors.accentFor(Brightness)` / `amberFor(Brightness)`
   helper দিয়ে ঠিক করা হয়েছে; error লাল এখন
   `Theme.colorScheme.error`।
9. **`MediaQuery.textScalerOf(context)` root widget-এ throw
   করে** (MaterialApp-এর ওপরে কোনো MediaQuery নেই) — font
   scaling `MaterialApp.builder`-এ সরানো হয়েছে।
10. **Word-list test-এ `scrollUntilVisible` ভুল ধরা** —
    TabBarView-এ তিনটি ListView থাকায় finder একাধিক Scrollable
    পেত ("Too many elements")। সমাধান: test viewport লম্বা
    করা (800×3000) যাতে দুই row-ই visible থাকে — scroll ছাড়াই
    tap করা যায়। এটা test-এর সমস্যা ছিল, অ্যাপের নয়।
11. **শেয়ার কার্ডের wordmark হার্ডকোড ছিল** ('সারাংশ প্লাস')
    — এখন `state.t('appName')` দিয়ে ভাষা অনুযায়ী বদলায়।

### যাচাই (২০২৬-১১-০৮, চূড়ান্ত)

```bash
python3 tools/check_data.py   # ALL CHECKS PASSED (৫৭৯টি)
flutter analyze               # No issues found
flutter test                  # ৪/৪ widget test পাস
flutter build apk --release --split-per-abi   # arm64 17.5 MB
flutter build apk --release --analyze-size --target-platform android-arm64
flutter build apk --release   # fat 49.0 MB
```

APK আকার (v2, চূড়ান্ত): arm64-v8a **17.5 MB** (17,457,750
bytes, SHA-1 `8b9ee5cff1b5bf737207f2c39aaed08be31b8a67`),
armeabi-v7a 14.9 MB, x86_64 18.6 MB, fat 49.0 MB (SHA-1
`8c063a845244eed8ce574e2cc28a7f0ddf77ee3e`)। `aapt2 dump
badging` যাচাই: package `com.sarangsho.plus`, versionCode
2002 (arm64 split) / 2 (fat), versionName 1.1.0, লেবেল
"সারাংশ প্লাস"। APK-র ভেতরের লঞ্চার আইকন পরীক্ষা করা হয়েছে
— গড় RGB (49,114,87), emerald-dominant, কমলা নেই।

**সৎ সীমা (আগের মতোই):** কোনো আসল ফোন/এমুলেটরে চালানো
হয়নি — Rudro-র ইনস্টলই চূড়ান্ত পরীক্ষা; বাংলা prose
unreviewed; debug-signed; শেয়ার/FileProvider ও নতুন সব
flow আসল ডিভাইসে অপরীক্ষিত।

## ১১. Backfill পুনর্নির্মাণ — ২০২৬-১১-০৮ (এই VM-এ বিল্ড আটকে গিয়েছিল)

Flutter SDK: `~/tools/flutter/bin/flutter` (PATH-এ নেই — সরাসরি
পাথে চালাতে হয়)। Flutter 3.35.7 stable।

### সমস্যা ১ — Gradle daemon-এর loopback সংযোগ sandbox-এ আটকায়

লক্ষণ: `flutter build apk` ব্যর্থ — `Could not receive a message
from the daemon` / `Unexpected type tag 109 found`। strace-এ ধরা
পড়ে: daemon-এর client socket থেকে প্রথম byte `m` আসে, অর্থাৎ
`"muse: Other TCP connections is turned off for this assistant…"`
— sandbox-এর network filter IPv6 socket-এর সংযোগ আটকে error
বার্তা ফেরত দেয়। Java ডিফল্টভাবে loopback-এ IPv6-mapped socket
(`::ffff:127.0.0.1`) ব্যবহার করে; sandbox শুধু IPv4 loopback
অনুমোদন করে (পরীক্ষায় প্রমাণিত: AF_INET6 → আটকায়, AF_INET → চলে)।

সমাধান (দুটোই লাগে — client JVM + daemon JVM):

```bash
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"
export GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"
flutter build apk --release --split-per-abi
```

দ্রষ্টব্য: `app/android/gradle.properties`-এর `org.gradle.jvmargs`-এ
`-Djava.net.preferIPv4Stack=true` আগে থেকেই আছে, কিন্তু daemon-এর
command line-এ তা আসে না — Gradle এই flag `jvmargs` থেকে daemon-এ
পাঠায় না। তাই env var-ই ভরসা।

### সমস্যা ২ — Gradle proxy password পুরনো

`~/.gradle/gradle.properties`-এ egress proxy password বর্তমান
env password-এর সঙ্গে মিলত না (wrapper Gradle 8.11.1 ডাউনলোড করতে
গিয়ে SSL error)। বর্তমান password বসানো হয়েছে
`~/.gradle/gradle.properties` ও `/root/.gradle/gradle.properties`
— দুটোতেই (build root হিসেবে চলে, তাই Gradle home `/root/.gradle`;
Gradle 8.11.1 zip `~/tools/downloads/gradle-8.11.1-all.zip` থেকে
দুই home-এর wrapper dist-এ seed করা আছে)।

### সমস্যা ৩ — Hatch egress CA ঘুরেছে (rotated)

লক্ষণ: Android Gradle Plugin 8.9.2 resolve হয় না —
`dl.google.com`-এর MITM সার্টিফিকেট Java-তে `PKIX path validation
failed: signature check failed`। কারণ: `hatch-ca.jks`-এ থাকা
"Hatch Sandbox Egress CA"-র key পুরনো (SHA-256
`46:66:34:…:7E`), আর proxy এখন নতুন key-তে সই করে (SHA-256
`C6:4B:44:…:93`)। curl/openssl চলে (system CA bundle-এ নতুন CA
আছে), Java চলে না। AGP marker শুধু `dl.google.com`-এই আছে
(Maven Central 404, Plugin Portal Maven Central-এ redirect করে)।

সমাধান: live CA সার্টিফিকেট keystore-এ যোগ করা হয়েছে
(alias `hatch-live-egress`, এখন ১২৩টি entry)। Backup:
`/tmp/hatch-ca-backup.jks`। এরপর Java-তেও `dl.google.com` 200 দেয়।

### সমস্যা ৪ — `reportlab` আবার অনুপস্থিত

env reset-এর পর `pip3 install --break-system-packages reportlab`
দিয়ে পুনরায় ইনস্টল — publish-এর আগে যাচাই করা ভালো।

### Backfill বিল্ডের ফল (২০২৬-১১-০৮)

```bash
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"
export GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"
flutter build apk --release --split-per-abi   # arm64 17.7 MB
flutter build apk --release                   # fat 49.2 MB (49,170,603 bytes, SHA-1 4f60a76f1e9e043ede0d18d3c62cc0ccacb4a79916)
flutter test                                  # ৪/৪ পাস
flutter analyze                               # No issues found
python3 tools/check_data.py                   # ALL CHECKS PASSED (১,৭৬১টি)
```

APK আকার (backfill build): arm64-v8a **17.7 MB** (17,654,714
bytes, SHA-1 `073294644384a450317894be9c9f0f2d608d832c`),
armeabi-v7a 15.1 MB, x86_64 18.8 MB। arm64 ১৭.৫ → ১৭.৭ MB
(+০.২ MB — ৬টি নতুন সংস্করণের JSON)। Test আপডেট: loader test-এ
সংস্করণ সংখ্যা ২ → ৮, সবচেয়ে পুরনো সংস্করণ ২০২৬-১১-০১ (১৫ খবর)।
