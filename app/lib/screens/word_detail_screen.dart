/// Word detail — Phase 3 redesign (mockup image-7, "gratuity").
///
/// Order, top to bottom: app bar (back, "শব্দ ৯ / ২০" position, ONE
/// bookmark), part of speech (Bangla · English, always the same
/// Title-Case capitalisation) + difficulty dots, large serif
/// headword + speaker (device TTS) + IPA + Bangla phonetic, tinted
/// Bangla-meaning box with the English definition, the newspaper
/// sentence with the headword highlighted + source line + hide-word
/// self-test button, tag rows (synonyms / collocations / word
/// family), "খবরে কীভাবে এসেছে" visible, ONE collapsed
/// "পরীক্ষার তথ্য ও সূত্র" row, bottom bar "জানি না" / "জানি".
///
/// Hidden, never shown: any empty row, any "No direct antonym"
/// (or equivalent placeholder) notice, "Priority", and the long BCS
/// relevance text. The data files are untouched — this is display
/// only (data fixes belong to Phase 5).
///
/// জানি / জানি না persists in [AppState] (shared_preferences, the
/// same mechanism as bookmarks and story recall): "জানি" keeps the
/// word out of revision; "জানি না" brings it back after 1, then 3,
/// then 7 days, and the revision tab shows those due words.
///
/// Style: the Phase 2 story screen's language — warm off-white
/// #FBF8F3, near-black text, ONE accent #B3202A used sparingly
/// (POS line, difficulty dots, highlighted headword, blank), Hind
/// Siliguri body, distinct components per section, no tinted cards
/// with coloured left bars, no red square bullets. Side padding 20,
/// touch targets >= 48dp, dark mode matches the structure.
library;

import 'package:flutter/material.dart';

import '../data/exam_patterns.dart';
import '../data/strings.dart';
import '../data/word_display.dart';
import '../models.dart';
import '../services/tts_service.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/word_card.dart';

class WordDetailScreen extends StatefulWidget {
  final Edition edition;
  final VocabWord word;
  final AppState state;

  /// TTS engine. Defaults to the device engine; tests inject a fake.
  final WordTts? tts;

  const WordDetailScreen({
    super.key,
    required this.edition,
    required this.word,
    required this.state,
    this.tts,
  });

  @override
  State<WordDetailScreen> createState() => _WordDetailScreenState();
}

class _WordDetailScreenState extends State<WordDetailScreen> {
  /// The headword is hidden inside the newspaper sentence only.
  bool _wordHidden = false;

  /// Collapsed "পরীক্ষার তথ্য ও সূত্র" row.
  bool _examOpen = false;

  late final WordTts _tts = widget.tts ?? DeviceWordTts();

  Edition get _edition => widget.edition;
  VocabWord get _word => widget.word;
  AppState get _state => widget.state;

  @override
  void dispose() {
    // Never throws, even with no TTS engine on the device.
    _tts.stop();
    super.dispose();
  }

  /// Position in the day's word list ("শব্দ ৯ / ২০"), Bangla digits
  /// in Bengali. Words opened from the revision tab use their
  /// position in that tab's list instead.
  String _positionText() {
    final lang = _state.lang;
    var idx =
        _edition.words.indexWhere((w) => w.headword == _word.headword);
    var total = _edition.words.length;
    if (idx < 0) {
      idx = _edition.revisionWords
          .indexWhere((w) => w.headword == _word.headword);
      total = _edition.revisionWords.length;
    }
    final pos = idx < 0 ? 1 : idx + 1;
    return storyDigits('${_state.t('words')} $pos / $total', lang);
  }

  Future<void> _speak() async {
    final ok = await _tts.speak(_word.headword);
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_state.t('ttsUnavailable'))),
      );
    }
  }

  Future<void> _mark(bool known) async {
    await _state.setWordResult(_edition.date, _word.headword, known);
    if (!mounted) return;
    setState(() {});
    if (!known) {
      final due = _state.wordDueDate(_edition.date, _word.headword);
      if (due != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '${_state.t('nextRevision')}: '
              '${formatEditionDate(due, _state.lang)}',
            ),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    }
  }

  /// Newspaper sentence with the headword highlighted in the accent
  /// (or replaced by a blank while the self-test hide is on).
  List<InlineSpan> _exampleSpans(Color ink, Color accent) {
    const base = TextStyle(fontWeight: FontWeight.w400);
    final sentence = _word.example ?? '';
    final head = _word.headword.trim();
    if (head.isEmpty) return [TextSpan(text: sentence, style: base)];
    final pattern = RegExp(RegExp.escape(head), caseSensitive: false);
    final matches = pattern.allMatches(sentence).toList();
    if (matches.isEmpty) return [TextSpan(text: sentence, style: base)];
    final spans = <InlineSpan>[];
    var start = 0;
    for (final m in matches) {
      if (m.start > start) {
        spans.add(
          TextSpan(text: sentence.substring(start, m.start), style: base),
        );
      }
      spans.add(
        TextSpan(
          text: _wordHidden ? '________' : m.group(0)!,
          style: TextStyle(fontWeight: FontWeight.w800, color: accent),
        ),
      );
      start = m.end;
    }
    if (start < sentence.length) {
      spans.add(TextSpan(text: sentence.substring(start), style: base));
    }
    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final lang = _state.lang;
    final t = _state.t;
    final word = _word;
    final brightness = Theme.of(context).brightness;
    final paper = AppColors.storyPaperFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final surface = AppColors.storySurfaceFor(brightness);
    final soft = AppColors.surfaceSoftFor(brightness);
    final bookmarked = _state.isWordBookmarked(_edition.date, word.headword);
    final result = _state.wordResult(_edition.date, word.headword);
    final related = _edition.relatedPhrasesFor(word);
    final examTypes = examTypesFor(word, _edition);
    final verifiedPattern = verifiedExamPatterns[word.headword.toLowerCase()];
    final sourceLine = exampleSourceLine(word, lang);
    final pos = posDisplay(word.partOfSpeech, _state.lang);
    final dots = difficultyDots(word.difficulty);
    final difficultyWord = switch (word.difficulty?.trim()) {
      'Advanced' => t('difficultyAdvanced'),
      'Intermediate' => t('difficultyIntermediate'),
      'Basic' => t('difficultyBasic'),
      'Previously covered' => t('difficultyPreviously'),
      _ => '',
    };

    final sections = <Widget>[
      // --- Part of speech + difficulty dots (mockup top line) ---
      if (pos.isNotEmpty || dots > 0)
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 8,
          runSpacing: 4,
          children: [
            if (pos.isNotEmpty)
              Text(
                pos,
                style: TextStyle(
                  fontFamily: 'HindSiliguri',
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  color: accent,
                ),
              ),
            if (pos.isNotEmpty && dots > 0)
              Text('·', style: TextStyle(fontSize: 15, color: secondary)),
            if (dots > 0) ...[
              Text(
                t('difficulty'),
                style: TextStyle(
                  fontFamily: 'HindSiliguri',
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: secondary,
                ),
              ),
              Semantics(
                label: difficultyWord.isEmpty
                    ? null
                    : '${t('difficulty')}: $difficultyWord',
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(3, (i) {
                    final on = i < dots;
                    return Padding(
                      padding: const EdgeInsets.only(right: 4),
                      child: Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: on ? accent : Colors.transparent,
                          border: on
                              ? null
                              : Border.all(color: hairline, width: 1.5),
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ],
          ],
        ),
      const SizedBox(height: 12),
      // --- Headword (large serif; FittedBox so one long word never
      // overflows at 200% text scale — it shrinks instead) ---
      FittedBox(
        alignment: Alignment.centerLeft,
        fit: BoxFit.scaleDown,
        child: Text(
          word.headword,
          style: const TextStyle(
            fontFamily: 'NotoSerifBengali',
            fontFamilyFallback: ['HindSiliguri'],
            fontSize: 36,
            height: 1.2,
            fontWeight: FontWeight.w700,
          ).copyWith(color: ink),
        ),
      ),
      const SizedBox(height: 12),
      // --- Speaker + IPA + Bangla phonetic (mockup row) ---
      Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 48,
            height: 48,
            child: OutlinedButton(
              onPressed: _speak,
              style: OutlinedButton.styleFrom(
                shape: const CircleBorder(),
                side: BorderSide(color: hairline),
                padding: EdgeInsets.zero,
                minimumSize: const Size(48, 48),
              ),
              child: Icon(Icons.volume_up, size: 24, color: ink),
            ),
          ),
          const SizedBox(width: 12),
          if (hasValue(word.ipa) || hasValue(word.banglaPhonetic))
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (hasValue(word.ipa))
                      Text(
                        word.ipa!,
                        style: TextStyle(
                          fontSize: 16,
                          height: 1.5,
                          color: ink,
                        ),
                      ),
                    if (hasValue(word.banglaPhonetic))
                      Text(
                        word.banglaPhonetic!,
                        style: TextStyle(
                          fontFamily: 'HindSiliguri',
                          fontSize: 16,
                          height: 1.5,
                          color: ink,
                        ),
                      ),
                  ],
                ),
              ),
            ),
        ],
      ),
      const SizedBox(height: 28),
      // --- Tinted Bangla-meaning box + English definition ---
      if (hasValue(word.banglaMeaning) || hasValue(word.englishDefinition))
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: soft,
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (hasValue(word.banglaMeaning)) ...[
                Text(
                  t('banglaMeaningLabel'),
                  style: TextStyle(
                    fontFamily: 'HindSiliguri',
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: secondary,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  word.banglaMeaning!,
                  style: TextStyle(
                    fontFamily: 'HindSiliguri',
                    fontSize: 22,
                    height: 1.4,
                    fontWeight: FontWeight.w700,
                    color: ink,
                  ),
                ),
              ],
              if (hasValue(word.englishDefinition)) ...[
                const SizedBox(height: 8),
                Text(
                  word.englishDefinition!,
                  style: TextStyle(
                    fontSize: 16,
                    height: 1.6,
                    color: ink,
                  ),
                ),
              ],
            ],
          ),
        ),
      // --- Newspaper sentence + source + hide-word self-test ---
      if (hasValue(word.example)) ...[
        const SizedBox(height: 28),
        _WordSectionHeading(title: t('newspaperSentence'), ink: ink),
        const SizedBox(height: 12),
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: surface,
            border: Border.all(color: hairline),
            borderRadius: BorderRadius.circular(8),
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              RichText(
                key: const ValueKey('word-example'),
                text: TextSpan(
                  style: AppType.storyBody
                      .copyWith(color: ink, fontSize: 17),
                  children: _exampleSpans(ink, accent),
                ),
              ),
              if (sourceLine != null) ...[
                const SizedBox(height: 8),
                Text(
                  sourceLine,
                  style: TextStyle(
                    fontSize: 13,
                    height: 1.5,
                    color: secondary,
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            key: const ValueKey('hide-word-toggle'),
            onPressed: () => setState(() => _wordHidden = !_wordHidden),
            child: Text(
              _wordHidden ? t('showWord') : t('hideWordForSelfTest'),
            ),
          ),
        ),
      ],
      // --- Tag rows: synonyms / collocations / word family ---
      // Each row is hidden entirely when it has no items.
      if (word.hasSynonyms) ...[
        const SizedBox(height: 28),
        _TagRow(label: t('synonymsLabel'), items: word.synonyms),
      ],
      if (word.hasCollocations) ...[
        const SizedBox(height: 20),
        _TagRow(label: t('collocationsLabel'), items: word.collocations),
      ],
      if (word.hasWordFamily) ...[
        const SizedBox(height: 20),
        _TagRow(label: t('wordFamilyLabel'), items: word.wordFamily),
      ],
      // --- "খবরে কীভাবে এসেছে": always visible, never collapsed ---
      if (hasValue(word.contextNote)) ...[
        const SizedBox(height: 28),
        _WordSectionHeading(title: t('howItAppeared'), ink: ink),
        const SizedBox(height: 8),
        Text(
          word.contextNote!,
          style: AppType.storyBody.copyWith(color: ink, fontSize: 17),
        ),
      ],
      // --- ONE collapsed row: everything else ---
      const SizedBox(height: 28),
      _ExamInfo(
        word: word,
        related: related,
        examTypes: examTypes,
        verifiedPattern: verifiedPattern,
        title: t('examInfoSources'),
        t: t,
        lang: lang,
        open: _examOpen,
        onToggle: () => setState(() => _examOpen = !_examOpen),
      ),
      const SizedBox(height: 24),
    ];

    return Scaffold(
      backgroundColor: paper,
      appBar: AppBar(
        backgroundColor: paper,
        centerTitle: true,
        title: Text(
          _positionText(),
          style: const TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 15,
            fontWeight: FontWeight.w800,
          ),
        ),
        bottom: appBarHairline(context),
        actions: [
          IconButton(
            icon: Icon(
              bookmarked ? Icons.bookmark : Icons.bookmark_border,
              color: bookmarked ? accent : null,
            ),
            tooltip: bookmarked ? t('removeBookmark') : t('bookmark'),
            onPressed: () => _state.toggleWordBookmark(
              _edition.date,
              word.headword,
            ),
          ),
        ],
      ),
      body: SafeArea(
        bottom: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: sections,
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Container(
          color: paper,
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _mark(false),
                  style: OutlinedButton.styleFrom(
                    backgroundColor: result == false
                        ? ink.withValues(alpha: 0.08)
                        : null,
                  ),
                  icon: Icon(
                    result == false
                        ? Icons.check
                        : Icons.close_outlined,
                    size: 18,
                  ),
                  label: Text(t('dontKnow')),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: ink,
                    foregroundColor: brightness == Brightness.dark
                        ? AppColors.darkPaper
                        : Colors.white,
                  ),
                  onPressed: () => _mark(true),
                  icon: Icon(
                    result == true ? Icons.check : Icons.check_outlined,
                    size: 18,
                  ),
                  label: Text(t('knowIt')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Ink section heading, same as the story screen's.
class _WordSectionHeading extends StatelessWidget {
  final String title;
  final Color ink;

  const _WordSectionHeading({required this.title, required this.ink});

  @override
  Widget build(BuildContext context) {
    return Text(title, style: AppType.storySection.copyWith(color: ink));
  }
}

/// One tag row: small grey label + pill chips. The caller hides the
/// row entirely when [items] is empty.
class _TagRow extends StatelessWidget {
  final String label;
  final List<String> items;

  const _TagRow({required this.label, required this.items});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final surface = AppColors.storySurfaceFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: secondary,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: items
              .map(
                (item) => Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: surface,
                    border: Border.all(color: hairline),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    item,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: ink,
                    ),
                  ),
                ),
              )
              .toList(),
        ),
      ],
    );
  }
}

/// ONE collapsed row holding everything else: spelling, antonyms
/// (only when present — never a "no antonym" notice), related
/// phrases, word structure, exam appearance, source. Collapsed by
/// default. Priority and the BCS relevance text are NOT here — they
/// are removed from the card entirely (Phase 3 spec).
class _ExamInfo extends StatelessWidget {
  final VocabWord word;
  final List<Phrase> related;
  final List<String> examTypes;
  final String? verifiedPattern;
  final String title;
  final String Function(String) t;
  final String lang;
  final bool open;
  final VoidCallback onToggle;

  const _ExamInfo({
    required this.word,
    required this.related,
    required this.examTypes,
    required this.verifiedPattern,
    required this.title,
    required this.t,
    required this.lang,
    required this.open,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Container(
      decoration: BoxDecoration(
        color: surface,
        border: Border.all(color: hairline),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: onToggle,
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 14,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: const TextStyle(
                        fontFamily: 'HindSiliguri',
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ).copyWith(color: ink),
                    ),
                  ),
                  Icon(
                    open
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                    color: secondary,
                  ),
                ],
              ),
            ),
          ),
          if (open) ...[
            Container(height: 1, color: hairline),
            Padding(
              padding: const EdgeInsets.all(14),
              child: _ExamInfoBody(
                word: word,
                related: related,
                examTypes: examTypes,
                verifiedPattern: verifiedPattern,
                t: t,
                lang: lang,
                ink: ink,
                secondary: secondary,
                accent: accent,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// The expanded body of the collapsed "পরীক্ষার তথ্য ও সূত্র" row.
class _ExamInfoBody extends StatelessWidget {
  final VocabWord word;
  final List<Phrase> related;
  final List<String> examTypes;
  final String? verifiedPattern;
  final String Function(String) t;
  final String lang;
  final Color ink;
  final Color secondary;
  final Color accent;

  const _ExamInfoBody({
    required this.word,
    required this.related,
    required this.examTypes,
    required this.verifiedPattern,
    required this.t,
    required this.lang,
    required this.ink,
    required this.secondary,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _Sub(
          label: t('spelling'),
          child: Wrap(
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
        ),
        if (word.hasAntonyms) ...[
          const SizedBox(height: 14),
          _Sub(
            label: t('antonyms'),
            child: Text(
              word.antonyms.join(' ; '),
              style: TextStyle(fontSize: 15, height: 1.6, color: ink),
            ),
          ),
        ],
        if (related.isNotEmpty) ...[
          const SizedBox(height: 14),
          _Sub(
            label: t('relatedPhrase'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: related
                  .map(
                    (p) => Padding(
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
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
        if (word.commonStem != null) ...[
          const SizedBox(height: 14),
          _Sub(
            label: t('wordStructure'),
            child: Text(
              '${word.commonStem} + ${word.wordFamily.join(' / ')}',
              style: TextStyle(fontSize: 15, height: 1.6, color: ink),
            ),
          ),
        ],
        const SizedBox(height: 14),
        _Sub(
          label: t('examAppearance'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: examTypes
                    .map(
                      (e) => Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 5,
                        ),
                        decoration: BoxDecoration(
                          color: surface,
                          border: Border.all(color: hairline),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          e,
                          style: TextStyle(fontSize: 13, color: ink),
                        ),
                      ),
                    )
                    .toList(),
              ),
              if (verifiedPattern != null) ...[
                const SizedBox(height: 8),
                Text(
                  '${t('examRefVerified')}: $verifiedPattern',
                  style: TextStyle(
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    height: 1.5,
                    color: ink,
                  ),
                ),
              ],
            ],
          ),
        ),
        if (hasValue(word.sourcePublication) ||
            hasValue(word.articleHeadline)) ...[
          const SizedBox(height: 14),
          _Sub(
            label: t('source'),
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
                    _sourceDate(word.publicationDate!),
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
      ],
    );
  }

  /// Source date: first ISO date in the raw field, rendered as a
  /// real date in the current language; falls back to the raw text
  /// when no ISO date is present.
  String _sourceDate(String raw) {
    final m = RegExp(r'\d{4}-\d{2}-\d{2}').firstMatch(raw);
    if (m == null) return raw;
    return formatEditionDate(m.group(0)!, lang);
  }
}

/// One labelled sub-row inside the collapsed exam-info body.
class _Sub extends StatelessWidget {
  final String label;
  final Widget child;

  const _Sub({required this.label, required this.child});

  @override
  Widget build(BuildContext context) {
    final secondary =
        AppColors.secondaryFor(Theme.of(context).brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: secondary,
          ),
        ),
        const SizedBox(height: 4),
        child,
      ],
    );
  }
}

/// Full-page phrase view: the complete phrase card on its own page,
/// reached by tapping a phrase in the day's phrase list. Mirrors
/// [WordDetailScreen] so words and phrases feel like one flow.
/// UNCHANGED in Phase 3 — phrase cards are out of scope.
class PhraseDetailScreen extends StatelessWidget {
  final Phrase phrase;
  final AppState state;

  const PhraseDetailScreen({
    super.key,
    required this.phrase,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          phrase.phrase,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        bottom: appBarHairline(context),
      ),
      body: SafeArea(
        top: false,
        bottom: true,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          child: PhraseCard(
            phrase: phrase,
            state: state,
          ),
        ),
      ),
    );
  }
}
