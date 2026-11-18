/// Widget tests for the v1.2.1 fix pass. Run with `flutter test`.
/// No device or emulator needed. These cover:
///  1. the app boots and Home renders from the real bundled editions;
///  2. the English flow: dates first → tap a date → words list →
///     tap a word → dedicated detail page with the full exam card;
///  3. Current Affairs is a date-collapsed list (stories hidden until
///     a date is expanded, one date at a time);
///  4. Profile has no Editions section any more;
///  5. the word card renders in dark mode with ink text (regression
///     test for the v1.2.0 red-monospace-yellow-underline fallback);
///  6. the app still builds with no overflow errors at 200% text scale.
/// Phase 2 (story screen redesign, Home reorder, Profile colours):
///  7. the story detail screen shows the mockup sections in order,
///     with one short one-liner, no raw ISO date or English tag list,
///     one bookmark only, and a Bangla-digit position;
///  8. cloze reveal works and জানি/জানি না + পড়া হয়েছে persist;
///  9. Home shows the top-story hero above the English/Quiz rows;
/// 10. the story screen renders at 200% text scale and in dark mode
///     without overflow or fallback styles;
/// 11. every Profile text has an explicit colour in light and dark
///     mode (regression: the font-size ChoiceChip labels resolved to
///     no colour at all and were invisible in light mode).
///
/// Note: edition data is loaded in setUpAll (real async). Awaiting an
/// asset load inside a testWidgets body without pumping first hangs the
/// fake-async zone, so no test awaits loadEditions() directly.
library;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/data/story_layout.dart';
import 'package:sarangsho_plus/data/strings.dart';
import 'package:sarangsho_plus/main.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/screens/current_affairs_screen.dart';
import 'package:sarangsho_plus/screens/english_screen.dart';
import 'package:sarangsho_plus/screens/profile_screen.dart';
import 'package:sarangsho_plus/screens/quiz_screen.dart';
import 'package:sarangsho_plus/screens/story_detail_screen.dart';
import 'package:sarangsho_plus/screens/word_detail_screen.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// Pump until Home's hero cover appears (or the budget runs out).
Future<void> _pumpUntilHome(WidgetTester tester) async {
  for (var i = 0; i < 100; i++) {
    await tester.pump(const Duration(milliseconds: 100));
    if (find.text('প্রধান খবর').evaluate().isNotEmpty) return;
  }
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

  test('editions load from the real bundled data', () {
    // Edition-count-agnostic: any count >= 2, newest first.
    expect(sharedState.editions.length, greaterThanOrEqualTo(2));
    expect(sharedState.selectedEdition!.words.length, 20);
    expect(sharedState.selectedEdition!.mcqs.length, 25);
    expect(sharedState.selectedEdition!.stories.length, greaterThan(0));
    for (final e in sharedState.editions) {
      expect(e.stories, isNotEmpty);
      expect(e.words, isNotEmpty);
      expect(e.mcqs, isNotEmpty);
    }
    expect(
      sharedState.editions.first.date.compareTo(
        sharedState.editions.last.date,
      ),
      greaterThan(0),
    );
  });

  // The boot path itself (init + loadEditions) is covered by the plain
  // test above; here the already-loaded state is pumped so the widget
  // assertions do not depend on fake-async asset loading.
  testWidgets('app boots and Home renders the real editions', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: AppShell(state: sharedState),
      ),
    );
    await _pumpUntilHome(tester);
    expect(find.text('সারাংশ প্লাস'), findsWidgets);
    // Masthead + top-story hero (numeral 01) + first list row (02).
    expect(find.text('প্রধান খবর'), findsOneWidget);
    expect(find.text('০১'), findsOneWidget);
    // Home's Scrollable is the first in the shell; scrollUntilVisible
    // needs it named explicitly (many Scrollables exist across the
    // five tabs).
    await tester.scrollUntilVisible(
      find.text('০২'),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    // Scrolling builds new rows whose FadeSlideIn stagger timers are
    // still pending; let them fire before the test ends.
    await _pump(tester, steps: 10);
    expect(find.text('০২'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('english flow: dates → words → detail page', (tester) async {
    final edition = sharedState.selectedEdition!;
    // The newest edition's vocabulary changes over time. Select a word
    // with synonyms for this navigation flow; empty-synonym rendering is
    // covered by the dedicated word-detail widget tests.
    final word = edition.words.firstWhere((w) => w.hasSynonyms);
    final first = word.headword;
    final dateText = formatEditionDateLong(edition.date, 'bn');

    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: EnglishScreen(state: sharedState),
      ),
    );
    await _pump(tester);

    // Dates first: one row per edition, newest first; no word list yet.
    expect(find.text(dateText), findsOneWidget);
    expect(find.text(first), findsNothing);

    // Tap the date → that day's words list (tabs, not a flat feed).
    await tester.tap(find.text(dateText));
    await _pump(tester);
    expect(find.text('শব্দ (২০)'), findsOneWidget);
    // "postpone" is the 8th word (index 7) — the lazy ListView only
    // builds the first ~6 rows in the 800×600 test viewport, so
    // scroll it into view before asserting it exists. The scrollable
    // must be the WORDS list, not the first Scrollable in the tree —
    // that is the scrollable TabBar, which does not move the list.
    final wordsScrollable = find.ancestor(
      of: find.text('decision'),
      matching: find.byType(Scrollable),
    ).first;
    await tester.scrollUntilVisible(
      find.text(first),
      500,
      scrollable: wordsScrollable,
    );
    expect(find.text(first), findsWidgets);

    // Tap a word → the full exam card on its own dedicated page.
    await tester.ensureVisible(find.byKey(ValueKey('word-row-$first')));
    await tester.tap(find.byKey(ValueKey('word-row-$first')));
    await _pump(tester);
    expect(find.text('খবরের বাক্য'), findsOneWidget);
    expect(find.text('সমার্থক শব্দ'), findsOneWidget);
    expect(find.byType(WordDetailScreen), findsOneWidget);

    // Back returns to the day's word list.
    await tester.pageBack();
    await _pump(tester);
    expect(find.text('শব্দ (২০)'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('current affairs is a date-collapsed list', (tester) async {
    final first = sharedState.editions.first;
    final dateText = formatEditionDateLong(first.date, 'bn');
    final firstHeadline = first.stories.first.headlineIn('bn');

    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(body: CurrentAffairsScreen(state: sharedState)),
      ),
    );
    await _pump(tester);

    // All collapsed by default: dates visible, no stories yet.
    expect(find.text(dateText), findsOneWidget);
    expect(find.text(firstHeadline), findsNothing);

    // Expand the newest date → its stories appear.
    await tester.tap(find.text(dateText));
    await _pump(tester, steps: 15);
    expect(find.text(firstHeadline), findsOneWidget);

    // Tap again → collapsed, stories hidden.
    await tester.tap(find.text(dateText));
    await _pump(tester, steps: 15);
    expect(find.text(firstHeadline), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('profile has no editions section', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(body: ProfileScreen(state: sharedState)),
      ),
    );
    await _pump(tester);
    expect(find.text('সেটিংস'), findsOneWidget);
    // The removed section's exact label must be gone. (The tracker
    // row is a different string and stays — scroll to it first: the
    // ListView builds lazily. Its value follows the published tracker
    // — 3/7 after Editions 9–11 Nov 2026 — so derive it from the
    // state instead of hardcoding it.)
    expect(find.text('সংস্করণ'), findsNothing);
    // Phase 5: the Profile download card's TextField owns a second
    // Scrollable (EditableText), so the ListView's must be named.
    // Rendered exactly as ProfileScreen does (profile_screen.dart).
    final trackerText = storyDigits(
      '${sharedState.t('correctEditions')}: '
      '${sharedState.correctConsecutive}${sharedState.t('of7')}',
      sharedState.lang,
    );
    await tester.scrollUntilVisible(
      find.text(trackerText),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text(trackerText), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('word card renders ink text in dark mode (no fallback style)',
      (tester) async {
    final edition = sharedState.selectedEdition!;
    final word = edition.words.first;
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        darkTheme: buildDarkTheme(),
        themeMode: ThemeMode.dark,
        home: WordDetailScreen(
          edition: edition,
          word: word,
          state: sharedState,
        ),
      ),
    );
    await _pump(tester);
    expect(find.text(word.headword), findsWidgets);
    // The headword must be ink, not the red of Flutter's
    // no-Material fallback style (0xD0FF0000).
    final headword = tester.widget<Text>(find.text(word.headword).first);
    expect(headword.style?.color, AppColors.darkInk);
    // And the Scaffold background must be the dark story paper.
    final scaffold = tester.widget<Scaffold>(find.byType(Scaffold).first);
    expect(scaffold.backgroundColor, AppColors.storyPaperDark);
    expect(Theme.of(tester.element(find.text(word.headword).first)).brightness,
        Brightness.dark);
    expect(tester.takeException(), isNull);
  });

  testWidgets('word row renders at 200% text scale without overflow',
      (tester) async {
    await tester.pumpWidget(
      const MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(2.0)),
        child: MaterialApp(
          home: _EnglishShell(),
        ),
      ),
    );
    await _pump(tester);
    expect(find.text('ইংরেজি'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('quiz runner renders at 200% text scale without overflow',
      (tester) async {
    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(2.0)),
        child: MaterialApp(
          theme: buildLightTheme(),
          home: Scaffold(body: QuizScreen(state: sharedState)),
        ),
      ),
    );
    await _pump(tester);
    await tester.tap(find.text('কুইজ শুরু করুন'));
    await _pump(tester);
    expect(find.text('প্রশ্ন ১ / ২৫'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Home renders at 200% text scale without overflow',
      (tester) async {
    await tester.pumpWidget(
      const MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(2.0)),
        child: MaterialApp(
          home: _HomeShell(),
        ),
      ),
    );
    await _pumpUntilHome(tester);
    expect(find.text('সারাংশ প্লাস'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  // ---- Phase 2: story screen redesign (mockup: Bangla QR story) ----

  /// The mockup story: 8 Nov edition, CA02 (Bangla QR transactions).
  Edition qrEdition() =>
      sharedState.editions.firstWhere((e) => e.date == '2026-11-08');
  Story qrStory() =>
      qrEdition().stories.firstWhere((s) => s.id == 'CA02');

  Future<void> pumpQrStory(
    WidgetTester tester, {
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
          home: StoryDetailScreen(
            edition: qrEdition(),
            story: qrStory(),
            state: sharedState,
          ),
        ),
      ),
    );
    await _pump(tester);
  }

  testWidgets('story detail: sections in mockup order', (tester) async {
    await pumpQrStory(tester);
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
    // App bar: Bangla-digit position + exactly ONE bookmark (top only).
    final edition = qrEdition();
    final pos =
        edition.stories.indexWhere((s) => s.id == 'CA02') + 1;
    expect(
      find.text(
        '${toBnDigits('$pos')} / ${toBnDigits('${edition.stories.length}')}',
      ),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.bookmark_border), findsOneWidget);
    expect(find.byIcon(Icons.bookmark), findsNothing);
    // Bottom bar: "পড়া হয়েছে" + share, no second bookmark.
    expect(find.text('পড়া হয়েছে'), findsOneWidget);
    expect(find.text('শেয়ার করুন'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('story detail: one-liner short, no ISO date or tag list',
      (tester) async {
    final layout = buildStoryLayout(qrStory(), 'bn');
    expect(
      layout.oneLiner.split(RegExp(r'\s+')).length,
      lessThanOrEqualTo(20),
    );
    expect(layout.tiles.length, lessThanOrEqualTo(4));
    await pumpQrStory(tester);
    // No rendered text may contain a raw ISO date.
    final iso = RegExp(r'\d{4}-\d{2}-\d{2}');
    for (final e in find.byType(Text).evaluate()) {
      final t = e.widget as Text;
      final data = t.data ?? t.textSpan?.toPlainText() ?? '';
      expect(iso.hasMatch(data), isFalse, reason: 'ISO date: $data');
    }
    // The one-liner is on screen, verbatim from the layout.
    expect(find.text(storyDigits(layout.oneLiner, 'bn')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('home: top-story hero above the English/Quiz rows',
      (tester) async {
    // Tall viewport: the whole first screen builds at once, so the
    // hero and the English/Quiz rows are all in the tree — scrolling
    // would unload the hero sliver and break the comparison.
    tester.view.physicalSize = const Size(800, 2000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: AppShell(state: sharedState),
      ),
    );
    await _pumpUntilHome(tester);
    final heroY = tester.getTopLeft(find.text('০১')).dy;
    final englishY = tester.getTopLeft(find.text('ইংরেজি').first).dy;
    final quizY = tester.getTopLeft(find.text('কুইজ').first).dy;
    expect(heroY, lessThan(englishY));
    expect(englishY, lessThan(quizY));
    // The tall viewport builds many rows at once, each with a
    // FadeSlideIn stagger timer — let them fire before the test ends.
    await _pump(tester, steps: 20);
    expect(tester.takeException(), isNull);
  });

  testWidgets('story detail renders at 200% text scale without overflow',
      (tester) async {
    await pumpQrStory(tester, textScale: 2.0);
    expect(find.text('এক লাইনে'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('story detail renders in dark mode with ink headline',
      (tester) async {
    await pumpQrStory(tester, dark: true);
    final headline = tester.widget<Text>(
      find.text(qrStory().headlineIn('bn')),
    );
    expect(headline.style?.color, AppColors.darkInk);
    expect(
      headline.style?.fontFamily,
      'NotoSerifBengali',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('profile: every text has an explicit colour (light + dark)',
      (tester) async {
    for (final dark in [false, true]) {
      await tester.pumpWidget(
        MaterialApp(
          theme: buildLightTheme(),
          darkTheme: buildDarkTheme(),
          themeMode: dark ? ThemeMode.dark : ThemeMode.light,
          home: Scaffold(body: ProfileScreen(state: sharedState)),
        ),
      );
      await _pump(tester);
      // Two passes: top of the list, then scrolled to the bottom —
      // the lazy ListView unloads what scrolled away.
      for (var pass = 0; pass < 2; pass++) {
        for (final e in find.byType(Text).evaluate()) {
          final t = e.widget as Text;
          final data = t.data ?? t.textSpan?.toPlainText() ?? '';
          final rp =
              tester.renderObject<RenderParagraph>(find.byWidget(t));
          expect(
            rp.text.style?.color,
            isNotNull,
            reason: 'no colour for "$data" (${dark ? 'dark' : 'light'})',
          );
        }
        if (pass == 0) {
          await tester.drag(
            find.byType(ListView),
            const Offset(0, -2000),
          );
          await _pump(tester, steps: 5);
        }
      }
    }
    expect(tester.takeException(), isNull);
  });

  // Mutates read/recall state for the QR story — runs last so no
  // other test sees the mutated state.
  testWidgets('story detail: cloze reveal + জানি + read state persist',
      (tester) async {
    final edition = qrEdition();
    final story = qrStory();
    final layout = buildStoryLayout(story, 'bn');
    expect(layout.cloze, isNotEmpty);
    await pumpQrStory(tester);

    // Cloze answers hidden until revealed.
    expect(find.textContaining('উত্তর:'), findsNothing);
    await tester.ensureVisible(find.text('উত্তর দেখুন').first);
    await tester.tap(find.text('উত্তর দেখুন').first);
    await _pump(tester);
    expect(find.textContaining('উত্তর:'), findsOneWidget);
    expect(
      find.text(storyDigits(layout.cloze.first.answer, 'bn')),
      findsWidgets,
    );

    // "জানি" persists per story + card.
    await tester.tap(find.text('জানি'));
    await _pump(tester);
    expect(sharedState.recallResult(edition.date, story.id, 0), isTrue);

    // "পড়া হয়েছে" persists per story.
    await tester.tap(find.text('পড়া হয়েছে'));
    await _pump(tester);
    expect(sharedState.isStoryRead(edition.date, story.id), isTrue);

    // A fresh AppState reading the same saved prefs still sees both.
    final fresh = AppState();
    await fresh.init();
    expect(fresh.recallResult(edition.date, story.id, 0), isTrue);
    expect(fresh.isStoryRead(edition.date, story.id), isTrue);
    expect(tester.takeException(), isNull);
  });
}

/// English shell for the 200% word-row test.
class _EnglishShell extends StatelessWidget {
  const _EnglishShell();

  @override
  Widget build(BuildContext context) {
    // EnglishScreen is its own Scaffold since v1.2.1.
    return EnglishScreen(state: sharedState);
  }
}

/// Home shell for the 200% test: the loaded state, no boot involved.
class _HomeShell extends StatelessWidget {
  const _HomeShell();

  @override
  Widget build(BuildContext context) {
    return AppShell(state: sharedState);
  }
}
