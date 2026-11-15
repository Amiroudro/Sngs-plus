/// Current Affairs tab (v1.2.1): a DATE-COLLAPSED list, not a flat
/// feed. One row per edition date (newest first, with that day's
/// counts), all collapsed by default. Tapping a date expands that
/// day's stories inline as the timeline — one date open at a time,
/// tap again to collapse. Tapping a story opens its detail page.
/// After many days a flat list becomes a mess; the date list stays
/// clean no matter how many editions arrive.
library;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/story_card.dart';
import 'story_detail_screen.dart';

class CurrentAffairsScreen extends StatefulWidget {
  final AppState state;

  const CurrentAffairsScreen({super.key, required this.state});

  @override
  State<CurrentAffairsScreen> createState() => _CurrentAffairsScreenState();
}

class _CurrentAffairsScreenState extends State<CurrentAffairsScreen> {
  /// The one expanded edition date, or null when all are collapsed.
  String? _openDate;

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final editions = state.editions; // already newest first (loader)
    if (editions.isEmpty) {
      return EmptyState(
        icon: Icons.newspaper,
        body: state.t('errorLoading'),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
          child: NewsSectionLabel(
            label: state.t('timeline'),
            heading: state.t('currentAffairs'),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.only(bottom: 16),
            itemCount: editions.length,
            itemBuilder: (context, i) {
              final edition = editions[i];
              final open = _openDate == edition.date;
              return Column(
                children: [
                  _DateRow(
                    edition: edition,
                    state: state,
                    open: open,
                    onTap: () => setState(() {
                      _openDate = open ? null : edition.date;
                    }),
                  ),
                  AnimatedSize(
                    duration: AppMotion.standard,
                    curve: AppMotion.curve,
                    alignment: Alignment.topCenter,
                    child: open
                        ? _DayStories(
                            edition: edition,
                            state: state,
                          )
                        : const SizedBox.shrink(),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

/// One date row: Bengali date, that day's counts, expand chevron.
/// NEXUS news-row styling: hairline below, no card, no fill.
class _DateRow extends StatelessWidget {
  final Edition edition;
  final AppState state;
  final bool open;
  final VoidCallback onTap;

  const _DateRow({
    required this.edition,
    required this.state,
    required this.open,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.screen,
                vertical: 14,
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    color: accent,
                    alignment: Alignment.center,
                    child: const Icon(
                      Icons.newspaper,
                      color: Colors.white,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          formatEditionDateLong(edition.date, state.lang),
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          storyDigits(
                            '${edition.storyCount} ${state.t('stories')} • '
                            '${edition.wordCount} ${state.t('words')} • '
                            '${edition.mcqCount} ${state.t('mcqs')}',
                            state.lang,
                          ),
                          style: TextStyle(
                            fontSize: 12,
                            color: AppColors.secondaryFor(
                              Theme.of(context).brightness,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  AnimatedRotation(
                    turns: open ? 0.5 : 0,
                    duration: AppMotion.standard,
                    curve: AppMotion.curve,
                    child: const Icon(Icons.keyboard_arrow_down),
                  ),
                ],
              ),
            ),
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
    );
  }
}

/// One expanded day: the edition's stories as the timeline — a quiet
/// rail with a red square per event, newest first. Rows are numbered
/// by timeline position (newest = 01).
class _DayStories extends StatelessWidget {
  final Edition edition;
  final AppState state;

  const _DayStories({required this.edition, required this.state});

  @override
  Widget build(BuildContext context) {
    final stories = List<Story>.of(edition.stories);
    stories.sort((a, b) {
      final da = a.eventDate ?? '';
      final db = b.eventDate ?? '';
      final cmp = db.compareTo(da);
      if (cmp != 0) return cmp;
      return a.id.compareTo(b.id);
    });
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return Column(
      children: [
        for (var i = 0; i < stories.length; i++)
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 16,
                  child: Column(
                    children: [
                      const SizedBox(height: 20),
                      Container(width: 8, height: 8, color: accent),
                      if (i < stories.length - 1)
                        Expanded(
                          child: Container(
                            width: 1,
                            color: dark
                                ? AppColors.darkHairline
                                : AppColors.hairline,
                          ),
                        ),
                    ],
                  ),
                ),
                Expanded(
                  child: StoryCard(
                    edition: edition,
                    story: stories[i],
                    state: state,
                    index: i,
                    showDivider: i < stories.length - 1,
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => StoryDetailScreen(
                          edition: edition,
                          story: stories[i],
                          state: state,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
