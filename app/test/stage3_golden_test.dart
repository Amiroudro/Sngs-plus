/// Stage 3 golden screenshots: Home, Words, Quiz home, Profile.
///
/// Light + dark, small phone (390x844) + large (768x1024), and 200%
/// text scale at the small size. First run creates the goldens:
///   flutter test test/stage3_golden_test.dart --update-goldens
/// Then READ every PNG in test/goldens/stage3/ yourself and fix any
/// overflow, invisible text or clipped label before reporting.
/// These tests assert no overflow (takeException null) as well as the
/// golden match, so a later visual regression fails loudly.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/main.dart';
import 'package:sarangsho_plus/screens/english_screen.dart';
import 'package:sarangsho_plus/screens/profile_screen.dart';
import 'package:sarangsho_plus/screens/quiz_screen.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

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

  Future<void> shot(
    WidgetTester tester,
    String name,
    Widget home, {
    Size size = const Size(390, 844),
    bool dark = false,
    double textScale = 1.0,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
        child: MaterialApp(
          theme: buildLightTheme(),
          darkTheme: buildDarkTheme(),
          themeMode: dark ? ThemeMode.dark : ThemeMode.light,
          home: home,
        ),
      ),
    );
    if (home is AppShell) {
      await _pumpUntilHome(tester);
    } else {
      await _pump(tester);
    }
    await _pump(tester, steps: 5);
    expect(tester.takeException(), isNull);
    await expectLater(
      find.byType(MaterialApp),
      matchesGoldenFile('goldens/stage3/$name.png'),
    );
  }

  group('stage3 goldens', () {
    testWidgets('home light small', (t) async {
      await shot(t, 'home_light_small', AppShell(state: sharedState));
    });
    testWidgets('home dark small', (t) async {
      await shot(
        t,
        'home_dark_small',
        AppShell(state: sharedState),
        dark: true,
      );
    });
    testWidgets('home light large', (t) async {
      await shot(
        t,
        'home_light_large',
        AppShell(state: sharedState),
        size: const Size(768, 1024),
      );
    });
    testWidgets('home light 200pct', (t) async {
      await shot(
        t,
        'home_light_200pct',
        AppShell(state: sharedState),
        textScale: 2.0,
      );
    });

    testWidgets('words light small', (t) async {
      await shot(
        t,
        'words_light_small',
        EditionWordsScreen(
          edition: sharedState.selectedEdition!,
          state: sharedState,
        ),
      );
    });
    testWidgets('words dark small', (t) async {
      await shot(
        t,
        'words_dark_small',
        EditionWordsScreen(
          edition: sharedState.selectedEdition!,
          state: sharedState,
        ),
        dark: true,
      );
    });
    testWidgets('words light large', (t) async {
      await shot(
        t,
        'words_light_large',
        EditionWordsScreen(
          edition: sharedState.selectedEdition!,
          state: sharedState,
        ),
        size: const Size(768, 1024),
      );
    });
    testWidgets('words light 200pct', (t) async {
      await shot(
        t,
        'words_light_200pct',
        EditionWordsScreen(
          edition: sharedState.selectedEdition!,
          state: sharedState,
        ),
        textScale: 2.0,
      );
    });

    testWidgets('quiz home light small', (t) async {
      await shot(
        t,
        'quiz_light_small',
        QuizScreen(state: sharedState),
      );
    });
    testWidgets('quiz home dark small', (t) async {
      await shot(
        t,
        'quiz_dark_small',
        QuizScreen(state: sharedState),
        dark: true,
      );
    });
    testWidgets('quiz home light 200pct', (t) async {
      await shot(
        t,
        'quiz_light_200pct',
        QuizScreen(state: sharedState),
        textScale: 2.0,
      );
    });

    testWidgets('profile light small', (t) async {
      await shot(
        t,
        'profile_light_small',
        Scaffold(body: ProfileScreen(state: sharedState)),
      );
    });
    testWidgets('profile dark small', (t) async {
      await shot(
        t,
        'profile_dark_small',
        Scaffold(body: ProfileScreen(state: sharedState)),
        dark: true,
      );
    });
    testWidgets('profile light 200pct', (t) async {
      await shot(
        t,
        'profile_light_200pct',
        Scaffold(body: ProfileScreen(state: sharedState)),
        textScale: 2.0,
      );
    });
  });
}
