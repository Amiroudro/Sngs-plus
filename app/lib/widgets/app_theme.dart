/// NEXUS editorial design system for Sarangsho Plus (v1.2.0 redesign).
///
/// Red / black / white newspaper system, Bengali-first.
/// * ONE accent only: cool crimson #B4232A (hue ~357, no orange), used
///   only as a thin accent — numerals, small labels, square arrow,
///   active nav item. Never a large fill, never a gradient.
/// * Paper is true white; surfaces are distinguished by hairlines, not
///   fills. News rows: radius 0, no card, no shadow. Learning surfaces:
///   radius 12, no shadow (except the flashcard, one soft shadow).
/// * Green survives ONLY as a state colour (success #1E7A46): correct
///   answers, "reviewed ✓", quiz ring at >=80%. Never a brand colour.
/// * Typography carries hierarchy: weight + size + spacing.
/// * One motion language: Cubic(0.16,1,0.3,1), 180/320/360ms.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/strings.dart';
import '../state/app_state.dart';

/// ---------------------------------------------------------------------------
/// Colours — NEXUS tokens (§2.1 of REDESIGN_PLAN.md)
/// ---------------------------------------------------------------------------
class AppColors {
  // The ONLY accent: cool crimson, blue-leaning, no orange.
  static const red = Color(0xFFB4232A);
  static const redDark = Color(0xFF8F1B21);
  static const redLight = Color(0xFFE5484D); // dark-mode accent
  static const redSoft = Color(0xFFFBECEC); // rare tint

  // Ink / paper neutrals (light).
  static const paper = Color(0xFFFFFFFF); // true white
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSoft = Color(0xFFF4F2EE); // learning surfaces only
  static const ink = Color(0xFF111110);
  static const inkSecondary = Color(0xFF5C564E);
  static const inkFaint = Color(0xFF8A847C);
  static const hairline = Color(0xFFE3DED6);
  static const amber = Color(0xFF9A6A12); // Medium relevance only
  static const amberSoft = Color(0xFFFBF3DF);
  static const error = Color(0xFFB3261E);

  /// Success green — a STATE colour only (correct answers, reviewed
  /// check, >=80% quiz ring). Never a background, button or header.
  static const success = Color(0xFF1E7A46);
  static const successLight = Color(0xFF6FC79B); // dark-mode success

  // Dark mode.
  static const darkPaper = Color(0xFF131311);
  static const darkSurface = Color(0xFF1E1E1B);
  static const darkSurfaceSoft = Color(0xFF2A2A26);
  static const darkInk = Color(0xFFF2EFE9);
  static const darkInkSecondary = Color(0xFFB8B2A8);
  static const darkInkFaint = Color(0xFF8A857C);
  static const darkHairline = Color(0xFF33332E);
  static const darkRedSoft = Color(0xFF2E1A1A);
  static const darkError = Color(0xFFFF8A80);
  static const darkAmber = Color(0xFFD9A441);

  /// Brand accent as text/icon colour for the current brightness.
  static Color accentFor(Brightness brightness) =>
      brightness == Brightness.dark ? redLight : red;

  /// Warning amber as text colour for the current brightness.
  static Color amberFor(Brightness brightness) =>
      brightness == Brightness.dark ? darkAmber : amber;

  static Color successFor(Brightness brightness) =>
      brightness == Brightness.dark ? successLight : success;

  static Color errorFor(Brightness brightness) =>
      brightness == Brightness.dark ? darkError : error;

  static Color inkFor(Brightness b) => b == Brightness.dark ? darkInk : ink;
  static Color secondaryFor(Brightness b) =>
      b == Brightness.dark ? darkInkSecondary : inkSecondary;
  static Color faintFor(Brightness b) =>
      b == Brightness.dark ? darkInkFaint : inkFaint;
  static Color paperFor(Brightness b) =>
      b == Brightness.dark ? darkPaper : paper;
  static Color surfaceFor(Brightness b) =>
      b == Brightness.dark ? darkSurface : surface;
  static Color surfaceSoftFor(Brightness b) =>
      b == Brightness.dark ? darkSurfaceSoft : surfaceSoft;
  static Color hairlineFor(Brightness b) =>
      b == Brightness.dark ? darkHairline : hairline;

  // --- Story screen tokens (Phase 2, mockup image-6) ------------------
  // Warm off-white paper, ONE accent #B3202A used only for key
  // numbers / answers. Dark mode is the same structure on a warm
  // dark paper with a restrained lighter accent.
  static const storyAccent = Color(0xFFB3202A);
  static const storyAccentDark = Color(0xFFE5484D);
  static const storyPaper = Color(0xFFFBF8F3);
  static const storyPaperDark = Color(0xFF1A1714);
  static const storySurface = Color(0xFFFFFFFF);
  static const storySurfaceDark = Color(0xFF262019);
  static const storyHairlineDark = Color(0xFF3A332B);

  static Color storyAccentFor(Brightness b) =>
      b == Brightness.dark ? storyAccentDark : storyAccent;
  static Color storyPaperFor(Brightness b) =>
      b == Brightness.dark ? storyPaperDark : storyPaper;
  static Color storySurfaceFor(Brightness b) =>
      b == Brightness.dark ? storySurfaceDark : storySurface;
  static Color storyHairlineFor(Brightness b) =>
      b == Brightness.dark ? storyHairlineDark : hairline;
}

/// ---------------------------------------------------------------------------
/// Spacing — strict 8pt grid (unchanged).
/// ---------------------------------------------------------------------------
class AppSpacing {
  static const double s4 = 4;
  static const double s8 = 8;
  static const double s12 = 12;
  static const double s16 = 16;
  static const double s24 = 24;
  static const double s32 = 32;
  static const double s48 = 48;
  static const double screen = 16;
  static const double sectionGap = 24;
  static const double cardPadding = 16;
}

/// ---------------------------------------------------------------------------
/// Radii — news 0–4px, learning 12px max.
/// ---------------------------------------------------------------------------
class AppRadii {
  static const double news = 0;
  static const double learn = 12;
  static const double button = 8;
  static const double sheet = 16;
  static const double chip = 999;
  static const double small = 4;
}

/// The one soft shadow left in the app: the flashcard only.
class AppShadows {
  static const List<BoxShadow> learn = [
    BoxShadow(
      color: Color(0x0F1C1A17),
      blurRadius: 16,
      offset: Offset(0, 4),
    ),
  ];
  static const List<BoxShadow> learnDark = [
    BoxShadow(
      color: Color(0x40000000),
      blurRadius: 16,
      offset: Offset(0, 4),
    ),
  ];
}

/// ---------------------------------------------------------------------------
/// Motion — ONE curve, ONE standard duration (unchanged).
/// ---------------------------------------------------------------------------
class AppMotion {
  static const Curve curve = Cubic(0.16, 1, 0.3, 1);
  static const Duration fast = Duration(milliseconds: 180);
  static const Duration standard = Duration(milliseconds: 320);
  static const Duration page = Duration(milliseconds: 360);
  static const Duration staggerStep = Duration(milliseconds: 45);
  static const int maxStaggerItems = 6;

  static Duration staggerDelay(int index) {
    final i = index.clamp(0, maxStaggerItems);
    return staggerStep * i;
  }
}

/// ---------------------------------------------------------------------------
/// Typography — system fonts only (no bundled font, size budget).
/// ---------------------------------------------------------------------------
class AppType {
  static const TextStyle masthead = TextStyle(
    fontSize: 30,
    height: 1.1,
    fontWeight: FontWeight.w900,
    letterSpacing: -0.5,
  );
  static const TextStyle display = TextStyle(
    fontSize: 28,
    height: 1.15,
    fontWeight: FontWeight.w900,
    letterSpacing: -0.3,
  );
  static const TextStyle title = TextStyle(
    fontSize: 22,
    height: 1.25,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle headline = TextStyle(
    fontSize: 22,
    height: 1.3,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle section = TextStyle(
    fontSize: 17,
    height: 1.35,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle body = TextStyle(
    fontSize: 16,
    height: 1.6,
    fontWeight: FontWeight.w400,
  );
  static const TextStyle bodySmall = TextStyle(
    fontSize: 14,
    height: 1.6,
    fontWeight: FontWeight.w400,
  );
  static const TextStyle caption = TextStyle(
    fontSize: 12,
    height: 1.4,
    fontWeight: FontWeight.w400,
  );
  static const TextStyle label = TextStyle(
    fontSize: 12,
    height: 1.4,
    fontWeight: FontWeight.w700,
    letterSpacing: 0.6,
  );
  static const TextStyle chip = TextStyle(
    fontSize: 13,
    height: 1.3,
    fontWeight: FontWeight.w700,
  );
  static const TextStyle numeral = TextStyle(
    fontSize: 40,
    height: 1.0,
    fontWeight: FontWeight.w900,
  );
  static const TextStyle headword = TextStyle(
    fontSize: 22,
    height: 1.3,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle headwordLarge = TextStyle(
    fontSize: 34,
    height: 1.2,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle ipa = TextStyle(
    fontSize: 15,
    height: 1.5,
    fontWeight: FontWeight.w400,
  );

  // Story screen (Phase 2): bundled fonts, offline. Noto Serif
  // Bengali has no Latin glyphs, so the headline falls back to Hind
  // Siliguri for Latin text. Body is Hind Siliguri 17sp / 1.75.
  static const TextStyle storyHeadline = TextStyle(
    fontFamily: 'NotoSerifBengali',
    fontFamilyFallback: ['HindSiliguri'],
    fontSize: 26,
    height: 1.4,
    fontWeight: FontWeight.w700,
  );
  static const TextStyle storyBody = TextStyle(
    fontFamily: 'HindSiliguri',
    fontSize: 17,
    height: 1.75,
    fontWeight: FontWeight.w400,
  );
  static const TextStyle storyOneLiner = TextStyle(
    fontFamily: 'HindSiliguri',
    fontSize: 18,
    height: 1.7,
    fontWeight: FontWeight.w600,
  );
  static const TextStyle storySection = TextStyle(
    fontFamily: 'HindSiliguri',
    fontSize: 17,
    height: 1.35,
    fontWeight: FontWeight.w800,
  );
  static const TextStyle storyLabel = TextStyle(
    fontFamily: 'HindSiliguri',
    fontSize: 13,
    height: 1.4,
    fontWeight: FontWeight.w800,
    letterSpacing: 0.4,
  );
}

/// 1px hairline under an AppBar (AppBarTheme cannot draw it).
PreferredSize appBarHairline(BuildContext context) {
  final dark = Theme.of(context).brightness == Brightness.dark;
  return PreferredSize(
    preferredSize: const Size.fromHeight(1),
    child: Container(
      height: 1,
      color: dark ? AppColors.darkHairline : AppColors.hairline,
    ),
  );
}

/// ---------------------------------------------------------------------------
/// ThemeData builders — light + dark (Material 3).
/// ---------------------------------------------------------------------------
ThemeData buildLightTheme() {
  const scheme = ColorScheme.light(
    primary: AppColors.red,
    onPrimary: Colors.white,
    secondary: AppColors.red,
    onSecondary: Colors.white,
    surface: AppColors.surface,
    onSurface: AppColors.ink,
    surfaceContainerLow: AppColors.surfaceSoft,
    error: AppColors.error,
  );
  return ThemeData(
    colorScheme: scheme,
    scaffoldBackgroundColor: AppColors.paper,
    useMaterial3: true,
    textTheme: const TextTheme(
      displayLarge: AppType.display,
      titleLarge: AppType.title,
      titleMedium: AppType.headline,
      titleSmall: AppType.section,
      bodyLarge: AppType.body,
      bodyMedium: AppType.bodySmall,
      bodySmall: AppType.caption,
      labelLarge: AppType.label,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.paper,
      foregroundColor: AppColors.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18,
        height: 1.3,
        fontWeight: FontWeight.w800,
        color: AppColors.ink,
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.surface,
      selectedColor: AppColors.ink,
      checkmarkColor: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.chip),
        side: const BorderSide(color: AppColors.hairline),
      ),
      labelStyle: AppType.chip,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.red,
        foregroundColor: Colors.white,
        disabledBackgroundColor: AppColors.hairline,
        disabledForegroundColor: AppColors.inkFaint,
        minimumSize: const Size(0, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.button),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.ink,
        minimumSize: const Size(0, 48),
        side: const BorderSide(color: AppColors.ink, width: 1.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.button),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.red,
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.all(Colors.white),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? AppColors.red
            : AppColors.hairline,
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.surface,
      selectedItemColor: AppColors.red,
      unselectedItemColor: AppColors.inkFaint,
      selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      unselectedLabelStyle: TextStyle(fontSize: 12),
      elevation: 0,
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: AppColors.red,
      unselectedLabelColor: AppColors.inkSecondary,
      indicatorColor: AppColors.red,
      indicatorSize: TabBarIndicatorSize.tab,
      labelStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
      unselectedLabelStyle: TextStyle(fontSize: 14),
    ),
    dividerTheme: const DividerThemeData(
      color: AppColors.hairline,
      thickness: 1,
      space: 1,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s16,
        vertical: 14,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.hairline),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.hairline),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.red, width: 1.5),
      ),
    ),
    pageTransitionsTheme: const PageTransitionsTheme(
      builders: {
        TargetPlatform.android: _PremiumPageTransitionsBuilder(),
        TargetPlatform.iOS: _PremiumPageTransitionsBuilder(),
      },
    ),
  );
}

ThemeData buildDarkTheme() {
  const scheme = ColorScheme.dark(
    primary: AppColors.redLight,
    onPrimary: Colors.white,
    secondary: AppColors.redLight,
    onSecondary: Colors.white,
    surface: AppColors.darkSurface,
    onSurface: AppColors.darkInk,
    surfaceContainerLow: AppColors.darkSurfaceSoft,
    error: AppColors.darkError,
  );
  return ThemeData(
    colorScheme: scheme,
    scaffoldBackgroundColor: AppColors.darkPaper,
    useMaterial3: true,
    textTheme: const TextTheme(
      displayLarge: AppType.display,
      titleLarge: AppType.title,
      titleMedium: AppType.headline,
      titleSmall: AppType.section,
      bodyLarge: AppType.body,
      bodyMedium: AppType.bodySmall,
      bodySmall: AppType.caption,
      labelLarge: AppType.label,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.darkPaper,
      foregroundColor: AppColors.darkInk,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18,
        height: 1.3,
        fontWeight: FontWeight.w800,
        color: AppColors.darkInk,
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.darkSurface,
      selectedColor: AppColors.darkInk,
      checkmarkColor: AppColors.darkPaper,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.chip),
        side: const BorderSide(color: AppColors.darkHairline),
      ),
      labelStyle: AppType.chip,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.redLight,
        foregroundColor: Colors.white,
        disabledBackgroundColor: AppColors.darkHairline,
        disabledForegroundColor: AppColors.darkInkFaint,
        minimumSize: const Size(0, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.button),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.darkInk,
        minimumSize: const Size(0, 48),
        side: const BorderSide(color: AppColors.darkInk, width: 1.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.button),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.redLight,
        textStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.all(Colors.white),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? AppColors.redLight
            : AppColors.darkHairline,
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.darkSurface,
      selectedItemColor: AppColors.redLight,
      unselectedItemColor: AppColors.darkInkFaint,
      selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      unselectedLabelStyle: TextStyle(fontSize: 12),
      elevation: 0,
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: AppColors.redLight,
      unselectedLabelColor: AppColors.darkInkSecondary,
      indicatorColor: AppColors.redLight,
      indicatorSize: TabBarIndicatorSize.tab,
      labelStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
      unselectedLabelStyle: TextStyle(fontSize: 14),
    ),
    dividerTheme: const DividerThemeData(
      color: AppColors.darkHairline,
      thickness: 1,
      space: 1,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.darkSurface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s16,
        vertical: 14,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.darkHairline),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.darkHairline),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.small),
        borderSide: const BorderSide(color: AppColors.redLight, width: 1.5),
      ),
    ),
    pageTransitionsTheme: const PageTransitionsTheme(
      builders: {
        TargetPlatform.android: _PremiumPageTransitionsBuilder(),
        TargetPlatform.iOS: _PremiumPageTransitionsBuilder(),
      },
    ),
  );
}

/// One page transition everywhere: soft fade + small upward slide.
class _PremiumPageTransitionsBuilder extends PageTransitionsBuilder {
  const _PremiumPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    final curved = CurvedAnimation(parent: animation, curve: AppMotion.curve);
    return FadeTransition(
      opacity: curved,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.03),
          end: Offset.zero,
        ).animate(curved),
        child: child,
      ),
    );
  }
}

/// ---------------------------------------------------------------------------
/// Shared widgets
/// ---------------------------------------------------------------------------

/// Learning surface: barely-off-white, radius 12, no border, no shadow.
/// Used on learning screens only — never on news screens.
///
/// The [Material] wrapper is load-bearing, not decorative: without a
/// [Material] ancestor, [Text] widgets fall back to Flutter's error
/// text style (red, monospace, yellow double underline). LearnSurface
/// is used on Scaffold-less routes and inside bottom sheets, so it
/// must supply a proper [DefaultTextStyle] itself.
class LearnSurface extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;
  final VoidCallback? onTap;

  const LearnSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.cardPadding),
    this.margin = const EdgeInsets.symmetric(
      horizontal: AppSpacing.screen,
      vertical: 4,
    ),
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final box = Container(
      margin: margin,
      padding: padding,
      decoration: BoxDecoration(
        color: dark ? AppColors.darkSurfaceSoft : AppColors.surfaceSoft,
        borderRadius: BorderRadius.circular(AppRadii.learn),
      ),
      child: child,
    );
    // Material supplies the ambient DefaultTextStyle (theme body text,
    // ink colour). Without it, text inside falls back to Flutter's
    // red-monospace-yellow-underline error style.
    final surfaced = Material(
      color: Colors.transparent,
      child: box,
    );
    if (onTap == null) return surfaced;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadii.learn),
        child: box,
      ),
    );
  }
}

/// One designed empty state for every screen: square hairline icon
/// tile with a red icon, a 64px hairline rule, title, one-line body.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String? title;
  final String body;
  final String? actionLabel;
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    required this.icon,
    this.title,
    required this.body,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: dark ? AppColors.darkSurface : AppColors.surface,
                border: Border.all(
                  color: dark ? AppColors.darkHairline : AppColors.hairline,
                ),
              ),
              child: Icon(icon, size: 32, color: accent),
            ),
            const SizedBox(height: 16),
            Container(
              width: 64,
              height: 1,
              color: dark ? AppColors.darkHairline : AppColors.hairline,
            ),
            if (title != null) ...[
              const SizedBox(height: 16),
              Text(
                title!,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
            const SizedBox(height: 6),
            Text(
              body,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                height: 1.6,
                color:
                    dark ? AppColors.darkInkSecondary : AppColors.inkSecondary,
              ),
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// News section label: small red label above an ink heading, hairline
/// below the pair. News screens only.
class NewsSectionLabel extends StatelessWidget {
  final String label;
  final String heading;
  final Widget? trailing;

  const NewsSectionLabel({
    super.key,
    required this.label,
    required this.heading,
    this.trailing,
  });

  /// Heading-only variant (no red label line).
  const NewsSectionLabel.heading(this.heading, {super.key, this.trailing})
      : label = '';

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label.isNotEmpty) ...[
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.6,
              color: accent,
            ),
          ),
          const SizedBox(height: 2),
        ],
        Row(
          children: [
            Expanded(
              child: Text(heading, style: AppType.section),
            ),
            if (trailing != null) trailing!,
          ],
        ),
        const SizedBox(height: 8),
        Container(
          height: 1,
          color: dark ? AppColors.darkHairline : AppColors.hairline,
        ),
      ],
    );
  }
}

/// Learning section label: plain ink 13px w800. Learning screens only.
class LearnSectionLabel extends StatelessWidget {
  final String text;
  final Widget? trailing;

  const LearnSectionLabel(this.text, {super.key, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.s8),
      child: Row(
        children: [
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

/// Staggered list entry: soft fade + 12px rise on the single motion
/// curve. Animate on first build only — callers pass index < 6 for the
/// stagger; rows beyond that render immediately.
class FadeSlideIn extends StatefulWidget {
  final Widget child;
  final int index;

  const FadeSlideIn({super.key, required this.child, this.index = 0});

  @override
  State<FadeSlideIn> createState() => _FadeSlideInState();
}

class _FadeSlideInState extends State<FadeSlideIn>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final Animation<double> _a;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: AppMotion.standard);
    _a = CurvedAnimation(parent: _c, curve: AppMotion.curve);
    final delay = AppMotion.staggerDelay(widget.index);
    if (delay == Duration.zero) {
      _c.forward();
    } else {
      Timer(delay, () {
        if (mounted) _c.forward();
      });
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _a,
      builder: (context, child) => Opacity(
        opacity: _a.value,
        child: Transform.translate(
          offset: Offset(0, 12 * (1 - _a.value)),
          child: child,
        ),
      ),
      child: widget.child,
    );
  }
}

/// Skeleton placeholder — pulsing blocks, not a spinner.
class SkeletonBox extends StatefulWidget {
  final double height;
  final double? width;
  final double radius;

  const SkeletonBox({
    super.key,
    required this.height,
    this.width,
    this.radius = AppRadii.small,
  });

  @override
  State<SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<SkeletonBox>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return AnimatedBuilder(
      animation: _c,
      builder: (context, _) => Container(
        height: widget.height,
        width: widget.width,
        decoration: BoxDecoration(
          color: (dark ? AppColors.darkSurfaceSoft : AppColors.surfaceSoft)
              .withValues(alpha: 0.55 + 0.35 * _c.value),
          borderRadius: BorderRadius.circular(widget.radius),
        ),
      ),
    );
  }
}

extension AppStateStrings on AppState {
  Map<String, String> get strings => stringsFor(lang);
  String t(String key) => strings[key] ?? key;
}

/// Opens a URL in the external browser. Returns false when the URL is
/// missing or cannot be launched.
Future<bool> openExternalUrl(String? url) async {
  if (url == null || url.trim().isEmpty) return false;
  final uri = Uri.tryParse(url.trim());
  if (uri == null) return false;
  if (!await canLaunchUrl(uri)) return false;
  return launchUrl(uri, mode: LaunchMode.externalApplication);
}
