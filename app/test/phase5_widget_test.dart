/// Phase 5 widget tests (verify skill: every screen, pushed routes,
/// light + dark, 100% + 200% text scale, SafeArea + explicit-colour
/// checks), plus the Phase 5 regressions:
///  1. the story screen renders authored Phase 5 fields (one-liner,
///     key-fact tiles, authored bullets, exam Q→A, recall cards) and
///     still matches the mockup sections in order;
///  2. the revision tab shows due words from across the last 7
///     editions (and not from 8 editions back);
///  3. the Profile download section shows the default Pages URL
///     when nothing is stored, saves a custom URL, restores the
///     default on clear, and shows the offline-fallback line when
///     a check fails.
/// Run with `flutter test test/phase5_widget_test.dart`.
library;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
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
import 'package:sarangsho_plus/services/edition_download_service.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

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
                    builder: (_) =>
                        screen is Scaffold ? screen : Scaffold(body: screen),
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

/// An edition carrying one story with the authored Phase 5 fields
/// (English + Bengali overlay), for the story-screen test.
Edition authoredEdition() {
  final story = Story(
    id: 'CA99',
    headline: 'Authored headline',
    category: 'Bangladesh',
    summary: 'Old summary first sentence. Old summary second sentence.',
    whyItMatters: 'Authored why this matters.',
    examFacts: 'Old fact one; Old fact two.',
    figures: 'Old figure 100 items shipped across regions.',
    sources: const [],
    oneLiner: 'Authored one-liner, short and exact.',
    keyFacts: const [
      KeyFact(label: 'Authored label', value: '৫০০ কোটি টাকা'),
      KeyFact(label: 'Second label', value: '৭৫ শতাংশ'),
    ],
    whatHappened: const ['Authored bullet one.', 'Authored bullet two.'],
    examQa: const [ExamQa(q: 'Authored question?', a: 'Authored answer.')],
    recallCards: const [
      RecallCard(cloze: 'The value was ______ কোটি টাকা.', answer: '৫০০'),
    ],
    detail: 'Authored full detail text.',
  );
  story.bn = const BnStory(
    headline: 'বাংলা শিরোনাম',
    summary: 'বাংলা সারাংশ প্রথম বাক্য। বাংলা সারাংশ দ্বিতীয় বাক্য।',
    oneLiner: 'বাংলা এক লাইন।',
    keyFacts: [
      KeyFact(label: 'বাংলা লেবেল', value: '৫০০ কোটি টাকা'),
    ],
    whatHappened: ['বাংলা বুলেট এক।', 'বাংলা বুলেট দুই।'],
    examQa: [ExamQa(q: 'বাংলা প্রশ্ন?', a: 'বাংলা উত্তর।')],
    recallCards: [
      RecallCard(cloze: 'মান ছিল ______ কোটি টাকা।', answer: '৫০০'),
    ],
    detail: 'বাংলা বিস্তারিত লেখা।',
  );
  return Edition(
    date: '2026-11-09',
    stories: [story],
    words: const [],
    revisionWords: const [],
    phrases: const [],
    mcqs: const [],
    sources: const [],
    counts: const {},
  );
}

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
  });

  // ---- Bug class: every screen, both themes, both text scales ----

  group('phase5: every screen pumps (light + dark, 100% + 200%)', () {
    final tabScreens = <String, Widget Function()>{
      'home': () => AppShell(state: sharedState),
      'current affairs': () =>
          Scaffold(body: CurrentAffairsScreen(state: sharedState)),
      'editorial': () => Scaffold(body: EditorialScreen(state: sharedState)),
      'library': () => Scaffold(body: LibraryScreen(state: sharedState)),
      'profile': () => Scaffold(body: ProfileScreen(state: sharedState)),
    };
    late Edition edition;
    late VocabWord firstWord;
    late Phrase firstPhrase;
    setUpAll(() {
      edition = sharedState.selectedEdition!;
      firstWord = edition.words.first;
      firstPhrase = edition.phrases.first;
    });
    Edition qrEdition() =>
        sharedState.editions.firstWhere((e) => e.date == '2026-11-08');
    Story qrStory() =>
        qrEdition().stories.firstWhere((s) => s.id == 'CA02');
    Map<String, Widget Function()> pushedScreens() => {
          'english': () => EnglishScreen(state: sharedState),
          'quiz': () => QuizScreen(state: sharedState),
          'flashcards': () => FlashcardScreen(state: sharedState),
          'search': () => SearchScreen(state: sharedState),
          'story detail': () => StoryDetailScreen(
                edition: qrEdition(),
                story: qrStory(),
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
            _assertAllTextHasColour(tester, '${entry.key} ($tag)');
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

  // ---- Bug class: authored story fields on the story screen ----

  testWidgets('story detail renders authored Phase 5 fields (bn)',
      (tester) async {
    final edition = authoredEdition();
    final story = edition.stories.first;
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: StoryDetailScreen(
          edition: edition,
          story: story,
          state: sharedState,
        ),
      ),
    );
    await _pump(tester);
    // Authored Bengali one-liner + bullets + tiles + QA + cloze.
    expect(find.text('বাংলা এক লাইন।'), findsOneWidget);
    expect(find.text('বাংলা বুলেট এক।'), findsOneWidget);
    expect(find.text('৫০০ কোটি টাকা'), findsWidgets);
    expect(find.text('বাংলা প্রশ্ন?'), findsOneWidget);
    expect(find.text('বাংলা উত্তর।'), findsOneWidget);
    expect(find.text('মান ছিল ______ কোটি টাকা।'), findsOneWidget);
    // Mockup section order is unchanged.
    const labels = [
      'এক লাইনে',
      'মনে রাখুন',
      'কী ঘটেছে',
      'কেন গুরুত্বপূর্ণ',
      'পরীক্ষায় যেভাবে আসে',
      'নিজেকে যাচাই করুন',
      'পুরো সারাংশ ও সূত্র দেখুন',
    ];
    double lastY = -1;
    for (final label in labels) {
      expect(find.text(label), findsOneWidget, reason: label);
      final y = tester.getTopLeft(find.text(label)).dy;
      expect(y, greaterThan(lastY), reason: '$label out of order');
      lastY = y;
    }
    expect(tester.takeException(), isNull);
  });

  testWidgets('story detail with authored fields: dark + 200% no overflow',
      (tester) async {
    final edition = authoredEdition();
    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(2.0)),
        child: MaterialApp(
          theme: buildLightTheme(),
          darkTheme: buildDarkTheme(),
          themeMode: ThemeMode.dark,
          home: StoryDetailScreen(
            edition: edition,
            story: edition.stories.first,
            state: sharedState,
          ),
        ),
      ),
    );
    await _pump(tester);
    expect(find.text('বাংলা এক লাইন।'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class: revision tab across the last 7 editions ----

  testWidgets('revision tab shows due words from older editions in-window',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    final state = AppState();
    await state.init();
    Edition fakeEdition(String date, String headword) => Edition(
          date: date,
          stories: const [],
          words: [VocabWord(headword: headword)],
          revisionWords: const [],
          phrases: const [],
          mcqs: const [],
          sources: const [],
          counts: const {},
        );
    final editions = [
      for (var i = 1; i <= 8; i++)
        fakeEdition(
          '2026-11-0$i',
          ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',
           'golf', 'hotel'][i - 1],
        ),
    ];
    await state.setEditions(editions, 0, null);
    // alpha (1 Nov, 8 back): due but out of window.
    await state.setWordResult(
      '2026-11-01', 'alpha', false, now: DateTime(2026, 11, 1),
    );
    // bravo (2 Nov, 7 back): due and in window.
    await state.setWordResult(
      '2026-11-02', 'bravo', false, now: DateTime(2026, 11, 2),
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: EditionWordsScreen(edition: editions.last, state: state),
      ),
    );
    await _pump(tester);
    // Open the revision tab (label carries the due count).
    await tester.tap(find.textContaining('পুনরালোচনা'));
    await _pump(tester);
    expect(find.text('bravo'), findsOneWidget);
    expect(find.text('alpha'), findsNothing);
    // The older edition's date is shown under the word.
    expect(find.text('২ নভেম্বর ২০২৬'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  // ---- Bug class: Profile download section ----

  testWidgets(
      'profile download section: default URL shown, save custom, clear restores default, check starts',
      (tester) async {
    await EditionDownloadService.setStoredIndexUrl('');
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(body: ProfileScreen(state: sharedState)),
      ),
    );
    await _pump(tester);
    // The TextField's EditableText also owns a Scrollable, so the
    // ListView's Scrollable must be named explicitly (as widget_test
    // does for Home) — otherwise scrollUntilVisible finds two.
    await tester.scrollUntilVisible(
      find.text('নতুন সংস্করণ'),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('নতুন সংস্করণ'), findsOneWidget);
    // Nothing stored: the field shows the EFFECTIVE (default Pages)
    // URL and the status says the default is in use.
    final field = find.byKey(const ValueKey('download-url-field'));
    expect(
      tester.widget<TextField>(field).controller?.text,
      EditionDownloadService.defaultIndexUrl,
    );
    expect(
      find.text('ডিফল্ট লিংক চলছে। নতুন সংস্করণ নিজে থেকেই আসবে।'),
      findsOneWidget,
    );

    // Save a custom URL: status confirms, and the URL is stored.
    await tester.enterText(
      field,
      'https://example.com/editions/index.json',
    );
    await tester.tap(find.text('সংরক্ষণ করুন'));
    await _pump(tester);
    expect(find.text('লিংক সংরক্ষণ করা হয়েছে।'), findsOneWidget);
    expect(
      await EditionDownloadService.getStoredIndexUrl(),
      'https://example.com/editions/index.json',
    );

    // Clear + save: the stored URL is gone and the field shows the
    // default URL again, with the default status line.
    await tester.enterText(field, '');
    await tester.tap(find.text('সংরক্ষণ করুন'));
    await _pump(tester);
    expect(
      await EditionDownloadService.getStoredIndexUrl(),
      isEmpty,
    );
    expect(
      tester.widget<TextField>(field).controller?.text,
      EditionDownloadService.defaultIndexUrl,
    );
    expect(
      find.text('ডিফল্ট লিংক চলছে। নতুন সংস্করণ নিজে থেকেই আসবে।'),
      findsOneWidget,
    );

    // Tapping "check" starts a check and shows the checking line.
    // (The network outcome itself is covered by the unit tests in
    // phase5_test.dart — widget tests fake HttpClient, so no real
    // request can complete here.)
    await tester.enterText(
      field,
      'http://127.0.0.1:9/editions/index.json',
    );
    await tester.tap(find.text('সংরক্ষণ করুন'));
    await _pump(tester);
    await tester.tap(find.text('নতুন সংস্করণ দেখুন'));
    await tester.pump();
    expect(find.text('যাচাই করছি…'), findsOneWidget);
    expect(tester.takeException(), isNull);
    // Leave the shared prefs clean for the other test files.
    await EditionDownloadService.setStoredIndexUrl('');
  });
}
