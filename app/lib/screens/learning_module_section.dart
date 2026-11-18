/// Learning module sections on the story screen — the 11-section
/// model (LEARNING_MODULE_MODEL_V2.md, confirmed 2026-11-18).
///
/// Renders the per-story `learning_module` in the app's existing story
/// design language: warm paper, near-black ink, ONE accent for key
/// numbers / answers only, Hind Siliguri body, hairline separators.
/// News facts and GK facts stay in separate sections with separate
/// sources — the verified-facts section carries the news sources, the
/// topic-GK, institutions and extra-knowledge sections carry their
/// own authoritative sources underneath. Nothing is invented: every
/// section renders only what the module JSON carries, and a missing
/// part renders nothing. A story without a module never reaches this
/// widget (the story screen guards on `story.learningModule != null`),
/// so the old screen is unchanged for older data. The 16 renovated
/// editions carry the v1 shape (`exam_notes` instead of the
/// institutions / extra-knowledge sections, plain-string news
/// source, map-keyed MCQ options) — the parser accepts both shapes
/// and this widget renders whatever keys a file carries.
///
/// Order: hero figure + news summary, verified facts, topic GK lesson,
/// institutions, extra knowledge, exam notes (v1 only), MCQ practice
/// (interactive: tap an option to reveal the correct answer +
/// explanation), written prep, vocabulary, revision, deep prep.
library;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';

class LearningModuleSection extends StatefulWidget {
  final LearningModule module;
  final String lang;
  final AppState state;

  const LearningModuleSection({
    super.key,
    required this.module,
    required this.lang,
    required this.state,
  });

  @override
  State<LearningModuleSection> createState() => _LearningModuleSectionState();
}

class _LearningModuleSectionState extends State<LearningModuleSection> {
  /// MCQ practice answers: question index -> picked option key.
  final Map<int, String> _answers = {};

  LearningModule get _m => widget.module;
  String get _lang => widget.lang;
  String _t(String key) => widget.state.t(key);

  String _d(String text) => storyDigits(text, _lang);

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final children = <Widget>[
      Container(height: 1, color: AppColors.storyHairlineFor(brightness)),
      const SizedBox(height: 16),
      _LmLabelHeading(label: _t('lmModuleTitle'), lang: _lang),
      if (_m.heroFigure != null) ...[
        const SizedBox(height: 16),
        _HeroFigure(module: _m, lang: _lang),
      ],
      if (_m.newsSummary != null &&
          _m.newsSummary!.trim().isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmLabelHeading(label: _t('lmNews'), lang: _lang),
        const SizedBox(height: 8),
        Text(
          _d(_m.newsSummary!),
          style: AppType.storyBody.copyWith(color: ink),
        ),
        // v2: the source is an explicit object — rendered as a
        // tappable link line (publication • Bangla date). v1 keeps
        // the plain source string below it.
        if (_m.newsSourceObj != null && !_m.newsSourceObj!.isEmpty)
          _NewsSourceLine(source: _m.newsSourceObj!, lang: _lang),
        if (_m.newsSource != null &&
            _m.newsSource!.trim().isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            '${_t('source')}: ${_d(_m.newsSource!)}',
            style: TextStyle(
              fontSize: 12,
              height: 1.5,
              color: AppColors.secondaryFor(brightness),
            ),
          ),
        ],
      ],
      if (_m.verifiedFacts.isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmVerifiedFacts'), lang: _lang),
        const SizedBox(height: 12),
        _FactRows(facts: _m.verifiedFacts, lang: _lang),
      ],
      if (_m.topicGk != null || _m.topicGkMarker != null) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmTopicGk'), lang: _lang),
        const SizedBox(height: 12),
        if (_m.topicGkMarker != null)
          Text(
            _d(_m.topicGkMarker!),
            style: TextStyle(
              fontSize: 16,
              height: 1.6,
              fontStyle: FontStyle.italic,
              color: AppColors.secondaryFor(brightness),
            ),
          )
        else if (_m.topicGk != null)
          _TopicGkBody(gk: _m.topicGk!, lang: _lang, state: widget.state),
      ],
      if (_m.examNotes != null || _m.examNotesMarker != null) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmExamNotes'), lang: _lang),
        const SizedBox(height: 12),
        if (_m.examNotesMarker != null)
          Text(
            _d(_m.examNotesMarker!),
            style: TextStyle(
              fontSize: 16,
              height: 1.6,
              fontStyle: FontStyle.italic,
              color: AppColors.secondaryFor(brightness),
            ),
          )
        else if (_m.examNotes != null)
          _ExamNotesBody(notes: _m.examNotes!, lang: _lang, state: widget.state),
      ],
      if (_m.institutions.isNotEmpty || _m.institutionsMarker != null) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmInstitutions'), lang: _lang),
        const SizedBox(height: 12),
        if (_m.institutionsMarker != null)
          _LmMarker(text: _d(_m.institutionsMarker!), lang: _lang)
        else
          _InstitutionsBody(items: _m.institutions, lang: _lang),
      ],
      if (_m.extraKnowledge.isNotEmpty ||
          _m.extraKnowledgeMarker != null) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmExtraKnowledge'), lang: _lang),
        const SizedBox(height: 12),
        if (_m.extraKnowledgeMarker != null)
          _LmMarker(text: _d(_m.extraKnowledgeMarker!), lang: _lang)
        else
          _ExtraKnowledgeBody(items: _m.extraKnowledge, lang: _lang),
      ],
      if (_m.mcqPractice.isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmMcqPractice'), lang: _lang),
        const SizedBox(height: 12),
        for (var i = 0; i < _m.mcqPractice.length; i++)
          Padding(
            padding: EdgeInsets.only(
              bottom: i < _m.mcqPractice.length - 1 ? 12 : 0,
            ),
            child: _LmMcqCard(
              mcq: _m.mcqPractice[i],
              index: i,
              selected: _answers[i],
              onSelect: (key) => setState(() => _answers[i] = key),
              lang: _lang,
              state: widget.state,
            ),
          ),
      ],
      if (_m.writtenPrep.isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmWrittenPrep'), lang: _lang),
        for (var i = 0; i < _m.writtenPrep.length; i++) ...[
          const SizedBox(height: 16),
          _WrittenItem(item: _m.writtenPrep[i], lang: _lang, state: widget.state),
        ],
      ],
      if (_m.vocabulary.isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmVocabulary'), lang: _lang),
        const SizedBox(height: 12),
        for (var i = 0; i < _m.vocabulary.length; i++) ...[
          _VocabRow(word: _m.vocabulary[i], lang: _lang, state: widget.state),
          if (i < _m.vocabulary.length - 1) ...[
            const SizedBox(height: 14),
            Container(
              height: 1,
              color: AppColors.storyHairlineFor(brightness),
            ),
            const SizedBox(height: 14),
          ],
        ],
      ],
      if (_m.revision != null) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmRevision'), lang: _lang),
        const SizedBox(height: 12),
        _RevisionBody(revision: _m.revision!, lang: _lang, state: widget.state),
      ],
      if (_m.deepPrep.isNotEmpty) ...[
        const SizedBox(height: 30),
        _LmSectionHeading(title: _t('lmDeepPrep'), lang: _lang),
        const SizedBox(height: 10),
        for (var i = 0; i < _m.deepPrep.length; i++)
          Padding(
            padding: EdgeInsets.only(
              bottom: i < _m.deepPrep.length - 1 ? 10 : 0,
            ),
            child: _LmBullet(text: _d(_m.deepPrep[i]), lang: _lang),
          ),
      ],
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }
}

/// Accent small label heading (same style as the story screen's
/// "এক লাইনে" / "কেন গুরুত্বপূর্ণ").
class _LmLabelHeading extends StatelessWidget {
  final String label;
  final String lang;

  const _LmLabelHeading({required this.label, required this.lang});

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.storyAccentFor(Theme.of(context).brightness);
    return Text(label, style: AppType.storyLabel.copyWith(color: accent));
  }
}

/// Ink section heading (same style as the story screen's "মনে রাখুন").
class _LmSectionHeading extends StatelessWidget {
  final String title;
  final String lang;

  const _LmSectionHeading({required this.title, required this.lang});

  @override
  Widget build(BuildContext context) {
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    return Text(title, style: AppType.storySection.copyWith(color: ink));
  }
}

/// Hero figure: the single most exam-askable number, big in the accent,
/// with its label underneath — the fact-tile visual language.
class _HeroFigure extends StatelessWidget {
  final LearningModule module;
  final String lang;

  const _HeroFigure({required this.module, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Container(
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
          Text(
            storyDigits(module.heroFigure!, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 28,
              height: 1.3,
              fontWeight: FontWeight.w800,
            ).copyWith(color: accent),
          ),
          if (module.heroLabel != null &&
              module.heroLabel!.trim().isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              storyDigits(module.heroLabel!, lang),
              style: TextStyle(fontSize: 13, height: 1.5, color: secondary),
            ),
          ],
          if (module.heroNote != null &&
              module.heroNote!.trim().isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              storyDigits(module.heroNote!, lang),
              style: TextStyle(fontSize: 13, height: 1.5, color: secondary),
            ),
          ],
          if (module.heroSource != null &&
              module.heroSource!.trim().isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              storyDigits(module.heroSource!, lang),
              style: TextStyle(fontSize: 12, height: 1.5, color: secondary),
            ),
          ],
        ],
      ),
    );
  }
}

/// Label/value fact rows with hairline separators. A fact without a
/// label renders as a dash bullet instead.
class _FactRows extends StatelessWidget {
  final List<LmFact> facts;
  final String lang;

  const _FactRows({required this.facts, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < facts.length; i++) ...[
          if (i > 0) ...[
            const SizedBox(height: 12),
            Container(height: 1, color: hairline),
            const SizedBox(height: 12),
          ],
          if (facts[i].label != null &&
              facts[i].label!.trim().isNotEmpty) ...[
            Text(
              storyDigits(facts[i].label!, lang),
              style: TextStyle(
                fontSize: 13,
                height: 1.4,
                fontWeight: FontWeight.w700,
                color: secondary,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              storyDigits(facts[i].value, lang),
              style: const TextStyle(
                fontFamily: 'HindSiliguri',
                fontSize: 16,
                height: 1.6,
                fontWeight: FontWeight.w700,
              ).copyWith(color: ink),
            ),
          ] else
            _LmBullet(text: storyDigits(facts[i].value, lang), lang: lang),
          // v2 verified facts carry a date; shown with the source,
          // never as a raw ISO string.
          if ((facts[i].source != null &&
                  facts[i].source!.trim().isNotEmpty) ||
              (facts[i].date != null &&
                  facts[i].date!.trim().isNotEmpty)) ...[
            const SizedBox(height: 2),
            Text(
              [
                if (facts[i].source != null &&
                    facts[i].source!.trim().isNotEmpty)
                  storyDigits(facts[i].source!, lang),
                if (facts[i].date != null &&
                    facts[i].date!.trim().isNotEmpty)
                  _displayDate(facts[i].date!, lang),
              ].join(' · '),
              style: TextStyle(fontSize: 12, height: 1.5, color: secondary),
            ),
          ],
        ],
      ],
    );
  }
}

/// An ISO date rendered as a Bangla date; any other text passes
/// through digit conversion only, never shown raw as ISO.
String _displayDate(String raw, String lang) {
  final m = RegExp(r'\d{4}-\d{2}-\d{2}').firstMatch(raw);
  if (m != null) return storyDigits(formatEditionDate(m.group(0)!, lang), lang);
  return storyDigits(raw, lang);
}

/// The v2 news source line: publication • Bangla date, tappable to
/// open the original article. The URL itself is never shown as text.
class _NewsSourceLine extends StatelessWidget {
  final LmNewsSource source;
  final String lang;

  const _NewsSourceLine({required this.source, required this.lang});

  @override
  Widget build(BuildContext context) {
    final secondary = AppColors.secondaryFor(Theme.of(context).brightness);
    final parts = [
      if (source.publication != null && source.publication!.trim().isNotEmpty)
        source.publication!.trim(),
      if (source.date != null && source.date!.trim().isNotEmpty)
        _displayDate(source.date!, lang),
    ].join(' · ');
    final line = parts.isEmpty ? null : storyDigits(parts, lang);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: InkWell(
        onTap: source.url != null && source.url!.trim().isNotEmpty
            ? () => openExternalUrl(source.url)
            : null,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (line != null)
              Expanded(
                child: Text(
                  line,
                  style: TextStyle(
                    fontSize: 12,
                    height: 1.5,
                    color: secondary,
                  ),
                ),
              ),
            if (source.url != null && source.url!.trim().isNotEmpty) ...[
              const SizedBox(width: 6),
              Icon(Icons.open_in_new, size: 16, color: secondary),
            ],
          ],
        ),
      ),
    );
  }
}

/// The per-section "যাচাই করা যায়নি" marker: italic secondary text,
/// shown instead of content for that section only.
class _LmMarker extends StatelessWidget {
  final String text;
  final String lang;

  const _LmMarker({required this.text, required this.lang});

  @override
  Widget build(BuildContext context) {
    return Text(
      storyDigits(text, lang),
      style: TextStyle(
        fontSize: 16,
        height: 1.6,
        fontStyle: FontStyle.italic,
        color: AppColors.secondaryFor(Theme.of(context).brightness),
      ),
    );
  }
}

/// One dash bullet row (same as the story screen's "কী ঘটেছে" bullets).
class _LmBullet extends StatelessWidget {
  final String text;
  final String lang;

  const _LmBullet({required this.text, required this.lang});

  @override
  Widget build(BuildContext context) {
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('–', style: AppType.storyBody.copyWith(color: ink)),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            storyDigits(text, lang),
            style: AppType.storyBody.copyWith(color: ink),
          ),
        ),
      ],
    );
  }
}

/// The topic-GK lesson body: title, intro paragraph, fact rows,
/// distinctions, then its own authoritative sources.
class _TopicGkBody extends StatelessWidget {
  final LmTopicGk gk;
  final String lang;
  final AppState state;

  const _TopicGkBody({
    required this.gk,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (gk.title != null && gk.title!.trim().isNotEmpty) ...[
          Text(
            storyDigits(gk.title!, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w800,
            ).copyWith(color: ink),
          ),
          const SizedBox(height: 8),
        ],
        if (gk.intro != null && gk.intro!.trim().isNotEmpty) ...[
          Text(
            storyDigits(gk.intro!, lang),
            style: AppType.storyBody.copyWith(color: ink),
          ),
          const SizedBox(height: 12),
        ],
        if (gk.facts.isNotEmpty) _FactRows(facts: gk.facts, lang: lang),
        // v2: titled label/value tables inside the lesson.
        if (gk.tables.isNotEmpty) ...[
          for (var t = 0; t < gk.tables.length; t++) ...[
            const SizedBox(height: 16),
            if (gk.tables[t].title != null &&
                gk.tables[t].title!.trim().isNotEmpty) ...[
              Text(
                storyDigits(gk.tables[t].title!, lang),
                style: TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  fontWeight: FontWeight.w800,
                  color: secondary,
                ),
              ),
              const SizedBox(height: 8),
            ],
            if (gk.tables[t].rows.isNotEmpty)
              _FactRows(facts: gk.tables[t].rows, lang: lang),
          ],
        ],
        if (gk.distinctions.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            state.t('lmDistinctions'),
            style: TextStyle(
              fontSize: 13,
              height: 1.4,
              fontWeight: FontWeight.w800,
              color: secondary,
            ),
          ),
          const SizedBox(height: 8),
          for (var i = 0; i < gk.distinctions.length; i++)
            Padding(
              padding: EdgeInsets.only(
                bottom: i < gk.distinctions.length - 1 ? 10 : 0,
              ),
              child: _DistinctionRow(
                distinction: gk.distinctions[i],
                lang: lang,
              ),
            ),
        ],
        if (gk.sources.isNotEmpty) ...[
          const SizedBox(height: 16),
          _LmSources(sources: gk.sources, lang: lang, state: state),
        ],
      ],
    );
  }
}

/// One distinction: "title — text" when titled, plain bullet otherwise.
class _DistinctionRow extends StatelessWidget {
  final LmDistinction distinction;
  final String lang;

  const _DistinctionRow({required this.distinction, required this.lang});

  @override
  Widget build(BuildContext context) {
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    // v2 comparison shape {a, b, points}: "A — B" with the
    // differences as sub-bullets. No invented connective word.
    if (distinction.isComparison) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('–', style: AppType.storyBody.copyWith(color: ink)),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${storyDigits(distinction.a!, lang)} — ${storyDigits(distinction.b!, lang)}',
                  style: AppType.storyBody.copyWith(
                    color: ink,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          if (distinction.points.isNotEmpty) ...[
            const SizedBox(height: 6),
            for (var i = 0; i < distinction.points.length; i++)
              Padding(
                padding: EdgeInsets.only(
                  left: 24,
                  bottom: i < distinction.points.length - 1 ? 6 : 0,
                ),
                child: _LmBullet(
                  text: storyDigits(distinction.points[i], lang),
                  lang: lang,
                ),
              ),
          ],
        ],
      );
    }
    if (distinction.title == null || distinction.title!.trim().isEmpty) {
      return _LmBullet(
        text: storyDigits(distinction.text, lang),
        lang: lang,
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('–', style: AppType.storyBody.copyWith(color: ink)),
        const SizedBox(width: 10),
        Expanded(
          child: Text.rich(
            TextSpan(
              style: AppType.storyBody.copyWith(color: ink),
              children: [
                TextSpan(
                  text: storyDigits(distinction.title!, lang),
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                TextSpan(text: ' — ${storyDigits(distinction.text, lang)}'),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

/// The exam-notes body: optional intro paragraph, bullets, then its
/// own authoritative sources.
class _ExamNotesBody extends StatelessWidget {
  final LmExamNotes notes;
  final String lang;
  final AppState state;

  const _ExamNotesBody({
    required this.notes,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final ink = AppColors.inkFor(Theme.of(context).brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (notes.intro != null && notes.intro!.trim().isNotEmpty) ...[
          Text(
            storyDigits(notes.intro!, lang),
            style: AppType.storyBody.copyWith(color: ink),
          ),
          const SizedBox(height: 12),
        ],
        for (var i = 0; i < notes.bullets.length; i++)
          Padding(
            padding: EdgeInsets.only(
              bottom: i < notes.bullets.length - 1 ? 10 : 0,
            ),
            child: _LmBullet(
              text: storyDigits(notes.bullets[i], lang),
              lang: lang,
            ),
          ),
        if (notes.sources.isNotEmpty) ...[
          const SizedBox(height: 16),
          _LmSources(sources: notes.sources, lang: lang, state: state),
        ],
      ],
    );
  }
}

/// The institutions section (v2, section 5): one entry per
/// institution — name (+ full name), one-line role, source where the
/// role is stated. Hairline-separated rows.
class _InstitutionsBody extends StatelessWidget {
  final List<LmInstitution> items;
  final String lang;

  const _InstitutionsBody({required this.items, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < items.length; i++) ...[
          if (i > 0) ...[
            const SizedBox(height: 12),
            Container(height: 1, color: hairline),
            const SizedBox(height: 12),
          ],
          Text(
            storyDigits(
              [
                items[i].name,
                if (items[i].fullName != null &&
                    items[i].fullName!.trim().isNotEmpty)
                  '(${items[i].fullName!.trim()})',
              ].join(' '),
              lang,
            ),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: ink),
          ),
          if (items[i].role != null && items[i].role!.trim().isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              storyDigits(items[i].role!, lang),
              style: AppType.storyBody.copyWith(color: ink),
            ),
          ],
          if (items[i].source != null &&
              items[i].source!.trim().isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              storyDigits(items[i].source!, lang),
              style: TextStyle(fontSize: 12, height: 1.5, color: secondary),
            ),
          ],
        ],
      ],
    );
  }
}

/// The extra-knowledge section (v2, section 6): term (+ full name),
/// one-line meaning, source. Hairline-separated rows.
class _ExtraKnowledgeBody extends StatelessWidget {
  final List<LmExtraTerm> items;
  final String lang;

  const _ExtraKnowledgeBody({required this.items, required this.lang});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < items.length; i++) ...[
          if (i > 0) ...[
            const SizedBox(height: 12),
            Container(height: 1, color: hairline),
            const SizedBox(height: 12),
          ],
          Text(
            storyDigits(
              [
                items[i].term,
                if (items[i].fullName != null &&
                    items[i].fullName!.trim().isNotEmpty)
                  '(${items[i].fullName!.trim()})',
              ].join(' '),
              lang,
            ),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: ink),
          ),
          if (items[i].meaning != null &&
              items[i].meaning!.trim().isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              storyDigits(items[i].meaning!, lang),
              style: AppType.storyBody.copyWith(color: ink),
            ),
          ],
          if (items[i].source != null &&
              items[i].source!.trim().isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              storyDigits(items[i].source!, lang),
              style: TextStyle(fontSize: 12, height: 1.5, color: secondary),
            ),
          ],
        ],
      ],
    );
  }
}

/// A GK section's own sources: the "সূত্র" label plus tappable source
/// names. Separate from the news sources — never merged with them.
class _LmSources extends StatelessWidget {
  final List<LmSource> sources;
  final String lang;
  final AppState state;

  const _LmSources({
    required this.sources,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          state.t('source'),
          style: TextStyle(
            fontSize: 13,
            height: 1.4,
            fontWeight: FontWeight.w800,
            color: secondary,
          ),
        ),
        const SizedBox(height: 4),
        for (final src in sources)
          Column(
            children: [
              InkWell(
                onTap: src.url != null
                    ? () => openExternalUrl(src.url)
                    : null,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          src.name,
                          style: const TextStyle(
                            fontSize: 14,
                            height: 1.5,
                            fontWeight: FontWeight.w700,
                          ).copyWith(color: ink),
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
          ),
      ],
    );
  }
}

/// One interactive MCQ practice card: tap an option to reveal the
/// correct answer + explanation. Correct goes green, a wrong pick goes
/// red; the other options dim. Green is the state colour for correct
/// answers (per the design system), never a brand colour.
class _LmMcqCard extends StatelessWidget {
  final LmMcq mcq;
  final int index;
  final String? selected;
  final ValueChanged<String> onSelect;
  final String lang;
  final AppState state;

  const _LmMcqCard({
    required this.mcq,
    required this.index,
    required this.selected,
    required this.onSelect,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final surface = AppColors.storySurfaceFor(brightness);
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final faint = AppColors.faintFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final success = AppColors.successFor(brightness);
    final error = AppColors.errorFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    final answered = selected != null;
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
          Text(
            storyDigits(mcq.question, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: ink),
          ),
          const SizedBox(height: 10),
          for (final key in mcq.optionKeys) ...[
            _OptionRow(
              letter: key,
              text: storyDigits(mcq.options[key] ?? '', lang),
              state: !answered
                  ? _OptionState.idle
                  : key == mcq.correct
                      ? _OptionState.correct
                      : key == selected
                          ? _OptionState.wrongPick
                          : _OptionState.dimmed,
              onTap: answered ? null : () => onSelect(key),
              ink: ink,
              secondary: secondary,
              faint: faint,
              accent: accent,
              success: success,
              error: error,
              hairline: hairline,
            ),
            const SizedBox(height: 8),
          ],
          if (!answered)
            Text(
              state.t('lmTapOption'),
              style: TextStyle(fontSize: 13, height: 1.5, color: secondary),
            )
          else ...[
            Container(height: 1, color: hairline),
            const SizedBox(height: 10),
            Text(
              selected == mcq.correct
                  ? '${state.t('correct')} ✓'
                  : '${state.t('correctAnswer')}: ${mcq.correct}',
              style: TextStyle(
                fontSize: 15,
                height: 1.5,
                fontWeight: FontWeight.w800,
                color: success,
              ),
            ),
            if (mcq.explanation != null &&
                mcq.explanation!.trim().isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                state.t('explanation'),
                style: TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  fontWeight: FontWeight.w800,
                  color: secondary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                storyDigits(mcq.explanation!, lang),
                style: TextStyle(fontSize: 15, height: 1.6, color: ink),
              ),
            ],
          ],
        ],
      ),
    );
  }
}

enum _OptionState { idle, correct, wrongPick, dimmed }

/// One MCQ option row: letter chip + option text.
class _OptionRow extends StatelessWidget {
  final String letter;
  final String text;
  final _OptionState state;
  final VoidCallback? onTap;
  final Color ink;
  final Color secondary;
  final Color faint;
  final Color accent;
  final Color success;
  final Color error;
  final Color hairline;

  const _OptionRow({
    required this.letter,
    required this.text,
    required this.state,
    required this.onTap,
    required this.ink,
    required this.secondary,
    required this.faint,
    required this.accent,
    required this.success,
    required this.error,
    required this.hairline,
  });

  @override
  Widget build(BuildContext context) {
    final border = switch (state) {
      _OptionState.correct => success,
      _OptionState.wrongPick => error,
      _ => hairline,
    };
    final letterColor = switch (state) {
      _OptionState.correct => success,
      _OptionState.wrongPick => error,
      _OptionState.dimmed => faint,
      _ => ink,
    };
    final textColor = switch (state) {
      _OptionState.correct => success,
      _OptionState.wrongPick => error,
      _OptionState.dimmed => faint,
      _ => ink,
    };
    final icon = switch (state) {
      _OptionState.correct => Icons.check,
      _OptionState.wrongPick => Icons.close,
      _ => null,
    };
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          decoration: BoxDecoration(
            border: Border.all(color: border, width: 1.5),
            borderRadius: BorderRadius.circular(8),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: border, width: 1.5),
                ),
                alignment: Alignment.center,
                child: Text(
                  letter,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: letterColor,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  text,
                  style: TextStyle(
                    fontFamily: 'HindSiliguri',
                    fontSize: 16,
                    height: 1.5,
                    fontWeight: state == _OptionState.correct
                        ? FontWeight.w700
                        : FontWeight.w400,
                    color: textColor,
                  ),
                ),
              ),
              if (icon != null) ...[
                const SizedBox(width: 8),
                Icon(icon, size: 20, color: letterColor),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// One written-prep question: type label, question, model outline.
class _WrittenItem extends StatelessWidget {
  final LmWrittenItem item;
  final String lang;
  final AppState state;

  const _WrittenItem({
    required this.item,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          item.isAnalytical
              ? state.t('lmWrittenAnalytical')
              : state.t('lmWrittenShort'),
          style: AppType.storyLabel.copyWith(color: accent),
        ),
        const SizedBox(height: 6),
        Text(
          storyDigits(item.question, lang),
          style: const TextStyle(
            fontFamily: 'HindSiliguri',
            fontSize: 16,
            height: 1.6,
            fontWeight: FontWeight.w700,
          ).copyWith(color: ink),
        ),
        if (item.outline.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            state.t('lmOutline'),
            style: TextStyle(
              fontSize: 13,
              height: 1.4,
              fontWeight: FontWeight.w800,
              color: secondary,
            ),
          ),
          const SizedBox(height: 6),
          for (var i = 0; i < item.outline.length; i++)
            Padding(
              padding: EdgeInsets.only(
                bottom: i < item.outline.length - 1 ? 10 : 0,
              ),
              child: _LmBullet(
                text: storyDigits(item.outline[i], lang),
                lang: lang,
              ),
            ),
        ],
      ],
    );
  }
}

/// One vocabulary row: English headword, Bengali meaning, example,
/// synonyms / antonyms.
class _VocabRow extends StatelessWidget {
  final LmVocab word;
  final String lang;
  final AppState state;

  const _VocabRow({
    required this.word,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          word.word,
          style: const TextStyle(
            fontSize: 17,
            height: 1.4,
            fontWeight: FontWeight.w800,
          ).copyWith(color: ink),
        ),
        if (word.banglaMeaning != null &&
            word.banglaMeaning!.trim().isNotEmpty) ...[
          const SizedBox(height: 2),
          Text(
            storyDigits(word.banglaMeaning!, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: ink),
          ),
        ],
        if (word.example != null && word.example!.trim().isNotEmpty) ...[
          const SizedBox(height: 4),
          // English example sentence, verbatim from the article — rendered
          // raw in curly quotes exactly like word_card.dart, so the
          // Phase 4 tests recognise it as English learning content.
          // (storyDigits would convert its digits and break that match.)
          Text(
            '“${word.example!.trim()}”',
            style: TextStyle(
              fontSize: 15,
              height: 1.6,
              fontStyle: FontStyle.italic,
              color: secondary,
            ),
          ),
        ],
        if (word.synonyms.isNotEmpty || word.antonyms.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            [
              if (word.synonyms.isNotEmpty)
                '${state.t('synonyms')}: ${storyDigits(word.synonyms.join('; '), lang)}',
              if (word.antonyms.isNotEmpty)
                '${state.t('antonyms')}: ${storyDigits(word.antonyms.join('; '), lang)}',
            ].join('  ·  '),
            style: TextStyle(fontSize: 14, height: 1.6, color: secondary),
          ),
        ],
      ],
    );
  }
}

/// Revision body: flashcards as Q→A rows, then the next-revision
/// questions.
class _RevisionBody extends StatelessWidget {
  final LmRevision revision;
  final String lang;
  final AppState state;

  const _RevisionBody({
    required this.revision,
    required this.lang,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink = AppColors.inkFor(brightness);
    final accent = AppColors.storyAccentFor(brightness);
    final secondary = AppColors.secondaryFor(brightness);
    final hairline = AppColors.storyHairlineFor(brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < revision.flashcards.length; i++) ...[
          if (i > 0) ...[
            const SizedBox(height: 14),
            Container(height: 1, color: hairline),
            const SizedBox(height: 14),
          ],
          Text(
            storyDigits(revision.flashcards[i].q, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: ink),
          ),
          const SizedBox(height: 4),
          Text(
            storyDigits(revision.flashcards[i].a, lang),
            style: const TextStyle(
              fontFamily: 'HindSiliguri',
              fontSize: 16,
              height: 1.6,
              fontWeight: FontWeight.w700,
            ).copyWith(color: accent),
          ),
        ],
        if (revision.nextRevision.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            state.t('nextRevision'),
            style: TextStyle(
              fontSize: 13,
              height: 1.4,
              fontWeight: FontWeight.w800,
              color: secondary,
            ),
          ),
          const SizedBox(height: 8),
          for (var i = 0; i < revision.nextRevision.length; i++)
            Padding(
              padding: EdgeInsets.only(
                bottom: i < revision.nextRevision.length - 1 ? 10 : 0,
              ),
              child: _LmBullet(
                text: storyDigits(revision.nextRevision[i], lang),
                lang: lang,
              ),
            ),
        ],
      ],
    );
  }
}
