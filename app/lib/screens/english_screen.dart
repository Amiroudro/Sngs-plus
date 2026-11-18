/// English screen (v1.2.1): DATES FIRST, then words, then a separate
/// detail page.
///
/// Flow: date list (one row per edition, newest first, with that
/// day's word/phrase counts) → tap a date → that day's words list
/// (tabs: words / phrases / revision) → tap a word → the full exam
/// word card on its own dedicated page ([WordDetailScreen]).
/// No inline expansion in the list any more: the list stays a clean
/// list, and the full card reads as a page. Flashcards stay reachable
/// from the AppBar.
library;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/word_card.dart';
import 'flashcard_screen.dart';
import 'word_detail_screen.dart';

class EnglishScreen extends StatelessWidget {
  final AppState state;

  const EnglishScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final editions = state.editions; // already newest first (loader)
    if (editions.isEmpty) {
      return Scaffold(
        appBar: AppBar(
          title: Text(state.t('english')),
          bottom: appBarHairline(context),
        ),
        body: EmptyState(
          icon: Icons.translate,
          body: state.t('errorLoading'),
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: Text(state.t('english')),
        bottom: appBarHairline(context),
        actions: [
          IconButton(
            icon: const Icon(Icons.style_outlined),
            tooltip: state.t('flashcards'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => FlashcardScreen(state: state),
              ),
            ),
          ),
        ],
      ),
      // Bottom SafeArea: the list must end above the system nav bar,
      // never half-cut under it.
      body: SafeArea(
        top: false,
        bottom: true,
        child: ListView.builder(
          padding: const EdgeInsets.only(top: 8, bottom: 16),
          itemCount: editions.length,
          itemBuilder: (context, i) {
            final edition = editions[i];
            return _DateRow(
              edition: edition,
              state: state,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => EditionWordsScreen(
                    edition: edition,
                    state: state,
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

/// One date row: Bengali date, that day's counts, chevron. NEXUS
/// news-row styling: hairline below, no card, no fill.
class _DateRow extends StatelessWidget {
  final Edition edition;
  final AppState state;
  final VoidCallback onTap;

  const _DateRow({
    required this.edition,
    required this.state,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
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
                    color: primary,
                    alignment: Alignment.center,
                    child: const Icon(
                      Icons.translate,
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
                            '${edition.wordCount} ${state.t('words')} • '
                            '${edition.phraseCount} ${state.t('phrases')} • '
                            '${edition.revisionCount} ${state.t('revisionList')}',
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
                  const Icon(Icons.chevron_right, size: 24),
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

/// One edition's words: tabs for words / phrases / revision. Tapping
/// a word opens its full exam card on a dedicated page; tapping a
/// phrase opens the phrase detail page. No inline expansion here.
class EditionWordsScreen extends StatefulWidget {
  final Edition edition;
  final AppState state;

  const EditionWordsScreen({
    super.key,
    required this.edition,
    required this.state,
  });

  @override
  State<EditionWordsScreen> createState() => _EditionWordsScreenState();
}

class _EditionWordsScreenState extends State<EditionWordsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  void _openWord(VocabWord word) {
    _openWordFor(widget.edition, word);
  }

  void _openWordFor(Edition edition, VocabWord word) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => WordDetailScreen(
          edition: edition,
          word: word,
          state: widget.state,
        ),
      ),
    );
  }

  void _openPhrase(Phrase phrase) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PhraseDetailScreen(
          phrase: phrase,
          state: widget.state,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final edition = widget.edition;
    final state = widget.state;
    return Scaffold(
      appBar: AppBar(
        title: Text(formatEditionDate(edition.date, state.lang)),
        bottom: appBarHairline(context),
        actions: [
          IconButton(
            icon: const Icon(Icons.style_outlined),
            tooltip: state.t('flashcards'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => FlashcardScreen(state: state),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        bottom: true,
        child: Column(
          children: [
            TabBar(
              controller: _tabs,
              // Scrollable so the long Bengali tab labels
              // ('শব্দবন্ধ ও বাগধারা', 'পুনরালোচনা (5)') are never cut.
              // No labelColor here: the theme's pinkText active label
              // must apply in both modes. The old explicit
              // colorScheme.primary made the light-mode active label
              // forest while the underline stayed pink.
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              tabs: [
                Tab(
                  text: storyDigits(
                      '${state.t('wordList')} (${edition.words.length})',
                      state.lang),
                ),
                Tab(
                  text: storyDigits(
                      '${state.t('phraseList')} (${edition.phrases.length})',
                      state.lang),
                ),
                Tab(
                  // The count is the words actually DUE for revision
                  // across the last 7 editions, not the raw
                  // revision-word list (Phase 3, windowed in Phase 5).
                  text: storyDigits(
                      '${state.t('revisionList')} (${state.dueRevisionWords().length})',
                      state.lang),
                ),
              ],
            ),
            Expanded(
              child: TabBarView(
                controller: _tabs,
                children: [
                  _WordList(
                    edition: edition,
                    state: state,
                    onOpen: _openWord,
                  ),
                  _PhraseList(
                    edition: edition,
                    state: state,
                    onOpen: _openPhrase,
                  ),
                  _RevisionList(
                    edition: edition,
                    state: state,
                    onOpen: _openWordFor,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// The day's words: one collapsed row per word. Tap → dedicated
/// detail page (no inline expansion).
class _WordList extends StatelessWidget {
  final Edition edition;
  final AppState state;
  final void Function(VocabWord word) onOpen;

  const _WordList({
    required this.edition,
    required this.state,
    required this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      itemCount: edition.words.length,
      itemBuilder: (context, i) {
        final word = edition.words[i];
        return FadeSlideIn(
          index: i,
          child: CollapsedWordRow(
            edition: edition,
            word: word,
            state: state,
            open: false,
            onToggle: () => onOpen(word),
          ),
        );
      },
    );
  }
}

/// The day's phrases: one row per phrase. Tap → dedicated phrase
/// detail page.
class _PhraseList extends StatelessWidget {
  final Edition edition;
  final AppState state;
  final void Function(Phrase phrase) onOpen;

  const _PhraseList({
    required this.edition,
    required this.state,
    required this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      itemCount: edition.phrases.length,
      itemBuilder: (context, i) {
        final phrase = edition.phrases[i];
        return FadeSlideIn(
          index: i,
          child: _PhraseRow(
            phrase: phrase,
            state: state,
            onTap: () => onOpen(phrase),
          ),
        );
      },
    );
  }
}

/// One collapsed phrase row: phrase + Bengali meaning + chevron.
/// Mirrors [CollapsedWordRow] so the two lists feel like one screen.
class _PhraseRow extends StatelessWidget {
  final Phrase phrase;
  final AppState state;
  final VoidCallback onTap;

  const _PhraseRow({
    required this.phrase,
    required this.state,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      margin: const EdgeInsets.symmetric(
        horizontal: AppSpacing.screen,
        vertical: AppSpacing.s4,
      ),
      decoration: BoxDecoration(
        color: dark ? AppColors.darkSurfaceSoft : AppColors.surfaceSoft,
        borderRadius: AppShapes.soft,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppShapes.soft,
          child: Container(
            constraints: const BoxConstraints(minHeight: 56),
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.s16,
              vertical: 12,
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        phrase.phrase,
                        style: const TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w800,
                          height: 1.3,
                        ),
                      ),
                      if (hasValue(phrase.banglaMeaning))
                        Text(
                          phrase.banglaMeaning!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 14,
                            height: 1.5,
                            color: AppColors.secondaryFor(
                              Theme.of(context).brightness,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                if (hasValue(phrase.type))
                  // Flexible + ellipsis: a long type
                  // ("Phrasal verb / collocation") must never push
                  // the row past the screen at 200% text scale.
                  Flexible(
                    child: Text(
                      phrase.type!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.faintFor(
                          Theme.of(context).brightness,
                        ),
                      ),
                    ),
                  ),
                const SizedBox(width: 4),
                Icon(
                  Icons.chevron_right,
                  color: AppColors.secondaryFor(
                    Theme.of(context).brightness,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// The revision tab (Phase 3, windowed in Phase 5): ONLY the words
/// that are DUE from the LAST 7 editions — "জানি না" words whose
/// 1 / 3 / 7-day due date is today or past, overdue first. A word
/// marked "জানি" never appears here, and neither does a word never
/// answered. Words from older editions show their edition date under
/// the meaning. Tap a row → its detail page (with that word's own
/// edition), where জানি / জানি না re-schedules it. The old "পড়া
/// হয়েছে" toggle is gone: the detail page's জানি / জানি না is now
/// the revision mechanism (the stored reviewed flags are kept in
/// AppState, untouched).
class _RevisionList extends StatelessWidget {
  final Edition edition;
  final AppState state;
  final void Function(Edition edition, VocabWord word) onOpen;

  const _RevisionList({
    required this.edition,
    required this.state,
    required this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    final due = state.dueRevisionWords();
    if (due.isEmpty) {
      return ListView(
        padding: const EdgeInsets.only(top: 8, bottom: 16),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Text(
              state.t('revisionDueNote'),
              style: TextStyle(
                fontSize: 13,
                height: 1.5,
                color: AppColors.secondaryFor(
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ),
          EmptyState(
            icon: Icons.event_repeat,
            body: state.t('revisionDueEmpty'),
          ),
        ],
      );
    }
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return ListView(
      padding: const EdgeInsets.only(top: 8, bottom: 16),
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      state.t('dueToday'),
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  Text(
                    storyDigits('${due.length}', state.lang),
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                state.t('revisionDueNote'),
                style: TextStyle(
                  fontSize: 13,
                  height: 1.5,
                  color: AppColors.secondaryFor(
                    Theme.of(context).brightness,
                  ),
                ),
              ),
            ],
          ),
        ),
        for (final entry in due)
          LearnSurface(
            child: InkWell(
              onTap: () => onOpen(entry.edition, entry.word),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          entry.word.headword,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        if (hasValue(entry.word.banglaMeaning))
                          Text(
                            entry.word.banglaMeaning!,
                            style: const TextStyle(fontSize: 14),
                          ),
                        // A due word from an older edition says which
                        // day it comes from; words from this edition
                        // need no date line.
                        if (entry.edition.date != edition.date)
                          Text(
                            formatEditionDate(
                              entry.edition.date,
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
                  const SizedBox(width: 8),
                  Text(
                    _dueLabel(entry.edition.date, entry.word, state),
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: _isOverdue(entry.edition.date, entry.word, state)
                          ? accent
                          : null,
                    ),
                  ),
                  const Icon(Icons.chevron_right, size: 20),
                ],
              ),
            ),
          ),
      ],
    );
  }

  bool _isOverdue(String editionDate, VocabWord word, AppState state) {
    final due = state.wordDueDate(editionDate, word.headword);
    if (due == null) return false;
    final dt = DateTime.tryParse(due);
    if (dt == null) return false;
    final now = DateTime.now();
    return DateTime(dt.year, dt.month, dt.day)
        .isBefore(DateTime(now.year, now.month, now.day));
  }

  /// 'আজ' when due today, 'দেরি · ৭ নভেম্বর ২০২৬' when overdue.
  String _dueLabel(String editionDate, VocabWord word, AppState state) {
    final due = state.wordDueDate(editionDate, word.headword);
    if (due == null) return '';
    if (!_isOverdue(editionDate, word, state)) return state.t('dueTodayWord');
    return '${state.t('overdue')} · '
        '${formatEditionDate(due, state.lang)}';
  }
}
