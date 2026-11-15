/// Quiz tab: two modes for the selected edition.
/// 1. Edition quiz — the edition's own 25 MCQs, one question at a time,
///    score at the end, review with correct answers + explanations.
///    Wrong answers are saved to My Mistakes.
/// 2. Word practice — synonym / antonym / spelling / analogy questions
///    GENERATED from the edition's word data (see
///    lib/data/exam_patterns.dart). Clearly labelled as generated
///    practice, never confused with the edition MCQs.
/// The result moment is the delight: an animated score ring that counts
/// up, one verdict word, then the review.
library;

import 'package:flutter/material.dart';

import '../data/exam_patterns.dart';
import '../data/sections.dart';
import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';

class QuizScreen extends StatefulWidget {
  final AppState state;

  const QuizScreen({super.key, required this.state});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final edition = state.selectedEdition;
    if (edition == null) {
      return Center(child: Text(state.t('errorLoading')));
    }
    final practice = buildPracticeQuestions(edition);
    // Scaffold is load-bearing: without it this pushed route has no
    // Material ancestor and no background — the page renders black
    // and text falls back to Flutter's red-monospace-yellow-underline
    // error style. The AppBar also keeps the header below the
    // status bar.
    return Scaffold(
      appBar: AppBar(
        title: Text(state.t('quiz')),
        bottom: appBarHairline(context),
      ),
      body: SafeArea(
        top: false,
        bottom: true,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.screen),
          children: [
            Text(
              state.t('quizSubtitle'),
              style: TextStyle(
                fontSize: 13,
                color: AppColors.secondaryFor(
                  Theme.of(context).brightness,
                ),
              ),
            ),
            const SizedBox(height: 16),
            _ModeCard(
              icon: Icons.quiz_outlined,
              title: state.t('editionQuiz'),
              subtitle: storyDigits(
                  '${edition.mcqCount} ${state.t('mcqs')} • ${state.t('edition')}: ${formatEditionDate(edition.date, state.lang)}',
                  state.lang),
              buttonText: state.t('startQuiz'),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => _EditionQuizRunner(
                    edition: edition,
                    state: state,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            _ModeCard(
              icon: Icons.spellcheck_outlined,
              title: state.t('practiceQuiz'),
              subtitle: storyDigits(
                  '${practice.length} ${state.t('mcqs')} • ${state.t('practiceSynonym')} / ${state.t('practiceAntonym')} / ${state.t('practiceSpelling')} / ${state.t('practiceAnalogy')}',
                  state.lang),
              buttonText: state.t('startPractice'),
              note: state.t('practiceNote'),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => _PracticeQuizRunner(
                    edition: edition,
                    questions: practice,
                    state: state,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String buttonText;
  final String? note;
  final VoidCallback onTap;

  const _ModeCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.buttonText,
    this.note,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return LearnSurface(
      margin: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                // Solid red tile, same language as the Home rows and
                // date rows — not a bordered box (v1.2.1 craft pass).
                color: accent,
                child: Icon(icon, size: 24, color: Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(subtitle, style: const TextStyle(fontSize: 14, height: 1.5)),
          if (note != null) ...[
            const SizedBox(height: 6),
            Text(
              note!,
              style: TextStyle(
                fontSize: 12,
                fontStyle: FontStyle.italic,
                height: 1.5,
                color: AppColors.secondaryFor(
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ],
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: onTap,
              child: Text(buttonText),
            ),
          ),
        ],
      ),
    );
  }
}

/// One quiz question, in either mode.
class _Q {
  final String question;
  final List<String> options;
  final int correctIndex;
  final String? explanation;
  final String section;
  final int refNo; // MCQ no, or 0 for practice
  final String sourceWord;

  const _Q({
    required this.question,
    required this.options,
    required this.correctIndex,
    this.explanation,
    required this.section,
    required this.refNo,
    required this.sourceWord,
  });
}

class _QuizRunner extends StatefulWidget {
  final Edition edition;
  final List<_Q> questions;
  final String mode; // 'edition' | 'practice'
  final AppState state;

  const _QuizRunner({
    required this.edition,
    required this.questions,
    required this.mode,
    required this.state,
  });

  @override
  State<_QuizRunner> createState() => _QuizRunnerState();
}

class _QuizRunnerState extends State<_QuizRunner> {
  int _index = 0;
  int? _selected;
  final List<int?> _answers = [];
  bool _finished = false;

  @override
  void initState() {
    super.initState();
    _answers.addAll(List<int?>.filled(widget.questions.length, null));
  }

  void _next() {
    setState(() {
      _answers[_index] = _selected;
      if (_index < widget.questions.length - 1) {
        _index++;
        _selected = _answers[_index];
      } else {
        _finished = true;
        _saveResult();
      }
    });
  }

  void _saveResult() {
    final score = _score();
    final mistakes = <Mistake>[];
    for (var i = 0; i < widget.questions.length; i++) {
      final q = widget.questions[i];
      final a = _answers[i];
      if (a != q.correctIndex) {
        mistakes.add(Mistake(
          editionDate: widget.edition.date,
          mcqNo: q.refNo,
          question: q.question,
          chosen: a == null ? '' : q.options[a],
          correct: q.options[q.correctIndex],
          explanation: q.explanation,
          section: q.section,
          isPractice: widget.mode == 'practice',
        ));
      }
    }
    widget.state.addMistakes(mistakes);
    widget.state.recordQuizResult(QuizResult(
      editionDate: widget.edition.date,
      mode: widget.mode,
      score: score,
      total: widget.questions.length,
      timestamp: DateTime.now().toIso8601String(),
    ));
  }

  int _score() {
    var s = 0;
    for (var i = 0; i < widget.questions.length; i++) {
      if (_answers[i] == widget.questions[i].correctIndex) s++;
    }
    return s;
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    if (_finished) {
      return _ResultView(
        questions: widget.questions,
        answers: _answers,
        score: _score(),
        state: state,
        onRetake: () => setState(() {
          _index = 0;
          _selected = null;
          _answers.fillRange(0, _answers.length, null);
          _finished = false;
        }),
      );
    }
    final q = widget.questions[_index];
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final modeLabel = widget.mode == 'edition'
        ? state.t('editionQuiz')
        : mcqSectionName(q.section, state.lang);
    return Scaffold(
      appBar: AppBar(
        title: Text(
          storyDigits(
            '${state.t('questionOf')} ${_index + 1} / ${widget.questions.length}',
            state.lang,
          ),
        ),
        bottom: appBarHairline(context),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (_index + 1) / widget.questions.length,
                minHeight: 6,
                backgroundColor:
                    dark ? AppColors.darkHairline : AppColors.hairline,
                valueColor: AlwaysStoppedAnimation(accent),
              ),
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  modeLabel,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                    color: accent,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  q.question,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 16),
                for (var i = 0; i < q.options.length; i++)
                  _OptionRow(
                    text: q.options[i],
                    selected: _selected == i,
                    onTap: () => setState(() => _selected = i),
                  ),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _selected == null ? null : _next,
                  child: Text(
                    _index == widget.questions.length - 1
                        ? state.t('finish')
                        : state.t('next'),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// One answer option: a tappable row with a radio dot. Selected state
/// is a red border + tint fill — instant, quiet feedback.
class _OptionRow extends StatelessWidget {
  final String text;
  final bool selected;
  final VoidCallback onTap;

  const _OptionRow({
    required this.text,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadii.button),
          child: Container(
            padding: const EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 14,
            ),
            decoration: BoxDecoration(
              color: selected
                  ? AppColors.accentFor(
                      Theme.of(context).brightness,
                    ).withValues(alpha: 0.08)
                  : (dark ? AppColors.darkSurface : AppColors.surface),
              borderRadius: BorderRadius.circular(AppRadii.button),
              border: Border.all(
                color: selected
                    ? AppColors.accentFor(
                        Theme.of(context).brightness,
                      )
                    : (dark ? AppColors.darkHairline : AppColors.hairline),
                width: selected ? 1.5 : 1,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: selected
                          ? AppColors.accentFor(
                              Theme.of(context).brightness,
                            )
                          : AppColors.faintFor(
                              Theme.of(context).brightness,
                            ),
                      width: 2,
                    ),
                    color: selected
                        ? AppColors.accentFor(
                            Theme.of(context).brightness,
                          )
                        : Colors.transparent,
                  ),
                  child: selected
                      ? const Icon(
                          Icons.check,
                          size: 13,
                          color: Colors.white,
                        )
                      : null,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    text,
                    style: const TextStyle(fontSize: 15, height: 1.5),
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

/// The result moment: an animated score ring that counts up, one
/// verdict word, then the review. Retake returns to the mode list.
class _ResultView extends StatelessWidget {
  final List<_Q> questions;
  final List<int?> answers;
  final int score;
  final AppState state;
  final VoidCallback onRetake;

  const _ResultView({
    required this.questions,
    required this.answers,
    required this.score,
    required this.state,
    required this.onRetake,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = questions.isEmpty ? 0.0 : score / questions.length;
    final verdict = ratio >= 0.8
        ? state.t('verdictGreat')
        : ratio >= 0.5
            ? state.t('verdictGood')
            : state.t('verdictRetry');
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final success = AppColors.successFor(Theme.of(context).brightness);
    final ringColor = ratio >= 0.8 ? success : accent;
    return Scaffold(
      appBar: AppBar(
        title: Text(state.t('seeResults')),
        bottom: appBarHairline(context),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SizedBox(height: 8),
          Center(
            child: SizedBox(
              width: 180,
              height: 180,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 180,
                    height: 180,
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(end: ratio),
                      duration: const Duration(milliseconds: 900),
                      curve: AppMotion.curve,
                      builder: (context, value, _) => CircularProgressIndicator(
                        value: value,
                        strokeWidth: 12,
                        backgroundColor:
                            dark ? AppColors.darkHairline : AppColors.hairline,
                        valueColor: AlwaysStoppedAnimation(ringColor),
                      ),
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TweenAnimationBuilder<int>(
                        tween: IntTween(end: score),
                        duration: const Duration(milliseconds: 900),
                        curve: AppMotion.curve,
                        builder: (context, value, _) => Text(
                          storyDigits(
                              '$value / ${questions.length}', state.lang),
                          style: const TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      Text(
                        verdict,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: ringColor,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: onRetake,
                  child: Text(state.t('retake')),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(state.t('done')),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            state.t('reviewAnswers'),
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 10),
          for (var i = 0; i < questions.length; i++)
            _ReviewItem(
              q: questions[i],
              chosen: answers[i],
              state: state,
            ),
        ],
      ),
    );
  }
}

class _ReviewItem extends StatelessWidget {
  final _Q q;
  final int? chosen;
  final AppState state;

  const _ReviewItem({
    required this.q,
    required this.chosen,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final isCorrect = chosen == q.correctIndex;
    final success = AppColors.successFor(Theme.of(context).brightness);
    final error = AppColors.errorFor(Theme.of(context).brightness);
    return LearnSurface(
      margin: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isCorrect ? Icons.check_circle : Icons.cancel,
                color: isCorrect ? success : error,
              ),
              const SizedBox(width: 6),
              Text(
                isCorrect ? state.t('correct') : state.t('wrong'),
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: isCorrect ? success : error,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            q.question,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${state.t('yourAnswer')}: ${chosen == null ? state.t('notAnswered') : q.options[chosen!]}',
            style: const TextStyle(fontSize: 14, height: 1.4),
          ),
          Text(
            '${state.t('correctAnswer')}: ${q.options[q.correctIndex]}',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              height: 1.4,
            ),
          ),
          if (q.explanation != null) ...[
            const SizedBox(height: 4),
            Text(
              '${state.t('explanation')}: ${q.explanation}',
              style: TextStyle(
                fontSize: 13,
                height: 1.5,
                color: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.color
                    ?.withValues(alpha: 0.8),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _EditionQuizRunner extends StatelessWidget {
  final Edition edition;
  final AppState state;

  const _EditionQuizRunner({required this.edition, required this.state});

  @override
  Widget build(BuildContext context) {
    final lang = state.lang;
    final questions = edition.mcqs.map((m) {
      final keys = m.optionKeys;
      return _Q(
        question: m.questionIn(lang),
        options: keys.map((k) => m.optionIn(lang, k)).toList(),
        correctIndex: keys.indexOf(m.correct),
        explanation: m.explanationIn(lang),
        section: m.section,
        refNo: m.no,
        sourceWord: '',
      );
    }).toList();
    return _QuizRunner(
      edition: edition,
      questions: questions,
      mode: 'edition',
      state: state,
    );
  }
}

class _PracticeQuizRunner extends StatelessWidget {
  final Edition edition;
  final List<PracticeQuestion> questions;
  final AppState state;

  const _PracticeQuizRunner({
    required this.edition,
    required this.questions,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final qs = questions.map((p) {
      final typeLabel = switch (p.type) {
        'synonym' => state.t('practiceSynonym'),
        'antonym' => state.t('practiceAntonym'),
        'spelling' => state.t('practiceSpelling'),
        'analogy' => state.t('practiceAnalogy'),
        _ => p.type,
      };
      return _Q(
        question: p.question,
        options: p.options,
        correctIndex: p.correctIndex,
        explanation: p.explanation,
        section: typeLabel,
        refNo: 0,
        sourceWord: p.sourceWord,
      );
    }).toList();
    return _QuizRunner(
      edition: edition,
      questions: qs,
      mode: 'practice',
      state: state,
    );
  }
}
