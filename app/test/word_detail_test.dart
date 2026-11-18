/// Phase 3 tests: the redesigned word detail page (mockup image-7)
/// and the জানি / জানি না SRS with 1 / 3 / 7-day revision.
///
///  1. POS normalisation: one Title-Case rule, every word.
///  2. Detail page hides Priority, the BCS relevance text and any
///     "No direct antonym" notice; the exam info sits in ONE
///     collapsed row; "খবরে কীভাবে এসেছে" stays visible.
///  3. Hide-word self-test toggle works (headword -> blank).
///  4. জানি / জানি না persists and schedules 1, then 3, then 7 days;
///     "জানি" clears the due date.
///  5. The revision tab shows due words only, overdue first.
///  6. Speaker button present, speaks the headword, and fails
///     gracefully (SnackBar, no crash) when TTS is unavailable.
///  7. Detail page renders at 200% text scale and in dark mode
///     without overflow or fallback styles.
///
/// Edition data is loaded once in setUpAll (real async). Each test
/// gets a fresh AppState so SRS marks never leak between tests.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/data/word_display.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/screens/english_screen.dart';
import 'package:sarangsho_plus/screens/word_detail_screen.dart';
import 'package:sarangsho_plus/services/tts_service.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late List<Edition> allEditions;

Edition get edition8Nov =>
    allEditions.firstWhere((e) => e.date == '2026-11-08');

VocabWord get gratuity =>
    edition8Nov.words.firstWhere((w) => w.headword == 'gratuity');

Future<AppState> freshState() async {
  SharedPreferences.setMockInitialValues({});
  final state = AppState();
  await state.init();
  await state.setEditions(allEditions, 0, null);
  return state;
}

Future<void> _pump(WidgetTester tester, {int steps = 20}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// Fake TTS: records what it was asked to speak; [fail] makes
/// [speak] return false, like a phone with no TTS engine.
class FakeTts implements WordTts {
  final List<String> spoken = [];
  bool fail = false;

  @override
  Future<bool> speak(String text) async {
    if (fail) return false;
    spoken.add(text);
    return true;
  }

  @override
  Future<void> stop() async {}
}

Future<void> _pumpDetail(
  WidgetTester tester,
  AppState state, {
  VocabWord? word,
  WordTts? tts,
  bool dark = false,
  double textScale = 1.0,
}) async {
  final w = word ?? gratuity;
  await tester.pumpWidget(
    MediaQuery(
      data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
      child: MaterialApp(
        theme: buildLightTheme(),
        darkTheme: buildDarkTheme(),
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: WordDetailScreen(
          edition: edition8Nov,
          word: w,
          state: state,
          tts: tts ?? FakeTts(),
        ),
      ),
    ),
  );
  await _pump(tester);
}

/// Plain text of a RichText found by [key] (its spans concatenated).
String _richPlainText(WidgetTester tester, Key key) {
  final rich = tester.widget<RichText>(find.byKey(key));
  return rich.text.toPlainText();
}

void main() {
  setUpAll(() async {
    SharedPreferences.setMockInitialValues({});
    final result = await loadEditions();
    allEditions = result.editions;
  });

  group('POS normalisation (one rule, every word)', () {
    test('Title Case regardless of the raw capitalisation', () {
      expect(normalizePosEn('noun'), 'Noun');
      expect(normalizePosEn('Noun'), 'Noun');
      expect(normalizePosEn('verb'), 'Verb');
      expect(normalizePosEn('Adjective'), 'Adjective');
      expect(normalizePosEn('noun / verb'), 'Noun / Verb');
      expect(normalizePosEn('Noun / Verb'), 'Noun / Verb');
      expect(normalizePosEn('verb / noun'), 'Verb / Noun');
    });

    test('Bangla POS matches the English segments', () {
      expect(posBangla('Noun'), 'বিশেষ্য');
      expect(posBangla('noun'), 'বিশেষ্য');
      expect(posBangla('noun / verb'), 'বিশেষ্য / ক্রিয়া');
      expect(posBangla('Adjective'), 'বিশেষণ');
      expect(posDisplay('noun'), 'বিশেষ্য');
      expect(posDisplay('verb / noun'), 'ক্রিয়া / বিশেষ্য');
      // English mode shows the English part of speech only.
      expect(posDisplay('noun', 'en'), 'Noun');
      expect(posDisplay('verb / noun', 'en'), 'Verb / Noun');
    });

    test('form suffixes are kept, data annotations are dropped', () {
      expect(normalizePosEn('Verb (past)'), 'Verb (Past)');
      expect(posBangla('Verb (past)'), 'ক্রিয়া (অতীত)');
      expect(normalizePosEn('noun (plural)'), 'Noun (Plural)');
      expect(
        normalizePosEn('Noun / adjective (see prior entry)'),
        'Noun / Adjective',
      );
      expect(posDisplay(''), '');
      expect(posDisplay(null), '');
    });

    test('difficulty maps to dot counts', () {
      expect(difficultyDots('Advanced'), 3);
      expect(difficultyDots('Intermediate'), 2);
      expect(difficultyDots('Basic'), 1);
      expect(difficultyDots('Previously covered'), 1);
      expect(difficultyDots('Unknown'), 0);
      expect(difficultyDots(null), 0);
    });

    test('hide-word replaces every occurrence, case-insensitively', () {
      expect(
        hideHeadwordIn('The retirement gratuity has been raised.', 'gratuity'),
        'The retirement ________ has been raised.',
      );
      expect(
        hideHeadwordIn('Gratuity and gratuity.', 'gratuity'),
        '________ and ________.',
      );
      expect(
        hideHeadwordIn('No match here.', 'gratuity'),
        'No match here.',
      );
    });

    test('source line uses a real Bangla date, never raw ISO', () {
      final line = exampleSourceLine(gratuity, 'bn');
      expect(line, contains('Prothom Alo English'));
      expect(line, contains('৭ নভেম্বর ২০২৬'));
      expect(line, isNot(contains('2026-11-07')));
      expect(exampleSourceLine(gratuity, 'en'), contains('7 November 2026'));
    });
  });

  group('SRS: জানি / জানি না + 1 / 3 / 7 days', () {
    test('first জানি না is due in 1 day, then 3, then 7', () async {
      final state = await freshState();
      final day0 = DateTime(2026, 11, 8);

      await state.setWordResult('2026-11-08', 'gratuity', false, now: day0);
      expect(state.wordResult('2026-11-08', 'gratuity'), false);
      expect(state.wordDueDate('2026-11-08', 'gratuity'), '2026-11-09');
      expect(state.wordUnknownStage('2026-11-08', 'gratuity'), 1);
      expect(state.isWordDue('2026-11-08', 'gratuity', now: day0), false);
      expect(
        state.isWordDue('2026-11-08', 'gratuity',
            now: DateTime(2026, 11, 9)),
        true,
      );

      // Reviewed again on the due day and marked unknown again: +3.
      await state.setWordResult('2026-11-08', 'gratuity', false,
          now: DateTime(2026, 11, 9));
      expect(state.wordDueDate('2026-11-08', 'gratuity'), '2026-11-12');
      expect(state.wordUnknownStage('2026-11-08', 'gratuity'), 2);

      // Third unknown: +7. A fourth stays at 7, never longer.
      await state.setWordResult('2026-11-08', 'gratuity', false,
          now: DateTime(2026, 11, 12));
      expect(state.wordDueDate('2026-11-08', 'gratuity'), '2026-11-19');
      expect(state.wordUnknownStage('2026-11-08', 'gratuity'), 3);
      await state.setWordResult('2026-11-08', 'gratuity', false,
          now: DateTime(2026, 11, 19));
      expect(state.wordDueDate('2026-11-08', 'gratuity'), '2026-11-26');
      expect(state.wordUnknownStage('2026-11-08', 'gratuity'), 3);
    });

    test('জানি clears the due date and keeps the word out of revision',
        () async {
      final state = await freshState();
      await state.setWordResult('2026-11-08', 'gratuity', false,
          now: DateTime(2026, 11, 8));
      expect(state.isWordDue('2026-11-08', 'gratuity',
          now: DateTime(2026, 11, 10)), true);
      await state.setWordResult('2026-11-08', 'gratuity', true);
      expect(state.wordResult('2026-11-08', 'gratuity'), true);
      expect(state.wordDueDate('2026-11-08', 'gratuity'), isNull);
      expect(state.isWordDue('2026-11-08', 'gratuity',
          now: DateTime(2026, 11, 10)), false);
      expect(state.dueWordsFor(edition8Nov), isEmpty);
      expect(state.wordResult('2026-11-08', 'conspiracy'), isNull);
    });

    test('due list is overdue-first and excludes known / unanswered',
        () async {
      final state = await freshState();
      // conspiracy: unknown on 5 Nov -> due 6 Nov (overdue).
      await state.setWordResult('2026-11-08', 'conspiracy', false,
          now: DateTime(2026, 11, 5));
      // suppress: unknown on 7 Nov -> due 8 Nov (due today).
      await state.setWordResult('2026-11-08', 'suppress', false,
          now: DateTime(2026, 11, 7));
      // uproar: unknown today -> due tomorrow (not due yet).
      await state.setWordResult('2026-11-08', 'uproar', false,
          now: DateTime(2026, 11, 8));
      // defaced: known -> never due.
      await state.setWordResult('2026-11-08', 'defaced', true);
      final due = state.dueWordsFor(edition8Nov, now: DateTime(2026, 11, 8));
      expect(
        due.map((w) => w.headword).toList(),
        ['conspiracy', 'suppress'],
      );
    });

    test('SRS state survives a fresh AppState load (shared_preferences)',
        () async {
      final first = await freshState();
      await first.setWordResult('2026-11-08', 'gratuity', false,
          now: DateTime(2026, 11, 8));
      // A second AppState over the same mock prefs must see it.
      final second = AppState();
      await second.init();
      await second.setEditions(allEditions, 0, null);
      expect(second.wordResult('2026-11-08', 'gratuity'), false);
      expect(second.wordDueDate('2026-11-08', 'gratuity'), '2026-11-09');
    });
  });

  group('word detail page (mockup image-7)', () {
    testWidgets('shows the mockup order and hides the removed rows',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state);

      // App bar: position (gratuity is word 1 of 20 on 8 Nov) + one
      // bookmark action, no headword title up there.
      expect(find.text('শব্দ ১ / ২০'), findsOneWidget);
      expect(find.byIcon(Icons.bookmark_border), findsOneWidget);

      // Top line: POS Bangla · English (one capitalisation) + dots.
      expect(find.text('বিশেষ্য'), findsOneWidget);
      // Headword + IPA + Bangla phonetic + speaker.
      expect(find.text('gratuity'), findsWidgets);
      expect(find.text('/ɡrəˈtʃuːəti/'), findsOneWidget);
      expect(find.text('গ্র্যাচুইটি'), findsOneWidget);
      expect(find.byIcon(Icons.volume_up), findsOneWidget);
      // Meaning box + definition.
      expect(find.text('বাংলা অর্থ'), findsOneWidget);
      expect(find.text('আনুতোষিক; অবসরকালীন ভাতা'), findsOneWidget);
      expect(
        find.text('A sum of money paid to an employee when they retire or '
            'leave a job.'),
        findsOneWidget,
      );
      // Newspaper sentence + source, tags, visible context section.
      expect(find.text('খবরের বাক্য'), findsOneWidget);
      expect(find.text('খবরে কীভাবে এসেছে'), findsOneWidget);
      expect(find.text('সমার্থক শব্দ'), findsOneWidget);
      expect(find.text('একসঙ্গে ব্যবহৃত হয়'), findsOneWidget);
      expect(find.text('শব্দপরিবার'), findsOneWidget);
      // Collapsed row, collapsed by default: its body is hidden.
      expect(find.text('পরীক্ষার তথ্য ও সূত্র'), findsOneWidget);
      expect(find.text('সঠিক বানান'), findsNothing);
      expect(find.text('পরীক্ষায় যেভাবে আসে'), findsNothing);
      // Bottom bar.
      expect(find.text('জানি না'), findsOneWidget);
      expect(find.text('জানি'), findsOneWidget);

      // Removed from the card: Priority, the long BCS relevance
      // text, and any "no antonym" notice (gratuity's data says
      // 'No direct antonym' — it must never render).
      expect(find.text('অগ্রাধিকার'), findsNothing);
      expect(find.textContaining('Priority'), findsNothing);
      expect(
        find.textContaining('Service rules, pay and retirement benefits'),
        findsNothing,
      );
      expect(find.textContaining('BCS / Bank প্রাসঙ্গিকতা'), findsNothing);
      expect(find.text('সরাসরি বিপরীত শব্দ নেই'), findsNothing);
      expect(find.textContaining('No direct antonym'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('collapsed exam row opens and shows spelling + source',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state);
      // The row sits below the fold in the test viewport.
      await tester.ensureVisible(find.text('পরীক্ষার তথ্য ও সূত্র'));
      await _pump(tester);
      await tester.tap(find.text('পরীক্ষার তথ্য ও সূত্র'));
      await _pump(tester);
      expect(find.text('সঠিক বানান'), findsOneWidget);
      expect(find.text('পরীক্ষায় যেভাবে আসে'), findsOneWidget);
      expect(find.text('সূত্র'), findsOneWidget);
      expect(find.text('Prothom Alo English'), findsOneWidget);
      // Still no Priority / BCS relevance, even when expanded.
      expect(find.text('অগ্রাধিকার'), findsNothing);
      expect(find.textContaining('Service rules'), findsNothing);
      // Antonyms stay hidden for gratuity (no direct antonym).
      expect(find.text('বিপরীত শব্দ'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('hide-word toggle blanks the headword in the sentence',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state);
      const key = ValueKey('word-example');
      expect(_richPlainText(tester, key), contains('gratuity'));
      expect(find.text('শব্দটি লুকিয়ে নিজেকে যাচাই করুন'), findsOneWidget);

      // The toggle sits below the fold in the test viewport.
      await tester.ensureVisible(
        find.byKey(const ValueKey('hide-word-toggle')),
      );
      await _pump(tester);
      await tester.tap(find.byKey(const ValueKey('hide-word-toggle')));
      await _pump(tester);
      expect(_richPlainText(tester, key), contains('________'));
      expect(_richPlainText(tester, key), isNot(contains('gratuity')));
      expect(find.text('শব্দটি দেখুন'), findsOneWidget);
      // The headword at the top of the page is untouched.
      expect(find.text('gratuity'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('hide-word-toggle')));
      await _pump(tester);
      expect(_richPlainText(tester, key), contains('gratuity'));
      expect(tester.takeException(), isNull);
    });

    testWidgets('speaker speaks the headword', (tester) async {
      final state = await freshState();
      final tts = FakeTts();
      await _pumpDetail(tester, state, tts: tts);
      await tester.tap(find.byIcon(Icons.volume_up));
      await _pump(tester);
      expect(tts.spoken, ['gratuity']);
      expect(find.text('উচ্চারণ চালাতে পারছি না।'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    // Separate test (fresh State): a pumpWidget replacement reuses
    // the first screen's State, so a second engine in the same test
    // would never be reached.
    testWidgets('speaker failure shows a message, never crashes',
        (tester) async {
      final state = await freshState();
      final failing = FakeTts()..fail = true;
      await _pumpDetail(tester, state, tts: failing);
      await tester.tap(find.byIcon(Icons.volume_up));
      await _pump(tester);
      expect(find.text('উচ্চারণ চালাতে পারছি না।'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('জানি / জানি না on the page persists in AppState',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state);
      await tester.tap(find.text('জানি না'));
      await _pump(tester);
      expect(state.wordResult('2026-11-08', 'gratuity'), false);
      expect(state.wordDueDate('2026-11-08', 'gratuity'), isNotNull);
      expect(find.textContaining('পরের পুনরালোচনা'), findsOneWidget);

      await tester.tap(find.text('জানি'));
      await _pump(tester);
      expect(state.wordResult('2026-11-08', 'gratuity'), true);
      expect(state.wordDueDate('2026-11-08', 'gratuity'), isNull);
      expect(tester.takeException(), isNull);
    });

    testWidgets('detail page renders at 200% text scale without overflow',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state, textScale: 2.0);
      expect(find.text('gratuity'), findsWidgets);
      await tester.scrollUntilVisible(
        find.text('পরীক্ষার তথ্য ও সূত্র'),
        500,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('detail page renders in dark mode with ink text',
        (tester) async {
      final state = await freshState();
      await _pumpDetail(tester, state, dark: true);
      final headword = tester.widget<Text>(find.text('gratuity').first);
      expect(headword.style?.color, AppColors.darkInk);
      final scaffold = tester.widget<Scaffold>(find.byType(Scaffold).first);
      expect(scaffold.backgroundColor, AppColors.storyPaperDark);
      expect(tester.takeException(), isNull);
    });
  });

  group('revision tab shows due words only', () {
    testWidgets('due word listed, known / not-due / unanswered hidden',
        (tester) async {
      final state = await freshState();
      final today = DateTime.now();
      // 2026-11-08 is outside the 7-edition revision window now
      // that 16 editions are bundled (window: 10..16 Nov), so the
      // due / not-due / known words come from 2026-11-16 instead.
      await state.setWordResult('2026-11-16', 'submerged', false,
          now: today.subtract(const Duration(days: 2)));
      await state.setWordResult('2026-11-16', 'embankment', false,
          now: today); // due tomorrow, not due yet
      await state.setWordResult('2026-11-16', 'equivalent', true);

      await tester.pumpWidget(
        MaterialApp(
          theme: buildLightTheme(),
          home: EditionWordsScreen(edition: edition8Nov, state: state),
        ),
      );
      await _pump(tester);
      expect(find.text('পুনরালোচনা (১)'), findsOneWidget);
      await tester.tap(find.text('পুনরালোচনা (১)'));
      await _pump(tester);
      expect(find.text('submerged'), findsOneWidget);
      expect(find.text('embankment'), findsNothing);
      expect(find.text('equivalent'), findsNothing);
      expect(find.text('annually'), findsNothing);
      expect(find.text('আজকের পড়া'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('empty when nothing is due', (tester) async {
      final state = await freshState();
      await tester.pumpWidget(
        MaterialApp(
          theme: buildLightTheme(),
          home: EditionWordsScreen(edition: edition8Nov, state: state),
        ),
      );
      await _pump(tester);
      expect(find.text('পুনরালোচনা (০)'), findsOneWidget);
      await tester.tap(find.text('পুনরালোচনা (০)'));
      await _pump(tester);
      expect(find.text('পুনরালোচনা (০)'), findsOneWidget);
      expect(
        find.textContaining('এখন পুনরালোচনার জন্য কোনো শব্দ নেই'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  });
}
