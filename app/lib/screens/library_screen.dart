/// Library tab: saved stories + words, quiz history, and the
/// My Mistakes deck. Story parts use the editorial system, word parts
/// the learning system — the contrast on one screen is intentional.
library;

import 'package:flutter/material.dart';

import '../data/sections.dart';
import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/story_card.dart';
import '../widgets/word_card.dart';
import 'story_detail_screen.dart';
import 'word_detail_screen.dart';

class LibraryScreen extends StatelessWidget {
  final AppState state;

  const LibraryScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final savedStories = <({Edition edition, Story story})>[];
    for (final key in state.bookmarkedStories) {
      final parts = key.split(':');
      if (parts.length != 2) continue;
      final story = state.findStory(parts[0], parts[1]);
      final edition = state.findEdition(parts[0]);
      if (story != null && edition != null) {
        savedStories.add((edition: edition, story: story));
      }
    }
    final savedWords = <({Edition edition, VocabWord word})>[];
    for (final key in state.bookmarkedWords) {
      final idx = key.indexOf(':');
      if (idx < 0) continue;
      final date = key.substring(0, idx);
      final headword = key.substring(idx + 1);
      final word = state.findWord(date, headword);
      final edition = state.findEdition(date);
      if (word != null && edition != null) {
        savedWords.add((edition: edition, word: word));
      }
    }

    return DefaultTabController(
      length: 4,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: NewsSectionLabel.heading(state.t('library')),
            ),
          ),
          const SizedBox(height: 8),
          TabBar(
            isScrollable: true,
            labelColor: Theme.of(context).colorScheme.primary,
            tabs: [
              Tab(text: state.t('savedStories')),
              Tab(text: state.t('savedWords')),
              Tab(text: state.t('myMistakes')),
              Tab(text: state.t('quizHistory')),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _SavedStoriesList(items: savedStories, state: state),
                _SavedWordsList(items: savedWords, state: state),
                _MistakesList(state: state),
                _HistoryList(state: state),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SavedStoriesList extends StatelessWidget {
  final List<({Edition edition, Story story})> items;
  final AppState state;

  const _SavedStoriesList({required this.items, required this.state});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return EmptyState(
        icon: Icons.bookmark_outline,
        body: state.t('noSaved'),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      itemCount: items.length,
      itemBuilder: (context, i) {
        final item = items[i];
        return StoryCard(
          edition: item.edition,
          story: item.story,
          state: state,
          index: i,
          showDivider: i < items.length - 1,
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => StoryDetailScreen(
                edition: item.edition,
                story: item.story,
                state: state,
              ),
            ),
          ),
        );
      },
    );
  }
}

class _SavedWordsList extends StatelessWidget {
  final List<({Edition edition, VocabWord word})> items;
  final AppState state;

  const _SavedWordsList({required this.items, required this.state});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return EmptyState(
        icon: Icons.bookmark_outline,
        body: state.t('noSaved'),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      itemCount: items.length,
      itemBuilder: (context, i) => ExpandableWordRow(
        edition: items[i].edition,
        word: items[i].word,
        state: state,
        onFullPage: () => Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => WordDetailScreen(
              edition: items[i].edition,
              word: items[i].word,
              state: state,
            ),
          ),
        ),
      ),
    );
  }
}

class _MistakesList extends StatelessWidget {
  final AppState state;

  const _MistakesList({required this.state});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final success = AppColors.successFor(Theme.of(context).brightness);
    final error = AppColors.errorFor(Theme.of(context).brightness);
    if (state.mistakes.isEmpty) {
      return EmptyState(
        icon: Icons.check_circle_outline,
        body: state.t('noMistakes'),
      );
    }
    return Column(
      children: [
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: () => state.clearMistakes(),
            child: Text(state.t('clearMistakes')),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.only(bottom: 16),
            itemCount: state.mistakes.length,
            itemBuilder: (context, i) {
              final m = state.mistakes[i];
              return LearnSurface(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          mcqSectionName(m.section, state.lang),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: accent,
                          ),
                        ),
                        const SizedBox(width: 8),
                        if (m.isPractice)
                          Text(
                            state.t('practiceQuiz'),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: dark
                                  ? AppColors.darkInkSecondary
                                  : AppColors.inkSecondary,
                            ),
                          ),
                        const Spacer(),
                        Text(
                          formatEditionDate(m.editionDate, state.lang),
                          style: const TextStyle(fontSize: 12),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      m.question,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${state.t('yourAnswer')}: ${m.chosen.isEmpty ? state.t('notAnswered') : m.chosen}',
                      style: TextStyle(fontSize: 14, color: error),
                    ),
                    Text(
                      '${state.t('correctAnswer')}: ${m.correct}',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: success,
                      ),
                    ),
                    if (m.explanation != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${state.t('explanation')}: ${m.explanation}',
                        style: const TextStyle(fontSize: 13, height: 1.5),
                      ),
                    ],
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _HistoryList extends StatelessWidget {
  final AppState state;

  const _HistoryList({required this.state});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    if (state.quizHistory.isEmpty) {
      return EmptyState(
        icon: Icons.quiz_outlined,
        body: state.t('noHistory'),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      itemCount: state.quizHistory.length,
      itemBuilder: (context, i) {
        final r = state.quizHistory[i];
        final ratio = r.total == 0 ? 0.0 : r.score / r.total;
        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
              child: Row(
                children: [
                  const Icon(Icons.quiz_outlined, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${r.mode == 'practice' ? state.t('practiceQuiz') : state.t('editionQuiz')} — ${formatEditionDate(r.editionDate, state.lang)}',
                          style: const TextStyle(fontSize: 14),
                        ),
                        Text(
                          r.timestamp.replaceAll('T', ' ').split('.').first,
                          style: TextStyle(
                            fontSize: 12,
                            color: dark
                                ? AppColors.darkInkFaint
                                : AppColors.inkFaint,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    storyDigits(
                        '${r.score} / ${r.total}', state.lang),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: ratio >= 0.8 ? accent : null,
                    ),
                  ),
                ],
              ),
            ),
            Container(
              height: 1,
              margin: const EdgeInsets.symmetric(horizontal: 16),
              color: dark ? AppColors.darkHairline : AppColors.hairline,
            ),
          ],
        );
      },
    );
  }
}
