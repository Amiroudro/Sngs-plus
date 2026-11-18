/// Flashcards: the edition's words as a flip deck. Tap a card to flip
/// it (3D rotation on the single motion curve): front shows the English
/// headword + pronunciation, back shows the Bengali meaning + synonyms
/// + newspaper example. "I know it" / "I don't know" moves on and
/// counts the deck; the end screen shows the honest count.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';

class FlashcardScreen extends StatefulWidget {
  final AppState state;

  const FlashcardScreen({super.key, required this.state});

  @override
  State<FlashcardScreen> createState() => _FlashcardScreenState();
}

class _FlashcardScreenState extends State<FlashcardScreen> {
  final PageController _pages = PageController();
  int _index = 0;
  bool _flipped = false;
  int _known = 0;
  int _unknown = 0;
  bool _done = false;

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  List<VocabWord> get _words => widget.state.selectedEdition?.words ?? const [];

  void _answer(bool known) {
    setState(() {
      if (known) {
        _known++;
      } else {
        _unknown++;
      }
      if (_index >= _words.length - 1) {
        _done = true;
      } else {
        _index++;
        _flipped = false;
        _pages.nextPage(
          duration: AppMotion.standard,
          curve: AppMotion.curve,
        );
      }
    });
  }

  void _restart() {
    setState(() {
      _index = 0;
      _known = 0;
      _unknown = 0;
      _done = false;
      _flipped = false;
    });
    _pages.jumpToPage(0);
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final words = _words;
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      appBar: AppBar(
        title: Text(state.t('flashcards')),
        bottom: appBarHairline(context),
      ),
      // Bottom SafeArea: the Know / Don't-know buttons must sit above
      // the system nav bar, never half-cut under it.
      body: SafeArea(
        top: false,
        bottom: true,
        child: words.isEmpty
            ? EmptyState(
                icon: Icons.style_outlined, body: state.t('noDataForWord'))
            : _done
                ? _DoneView(
                    known: _known,
                    unknown: _unknown,
                    total: words.length,
                    state: state,
                    onRestart: _restart,
                  )
                : Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                        child: Row(
                          children: [
                            Expanded(
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: LinearProgressIndicator(
                                  value: (_index + 1) / words.length,
                                  minHeight: 6,
                                  backgroundColor: dark
                                      ? AppColors.darkHairline
                                      : AppColors.hairline,
                                  valueColor: const AlwaysStoppedAnimation(
                                    AppColors.pink,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              storyDigits(
                                  '${_index + 1} / ${words.length}',
                                  state.lang),
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: PageView.builder(
                          controller: _pages,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: words.length,
                          onPageChanged: (i) => setState(() {
                            _index = i;
                            _flipped = false;
                          }),
                          itemBuilder: (context, i) => Padding(
                            padding: const EdgeInsets.all(16),
                            child: _FlipCard(
                              word: words[i],
                              flipped: _flipped,
                              flipHint: state.t('flipHint'),
                              onTap: () => setState(() => _flipped = !_flipped),
                            ),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                        child: Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: () => _answer(false),
                                child: Text(state.t('dontKnow')),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: FilledButton(
                                onPressed: () => _answer(true),
                                child: Text(state.t('knowIt')),
                              ),
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

class _DoneView extends StatelessWidget {
  final int known;
  final int unknown;
  final int total;
  final AppState state;
  final VoidCallback onRestart;

  const _DoneView({
    required this.known,
    required this.unknown,
    required this.total,
    required this.state,
    required this.onRestart,
  });

  @override
  Widget build(BuildContext context) {
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 56,
              height: 56,
              // Quiet mark, not an oversized badge (v1.2.1 craft pass).
              color: primary,
              child: const Icon(
                Icons.check,
                size: 28,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              state.t('deckDone'),
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              storyDigits(
                  '$known / $total ${state.t('knowIt')}', state.lang),
              style: const TextStyle(fontSize: 16, height: 1.6),
            ),
            if (unknown > 0)
              Text(
                storyDigits('$unknown ${state.t('dontKnow')}', state.lang),
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.secondaryFor(
                    Theme.of(context).brightness,
                  ),
                ),
              ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: onRestart,
              child: Text(state.t('restart')),
            ),
          ],
        ),
      ),
    );
  }
}

/// A single flip card: front = headword + IPA, back = Bengali meaning +
/// synonyms + example. The flip is a true 3D rotation (perspective
/// transform) on the single motion curve — no bounce.
class _FlipCard extends StatefulWidget {
  final VocabWord word;
  final bool flipped;
  final String flipHint;
  final VoidCallback onTap;

  const _FlipCard({
    required this.word,
    required this.flipped,
    required this.flipHint,
    required this.onTap,
  });

  @override
  State<_FlipCard> createState() => _FlipCardState();
}

class _FlipCardState extends State<_FlipCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final Animation<double> _a;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: AppMotion.standard);
    _a = CurvedAnimation(parent: _c, curve: AppMotion.curve);
    if (widget.flipped) _c.value = 1.0;
  }

  @override
  void didUpdateWidget(_FlipCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.flipped != oldWidget.flipped) {
      if (widget.flipped) {
        _c.forward();
      } else {
        _c.reverse();
      }
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _a,
        builder: (context, _) {
          final value = _a.value;
          final angle = value * math.pi;
          final showBack = value >= 0.5;
          return Transform(
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.0015)
              ..rotateY(angle),
            alignment: Alignment.center,
            child: Transform(
              transform: Matrix4.identity()..rotateY(showBack ? math.pi : 0),
              alignment: Alignment.center,
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: dark ? AppColors.darkSurface : AppColors.surface,
                  borderRadius: BorderRadius.circular(AppRadii.learn),
                  border: Border.all(
                    color: dark ? AppColors.darkHairline : AppColors.hairline,
                  ),
                  boxShadow: dark ? AppShadows.learnDark : AppShadows.learn,
                ),
                child: showBack
                    ? _Back(word: widget.word)
                    : _Front(
                        word: widget.word,
                        flipHint: widget.flipHint,
                      ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _Front extends StatelessWidget {
  final VocabWord word;
  final String flipHint;

  const _Front({required this.word, required this.flipHint});

  @override
  Widget build(BuildContext context) {
    // Scrollable like _Back: at 200% text scale a long headword wraps to
    // two lines and the front would otherwise overflow the card (the
    // 11 Nov first word "prohibitive" overflowed by 51 px; the old
    // first word "gratuity" fit on one line, so the bug stayed hidden).
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
          Text(
            word.headword,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 34,
              fontWeight: FontWeight.w800,
              // Ink, not red: the headword is the content, not an
              // accent. (Red here was the templated look — v1.2.1
              // craft pass.) Matches the word-card headword.
              color: AppColors.inkFor(Theme.of(context).brightness),
            ),
          ),
          if (hasValue(word.ipa)) ...[
            const SizedBox(height: 8),
            Text(
              word.ipa!,
              style: TextStyle(
                fontSize: 16,
                color: AppColors.secondaryFor(
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ],
          if (hasValue(word.banglaPhonetic)) ...[
            const SizedBox(height: 4),
            Text(
              word.banglaPhonetic!,
              style: const TextStyle(fontSize: 16, height: 1.5),
            ),
          ],
          const SizedBox(height: 20),
          Text(
            flipHint,
            style: TextStyle(
              fontSize: 12,
              color: AppColors.faintFor(Theme.of(context).brightness),
            ),
          ),
        ],
        ),
      ),
    );
  }
}

class _Back extends StatelessWidget {
  final VocabWord word;

  const _Back({required this.word});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            word.headword,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          if (hasValue(word.banglaMeaning)) ...[
            const SizedBox(height: 8),
            Text(
              word.banglaMeaning!,
              style: const TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.w700,
                height: 1.5,
              ),
            ),
          ],
          if (word.hasSynonyms) ...[
            const SizedBox(height: 12),
            Text(
              word.synonyms.join(' ; '),
              style: const TextStyle(fontSize: 15, height: 1.6),
            ),
          ],
          if (hasValue(word.example)) ...[
            const SizedBox(height: 12),
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    width: 4,
                    color: AppColors.accentFor(
                      Theme.of(context).brightness,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '“${word.example!}”',
                      style: const TextStyle(
                        fontSize: 15,
                        fontStyle: FontStyle.italic,
                        height: 1.6,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (!hasValue(word.banglaMeaning) &&
              !word.hasSynonyms &&
              !hasValue(word.example))
            const Text('—'),
        ],
      ),
    );
  }
}
