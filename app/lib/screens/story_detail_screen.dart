/// Story detail — Phase 2 redesign (mockup image-6).
///
/// Order, top to bottom: app bar (back, "৩ / ১৪" position, ONE
/// bookmark), meta line (category · Bangla date · source) + importance
/// dots, serif headline, "এক লাইনে", "মনে রাখুন" fact tiles (+ bar
/// chart when 3+ comparable numbers), "কী ঘটেছে" bullets, "কেন
/// গুরুত্বপূর্ণ", "পরীক্ষায় যেভাবে আসে" Q→A, "নিজেকে যাচাই করুন"
/// cloze cards, collapsed "পুরো সারাংশ ও সূত্র দেখুন", bottom bar
/// ("পড়া হয়েছে" + share). Every fact appears once in the display
/// sections; the Q→A and cloze sections test those same facts (that
/// is the mockup's design). Nothing is invented: the sections come
/// from [buildStoryLayout], which derives them mechanically from the
/// story's own fields.
///
/// Style: warm off-white #FBF8F3, near-black text, ONE accent
/// #B3202A for key numbers / answers only. Each section is a
/// different component (tiles, chart, Q→A rows, cloze cards) — no
/// tinted cards with coloured left bars, no red square bullets, no
/// single heading style everywhere. Body Hind Siliguri 17sp / 1.75,
/// side padding 20, section gap 30. Dark mode matches the structure.
library;

import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../data/sections.dart';
import '../data/story_layout.dart';
import '../data/strings.dart';
import '../models.dart';
import '../services/share_service.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';

class StoryDetailScreen extends StatefulWidget {
  final Edition edition;
  final Story story;
  final AppState state;

  const StoryDetailScreen({
    super.key,
    required this.edition,
    required this.story,
    required this.state,
  });

  @override
  State<StoryDetailScreen> createState() => _StoryDetailScreenState();
}

class _StoryDetailScreenState extends State<StoryDetailScreen> {
  /// Cloze cards whose answer is revealed (per card index).
  final Set<int> _revealed = {};

  /// Collapsed "পুরো সারাংশ ও সূত্র দেখুন" section.
  bool _summaryOpen = false;

  Story get _story => widget.story;
  Edition get _edition => widget.edition;
  AppState get _state => widget.state;

  String get _heroTag => 'headline-${_edition.date}-${_story.id}';

  /// Position in the day's edition ("৩ / ১৪"), Bangla digits.
  String _positionText(String lang) {
    final i = _edition.stories.indexWhere((s) => s.id == _story.id);
    final pos = i < 0 ? 1 : i + 1;
    return storyDigits('$pos / ${_edition.stories.length}', lang);
  }

  /// Article date, first ISO date in the raw field, else the edition
  /// date — always rendered as a Bangla date, never raw ISO.
  String _metaDate(String lang) {
    final raw = _story.articleDate ?? '';
    final m = RegExp(r'\d{4}-\d{2}-\d{2}').firstMatch(raw);
    final iso = m?.group(0) ?? _edition.date;
    return storyDigits(formatEditionDate(iso, lang), lang);
  }

  @override
  Widget build(BuildContext context) {
    final lang = _state.lang;
    final t = _state.t;
    final story = _story;
    final edition = _edition;
    final layout = buildStoryLayout(story, lang);
    final brightness = Theme.of(context).brightness;
    final paper = AppColors.storyPaperFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final bookmarked = _state.isStoryBookmarked(edition.date, story.id);
    final read = _state.isStoryRead(edition.date, story.id);
    final section = sectionFor(story.category);

    final sections = <Widget>[
      _MetaLine(
        category: sectionName(section, lang),
        date: _metaDate(lang),
        source: story.sourcePublications.isNotEmpty
            ? story.sourcePublications.first
            : null,
        level: story.relevanceLevel,
        lang: lang,
      ),
      const SizedBox(height: 14),
      Hero(
        tag: _heroTag,
        child: Material(
          type: MaterialType.transparency,
          child: Text(
            story.headlineIn(lang),
            style: AppType.storyHeadline.copyWith(color: ink),
          ),
        ),
      ),
      const SizedBox(height: 30),
      _LabelHeading(label: t('oneLiner'), accent: accent),
      const SizedBox(height: 8),
      Text(
        storyDigits(layout.oneLiner, lang),
        style: AppType.storyOneLiner.copyWith(color: ink),
      ),
      if (layout.tiles.isNotEmpty) ...[
        const SizedBox(height: 30),
        _SectionHeading(title: t('remember'), ink: ink),
        const SizedBox(height: 12),
        _FactTiles(tiles: layout.tiles, lang: lang),
        if (layout.chart != null) ...[
          const SizedBox(height: 20),
          _BarChart(chart: layout.chart!, lang: lang),
        ],
      ],
      if (layout.bullets.isNotEmpty) ...[
        const SizedBox(height: 30),
        _SectionHeading(title: t('whatHappened'), ink: ink),
        const SizedBox(height: 10),
        for (var i = 0; i < layout.bullets.length; i++)
          Padding(
            padding: EdgeInsets.only(
              bottom: i < layout.bullets.length - 1 ? 10 : 0,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '–',
                  style: AppType.storyBody.copyWith(color: ink),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    storyDigits(layout.bullets[i], lang),
                    style: AppType.storyBody.copyWith(color: ink),
                  ),
                ),
              ],
            ),
          ),
      ],
      if (layout.whySentence != null) ...[
        const SizedBox(height: 30),
        _LabelHeading(label: t('whyItMatters'), accent: accent),
        const SizedBox(height: 8),
        Text(
          storyDigits(layout.whySentence!, lang),
          style: AppType.storyBody.copyWith(color: ink),
        ),
      ],
      if (layout.qa.isNotEmpty) ...[
        const SizedBox(height: 30),
        _SectionHeading(title: t('examAppearance'), ink: ink),
        const SizedBox(height: 12),
        for (var i = 0; i < layout.qa.length; i++) ...[
          _QaRow(
            pair: layout.qa[i],
            lang: lang,
            ink: ink,
            accent: accent,
          ),
          if (i < layout.qa.length - 1) ...[
            const SizedBox(height: 14),
            Container(height: 1, color: hairline),
            const SizedBox(height: 14),
          ],
        ],
      ],
      if (layout.cloze.isNotEmpty) ...[
        const SizedBox(height: 30),
        _SectionHeading(title: t('selfTest'), ink: ink),
        const SizedBox(height: 12),
        for (var i = 0; i < layout.cloze.length; i++)
          Padding(
            padding: EdgeInsets.only(
              bottom: i < layout.cloze.length - 1 ? 12 : 0,
            ),
            child: _ClozeCard(
              card: layout.cloze[i],
              index: i,
              revealed: _revealed.contains(i),
              onReveal: () => setState(() => _revealed.add(i)),
              editionDate: edition.date,
              storyId: story.id,
              state: _state,
              lang: lang,
            ),
          ),
      ],
      const SizedBox(height: 30),
      _FullSummary(
        layout: layout,
        lang: lang,
        state: _state,
        open: _summaryOpen,
        onToggle: () => setState(() => _summaryOpen = !_summaryOpen),
      ),
      const SizedBox(height: 24),
    ];

    return Scaffold(
      backgroundColor: paper,
      appBar: AppBar(
        backgroundColor: paper,
        centerTitle: true,
        title: Text(
          _positionText(lang),
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
            onPressed: () => _state.toggleStoryBookmark(
              edition.date,
              story.id,
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
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: accent,
                    foregroundColor: Colors.white,
                  ),
                  onPressed: () => _state.toggleStoryRead(
                    edition.date,
                    story.id,
                  ),
                  icon: Icon(
                    read ? Icons.check : Icons.check_box_outline_blank,
                    size: 20,
                  ),
                  label: Text(read ? t('reviewed') : t('markReviewed')),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _shareStory(context),
                  icon: const Icon(Icons.share_outlined, size: 20),
                  label: Text(t('share')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _shareStory(BuildContext context) async {
    final key = GlobalKey();
    final path = await showDialog<String>(
      context: context,
      builder: (dialogContext) => _SharePreviewDialog(
        boundaryKey: key,
        edition: widget.edition,
        story: widget.story,
        state: widget.state,
      ),
    );
    if (path == null || !context.mounted) return;
    bool ok;
    if (path.isEmpty) {
      ok = await ShareService.shareText(
        widget.story.headlineIn(widget.state.lang),
      );
    } else {
      ok = await ShareService.shareImage(
        path,
        widget.story.headlineIn(widget.state.lang),
      );
    }
    if (!ok && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.state.t('shareFailed'))),
      );
    }
  }
}

/// Meta line: category · Bangla date · source, then the importance
/// row ("পরীক্ষায় গুরুত্ব" + 3 dots + word). Never a raw ISO date
/// or an English tag list.
class _MetaLine extends StatelessWidget {
  final String category;
  final String date;
  final String? source;
  final String? level;
  final String lang;

  const _MetaLine({
    required this.category,
    required this.date,
    required this.source,
    required this.level,
    required this.lang,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final meta = [
      category,
      date,
      if (source != null) source!,
    ].join(' · ');
    final filled = switch (level) {
      'High' => 3,
      'Medium' => 2,
      'Low' => 1,
      _ => 0,
    };
    final levelWord = switch (level) {
      'High' => lang == 'bn' ? 'উচ্চ' : 'High',
      'Medium' => lang == 'bn' ? 'মধ্যম' : 'Medium',
      'Low' => lang == 'bn' ? 'কম' : 'Low',
      _ => '',
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          meta,
          style: TextStyle(fontSize: 13, height: 1.5, color: secondary),
        ),
        if (filled > 0) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              Text(
                lang == 'bn' ? 'পরীক্ষায় গুরুত্ব' : 'Exam relevance',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: ink,
                ),
              ),
              const SizedBox(width: 8),
              Row(
                children: List.generate(3, (i) {
                  final on = i < filled;
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
              const SizedBox(width: 4),
              Text(
                levelWord,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                  color: accent,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}

/// Small accent label heading (used for "এক লাইনে" and
/// "কেন গুরুত্বপূর্ণ").
class _LabelHeading extends StatelessWidget {
  final String label;
  final Color accent;

  const _LabelHeading({required this.label, required this.accent});

  @override
  Widget build(BuildContext context) {
    return Text(label, style: AppType.storyLabel.copyWith(color: accent));
  }
}

/// Ink section heading (used for "মনে রাখুন", "কী ঘটেছে",
/// "পরীক্ষায় যেভাবে আসে", "নিজেকে যাচাই করুন").
class _SectionHeading extends StatelessWidget {
  final String title;
  final Color ink;

  const _SectionHeading({required this.title, required this.ink});

  @override
  Widget build(BuildContext context) {
    return Text(title, style: AppType.storySection.copyWith(color: ink));
  }
}

/// "মনে রাখুন": max 4 fact tiles in a 2-column grid. Rows stretch to
/// the taller tile, so nothing clips at large text scale. Label small
/// grey, value large bold (accent when numeric, ink otherwise), tiny
/// grey original English figure underneath.
class _FactTiles extends StatelessWidget {
  final List<FactTile> tiles;
  final String lang;

  const _FactTiles({required this.tiles, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final rows = <Widget>[];
    for (var i = 0; i < tiles.length; i += 2) {
      final pair = tiles.skip(i).take(2).toList();
      rows.add(
        Padding(
          padding: EdgeInsets.only(bottom: i + 2 < tiles.length ? 12 : 0),
          // IntrinsicHeight: the Row lives inside a SingleChildScrollView
          // (unbounded height), so CrossAxisAlignment.stretch alone
          // crashes layout ("BoxConstraints forces an infinite height").
          // IntrinsicHeight measures the tallest tile first, giving the
          // Row a bounded height and equal-height tiles.
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (var j = 0; j < pair.length; j++) ...[
                  if (j > 0) const SizedBox(width: 12),
                  Expanded(
                    child: Container(
                    decoration: BoxDecoration(
                      color: surface,
                      border: Border.all(color: hairline),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (pair[j].label.isNotEmpty) ...[
                          Text(
                            storyDigits(pair[j].label, lang),
                            style: TextStyle(
                              fontSize: 12,
                              height: 1.4,
                              color: secondary,
                            ),
                          ),
                          const SizedBox(height: 4),
                        ],
                        Text(
                          storyDigits(pair[j].value, lang),
                          style: TextStyle(
                            fontFamily: 'HindSiliguri',
                            fontSize: 20,
                            height: 1.3,
                            fontWeight: FontWeight.w800,
                            color: pair[j].isNumeric ? accent : ink,
                          ),
                        ),
                        if (pair[j].original != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            pair[j].original!,
                            style: TextStyle(
                              fontSize: 11,
                              height: 1.4,
                              color: secondary,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
              // A lone tile in the last row takes half the width,
              // like the mockup's 2-column grid.
              if (pair.length == 1) const Expanded(child: SizedBox.shrink()),
            ],
          ),
        ),
        ),
      );
    }
    return Column(children: rows);
  }
}

/// Small bar chart for 3+ comparable numbers: value above the bar,
/// label below. The tallest bar is the full accent; the others are
/// the same accent at lower opacity (one accent, one scale).
class _BarChart extends StatelessWidget {
  final ChartData chart;
  final String lang;

  const _BarChart({required this.chart, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final maxValue = chart.bars
        .map((b) => b.value)
        .fold<double>(0, (a, b) => a > b ? a : b);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          storyDigits(chart.title, lang),
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: secondary,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            for (final bar in chart.bars)
              Expanded(
                child: Column(
                  children: [
                    Text(
                      storyDigits(bar.display, lang),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: accent,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      width: 44,
                      height: maxValue <= 0
                          ? 8
                          : (bar.value / maxValue * 110).clamp(8, 110),
                      color: bar.value == maxValue
                          ? accent
                          : accent.withValues(alpha: 0.55),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      storyDigits(bar.label, lang),
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 11,
                        height: 1.4,
                        color: secondary,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
        const SizedBox(height: 6),
        Container(height: 1, color: hairline),
      ],
    );
  }
}

/// One exam Q→A row: question in bold ink, answer in bold accent.
class _QaRow extends StatelessWidget {
  final QaPair pair;
  final String lang;
  final Color ink;
  final Color accent;

  const _QaRow({
    required this.pair,
    required this.lang,
    required this.ink,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          storyDigits(pair.question, lang),
          style: const TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 16,
            height: 1.6,
            fontWeight: FontWeight.w700,
          ).copyWith(color: ink),
        ),
        const SizedBox(height: 4),
        Text(
          storyDigits(pair.answer, lang),
          style: const TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 16,
            height: 1.6,
            fontWeight: FontWeight.w700,
          ).copyWith(color: accent),
        ),
      ],
    );
  }
}

/// One cloze card: the sentence with the blank in accent, an
/// "উত্তর দেখুন" button, then the revealed answer plus
/// "জানি" / "জানি না" (persisted per story via AppState).
class _ClozeCard extends StatelessWidget {
  final ClozeCard card;
  final int index;
  final bool revealed;
  final VoidCallback onReveal;
  final String editionDate;
  final String storyId;
  final AppState state;
  final String lang;

  const _ClozeCard({
    required this.card,
    required this.index,
    required this.revealed,
    required this.onReveal,
    required this.editionDate,
    required this.storyId,
    required this.state,
    required this.lang,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final result = state.recallResult(editionDate, storyId, index);
    return Container(
      decoration: BoxDecoration(
        color: surface,
        border: Border.all(color: hairline),
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ClozeText(text: card.text, lang: lang, ink: ink, accent: accent),
          const SizedBox(height: 12),
          if (!revealed)
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: onReveal,
                child: Text(state.t('showAnswer')),
              ),
            )
          else ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${state.t('answerLabel')}: ',
                  style: TextStyle(
                    fontSize: 16,
                    height: 1.6,
                    fontWeight: FontWeight.w700,
                    color: secondary,
                  ),
                ),
                Expanded(
                  child: Text(
                    storyDigits(card.answer, lang),
                    style: TextStyle(
                      fontSize: 16,
                      height: 1.6,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: result == true
                          ? accent
                          : accent.withValues(alpha: 0.85),
                    ),
                    onPressed: () => state.setRecallResult(
                      editionDate,
                      storyId,
                      index,
                      true,
                    ),
                    icon: Icon(
                      result == true ? Icons.check : Icons.check_outlined,
                      size: 18,
                    ),
                    label: Text(state.t('knowIt')),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => state.setRecallResult(
                      editionDate,
                      storyId,
                      index,
                      false,
                    ),
                    icon: Icon(
                      result == false
                          ? Icons.check
                          : Icons.close_outlined,
                      size: 18,
                    ),
                    label: Text(state.t('dontKnow')),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// Cloze sentence with the '______' blank rendered in the accent.
class _ClozeText extends StatelessWidget {
  final String text;
  final String lang;
  final Color ink;
  final Color accent;

  const _ClozeText({
    required this.text,
    required this.lang,
    required this.ink,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    final shown = storyDigits(text, lang);
    final parts = shown.split('______');
    return Text.rich(
      TextSpan(
        style: AppType.storyBody.copyWith(color: ink, fontSize: 16),
        children: [
          for (var i = 0; i < parts.length; i++) ...[
            if (i > 0)
              TextSpan(
                text: '______',
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: accent,
                ),
              ),
            TextSpan(text: parts[i]),
          ],
        ],
      ),
    );
  }
}

/// Collapsed "পুরো সারাংশ ও সূত্র দেখুন": full summary, key people,
/// and tappable source links. Collapsed by default.
class _FullSummary extends StatelessWidget {
  final StoryLayout layout;
  final String lang;
  final AppState state;
  final bool open;
  final VoidCallback onToggle;

  const _FullSummary({
    required this.layout,
    required this.lang,
    required this.state,
    required this.open,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
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
                      state.t('fullSummarySources'),
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    storyDigits(layout.fullSummary, lang),
                    style: AppType.storyBody.copyWith(
                      color: ink,
                      fontSize: 16,
                    ),
                  ),
                  if (layout.people.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text(
                      state.t('keyPeople'),
                      style: AppType.storyLabel.copyWith(color: secondary),
                    ),
                    const SizedBox(height: 8),
                    for (final p in layout.people)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '–',
                              style: AppType.storyBody.copyWith(color: ink),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                storyDigits(p, lang),
                                style: AppType.storyBody.copyWith(
                                  color: ink,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                  if (layout.sources.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text(
                      state.t('sourcesTitle'),
                      style: AppType.storyLabel.copyWith(color: secondary),
                    ),
                    const SizedBox(height: 8),
                    for (final src in layout.sources)
                      _SourceRow(src: src, lang: lang),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// One tappable source row inside the collapsed section.
class _SourceRow extends StatelessWidget {
  final SourceRef src;
  final String lang;

  const _SourceRow({required this.src, required this.lang});

  String? _sourceDate() {
    final raw = src.date ?? '';
    final m = RegExp(r'\d{4}-\d{2}-\d{2}').firstMatch(raw);
    if (m == null) return null;
    return storyDigits(formatEditionDate(m.group(0)!, lang), lang);
  }

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final date = _sourceDate();
    return Column(
      children: [
        InkWell(
          onTap: src.url != null ? () => openExternalUrl(src.url) : null,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        src.publication,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                        ).copyWith(color: ink),
                      ),
                      if (src.headline.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          src.headline,
                          style: TextStyle(
                            fontSize: 14,
                            height: 1.5,
                            color: secondary,
                          ),
                        ),
                      ],
                      if (date != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          date,
                          style: TextStyle(fontSize: 12, color: secondary),
                        ),
                      ],
                    ],
                  ),
                ),
                if (src.url != null)
                  Icon(Icons.open_in_new, size: 18, color: secondary),
              ],
            ),
          ),
        ),
        Container(height: 1, color: hairline),
      ],
    );
  }
}

/// Share preview dialog: paper background, radius 12, the exact image
/// card the user will share. Renders to PNG while still mounted.
class _SharePreviewDialog extends StatelessWidget {
  final GlobalKey boundaryKey;
  final Edition edition;
  final Story story;
  final AppState state;

  const _SharePreviewDialog({
    required this.boundaryKey,
    required this.edition,
    required this.story,
    required this.state,
  });

  Future<void> _onShare(BuildContext context) async {
    String path = '';
    try {
      final boundary = boundaryKey.currentContext?.findRenderObject()
          as RenderRepaintBoundary?;
      if (boundary != null) {
        final image = await boundary.toImage(pixelRatio: 3.0);
        final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
        final bytes = byteData?.buffer.asUint8List();
        final dir = await ShareService.cacheDir();
        if (bytes != null && dir != null) {
          final file = File('$dir/share-${story.id}.png');
          await file.writeAsBytes(bytes);
          path = file.path;
        }
      }
    } catch (_) {
      path = '';
    }
    if (context.mounted) Navigator.of(context).pop(path);
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Dialog(
      backgroundColor: dark ? AppColors.darkSurface : AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.learn),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RepaintBoundary(
              key: boundaryKey,
              child: _ShareCard(edition: edition, story: story, state: state),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(state.t('close')),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: () => _onShare(context),
                  child: Text(state.t('share')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Branded image card: white, radius 4, 1px ink border, 4px red rule
/// at the top, ink wordmark + date, headline, summary, relevance mark
/// + first source. No invented content.
class _ShareCard extends StatelessWidget {
  final Edition edition;
  final Story story;
  final AppState state;

  const _ShareCard({
    required this.edition,
    required this.story,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final lang = state.lang;
    const accent = AppColors.red;
    return Container(
      width: 320,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AppRadii.small),
        border: Border.all(color: AppColors.ink),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(height: 4, color: accent),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Text(
                  state.t('appName'),
                  style: const TextStyle(
                    color: AppColors.ink,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const Spacer(),
                Text(
                  formatEditionDate(edition.date, lang),
                  style: const TextStyle(
                    color: AppColors.inkSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  story.headlineIn(lang),
                  style: const TextStyle(
                    fontFamily: 'NotoSerifBengali',
                    fontFamilyFallback: ['HindSiliguri'],
                    fontSize: 19,
                    height: 1.35,
                    fontWeight: FontWeight.w700,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  story.summaryIn(lang),
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontFamily: 'HindSiliguri',
                    fontSize: 13,
                    height: 1.6,
                    color: AppColors.inkSecondary,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    if (story.sourcePublications.isNotEmpty)
                      Flexible(
                        child: Text(
                          story.sourcePublications.first,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12,
                            fontStyle: FontStyle.italic,
                            color: AppColors.inkFaint,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
