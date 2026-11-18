/// Stage 2 tests: design tokens, AppShapes, theme-level shapes,
/// and the reusable components built in Stage 2 (MetaPill,
/// NumberedStoryRow, TopStoryHero, Masthead). Behaviour tests
/// (bookmarks, quiz, SRS, search) live in the other test files and
/// are untouched here.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:sarangsho_plus/widgets/masthead.dart';
import 'package:sarangsho_plus/widgets/story_card.dart';

Edition _fixtureEdition() {
  final story = Story(
    id: 'CA01',
    headline: 'পরীক্ষার শিরোনাম',
    category: 'জাতীয়',
    summary: 'সারসংক্ষেপ।',
    examRelevance: 'High',
    sources: const [],
  );
  return Edition(
    date: '2026-11-17',
    stories: [story],
    words: const [],
    revisionWords: const [],
    phrases: const [],
    mcqs: const [],
    sources: const [],
    counts: const {'stories': 1, 'words': 0, 'mcqs': 0},
  );
}

void main() {
  test('2.0 colour tokens (light + dark accent)', () {
    // Palette set by Rudro 2026-11-18 (replaces NEXUS red): Forest
    // Green #1E3A2B primary, Oat #EEE6D6 light paper, Flamingo Pink
    // #FF7AB8 restrained accent. Text accent is the darkened pink on
    // light / lightened pink on dark — never raw pink (1.94:1 on oat).
    expect(AppColors.forest, const Color(0xFF1E3A2B));
    expect(AppColors.oat, const Color(0xFFEEE6D6));
    expect(AppColors.pink, const Color(0xFFFF7AB8));
    expect(AppColors.pinkText, const Color(0xFF9E2A5C));
    expect(AppColors.pinkLight, const Color(0xFFFF9ECB));
    expect(
      AppColors.accentFor(Brightness.light),
      AppColors.pinkText,
    );
    expect(AppColors.accentFor(Brightness.dark), AppColors.pinkLight);
    // Primary fills: forest on light, lighter forest on dark; white
    // text on both.
    expect(AppColors.primaryFor(Brightness.light), AppColors.forest);
    expect(
      AppColors.primaryFor(Brightness.dark),
      AppColors.forestLight,
    );
    expect(AppColors.paper, const Color(0xFFEEE6D6));
    expect(AppColors.ink, const Color(0xFF111110));
    expect(AppColors.paperFor(Brightness.dark), const Color(0xFF14261C));
    expect(AppColors.inkFor(Brightness.dark), const Color(0xFFEEE6D6));
    // Success is a forest shade now, error a pink shade — no new hues.
    expect(AppColors.success, AppColors.forest);
    expect(AppColors.error, AppColors.pinkText);
  });

  test('radii + type tokens match MASTER.md §2.2–§3.3', () {
    expect(AppRadii.news, 0);
    expect(AppRadii.learn, 12);
    expect(AppRadii.button, 8);
    expect(AppRadii.sheet, 16);
    expect(AppRadii.chip, 999);
    expect(AppRadii.small, 4);
    expect(AppType.title.fontSize, 20);
    expect(AppType.masthead.fontSize, 30);
    expect(AppType.numeral.fontSize, 40);
    expect(AppType.headword.fontSize, 22);
    expect(AppType.headwordLarge.fontSize, 34);
    expect(AppType.ipa.fontSize, 15);
    expect(AppShadows.none, isEmpty);
    expect(AppShadows.learn, hasLength(1));
  });

  test('AppShapes roles read the token values (one-line change test)', () {
    // The roles ARE the token values: editing a role here changes
    // every use of that role with no other file edited.
    expect(AppShapes.card.radius, BorderRadius.circular(AppRadii.news));
    expect(AppShapes.cardSoft.radius, BorderRadius.circular(AppRadii.learn));
    expect(AppShapes.button.radius, BorderRadius.circular(AppRadii.button));
    expect(AppShapes.button.minHeight, AppSpacing.s48);
    expect(AppShapes.chip.radius, BorderRadius.circular(AppRadii.chip));
    expect(AppShapes.input.radius, BorderRadius.circular(AppRadii.small));
    expect(AppShapes.dialog.radius, BorderRadius.circular(AppRadii.learn));
    expect(AppShapes.sheet.topLeft, const Radius.circular(AppRadii.sheet));
    expect(AppShapes.sheet.bottomLeft, Radius.zero);
    expect(AppShapes.box, BorderRadius.zero);
    expect(AppShapes.cardSoft.padding,
        const EdgeInsets.all(AppSpacing.s16));
    // Borders resolve per brightness from the hairline token.
    expect(
      AppShapes.card.borderFor(Brightness.light).color,
      AppColors.hairline,
    );
    expect(
      AppShapes.card.borderFor(Brightness.dark).color,
      AppColors.darkHairline,
    );
    expect(AppShapes.card.borderFor(Brightness.light).width, 1);
    expect(AppShapes.cardSoft.borderFor(Brightness.light),
        BorderSide.none);
    final deco = AppShapes.cardSoft.decoration(
      Brightness.light,
      color: AppColors.surfaceSoft,
    );
    expect(deco.borderRadius, BorderRadius.circular(AppRadii.learn));
    expect(deco.color, AppColors.surfaceSoft);
  });

  test('theme-level widgets read AppShapes (light + dark)', () {
    final light = buildLightTheme();
    final dark = buildDarkTheme();
    Color? resolve(ButtonStyle? s, Set<WidgetState> states) =>
        s?.backgroundColor?.resolve(states);
    expect(resolve(light.filledButtonTheme.style, {}), AppColors.forest);
    expect(
      resolve(dark.filledButtonTheme.style, {}),
      AppColors.forestLight,
    );
    expect(light.segmentedButtonTheme.style, isNotNull);
    expect(dark.segmentedButtonTheme.style, isNotNull);
    expect(
      resolve(light.segmentedButtonTheme.style, {WidgetState.selected}),
      AppColors.ink,
    );
    expect(
      resolve(dark.segmentedButtonTheme.style, {WidgetState.selected}),
      AppColors.darkInk,
    );
    expect(light.dialogTheme.shape, isNotNull);
    expect(light.bottomSheetTheme.shape, isNotNull);
    expect(
      light.inputDecorationTheme.focusedBorder?.borderSide.color,
      AppColors.pinkText,
    );
    expect(
      light.inputDecorationTheme.focusedBorder?.borderSide.width,
      AppShapes.strongBorderWidth,
    );
    expect(
      dark.inputDecorationTheme.focusedBorder?.borderSide.color,
      AppColors.pinkLight,
    );
  });

  testWidgets('MetaPill renders square pill with text + icon',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: const Scaffold(
          body: MetaPill(text: 'ডাউনলোড করা', icon: Icons.check),
        ),
      ),
    );
    expect(find.text('ডাউনলোড করা'), findsOneWidget);
    expect(find.byIcon(Icons.check), findsOneWidget);
  });

  testWidgets('EmptyState renders body and fires its action',
      (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(
          body: EmptyState(
            icon: Icons.search,
            body: 'কিছু পাওয়া যায়নি',
            actionLabel: 'আবার চেষ্টা করুন',
            onAction: () => tapped = true,
          ),
        ),
      ),
    );
    expect(find.text('কিছু পাওয়া যায়নি'), findsOneWidget);
    expect(find.byIcon(Icons.search), findsOneWidget);
    await tester.tap(find.text('আবার চেষ্টা করুন'));
    expect(tapped, isTrue);
  });

  testWidgets('LearnSurface renders its child on the soft surface',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: const Scaffold(
          body: LearnSurface(child: Text('শেখার পৃষ্ঠা')),
        ),
      ),
    );
    expect(find.text('শেখার পৃষ্ঠা'), findsOneWidget);
  });

  testWidgets('NumberedStoryRow renders numeral, headline, arrow',
      (tester) async {
    final edition = _fixtureEdition();
    final state = AppState();
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(
          body: NumberedStoryRow(
            edition: edition,
            story: edition.stories.first,
            state: state,
            onTap: () {},
            index: 1,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('০২'), findsOneWidget);
    expect(find.text('পরীক্ষার শিরোনাম'), findsOneWidget);
    expect(find.byIcon(Icons.arrow_forward), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('TopStoryHero renders giant numeral + top-story label',
      (tester) async {
    final edition = _fixtureEdition();
    final state = AppState();
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(
          body: TopStoryHero(
            edition: edition,
            story: edition.stories.first,
            state: state,
            onTap: () {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('০১'), findsOneWidget);
    expect(find.text('প্রধান খবর'), findsOneWidget);
    expect(find.text('পরীক্ষার শিরোনাম'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('StoryCard delegates: hero flag picks TopStoryHero',
      (tester) async {
    final edition = _fixtureEdition();
    final state = AppState();
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(
          body: StoryCard(
            edition: edition,
            story: edition.stories.first,
            state: state,
            onTap: () {},
            hero: true,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('প্রধান খবর'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Masthead renders wordmark + dateline',
      (tester) async {
    final edition = _fixtureEdition();
    final state = AppState();
    state.editions = [edition];
    await tester.pumpWidget(
      MaterialApp(
        theme: buildLightTheme(),
        home: Scaffold(
          body: Masthead(
            state: state,
            greeting: 'শুভ সকাল',
            onEditionTap: () {},
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.text('সারাংশ প্লাস'), findsOneWidget);
    expect(find.text('শুভ সকাল'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
