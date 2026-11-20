/// Editorial design system for Sarangsho Plus (2.0 palette).
///
/// Forest Green / Oat / Flamingo Pink (Rudro, 2026-11-18 — replaces
/// the NEXUS red-black-white palette; layout and components stay).
/// * Forest #1E3A2B is the primary: logo block, numeral block, square
///   arrow buttons, primary buttons, dark-mode base. White text on it.
/// * Oat #EEE6D6 is the light paper/surface. Ink text on oat is 15:1.
/// * Pink #FF7AB8 is a restrained accent ONLY: dots, indicators,
///   active states, small pops. Never a large pink surface, never
///   pink body text (1.94:1 on oat) — text uses darkened pink
///   #9E2A5C (light) / lightened pink #FF9ECB (dark).
/// * Paper is oat; surfaces are distinguished by hairlines, not
///   fills. News rows: radius 0, no card, no shadow. Learning surfaces:
///   radius 12, no shadow (except the flashcard, one soft shadow).
/// * Success is a forest shade, error a pink shade — no new hues.
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
  // --- The 2.0 palette (Rudro, 2026-11-18 — replaces NEXUS red) ---------
  // Forest Green #1E3A2B: primary/deep — headers, primary elements,
  // dark-mode base. Oat #EEE6D6: light background/surface.
  // Flamingo Pink #FF7AB8: restrained accent ONLY — small pops,
  // indicators, active states. Never a large pink surface, never pink
  // body text: raw pink on oat is 1.94:1. Text uses the darkened pink
  // `pinkText` (light) or the lightened pink `pinkLight` (dark).
  // Only these three hues plus their tints/shades plus neutral text
  // colours — no new hues. Success is a forest shade, error a pink
  // shade, medium relevance a neutral (see below).
  static const forest = Color(0xFF1E3A2B);
  static const forestLight = Color(0xFF2F5442); // dark-mode primary fill
  static const oat = Color(0xFFEEE6D6);
  static const oatSoft = Color(0xFFF5EFE0); // lighter oat tint
  static const pink = Color(0xFFFF7AB8);
  static const pinkText = Color(0xFF9E2A5C); // darkened pink, text on light
  static const pinkLight = Color(0xFFFF9ECB); // lightened pink, text on dark
  static const pinkSoft = Color(0xFFF9DCE8); // rare light pink tint

  // Ink / paper neutrals (light) — oat paper, near-black ink.
  static const paper = oat;
  static const surface = oat;
  static const surfaceSoft = oatSoft;
  static const ink = Color(0xFF111110);
  static const inkSecondary = Color(0xFF5C564E);
  // Darkened from the old #8A847C: 4.77:1 on oat (the old value was
  // 2.98:1 on oat and failed WCAG for 12px captions).
  static const inkFaint = Color(0xFF6B6357);
  static const hairline = Color(0xFFB5A67F); // oat-dark divider, visible
  static const error = pinkText;

  /// Success is a STATE colour only (correct answers, reviewed
  /// check, >=80% quiz ring) — a forest shade, never a new hue.
  static const success = forest;
  static const successLight = Color(0xFF7FB89A); // dark-mode success

  // Dark mode — base is Forest Green.
  static const darkPaper = Color(0xFF14261C); // darker forest shade
  static const darkSurface = forest;
  static const darkSurfaceSoft = Color(0xFF2A4A3A); // lighter forest tint
  static const darkInk = oat;
  static const darkInkSecondary = Color(0xFFCFC6B2); // muted oat
  static const darkInkFaint = Color(0xFFBFB69E); // dim oat (4.86:1 on soft)
  static const darkHairline = Color(0xFF33503F);
  static const darkPinkSoft = Color(0xFF3A2430);
  static const darkError = pinkLight;

  /// Text accent for the current brightness: darkened pink on light
  /// (5.76:1 on oat), lightened pink on dark (8.31:1 on dark paper).
  /// Use for accent TEXT (numerals, category labels, active tab,
  /// search highlight, quiz mode label). Never for a fill behind
  /// white text — use [primaryFor] for fills.
  static Color accentFor(Brightness brightness) =>
      brightness == Brightness.dark ? pinkLight : pinkText;

  /// Primary fill for the current brightness: forest on light, a
  /// lighter forest on dark. White text/icons on it in both modes
  /// (12.39:1 light, 8.51:1 dark). Use for the logo block, numeral
  /// block, square arrow buttons, icon tiles, primary buttons.
  static Color primaryFor(Brightness brightness) =>
      brightness == Brightness.dark ? forestLight : forest;

  /// Text/icon colour on a raw-pink accent fill: white on light,
  /// forest on dark (raw pink takes dark text in dark mode).
  static Color onAccentFor(Brightness brightness) =>
      brightness == Brightness.dark ? forest : Colors.white;

  /// Raw pink pop (non-text only): dots, indicator bars, progress
  /// value, switch track, selected-option border. Never text.
  static const Color pop = pink;

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
  // The Story screen is restyled LAST (after the corrected
  // learning-module model). Its tokens keep the "one accent" shape
  // but now point at the 2.0 palette: the accent is the primary
  // (forest) because the story screen uses it as a FilledButton
  // background behind WHITE text — raw pink would be 2.41:1 there.
  // Text and fill are SPLIT (Stage 4): small label text in the fill
  // accent (forestLight) is only 2.10:1 on the warm dark story paper
  // #1A1714, so text uses [storyTextAccentFor] instead.
  static const storyAccent = forest;
  static const storyAccentDark = forestLight;

  /// Text accent for the Story screen ONLY: small labels, tile
  /// values, Q→A answers and cloze text. Light keeps forest
  /// (11.69:1 on story paper #FBF8F3, 12.39:1 on story surface
  /// #FFFFFF); dark uses the lighter forest tint successLight
  /// #7FB89A (7.84:1 on story paper #1A1714, 7.08:1 on story surface
  /// #262019) — the same hue family as the fill accent, so the
  /// screen keeps its one-accent identity. Fills (primary button,
  /// chart bars, relevance dots) keep [storyAccentFor]: white text
  /// on forestLight is 8.51:1.
  static const storyTextAccent = forest;
  static const storyTextAccentDark = successLight;

  static Color storyTextAccentFor(Brightness b) =>
      b == Brightness.dark ? storyTextAccentDark : storyTextAccent;
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
  /// News system: shadows deleted entirely.
  static const List<BoxShadow> none = [];

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
/// Shapes — ONE centralized shape system (MASTER.md §3.4).
///
/// Every box, round, corner, button and shape in the app comes from
/// here. [AppShapes] is the semantic layer on top of the raw
/// [AppRadii] numbers: the NEXUS radii ARE the shape tokens' values,
/// so the two can never drift apart.
///
/// * The default shape is the **box** (radius 0), used most of the
///   time: every news surface, row, tile, the masthead logo block,
///   the numeral block, the square arrow button, the bottom nav.
/// * Variants ([box]/[small]/[medium]/[soft]/[round]/[sheet]) are
///   used on demand only, via a [ShapeRole].
/// * A screen that needs a shape it does not have asks [AppShapes]
///   for a variant — it never invents a radius inline. If no existing
///   role fits, add a role; do not reuse a wrong role.
///
/// One-line change test: editing one value in [AppShapes] changes
/// every use of that role across all five tabs with no other file
/// edited. Theme-level widgets ([buildLightTheme]/[buildDarkTheme])
/// and components ([LearnSurface], [MetaPill]) read their shapes
/// from here too, so theme and components agree by construction.
///
/// The roles hold theme-independent geometry only (radius, padding,
/// border width, min height, shadows). Colours are resolved per
/// brightness through [ShapeRole.borderFor]/[ShapeRole.decoration],
/// which read [AppColors] — never a literal colour or number in a
/// role. The three dimensions with no [AppSpacing] token
/// ([inputVerticalPadding], [metaPillRadius]) are named constants
/// owned here, so the roles themselves contain no literals.
/// ---------------------------------------------------------------------------
class ShapeRole {
  /// Corner radii for this role.
  final BorderRadius radius;

  /// Inner padding for this role.
  final EdgeInsets padding;

  /// Border width in logical pixels; 0 means no border.
  final double borderWidth;

  /// Minimum height (buttons), or null when the role has none.
  final double? minHeight;

  /// Shadows for this role (news roles: [AppShadows.none]).
  final List<BoxShadow> shadows;

  const ShapeRole({
    required this.radius,
    required this.padding,
    this.borderWidth = 0,
    this.minHeight,
    this.shadows = const [],
  });

  /// The role's border in the current brightness. The colour is the
  /// hairline token (or [color] when a caller needs pink, e.g. a
  /// focused input); the width comes from the role.
  BorderSide borderFor(Brightness brightness, {Color? color}) {
    if (borderWidth == 0) return BorderSide.none;
    return BorderSide(
      color: color ?? AppColors.hairlineFor(brightness),
      width: borderWidth,
    );
  }

  /// A full [BoxDecoration] for this role: radius + border + shadow,
  /// filled with [color].
  BoxDecoration decoration(
    Brightness brightness, {
    required Color color,
    Color? borderColor,
  }) {
    return BoxDecoration(
      color: color,
      borderRadius: radius,
      border: borderWidth == 0
          ? null
          : Border.all(
              color: borderColor ?? AppColors.hairlineFor(brightness),
              width: borderWidth,
            ),
      boxShadow: shadows,
    );
  }
}

class AppShapes {
  /// 1px hairline border width (cards, chips, inputs).
  static const double hairlineWidth = 1;

  /// 1.5px border width (focused input, selected option).
  static const double strongBorderWidth = 1.5;

  /// Input vertical padding — 14px; no [AppSpacing] token exists
  /// for 14, so the shape system owns this value.
  static const double inputVerticalPadding = 14;

  /// MetaPill corner radius — 2px (square pill); no [AppRadii]
  /// token exists for 2, so the shape system owns this value.
  static const double metaPillRadius = 2;

  // --- Variants (on demand only) -------------------------------------
  /// Default shape: box, square corners. Used most of the time.
  static BorderRadius get box => BorderRadius.circular(AppRadii.news);

  /// 4px: search field, rendered share card.
  static BorderRadius get small => BorderRadius.circular(AppRadii.small);

  /// 8px: buttons.
  static BorderRadius get medium => BorderRadius.circular(AppRadii.button);

  /// 12px: learning surfaces (LearnSurface, flashcard).
  static BorderRadius get soft => BorderRadius.circular(AppRadii.learn);

  /// 999px: chips — the one round element, learning contexts only.
  static BorderRadius get round => BorderRadius.circular(AppRadii.chip);

  /// 16px, top corners only: bottom sheets.
  static BorderRadius get sheet =>
      const BorderRadius.vertical(top: Radius.circular(AppRadii.sheet));

  /// 2px: MetaPill.
  static BorderRadius get metaPill =>
      BorderRadius.circular(metaPillRadius);

  // --- Semantic roles --------------------------------------------------
  /// News rows, story rows, saved-story rows: a "card" here is a
  /// ruled row, not a rounded card. Box, 16px padding, 1px hairline
  /// border, no shadow.
  static const ShapeRole card = ShapeRole(
    radius: BorderRadius.zero,
    padding: EdgeInsets.all(AppSpacing.s16),
    borderWidth: hairlineWidth,
  );

  /// Learning surfaces: LearnSurface, collapsed word rows, phrase
  /// cards, revision rows, quiz mode/review/mistake items, Profile
  /// cards. Soft 12px, 16px padding, no border, no shadow.
  static const ShapeRole cardSoft = ShapeRole(
    radius: BorderRadius.all(Radius.circular(AppRadii.learn)),
    padding: EdgeInsets.all(AppSpacing.s16),
  );

  /// Primary / secondary / text buttons: always medium 8px, min
  /// height 48px, horizontal 16px / vertical 12px padding.
  static const ShapeRole button = ShapeRole(
    radius: BorderRadius.all(Radius.circular(AppRadii.button)),
    padding: EdgeInsets.symmetric(
      horizontal: AppSpacing.s16,
      vertical: AppSpacing.s12,
    ),
    minHeight: AppSpacing.s48,
  );

  /// Font-size chips, search-recents ActionChips, word-form /
  /// exam-type chips: always round, horizontal 12px / vertical 8px,
  /// 1px hairline border.
  static const ShapeRole chip = ShapeRole(
    radius: BorderRadius.all(Radius.circular(AppRadii.chip)),
    padding: EdgeInsets.symmetric(
      horizontal: AppSpacing.s12,
      vertical: AppSpacing.s8,
    ),
    borderWidth: hairlineWidth,
  );

  /// Masthead block, TopStoryHero, story banner/hero image area:
  /// box, full-bleed, 16px padding. (The 1px hairline *below* a
  /// banner is a layout rule, not a box border.)
  static const ShapeRole banner = ShapeRole(
    radius: BorderRadius.zero,
    padding: EdgeInsets.all(AppSpacing.s16),
  );

  /// Share-preview dialog, alerts: 12px, 16px padding.
  /// Use [sheet] when the dialog is a bottom sheet.
  static const ShapeRole dialog = ShapeRole(
    radius: BorderRadius.all(Radius.circular(AppRadii.learn)),
    padding: EdgeInsets.all(AppSpacing.s16),
  );

  /// Search field: always small 4px, horizontal 16px / vertical
  /// 14px, 1px hairline border (focused: 1.5px pink — applied by the
  /// input theme, not the role).
  static const ShapeRole input = ShapeRole(
    radius: BorderRadius.all(Radius.circular(AppRadii.small)),
    padding: EdgeInsets.symmetric(
      horizontal: AppSpacing.s16,
      vertical: inputVerticalPadding,
    ),
    borderWidth: hairlineWidth,
  );
}

/// ---------------------------------------------------------------------------
/// AppShape + AppBox — the ONE place a screen asks for a shape.
///
/// Screens never write a radius. They use [AppBox] and, only when a
/// page needs something other than the default square box, pass a
/// named [AppShape]. Changing what "soft" or "round" means (or the
/// app-wide default) is one edit in [AppShapes], and every page
/// follows. See docs/AI_GUIDE.md "UI rules".
/// ---------------------------------------------------------------------------
enum AppShape {
  /// Default: square corners.
  box,

  /// 4px corners.
  small,

  /// 8px corners (buttons).
  medium,

  /// 12px corners (learning surfaces).
  soft,

  /// Fully rounded ends (chips, pills).
  round,

  /// Perfect circle (avatars, number badges). Use on square boxes.
  circle,

  /// Rounded top corners only (bottom sheets).
  sheet,
}

extension AppShapeRadius on AppShape {
  /// Corner radii for this shape. [AppShape.circle] has no corner
  /// radius of its own (it is a [BoxShape.circle]); it reports the
  /// pill radius for callers that only need a clip radius.
  BorderRadius get radius {
    switch (this) {
      case AppShape.box:
        return AppShapes.box;
      case AppShape.small:
        return AppShapes.small;
      case AppShape.medium:
        return AppShapes.medium;
      case AppShape.soft:
        return AppShapes.soft;
      case AppShape.round:
      case AppShape.circle:
        return AppShapes.round;
      case AppShape.sheet:
        return AppShapes.sheet;
    }
  }
}

/// A themed container. Pass a [role] for padding/border/shadow
/// defaults (e.g. [AppShapes.card]) and, only when needed, a [shape]
/// to override the role's corners.
class AppBox extends StatelessWidget {
  final Widget? child;

  /// Padding, border width and shadows come from this role. Defaults
  /// to [AppShapes.banner] (square, 16px padding, no border).
  final ShapeRole role;

  /// Optional corner override; null keeps the role's own corners.
  final AppShape? shape;

  /// Fill colour; null means transparent.
  final Color? color;

  /// Draw the role's hairline border (only if the role has one).
  final bool bordered;

  /// Overrides the role's padding when set.
  final EdgeInsetsGeometry? padding;

  const AppBox({
    super.key,
    this.child,
    this.role = AppShapes.banner,
    this.shape,
    this.color,
    this.bordered = true,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final isCircle = shape == AppShape.circle;
    final radius = shape?.radius ?? role.radius;
    final side = bordered
        ? role.borderFor(brightness)
        : BorderSide.none;
    return Container(
      padding: padding ?? role.padding,
      constraints: role.minHeight == null
          ? null
          : BoxConstraints(minHeight: role.minHeight!),
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: color,
        shape: isCircle ? BoxShape.circle : BoxShape.rectangle,
        borderRadius: isCircle ? null : radius,
        border: side == BorderSide.none ? null : Border.fromBorderSide(side),
        boxShadow: role.shadows,
      ),
      child: child,
    );
  }
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
    fontSize: 20,
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
    primary: AppColors.forest,
    onPrimary: Colors.white,
    secondary: AppColors.pinkText,
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
        borderRadius: AppShapes.chip.radius,
        side: AppShapes.chip.borderFor(Brightness.light),
      ),
      labelStyle: AppType.chip,
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? AppColors.ink
              : AppColors.paper,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? Colors.white
              : AppColors.ink,
        ),
        side: WidgetStateProperty.all(
          const BorderSide(
            color: AppColors.hairline,
            width: AppShapes.hairlineWidth,
          ),
        ),
        shape: WidgetStateProperty.all(
          RoundedRectangleBorder(borderRadius: AppShapes.button.radius),
        ),
        textStyle: WidgetStateProperty.all(
          const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(borderRadius: AppShapes.dialog.radius),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: AppColors.surface,
      modalBackgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(borderRadius: AppShapes.sheet),
      dragHandleColor: AppColors.inkFaint,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.forest,
        foregroundColor: Colors.white,
        disabledBackgroundColor: AppColors.hairline,
        disabledForegroundColor: AppColors.inkFaint,
        minimumSize: const Size(0, 48),
        shape: RoundedRectangleBorder(
          borderRadius: AppShapes.button.radius,
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
          borderRadius: AppShapes.button.radius,
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.pinkText,
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
            ? AppColors.pink
            : AppColors.hairline,
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.surface,
      selectedItemColor: AppColors.pinkText,
      unselectedItemColor: AppColors.inkFaint,
      selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      unselectedLabelStyle: TextStyle(fontSize: 12),
      elevation: 0,
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: AppColors.pinkText,
      unselectedLabelColor: AppColors.inkSecondary,
      indicatorColor: AppColors.pinkText,
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
      contentPadding: AppShapes.input.padding,
      border: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: AppShapes.input.borderFor(Brightness.light),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: AppShapes.input.borderFor(Brightness.light),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: const BorderSide(
          color: AppColors.pinkText,
          width: AppShapes.strongBorderWidth,
        ),
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
    primary: AppColors.pinkLight,
    onPrimary: AppColors.forest,
    secondary: AppColors.pinkLight,
    onSecondary: AppColors.forest,
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
        borderRadius: AppShapes.chip.radius,
        side: AppShapes.chip.borderFor(Brightness.dark),
      ),
      labelStyle: AppType.chip,
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? AppColors.darkInk
              : AppColors.darkSurface,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? AppColors.darkPaper
              : AppColors.darkInk,
        ),
        side: WidgetStateProperty.all(
          const BorderSide(
            color: AppColors.darkHairline,
            width: AppShapes.hairlineWidth,
          ),
        ),
        shape: WidgetStateProperty.all(
          RoundedRectangleBorder(borderRadius: AppShapes.button.radius),
        ),
        textStyle: WidgetStateProperty.all(
          const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
        ),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: AppColors.darkSurface,
      shape: RoundedRectangleBorder(borderRadius: AppShapes.dialog.radius),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: AppColors.darkSurface,
      modalBackgroundColor: AppColors.darkSurface,
      shape: RoundedRectangleBorder(borderRadius: AppShapes.sheet),
      dragHandleColor: AppColors.darkInkFaint,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.forestLight,
        foregroundColor: Colors.white,
        disabledBackgroundColor: AppColors.darkHairline,
        disabledForegroundColor: AppColors.darkInkFaint,
        minimumSize: const Size(0, 48),
        shape: RoundedRectangleBorder(
          borderRadius: AppShapes.button.radius,
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
          borderRadius: AppShapes.button.radius,
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.pinkLight,
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
            ? AppColors.pink
            : AppColors.darkHairline,
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.darkSurface,
      selectedItemColor: AppColors.pinkLight,
      unselectedItemColor: AppColors.darkInkFaint,
      selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
      unselectedLabelStyle: TextStyle(fontSize: 12),
      elevation: 0,
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: AppColors.pinkLight,
      unselectedLabelColor: AppColors.darkInkSecondary,
      indicatorColor: AppColors.pinkLight,
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
      contentPadding: AppShapes.input.padding,
      border: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: AppShapes.input.borderFor(Brightness.dark),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: AppShapes.input.borderFor(Brightness.dark),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: AppShapes.input.radius,
        borderSide: const BorderSide(
          color: AppColors.pinkLight,
          width: AppShapes.strongBorderWidth,
        ),
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

  /// Default padding mirrors [AppShapes.cardSoft] padding (16px);
  /// it is spelled out here because a const constructor default
  /// cannot read a field off another const object.
  const LearnSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.s16),
    this.margin = const EdgeInsets.symmetric(
      horizontal: AppSpacing.screen,
      vertical: AppSpacing.s4,
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
        borderRadius: AppShapes.cardSoft.radius,
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
        borderRadius: AppShapes.cardSoft.radius,
        child: box,
      ),
    );
  }
}

/// Status pill, restyled as [MetaPill] (replaces the old green
/// `StatusPill`): square (2px radius), 1px hairline border, paper
/// background, ink 12px w700 text, optional 13px icon. No tint fill.
/// Display-only — not a button, so it has no 44px touch target.
class MetaPill extends StatelessWidget {
  final String text;
  final IconData? icon;

  const MetaPill({super.key, required this.text, this.icon});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s8,
        vertical: AppSpacing.s4,
      ),
      decoration: BoxDecoration(
        color: dark ? AppColors.darkSurface : AppColors.surface,
        border: Border.all(
          color: dark ? AppColors.darkHairline : AppColors.hairline,
          width: AppShapes.hairlineWidth,
        ),
        borderRadius: AppShapes.metaPill,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(
              icon,
              size: 13,
              color: dark ? AppColors.darkInk : AppColors.ink,
            ),
            const SizedBox(width: AppSpacing.s4),
          ],
          Text(
            text,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: dark ? AppColors.darkInk : AppColors.ink,
            ),
          ),
        ],
      ),
    );
  }
}

/// One designed empty state for every screen: square hairline icon
/// tile with a pink icon, a 64px hairline rule, title, one-line body.
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

/// News section label: small pink label above an ink heading, hairline
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
