/// Word card — the exam-focused meaning section (NEXUS learning
/// system: LearnSurface, radius 12, ink headwords, red rule under
/// section titles, red doubled letters, red left bar on the example).
///
/// For EVERY word it shows (labels in Bengali; the word data itself in
/// English): (1) headword + Bengali meaning (2) pronunciation / IPA
/// (3) part of speech + word forms (4) synonyms (5) antonyms
/// (6) correct spelling (7) example (8) collocations (9) related
/// idiom/phrase/group verb (10) root/prefix/suffix (11) exam appearance.
///
/// HONESTY: any item the edition data does not supply is shown as
/// absent — never invented.
library;

import 'package:flutter/material.dart';

import '../data/exam_patterns.dart';
import '../models.dart';
import '../state/app_state.dart';
import 'app_theme.dart';
import 'highlight_text.dart';

/// Collapsed word row, shared by English, Search and Library.
/// LearnSurface, ink headword, red left edge when open, red bookmark
/// glyph when bookmarked, chevron rotates when open.
class CollapsedWordRow extends StatelessWidget {
  final Edition edition;
  final VocabWord word;
  final AppState state;
  final bool open;
  final VoidCallback onToggle;
  final String? highlight;

  const CollapsedWordRow({
    super.key,
    required this.edition,
    required this.word,
    required this.state,
    required this.open,
    required this.onToggle,
    this.highlight,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final bookmarked = state.isWordBookmarked(edition.date, word.headword);
    return Container(
      key: ValueKey('word-row-${word.headword}'),
      margin: const EdgeInsets.symmetric(
        horizontal: AppSpacing.screen,
        vertical: 4,
      ),
      decoration: BoxDecoration(
        color: dark ? AppColors.darkSurfaceSoft : AppColors.surfaceSoft,
        borderRadius: BorderRadius.circular(AppRadii.learn),
        border: Border(
          left: BorderSide(
            color: open ? accent : Colors.transparent,
            width: 4,
          ),
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onToggle,
          borderRadius: BorderRadius.circular(AppRadii.learn),
          child: Container(
            constraints: const BoxConstraints(minHeight: 56),
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.s16,
              vertical: 12,
            ),
            child: Row(
              children: [
                if (open)
                  SizedBox(
                    key: ValueKey('word-open-${word.headword}'),
                    width: 0,
                    height: 0,
                  ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: highlight != null
                                ? HighlightText(
                                    text: word.headword,
                                    query: highlight!,
                                    style: const TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.w800,
                                      height: 1.3,
                                    ),
                                  )
                                : Text(
                                    word.headword,
                                    style: const TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.w800,
                                      height: 1.3,
                                    ),
                                  ),
                          ),
                          if (bookmarked) ...[
                            const SizedBox(width: 6),
                            Icon(
                              Icons.bookmark,
                              size: 16,
                              color: accent,
                            ),
                          ],
                        ],
                      ),
                      if (hasValue(word.banglaMeaning))
                        Text(
                          word.banglaMeaning!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 14,
                            height: 1.5,
                            color: dark
                                ? AppColors.darkInkSecondary
                                : AppColors.inkSecondary,
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                if (hasValue(word.partOfSpeech))
                  Text(
                    word.partOfSpeech!,
                    style: TextStyle(
                      fontSize: 12,
                      color: dark ? AppColors.darkInkFaint : AppColors.inkFaint,
                    ),
                  ),
                const SizedBox(width: 4),
                AnimatedRotation(
                  turns: open ? 0.5 : 0,
                  duration: AppMotion.standard,
                  curve: AppMotion.curve,
                  child: Icon(
                    Icons.keyboard_arrow_down,
                    color: AppColors.secondaryFor(
                      Theme.of(context).brightness,
                    ),
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

/// Self-contained expandable word row for Search and Library: the
/// collapsed row + inline full card on tap (its own open state).
/// English uses [CollapsedWordRow] directly (one open at a time).
class ExpandableWordRow extends StatefulWidget {
  final Edition edition;
  final VocabWord word;
  final AppState state;
  final String? highlight;
  final VoidCallback? onFullPage;

  const ExpandableWordRow({
    super.key,
    required this.edition,
    required this.word,
    required this.state,
    this.highlight,
    this.onFullPage,
  });

  @override
  State<ExpandableWordRow> createState() => _ExpandableWordRowState();
}

class _ExpandableWordRowState extends State<ExpandableWordRow> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        CollapsedWordRow(
          edition: widget.edition,
          word: widget.word,
          state: widget.state,
          open: _open,
          highlight: widget.highlight,
          onToggle: () => setState(() => _open = !_open),
        ),
        AnimatedSize(
          duration: AppMotion.standard,
          curve: AppMotion.curve,
          alignment: Alignment.topCenter,
          child: _open
              ? Column(
                  children: [
                    WordCard(
                      edition: widget.edition,
                      word: widget.word,
                      state: widget.state,
                      highlight: widget.highlight,
                    ),
                    if (widget.onFullPage != null)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                        child: SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: widget.onFullPage,
                            icon: const Icon(Icons.open_in_full, size: 18),
                            label: Text(widget.state.t('fullPage')),
                          ),
                        ),
                      ),
                  ],
                )
              : const SizedBox.shrink(),
        ),
      ],
    );
  }
}

class WordCard extends StatelessWidget {
  final Edition edition;
  final VocabWord word;
  final AppState state;
  final String? highlight;
  final EdgeInsetsGeometry margin;

  const WordCard({
    super.key,
    required this.edition,
    required this.word,
    required this.state,
    this.highlight,
    this.margin = const EdgeInsets.symmetric(
      horizontal: AppSpacing.screen,
      vertical: 4,
    ),
  });

  @override
  Widget build(BuildContext context) {
    final t = state.t;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    // Every text colour is explicit ink here. Nothing in this card
    // may inherit a colour: an inherited style is what let Flutter's
    // red-monospace-yellow-underline fallback style leak in when the
    // card had no Material ancestor (v1.2.0 bug).
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    final secondary = AppColors.secondaryFor(Theme.of(context).brightness);
    final bookmarked = state.isWordBookmarked(edition.date, word.headword);
    final related = edition.relatedPhrasesFor(word);
    final examTypes = examTypesFor(word, edition);
    final verifiedPattern = verifiedExamPatterns[word.headword.toLowerCase()];

    return LearnSurface(
      margin: margin,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: highlight != null
                    ? HighlightText(
                        text: word.headword,
                        query: highlight!,
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: ink,
                        ),
                      )
                    : Text(
                        word.headword,
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: ink,
                        ),
                      ),
              ),
              IconButton(
                icon: Icon(
                  bookmarked ? Icons.bookmark : Icons.bookmark_border,
                  color: bookmarked ? accent : null,
                ),
                tooltip: bookmarked ? t('removeBookmark') : t('bookmark'),
                onPressed: () =>
                    state.toggleWordBookmark(edition.date, word.headword),
              ),
            ],
          ),
          if (hasValue(word.banglaMeaning))
            Text(
              word.banglaMeaning!,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                height: 1.4,
                color: ink,
              ),
            ),
          const SizedBox(height: 4),
          _MetaRow(
            label: t('difficulty'),
            value: _difficultyLabel(word.difficulty, state),
          ),
          if (hasValue(word.priority))
            _MetaRow(
              label: t('priority'),
              value: _priorityLabel(word.priority, state),
            ),
          const Divider(height: 20),
          _Section(
            title: t('pronunciation'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (hasValue(word.ipa))
                  Text(
                    word.ipa!,
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.5,
                      color: ink,
                    ),
                  ),
                if (hasValue(word.banglaPhonetic))
                  Text(
                    word.banglaPhonetic!,
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.5,
                      color: ink,
                    ),
                  ),
                if (!hasValue(word.ipa) && !hasValue(word.banglaPhonetic))
                  _Absent(text: t('noDataForWord')),
              ],
            ),
          ),
          _Section(
            title: t('partOfSpeech'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (hasValue(word.partOfSpeech))
                  Text(
                    word.partOfSpeech!,
                    style: TextStyle(fontSize: 15, color: ink),
                  ),
                const SizedBox(height: 6),
                Text(
                  t('wordForms'),
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: ink,
                  ),
                ),
                const SizedBox(height: 4),
                if (word.hasWordFamily)
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: word.wordFamily
                        .map((f) => _LearnChip(label: f))
                        .toList(),
                  )
                else
                  _Absent(text: t('noDataForWord')),
              ],
            ),
          ),
          _Section(
            title: t('synonyms'),
            child: word.hasSynonyms
                ? Text(
                    word.synonyms.join(' ; '),
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.6,
                      color: ink,
                    ),
                  )
                : _Absent(text: t('noDataForWord')),
          ),
          _Section(
            title: t('antonyms'),
            child: word.hasAntonyms
                ? Text(
                    word.antonyms.join(' ; '),
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.6,
                      color: ink,
                    ),
                  )
                : _Absent(text: t('noDirectAntonym')),
          ),
          _Section(
            title: t('spelling'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 1,
                  children: [
                    for (var i = 0; i < word.spellingLetters.length; i++)
                      Text(
                        word.spellingLetters[i],
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                          color: word.doubledLetterIndexes.contains(i)
                              ? accent
                              : ink,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  t('spellingNote'),
                  style: TextStyle(fontSize: 12, color: secondary),
                ),
              ],
            ),
          ),
          _Section(
            title: t('example'),
            child: hasValue(word.example)
                ? IntrinsicHeight(
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Container(width: 4, color: accent),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            '“${word.example!}”',
                            style: TextStyle(
                              fontSize: 15,
                              fontStyle: FontStyle.italic,
                              height: 1.6,
                              color: ink,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                : _Absent(text: t('noDataForWord')),
          ),
          if (hasValue(word.contextNote))
            _Section(
              title: t('newspaperContext'),
              child: Text(
                word.contextNote!,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          _Section(
            title: t('collocations'),
            child: word.hasCollocations
                ? Text(
                    word.collocations.join(' ; '),
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.6,
                      color: ink,
                    ),
                  )
                : _Absent(text: t('noDataForWord')),
          ),
          _Section(
            title: t('relatedPhrase'),
            child: related.isNotEmpty
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: related
                        .map((p) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text(
                                '• ${p.phrase}'
                                '${hasValue(p.banglaMeaning) ? ' — ${p.banglaMeaning}' : ''}',
                                style: TextStyle(
                                  fontSize: 15,
                                  height: 1.6,
                                  color: ink,
                                ),
                              ),
                            ))
                        .toList(),
                  )
                : _Absent(text: t('noDataForWord')),
          ),
          _Section(
            title: t('wordStructure'),
            child: word.commonStem != null
                ? Text(
                    '${word.commonStem} + ${word.wordFamily.join(' / ')}',
                    style: TextStyle(
                      fontSize: 15,
                      height: 1.6,
                      color: ink,
                    ),
                  )
                : _Absent(text: t('noDataForWord')),
          ),
          _Section(
            title: t('examAppearance'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: examTypes.map((e) => _LearnChip(label: e)).toList(),
                ),
                const SizedBox(height: 8),
                if (verifiedPattern != null)
                  Text(
                    '${t('examRefVerified')}: $verifiedPattern',
                    style: TextStyle(
                      fontSize: 13,
                      fontStyle: FontStyle.italic,
                      height: 1.5,
                      color: ink,
                    ),
                  )
                else
                  Text(
                    t('examRefNone'),
                    style: TextStyle(
                      fontSize: 13,
                      fontStyle: FontStyle.italic,
                      color: secondary,
                    ),
                  ),
              ],
            ),
          ),
          const Divider(height: 20),
          if (hasValue(word.bcsRelevance))
            _Section(
              title: t('relevance'),
              child: Text(
                word.bcsRelevance!,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          if (hasValue(word.sourcePublication) ||
              hasValue(word.articleHeadline))
            _Section(
              title: t('source'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (hasValue(word.sourcePublication))
                    Text(
                      word.sourcePublication!,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: ink,
                      ),
                    ),
                  if (hasValue(word.articleHeadline))
                    Text(
                      word.articleHeadline!,
                      style: TextStyle(
                        fontSize: 14,
                        height: 1.4,
                        color: ink,
                      ),
                    ),
                  if (hasValue(word.publicationDate))
                    Text(
                      word.publicationDate!,
                      style: TextStyle(fontSize: 12, color: secondary),
                    ),
                  if (hasValue(word.sourceUrl))
                    TextButton.icon(
                      onPressed: () => openExternalUrl(word.sourceUrl),
                      icon: const Icon(Icons.open_in_new, size: 16),
                      label: Text(t('openSource')),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  String _difficultyLabel(String? value, AppState state) {
    return switch (value?.trim()) {
      'Advanced' => state.t('difficultyAdvanced'),
      'Intermediate' => state.t('difficultyIntermediate'),
      'Previously covered' =>
        state.lang == 'bn' ? 'আগে পড়া হয়েছে' : 'Previously covered',
      _ => value ?? '—',
    };
  }

  String _priorityLabel(String? value, AppState state) {
    return switch (value?.trim()) {
      'High' => state.t('priorityHigh'),
      'Medium' => state.t('priorityMedium'),
      _ => value ?? '—',
    };
  }
}

/// Paper chip with a hairline border — no tint fill.
class _LearnChip extends StatelessWidget {
  final String label;

  const _LearnChip({required this.label});

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: dark ? AppColors.darkSurface : AppColors.surface,
        border: Border.all(
          color: dark ? AppColors.darkHairline : AppColors.hairline,
        ),
        borderRadius: BorderRadius.circular(AppRadii.chip),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 13,
          color: AppColors.inkFor(Theme.of(context).brightness),
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final Widget child;

  const _Section({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    // Title colour is explicit ink: red belongs to the rule below,
    // never to the text itself.
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: ink,
            ),
          ),
          const SizedBox(height: 4),
          Container(width: 24, height: 2, color: accent),
          const SizedBox(height: 6),
          child,
        ],
      ),
    );
  }
}

class _Absent extends StatelessWidget {
  final String text;

  const _Absent({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 14,
        fontStyle: FontStyle.italic,
        color: AppColors.secondaryFor(Theme.of(context).brightness),
      ),
    );
  }
}

class _MetaRow extends StatelessWidget {
  final String label;
  final String value;

  const _MetaRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Text(
        '$label: $value',
        style: TextStyle(
          fontSize: 13,
          color: AppColors.secondaryFor(Theme.of(context).brightness),
        ),
      ),
    );
  }
}

/// Phrase card — same LearnSurface + section system as WordCard.
class PhraseCard extends StatelessWidget {
  final Phrase phrase;
  final AppState state;

  const PhraseCard({
    super.key,
    required this.phrase,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final t = state.t;
    // Explicit ink everywhere, same rule as WordCard: nothing here
    // may inherit a colour (v1.2.0 fallback-style bug).
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    final secondary = AppColors.secondaryFor(Theme.of(context).brightness);
    return LearnSurface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            phrase.phrase,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: ink,
            ),
          ),
          if (hasValue(phrase.banglaMeaning))
            Text(
              phrase.banglaMeaning!,
              style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  height: 1.4,
                  color: ink),
            ),
          if (hasValue(phrase.type))
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                phrase.type!,
                style: TextStyle(fontSize: 13, color: secondary),
              ),
            ),
          const SizedBox(height: 10),
          if (hasValue(phrase.englishExplanation))
            _Section(
              title: t('englishExplanation'),
              child: Text(
                phrase.englishExplanation!,
                style: TextStyle(
                  fontSize: 15,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          if (hasValue(phrase.usage))
            _Section(
              title: t('usage'),
              child: Text(
                phrase.usage!,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          if (hasValue(phrase.example1) || hasValue(phrase.example2))
            _Section(
              title: t('example'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (hasValue(phrase.example1))
                    Text(
                      '“${phrase.example1!}”',
                      style: TextStyle(
                        fontSize: 15,
                        fontStyle: FontStyle.italic,
                        height: 1.6,
                        color: ink,
                      ),
                    ),
                  if (hasValue(phrase.example2))
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        '“${phrase.example2!}”',
                        style: TextStyle(
                          fontSize: 15,
                          fontStyle: FontStyle.italic,
                          height: 1.6,
                          color: ink,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          if (phrase.collocations.isNotEmpty)
            _Section(
              title: t('collocations'),
              child: Text(
                phrase.collocations.join(' ; '),
                style: TextStyle(
                  fontSize: 15,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          if (hasValue(phrase.examValue))
            _Section(
              title: t('examValue'),
              child: Text(
                phrase.examValue!,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.6,
                  color: ink,
                ),
              ),
            ),
          if (hasValue(phrase.sourcePublication))
            Text(
              '${t('source')}: ${phrase.sourcePublication!}'
              '${hasValue(phrase.articleHeadline) ? ' — ${phrase.articleHeadline}' : ''}',
              style: TextStyle(
                fontSize: 13,
                color: secondary,
                height: 1.4,
              ),
            ),
          if (hasValue(phrase.sourceUrl))
            TextButton.icon(
              onPressed: () => openExternalUrl(phrase.sourceUrl),
              icon: const Icon(Icons.open_in_new, size: 16),
              label: Text(t('openSource')),
            ),
        ],
      ),
    );
  }
}
