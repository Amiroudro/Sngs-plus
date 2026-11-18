/// Phase 4 (Authentic Bengali) regression tests. Run with
/// `flutter test test/phase4_regression_test.dart` (or the full suite).
///
/// One test per bug class this phase could introduce:
///  1. Latin digits in a Bengali headline / rendered text;
///  2. an English month name leaking into Bengali data or UI;
///  3. 'Tk' in a chart title (must be 'টাকা' in bn mode);
///  4. 'Tk' or '$' leaking through a cloze card;
///  5. a hyphenated Bengali suffix on a Latin stem (e.g. 'QR-এ');
///  6. an English label in the Bengali UI (the 7 stringsBn fixes);
///  7. _monthWords mis-parsing a converted Bengali date as a tile value;
///  8. every screen pumped as a pushed route, light + dark, at 100%
///     and 200% text scale, with SafeArea + explicit-colour checks
///     (per ~/workspace/custom-skills/verify_flutter_apps/SKILL.md).
///
/// The one legitimate Latin-money slot — the tiny grey original figure
/// under a fact tile (e.g. 'Tk 13.5 bn', allowlisted in
/// tools/validate_bangla_allowlist.json) — is excluded from the
/// Latin-digit / Tk / $ scans by pattern, never by blanket skip.
library;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'fixtures/approved_bn_qr_story.dart';
import 'package:sarangsho_plus/data/story_layout.dart';
import 'package:sarangsho_plus/main.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/screens/current_affairs_screen.dart';
import 'package:sarangsho_plus/screens/editorial_screen.dart';
import 'package:sarangsho_plus/screens/english_screen.dart';
import 'package:sarangsho_plus/screens/flashcard_screen.dart';
import 'package:sarangsho_plus/screens/library_screen.dart';
import 'package:sarangsho_plus/screens/profile_screen.dart';
import 'package:sarangsho_plus/screens/quiz_screen.dart';
import 'package:sarangsho_plus/screens/search_screen.dart';
import 'package:sarangsho_plus/screens/story_detail_screen.dart';
import 'package:sarangsho_plus/screens/word_detail_screen.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:sarangsho_plus/widgets/word_card.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// All rendered text on screen right now (plain text of every Text).
List<String> _renderedTexts(WidgetTester tester) {
  final out = <String>[];
  for (final e in find.byType(Text).evaluate()) {
    final t = e.widget as Text;
    out.add(t.data ?? t.textSpan?.toPlainText() ?? '');
  }
  return out;
}

/// The single allowlisted slot: the tiny original English figure under
/// a fact tile, e.g. 'Tk 13.5 bn', 'Tk 2-3 bn', 'US$ 113.4 bn'.
final _originalSlot = RegExp(r'^(Tk|US\$) [\d.,–\- ]+(bn|mn)?$');

final _latinDigit = RegExp(r'[0-9]');
final _englishMonth = RegExp(
  r'\b(January|February|March|April|May|June|July|August|September|'
  r'October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|'
  r'Dec)\b',
);
/// The corrected HSC date strings (validator allowlist): "1 December" /
/// "1-31 December" are the corrected 2 Nov edition strings — the fix was
/// applied 2026-11-12 on Rudro's order "fix all and update all" (the
/// correct date is 1 December 2026). They stay in Latin in the Bengali
/// overlay because the edition validator enforces the exact strings as
/// its HSC baseline and BN MCQ 16 option B must match the EN option.
/// Data-level scans skip them.
bool _isHscPending(String s) =>
    s.contains('1 December') || s.contains('1-31 December');
final _hyphenSuffix = RegExp(r'[A-Za-z]+-[এেোয়কেতেথেরি]');

/// The vocabulary / phrase data is English learning content by design:
/// real newspaper words, phrases, examples, collocations and definitions,
/// figures included. The Bengali UI chrome around it is Bengali; the
/// vocabulary data itself is not Bengali text, so the Latin-digit /
/// English-month / Tk scans skip it — by exact match against the data's
/// own English fields (individual values and their ' ; '-joined list
/// forms, as word_card.dart renders them), never by blanket skip.
/// Bengali story content and the Bengali UI are NOT in this set and are
/// still fully scanned. (First hit 11 Nov 2026: the first phrase
/// "compared with" quotes the BRAC Bank sentence with Tk 21.21 /
/// Tk 15.36 billion, and its collocations carry "December 2025" — every
/// "compared with" sentence in that article carries figures, so no
/// digit-free example exists in the source.)
Set<String>? _englishContentCache;
Set<String> _englishContent() {
  if (_englishContentCache != null) return _englishContentCache!;
  final out = <String>{};
  void add(String? s) {
    if (s != null && s.isNotEmpty) out.add(s);
  }

  void addList(List<String> items) {
    for (final item in items) {
      add(item);
    }
    if (items.isNotEmpty) add(items.join(' ; '));
  }

  for (final edition in sharedState.editions) {
    // An edition whose Bengali overlay is pending review intentionally
    // renders its English source content. Exempt only those exact source
    // strings from Bengali-only digit/month checks; keep Bengali UI chrome
    // and any actually approved overlay under the full regression checks.
    if (edition.banglaPendingReview) {
      for (final story in edition.stories) {
        add(story.headline);
        add(story.summary);
        add(story.whyItMatters);
        add(story.examFacts);
        add(story.keyPeople);
        add(story.figures);
        add(story.oneLiner);
        add(story.detail);
      }
      for (final mcq in edition.mcqs) {
        add(mcq.question);
        for (final option in mcq.options.values) {
          add(option);
        }
        add(mcq.explanation);
      }
    }
    for (final w in edition.words) {
      add(w.headword);
      add(w.ipa);
      add(w.partOfSpeech);
      add(w.difficulty);
      add(w.priority);
      add(w.englishDefinition);
      add(w.example);
      add(w.contextNote);
      add(w.sourcePublication);
      add(w.articleHeadline);
      add(w.publicationDate);
      add(w.bcsRelevance);
      addList(w.synonyms);
      addList(w.antonyms);
      addList(w.wordFamily);
      addList(w.collocations);
    }
    for (final p in edition.phrases) {
      add(p.phrase);
      add(p.type);
      add(p.englishExplanation);
      add(p.usage);
      add(p.example1);
      add(p.example2);
      add(p.sourcePublication);
      add(p.articleHeadline);
      add(p.publicationDate);
      add(p.examValue);
      addList(p.collocations);
      // Phrase source line (word_card.dart renders it as ONE Text):
      // "সূত্র: <publication> — <headline>" (Bengali) /
      // "Source: <publication> — <headline>" (English). The Latin
      // digits in it come solely from the English headline (e.g. "Q3").
      if (p.sourcePublication != null &&
          p.sourcePublication!.isNotEmpty) {
        add('সূত্র: ${p.sourcePublication}');
        add('Source: ${p.sourcePublication}');
        if (p.articleHeadline != null && p.articleHeadline!.isNotEmpty) {
          add('সূত্র: ${p.sourcePublication} — ${p.articleHeadline}');
          add('Source: ${p.sourcePublication} — ${p.articleHeadline}');
        }
      }
    }
    // Per-story learning-module vocabulary (2026-11-17 renovation):
    // same English learning content as the edition words/phrases above
    // — headwords, examples, synonyms and antonyms are rendered verbatim
    // on the story screen, so they belong in the exemption set too.
    for (final story in edition.stories) {
      final module = story.learningModule;
      if (module == null) continue;
      for (final v in module.vocabulary) {
        add(v.word);
        add(v.example);
        add(v.synonym);
        add(v.antonym);
      }
    }
  }
  return _englishContentCache = out;
}

/// True when [t] is one of the English vocabulary/phrase strings
/// (word_card.dart renders examples wrapped in curly quotes: "…").
bool _isEnglishContent(String t) {
  final stripped = t.trim().replaceAll('“', '').replaceAll('”', '');
  return _englishContent().contains(stripped);
}

void _assertNoLatinDigits(List<String> texts, String where) {
  for (final t in texts) {
    if (_originalSlot.hasMatch(t.trim())) continue;
    if (_isEnglishContent(t)) continue;
    expect(
      _latinDigit.hasMatch(t),
      isFalse,
      reason: 'Latin digit in $where: "$t"',
    );
  }
}

void _assertNoEnglishMonth(List<String> texts, String where) {
  for (final t in texts) {
    if (_originalSlot.hasMatch(t.trim())) continue;
    if (_isEnglishContent(t)) continue;
    expect(
      _englishMonth.hasMatch(t),
      isFalse,
      reason: 'English month in $where: "$t"',
    );
  }
}

void _assertNoMoneyLeak(List<String> texts, String where) {
  for (final t in texts) {
    if (_originalSlot.hasMatch(t.trim())) continue;
    if (_isEnglishContent(t)) continue;
    expect(t, isNot(contains('Tk')), reason: 'Tk leak in $where: "$t"');
    expect(t, isNot(contains('\$')), reason: '\$ leak in $where: "$t"');
  }
}

void _assertNoHyphenSuffix(List<String> texts, String where) {
  for (final t in texts) {
    expect(
      _hyphenSuffix.hasMatch(t),
      isFalse,
      reason: 'hyphen suffix in $where: "$t"',
    );
  }
}

/// Every visible Text must resolve to an explicit colour (regression:
/// unselected ChoiceChip / SegmentedButton labels once resolved to no
/// colour at all and were invisible in light mode).
void _assertAllTextHasColour(WidgetTester tester, String where) {
  for (final e in find.byType(Text).evaluate()) {
    final t = e.widget as Text;
    final data = t.data ?? t.textSpan?.toPlainText() ?? '';
    final rp = tester.renderObject<RenderParagraph>(find.byWidget(t));
    expect(
      rp.text.style?.color,
      isNotNull,
      reason: 'no colour for "$data" ($where)',
    );
  }
}

Future<void> _pumpScreen(
  WidgetTester tester,
  Widget screen, {
  bool dark = false,
  double textScale = 1.0,
}) async {
  await tester.pumpWidget(
    MediaQuery(
      data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
      child: MaterialApp(
        theme: buildLightTheme(),
        darkTheme: buildDarkTheme(),
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: screen,
      ),
    ),
  );
  await _pump(tester);
}

/// Pump [screen] as a pushed route (the way the app actually opens it),
/// wrapped in a Scaffold so no bare Column/ListView is ever a route.
Future<void> _pumpPushed(
  WidgetTester tester,
  Widget screen, {
  bool dark = false,
  double textScale = 1.0,
}) async {
  await tester.pumpWidget(
    MediaQuery(
      data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
      child: MaterialApp(
        // Fresh key each time: otherwise the framework reuses the
        // previous Navigator (with its pushed route still on top) and
        // the 'go' button underneath is never found again.
        key: UniqueKey(),
        theme: buildLightTheme(),
        darkTheme: buildDarkTheme(),
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: Scaffold(
          body: Builder(
            builder: (context) => Center(
              child: TextButton(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => screen is Scaffold
                        ? screen
                        : Scaffold(body: screen),
                  ),
                ),
                child: const Text('go'),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await _pump(tester);
  await tester.tap(find.text('go'));
  await _pump(tester);
}

Edition _qrEdition() => createApprovedBanglaQrTestEdition();
Story _qrStory() => _qrEdition().stories.single;

void main() {
  setUpAll(() async {
    SharedPreferences.setMockInitialValues({});
    sharedState = AppState();
    await sharedState.init();
    final result = await loadEditions();
    await sharedState.setEditions(
      result.editions,
      result.correctConsecutive,
      result.correctRule,
    );

    // The story-screen regression uses a synthetic, fully reviewed fixture.
    // No bundled translation is promoted or marked approved by this test.
  });

  // ---- Bug class 1: Latin digits in Bengali text --------------------

  testWidgets('phase4: no Latin digits in a Bengali story headline',
      (tester) async {
    await _pumpPushed(
      tester,
      StoryDetailScreen(
        edition: _qrEdition(),
        story: _qrStory(),
        state: sharedState,
      ),
    );
    final texts = _renderedTexts(tester);
    // The headline itself, verbatim, in Bangla digits.
    expect(
      find.text(_qrStory().headlineIn('bn')),
      findsOneWidget,
    );
    expect(_latinDigit.hasMatch(_qrStory().headlineIn('bn')), isFalse);
    _assertNoLatinDigits(texts, 'story detail');
    _assertNoEnglishMonth(texts, 'story detail');
    _assertNoHyphenSuffix(texts, 'story detail');
    expect(tester.takeException(), isNull);
  });

  testWidgets('phase4: no Latin digits anywhere in Bengali data',
      (tester) async {
    // Data-level: every Bengali string the app can show.
    for (final edition in sharedState.editions.where((e) =>
        !e.banglaPendingReview &&
        e.stories.isNotEmpty &&
        e.stories.every((story) => story.bn != null))) {
      for (final story in edition.stories) {
        for (final s in [
          story.headlineIn('bn'),
          story.summaryIn('bn'),
          story.whyIn('bn') ?? '',
          story.factsIn('bn') ?? '',
          story.figuresIn('bn') ?? '',
          story.peopleIn('bn') ?? '',
        ]) {
          if (_isHscPending(s)) continue;
          expect(
            _latinDigit.hasMatch(s),
            isFalse,
            reason: '${edition.date} ${story.id}: "$s"',
          );
        }
      }
      for (final mcq in edition.mcqs) {
        final opts = [
          for (final k in mcq.optionKeys) mcq.optionIn('bn', k),
        ];
        for (final s in [
          mcq.questionIn('bn'),
          ...opts,
          mcq.explanationIn('bn') ?? '',
        ]) {
          if (_isHscPending(s)) continue;
          expect(
            _latinDigit.hasMatch(s),
            isFalse,
            reason: '${edition.date} MCQ ${mcq.no}: "$s"',
          );
        }
      }
    }
  });

  // ---- Bug class 2: English month in Bengali data/UI ----------------

  testWidgets('phase4: no English month in Bengali data or story screen',
      (tester) async {
    for (final edition in sharedState.editions.where((e) =>
        !e.banglaPendingReview &&
        e.stories.isNotEmpty &&
        e.stories.every((story) => story.bn != null))) {
      for (final story in edition.stories) {
        for (final s in [
          story.headlineIn('bn'),
          story.summaryIn('bn'),
          story.whyIn('bn') ?? '',
          story.factsIn('bn') ?? '',
          story.figuresIn('bn') ?? '',
        ]) {
          if (_isHscPending(s)) continue;
          expect(
            _englishMonth.hasMatch(s),
            isFalse,
            reason: '${edition.date} ${story.id}: "$s"',
          );
        }
      }
    }
    await _pumpPushed(
      tester,
      StoryDetailScreen(
        edition: _qrEdition(),
        story: _qrStory(),
        state: sharedState,
      ),
    );
    _assertNoEnglishMonth(_renderedTexts(tester), 'story detail');
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class 3: Tk in the chart title ---------------------------

  testWidgets('phase4: chart title is Bengali money, never Tk',
      (tester) async {
    final layout = buildStoryLayout(_qrStory(), 'bn');
    expect(layout.chart, isNotNull);
    expect(layout.chart!.title, contains('টাকা'));
    expect(layout.chart!.title, isNot(contains('Tk')));
    await _pumpPushed(
      tester,
      StoryDetailScreen(
        edition: _qrEdition(),
        story: _qrStory(),
        state: sharedState,
      ),
    );
    final texts = _renderedTexts(tester);
    expect(
      texts.any((t) => t.contains('টাকা')),
      isTrue,
      reason: 'no টাকা text rendered on the story screen',
    );
    _assertNoMoneyLeak(texts, 'story detail');
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class 4: Tk / $ leaking through cloze cards --------------

  testWidgets('phase4: cloze cards blank Bangla digits, no Tk leak',
      (tester) async {
    final layout = buildStoryLayout(_qrStory(), 'bn');
    expect(layout.cloze, isNotEmpty);
    for (final card in layout.cloze) {
      expect(card.answer, isNot(contains('Tk')));
      expect(card.answer, isNot(contains('\$')));
      expect(RegExp(r'[০-৯]').hasMatch(card.answer), isTrue,
          reason: 'cloze answer has no Bangla digit: "${card.answer}"');
    }
    await _pumpPushed(
      tester,
      StoryDetailScreen(
        edition: _qrEdition(),
        story: _qrStory(),
        state: sharedState,
      ),
    );
    // Reveal every cloze answer, then scan the whole screen.
    for (var i = 0; i < layout.cloze.length; i++) {
      await tester.ensureVisible(find.text('উত্তর দেখুন').first);
      await tester.tap(find.text('উত্তর দেখুন').first);
      await _pump(tester);
    }
    _assertNoMoneyLeak(_renderedTexts(tester), 'story detail + cloze');
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class 5: hyphenated Bengali suffix on a Latin stem -------

  testWidgets('phase4: no hyphen suffix on a Latin stem in Bengali data',
      (tester) async {
    for (final edition in sharedState.editions.where((e) =>
        !e.banglaPendingReview &&
        e.stories.isNotEmpty &&
        e.stories.every((story) => story.bn != null))) {
      for (final story in edition.stories) {
        for (final s in [
          story.headlineIn('bn'),
          story.summaryIn('bn'),
          story.factsIn('bn') ?? '',
          story.figuresIn('bn') ?? '',
        ]) {
          if (_isHscPending(s)) continue;
          expect(
            _hyphenSuffix.hasMatch(s),
            isFalse,
            reason: '${edition.date} ${story.id}: "$s"',
          );
        }
      }
    }
  });

  // ---- Bug class 6: English label in the Bengali UI -----------------

  testWidgets('phase4: the 7 fixed stringsBn values render in Bengali',
      (tester) async {
    // relatedPhrase + relevance render on the WORD CARD (word_card.dart),
    // not the detail screen — and only the related section's title is
    // always shown. 'turnaround' (7 Nov) has both: a related phrase
    // ('turnaround time') and a BCS relevance body.
    final ed7 = sharedState.findEdition('2026-11-07')!;
    final word = ed7.words.firstWhere((w) => w.headword == 'turnaround');
    expect(ed7.relatedPhrasesFor(word), isNotEmpty);
    expect(word.bcsRelevance, isNotNull);
    await _pumpScreen(
      tester,
      Scaffold(
        body: SingleChildScrollView(
          child: WordCard(edition: ed7, word: word, state: sharedState),
        ),
      ),
    );
    expect(find.text('সংশ্লিষ্ট বাগধারা / শব্দবন্ধ / গ্রুপ ভার্ব'),
        findsOneWidget);
    expect(find.text('বিসিএস / ব্যাংক প্রাসঙ্গিকতা'), findsOneWidget);
    // The old English forms must be gone from the whole card.
    final texts = _renderedTexts(tester);
    for (final t in texts) {
      expect(t, isNot(contains('সংশ্লিষ্ট idiom')));
      expect(t, isNot(contains('BCS / Bank')));
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets('phase4: quiz subtitle + practice labels are Bengali-only',
      (tester) async {
    await _pumpScreen(tester, Scaffold(body: QuizScreen(state: sharedState)));
    expect(find.text('২৫টি প্রশ্ন + শব্দ অনুশীলন'), findsWidgets);
    final texts = _renderedTexts(tester);
    for (final t in texts) {
      expect(t, isNot(contains('MCQ')));
      expect(t, isNot(contains('(Analogy)')));
    }
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class 7: _monthWords parses Bengali dates ----------------

  test('phase4: _monthWords rejects converted Bengali dates as numbers',
      () {
    // The bug this guards: _monthWords once knew English months only,
    // so a converted date like "৬ নভেম্বর ২০২৬" would be read as the
    // number 6 and become a tile value / chart bar. Dates ARE legitimate
    // tile values when they are the whole fact ("পরীক্ষা: ১৬ জানুয়ারি
    // ২০২৭" — an exam date is exactly what students must memorise), so
    // the assertion is on the parser, not on dates appearing in tiles:
    // firstNumber must return null for a date, and still parse real
    // figures with their unit.
    expect(
      firstNumber('ক্ষতি ধরা পড়ে শুক্রবার সকালে, ৬ নভেম্বর ২০২৬'),
      isNull,
    );
    expect(firstNumber('পরীক্ষা: ১৬ জানুয়ারি ২০২৭'), isNull);
    expect(firstNumber('আবেদন ১১-২৫ নভেম্বর ২০২৬'), isNull);
    expect(firstNumber('নভেম্বর ২০২৬-এ পুনরায় শুরু'), isNull);
    expect(firstNumber('৯-২২ নভেম্বর ২০২৬'), isNull);
    // Positive controls: real figures still parse, with the unit.
    final big = firstNumber('দৈনিক ১,৩৫০ কোটি টাকা (অক্টোবরের প্রথম সপ্তাহ)');
    expect(big, isNotNull);
    expect(big!.phrase, '১,৩৫০ কোটি টাকা');
    expect(numberUnit(big.phrase), 'tk|কোটি');
    final range = firstNumber('দৈনিক ২০০–৩০০ কোটি টাকা (মে মাসের শেষ)');
    expect(range, isNotNull);
    expect(range!.phrase, '২০০–৩০০ কোটি টাকা');
    expect(range.value, 250);
    // The date-heavy story (8 Nov CA07, rally figures) still tiles.
    final rally = sharedState
        .findEdition('2026-11-08')!
        .stories
        .firstWhere((s) => s.id == 'CA07');
    expect(buildStoryLayout(rally, 'bn').tiles, isNotEmpty);
  });

  // ---- Bug class 8: every screen, both themes, both text scales -----

  group('phase4: every screen pumps (light + dark, 100% + 200%)', () {
    // Tab screens (pumped inside a Scaffold, as AppShell does).
    final tabScreens = <String, Widget Function()>{
      'home': () => AppShell(state: sharedState),
      'current affairs': () =>
          Scaffold(body: CurrentAffairsScreen(state: sharedState)),
      'editorial': () => Scaffold(body: EditorialScreen(state: sharedState)),
      'library': () => Scaffold(body: LibraryScreen(state: sharedState)),
      'profile': () => Scaffold(body: ProfileScreen(state: sharedState)),
    };
    // Pushed routes.
    late Edition edition;
    late VocabWord firstWord;
    late Phrase firstPhrase;
    setUpAll(() {
      edition = sharedState.selectedEdition!;
      firstWord = edition.words.first;
      firstPhrase = edition.phrases.first;
    });
    Map<String, Widget Function()> pushedScreens() => {
          'english': () => EnglishScreen(state: sharedState),
          'quiz': () => QuizScreen(state: sharedState),
          'flashcards': () => FlashcardScreen(state: sharedState),
          'search': () => SearchScreen(state: sharedState),
          'story detail': () => StoryDetailScreen(
                edition: _qrEdition(),
                story: _qrStory(),
                state: sharedState,
              ),
          'word detail': () => WordDetailScreen(
                edition: edition,
                word: firstWord,
                state: sharedState,
              ),
          'phrase detail': () => PhraseDetailScreen(
                phrase: firstPhrase,
                state: sharedState,
              ),
          'edition words': () => EditionWordsScreen(
                edition: edition,
                state: sharedState,
              ),
        };

    for (final dark in [false, true]) {
      for (final scale in [1.0, 2.0]) {
        final tag = '${dark ? 'dark' : 'light'} ${scale}x';
        testWidgets('tab screens pump ($tag)', (tester) async {
          for (final entry in tabScreens.entries) {
            await _pumpScreen(
              tester,
              entry.value(),
              dark: dark,
              textScale: scale,
            );
            final texts = _renderedTexts(tester);
            _assertAllTextHasColour(tester, '${entry.key} ($tag)');
            expect(
              tester.takeException(),
              isNull,
              reason: '${entry.key} ($tag)',
            );
          }
        });
        testWidgets('pushed routes pump ($tag)', (tester) async {
          for (final entry in pushedScreens().entries) {
            await _pumpPushed(
              tester,
              entry.value(),
              dark: dark,
              textScale: scale,
            );
            final texts = _renderedTexts(tester);
            _assertNoMoneyLeak(texts, '${entry.key} ($tag)');
            _assertNoHyphenSuffix(texts, '${entry.key} ($tag)');
            _assertAllTextHasColour(tester, '${entry.key} ($tag)');
            // SafeArea: nothing renders under the status bar, and the
            // last content is not cut by the system nav bar.
            expect(find.byType(SafeArea), findsWidgets,
                reason: '${entry.key} ($tag): no SafeArea');
            expect(
              tester.takeException(),
              isNull,
              reason: '${entry.key} ($tag)',
            );
          }
        });
      }
    }
  });
}
