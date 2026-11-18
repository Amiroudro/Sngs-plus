/// NEXUS numbered story rows (Home, Timeline, Editorial, Search,
/// Library) + the asymmetric top-story hero.
///
/// News system: paper background, no card, no shadow, radius 0.
/// Rows are separated by 1px hairlines. The numeral is the story's
/// position in the CURRENT list (1-based; Bangla digits in Bengali
/// mode) — not the story id. Bookmarking happens on the detail page
/// and by long-press on a row (toggle + snackbar, reusing existing
/// strings).
///
/// [StoryCard] is the stable public API kept for all 5 call sites
/// (`edition`, `story`, `state`, `onTap`, `index`, `hero`,
/// `highlight`, `showDivider`). It delegates to the reusable
/// components: [NumberedStoryRow] for list rows and [TopStoryHero]
/// for the Home hero. The `Hero` tag `'headline-<date>-<id>'` is
/// preserved in both.
library;

import 'package:flutter/material.dart';

import '../data/sections.dart';
import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import 'app_theme.dart';
import 'highlight_text.dart';
import 'score_badge.dart';

String _heroTagFor(Edition edition, Story story) =>
    'headline-${edition.date}-${story.id}';

void _toggleStoryBookmark(
  BuildContext context,
  AppState state,
  Edition edition,
  Story story,
) {
  final was = state.isStoryBookmarked(edition.date, story.id);
  state.toggleStoryBookmark(edition.date, story.id);
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        was ? state.t('removeBookmark') : state.t('bookmark'),
      ),
      duration: const Duration(seconds: 2),
    ),
  );
}

class StoryCard extends StatelessWidget {
  final Edition edition;
  final Story story;
  final AppState state;
  final VoidCallback onTap;

  /// 0-based position in the current list (numeral = index + 1).
  final int index;

  /// True for the Home hero (the top story when filter is "All").
  final bool hero;

  /// Search query to highlight in the headline, if any.
  final String? highlight;

  /// Draw the hairline under the row. False for the last row.
  final bool showDivider;

  const StoryCard({
    super.key,
    required this.edition,
    required this.story,
    required this.state,
    required this.onTap,
    this.index = 0,
    this.hero = false,
    this.highlight,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context) {
    if (hero) {
      return TopStoryHero(
        edition: edition,
        story: story,
        state: state,
        onTap: onTap,
        index: index,
      );
    }
    return NumberedStoryRow(
      edition: edition,
      story: story,
      state: state,
      onTap: onTap,
      index: index,
      highlight: highlight,
      showDivider: showDivider,
    );
  }
}

/// The asymmetric NEXUS top-story hero (replaces the old hero card).
///
/// Left: solid red block (~96px wide, full hero height) with the
/// giant numeral (`01`, 64px w900 white) + "প্রধান খবর" stacked
/// under it, no rotation. Right: paper background, category label,
/// headline (`display` 28px w900), summary (max 3 lines), meta line,
/// red square arrow button at the bottom right. 2px ink rule above,
/// 1px hairline below. No gradient, no pill, no white-on-green text.
/// Shown for story #1 only when the Home filter is "সবগুলো".
class TopStoryHero extends StatelessWidget {
  final Edition edition;
  final Story story;
  final AppState state;
  final VoidCallback onTap;

  /// 0-based position in the current list (numeral = index + 1).
  final int index;

  const TopStoryHero({
    super.key,
    required this.edition,
    required this.story,
    required this.state,
    required this.onTap,
    this.index = 0,
  });

  String get _numeral => '${index + 1}'.padLeft(2, '0');

  @override
  Widget build(BuildContext context) {
    final lang = state.lang;
    final section = sectionFor(story.category);
    // Phase 4: the raw ISO date ("2026-11-07") rendered Latin digits
    // on every card in Bengali mode. Format it like the detail screen.
    final dateText = formatEditionDate(
      story.articleDate ?? story.eventDate ?? edition.date,
      lang,
    );
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
    return FadeSlideIn(
      index: index,
      child: Column(
        children: [
          Container(
            height: 2,
            color: dark ? AppColors.darkInk : AppColors.ink,
          ),
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              onLongPress: () =>
                  _toggleStoryBookmark(context, state, edition, story),
              child: IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Container(
                      constraints: const BoxConstraints(minWidth: 96),
                      color: primary,
                      padding: const EdgeInsets.fromLTRB(12, 16, 12, 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            storyDigits(_numeral, lang),
                            style: AppType.numeral.copyWith(
                              fontSize: 64,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            state.t('topStory'),
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.6,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              sectionName(section, lang),
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.6,
                                color: accent,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Hero(
                              tag: _heroTagFor(edition, story),
                              child: Material(
                                type: MaterialType.transparency,
                                child: Text(
                                  story.headlineIn(lang),
                                  style: AppType.display,
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              story.summaryIn(lang),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 14,
                                height: 1.6,
                                color: dark
                                    ? AppColors.darkInkSecondary
                                    : AppColors.inkSecondary,
                              ),
                            ),
                            const SizedBox(height: 10),
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    dateText,
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: dark
                                          ? AppColors.darkInkFaint
                                          : AppColors.inkFaint,
                                    ),
                                  ),
                                ),
                                _ArrowButton(onTap: onTap),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Container(
            height: 1,
            color: dark ? AppColors.darkHairline : AppColors.hairline,
          ),
        ],
      ),
    );
  }
}

/// One numbered story row: red numeral, category label, headline
/// (with `Hero` preserved), summary (max 3 lines), meta line
/// (date • first source • relevance mark), red square arrow button.
/// Full-width, paper background, no card, no shadow, no radius;
/// 1px hairline under the row (none after the last). Tap anywhere
/// goes to the detail page; long-press toggles the bookmark.
class NumberedStoryRow extends StatelessWidget {
  final Edition edition;
  final Story story;
  final AppState state;
  final VoidCallback onTap;

  /// 0-based position in the current list (numeral = index + 1).
  final int index;

  /// Search query to highlight in the headline, if any.
  final String? highlight;

  /// Draw the hairline under the row. False for the last row.
  final bool showDivider;

  const NumberedStoryRow({
    super.key,
    required this.edition,
    required this.story,
    required this.state,
    required this.onTap,
    this.index = 0,
    this.highlight,
    this.showDivider = true,
  });

  String get _numeral => '${index + 1}'.padLeft(2, '0');

  @override
  Widget build(BuildContext context) {
    final lang = state.lang;
    final section = sectionFor(story.category);
    // Phase 4: the raw ISO date ("2026-11-07") rendered Latin digits
    // on every card in Bengali mode. Format it like the detail screen.
    final dateText = formatEditionDate(
      story.articleDate ?? story.eventDate ?? edition.date,
      lang,
    );
    final pubs = story.sourcePublications;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final meta = <String>[
      dateText,
      if (pubs.isNotEmpty) pubs.first,
    ].join(' • ');
    return FadeSlideIn(
      index: index,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          onLongPress: () =>
              _toggleStoryBookmark(context, state, edition, story),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.screen,
                  vertical: AppSpacing.screen,
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ConstrainedBox(
                      constraints: const BoxConstraints(
                        minWidth: 44,
                        maxWidth: 96,
                      ),
                      child: Text(
                        storyDigits(_numeral, lang),
                        style: AppType.numeral.copyWith(color: accent),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            sectionName(section, lang),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.6,
                              color: accent,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Hero(
                            tag: _heroTagFor(edition, story),
                            child: Material(
                              type: MaterialType.transparency,
                              child: highlight != null
                                  ? HighlightText(
                                      text: story.headlineIn(lang),
                                      query: highlight!,
                                      style: const TextStyle(
                                        fontSize: 22,
                                        fontWeight: FontWeight.w800,
                                        height: 1.3,
                                      ),
                                    )
                                  : Text(
                                      story.headlineIn(lang),
                                      style: const TextStyle(
                                        fontSize: 22,
                                        fontWeight: FontWeight.w800,
                                        height: 1.3,
                                      ),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            story.summaryIn(lang),
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 14,
                              height: 1.6,
                              color: dark
                                  ? AppColors.darkInkSecondary
                                  : AppColors.inkSecondary,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  meta,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: dark
                                        ? AppColors.darkInkFaint
                                        : AppColors.inkFaint,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              RelevanceMark(story: story, state: state),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Padding(
                      padding: const EdgeInsets.only(top: 24),
                      child: _ArrowButton(onTap: onTap),
                    ),
                  ],
                ),
              ),
              if (showDivider)
                Container(
                  height: 1,
                  margin: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.screen,
                  ),
                  color: dark ? AppColors.darkHairline : AppColors.hairline,
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Solid red square arrow, 40x40, radius 0 — the NEXUS signature
/// action at the end of a story row. 48x48 hit area via padding.
class _ArrowButton extends StatelessWidget {
  final VoidCallback onTap;

  const _ArrowButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
    return SizedBox(
      width: 48,
      height: 48,
      child: Center(
        child: InkWell(
          onTap: onTap,
          child: Container(
            width: 40,
            height: 40,
            color: primary,
            child: const Icon(
              Icons.arrow_forward,
              size: 20,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
