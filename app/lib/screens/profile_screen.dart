/// Profile / settings tab: language toggle (Bengali default), font
/// size, light/dark theme, quiz streak + score history (computed from
/// the saved quiz history only), edition download state, the 7-day
/// tracker, GK and about — each trimmed to one short line where one
/// line is enough.
library;

import 'package:flutter/material.dart';

import '../data/loader.dart';
import '../data/strings.dart';
import '../services/edition_download_service.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';

class ProfileScreen extends StatelessWidget {
  final AppState state;

  const ProfileScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final t = state.t;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: AppColors.accentFor(
                  Theme.of(context).brightness,
                ),
                borderRadius: BorderRadius.circular(AppRadii.small),
              ),
              alignment: Alignment.center,
              child: const Text(
                'সা',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    t('appName'),
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  Text(
                    t('appTagline'),
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.secondaryFor(
                        Theme.of(context).brightness,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        LearnSectionLabel(t('settings')),
        _SettingsCard(state: state),
        const SizedBox(height: 16),
        LearnSectionLabel(t('downloadTitle')),
        _DownloadCard(state: state),
        const SizedBox(height: 16),
        _StreakCard(state: state),
        const SizedBox(height: 16),
        LearnSectionLabel(t('trackerTitle')),
        LearnSurface(
          margin: EdgeInsets.zero,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // Expanded: at large text scale the label must wrap
                  // instead of pushing the 7 tracker squares off-screen.
                  Expanded(
                    child: Text(
                      storyDigits(
                        '${t('correctEditions')}: ${state.correctConsecutive}${t('of7')}',
                        state.lang,
                      ),
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Row(
                    children: List.generate(7, (i) {
                      final done = i < state.correctConsecutive;
                      final dark =
                          Theme.of(context).brightness == Brightness.dark;
                      return Padding(
                        padding: const EdgeInsets.only(left: 3),
                        child: Container(
                          width: 18,
                          height: 18,
                          decoration: BoxDecoration(
                            color: done
                                ? AppColors.accentFor(
                                    Theme.of(context).brightness,
                                  )
                                : Colors.transparent,
                            border: done
                                ? null
                                : Border.all(
                                    color: dark
                                        ? AppColors.darkHairline
                                        : AppColors.hairline,
                                  ),
                          ),
                          child: done
                              ? const Icon(
                                  Icons.check,
                                  size: 14,
                                  color: Colors.white,
                                )
                              : null,
                        ),
                      );
                    }),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                t('trackerBody'),
                style: const TextStyle(fontSize: 13, height: 1.6),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        LearnSectionLabel(t('gkTitle')),
        LearnSurface(
          margin: EdgeInsets.zero,
          child: Text(
            t('gkBody'),
            style: const TextStyle(fontSize: 14, height: 1.6),
          ),
        ),
        const SizedBox(height: 16),
        LearnSectionLabel(t('about')),
        LearnSurface(
          margin: EdgeInsets.zero,
          child: Text(
            t('aboutBody'),
            style: const TextStyle(fontSize: 14, height: 1.6),
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }
}

/// Language, theme and font size in one settings card.
class _SettingsCard extends StatelessWidget {
  final AppState state;

  const _SettingsCard({required this.state});

  @override
  Widget build(BuildContext context) {
    final t = state.t;
    const scales = [0.9, 1.0, 1.15, 1.3];
    return LearnSurface(
      margin: EdgeInsets.zero,
      child: Column(
        children: [
          // Language row: stacked, not a ListTile with a trailing
          // SegmentedButton — at large text scale the trailing control
          // was squeezed and the 'বাংলা / English' segments clipped.
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.language),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            t('language'),
                            style: const TextStyle(fontSize: 15),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            t('languageNote'),
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
                  ],
                ),
                const SizedBox(height: 10),
                Padding(
                  padding: const EdgeInsets.only(left: 40),
                  child: SegmentedButton<String>(
                    style: SegmentedButton.styleFrom(
                      // Explicit colours in BOTH states. The unselected
                      // foreground was left null before, so the segment
                      // label resolved to no colour at all.
                      foregroundColor:
                          Theme.of(context).brightness == Brightness.dark
                              ? AppColors.darkInk
                              : AppColors.ink,
                      backgroundColor: Colors.transparent,
                      selectedBackgroundColor:
                          Theme.of(context).brightness == Brightness.dark
                              ? AppColors.darkInk
                              : AppColors.ink,
                      selectedForegroundColor:
                          Theme.of(context).brightness == Brightness.dark
                              ? AppColors.darkPaper
                              : Colors.white,
                      side: BorderSide(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? AppColors.darkHairline
                            : AppColors.hairline,
                      ),
                    ),
                    segments: const [
                      ButtonSegment(value: 'bn', label: Text('বাংলা')),
                      ButtonSegment(value: 'en', label: Text('English')),
                    ],
                    selected: {state.lang},
                    onSelectionChanged: (sel) => state.setLang(sel.first),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Material(
            color: Colors.transparent,
            child: SwitchListTile(
              contentPadding: EdgeInsets.zero,
              secondary: const Icon(Icons.dark_mode),
              title: Text(t('darkMode')),
              value: state.darkMode,
              onChanged: (v) => state.setDarkMode(v),
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.format_size),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('fontSize'),
                        style: const TextStyle(fontSize: 15),
                      ),
                      const SizedBox(height: 8),
                      // Custom toggle buttons, not ChoiceChip: the chip
                      // resolved its unselected label to NO colour at
                      // all (null), so the font-size labels were
                      // invisible in light mode. Every state here has
                      // an explicit text and background colour, in
                      // both light and dark mode.
                      Row(
                        children: scales.map((s) {
                          final label = switch (s) {
                            0.9 => t('fontSmall'),
                            1.0 => t('fontNormal'),
                            1.15 => t('fontLarge'),
                            _ => t('fontXLarge'),
                          };
                          return Expanded(
                            child: Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: _FontSizeButton(
                                label: label,
                                selected: state.fontScale == s,
                                onTap: () => state.setFontScale(s),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Font-size toggle button. Replaces ChoiceChip (see above): every state
/// has an explicit label colour and background colour, in light and dark
/// mode, at a 48dp touch target.
class _FontSizeButton extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _FontSizeButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final ink = dark ? AppColors.darkInk : AppColors.ink;
    final onInk = dark ? AppColors.darkPaper : Colors.white;
    return Material(
      color: selected ? ink : Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: selected
              ? ink
              : (dark ? AppColors.darkHairline : AppColors.hairline),
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: SizedBox(
          height: 48,
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: selected ? onInk : ink,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Quiz streak + score history, computed from the saved quiz history.
/// Streak = consecutive days with at least one quiz. Empty when no quiz
/// has been taken yet — the card then shows the one-line empty state.
class _StreakCard extends StatelessWidget {
  final AppState state;

  const _StreakCard({required this.state});

  @override
  Widget build(BuildContext context) {
    final t = state.t;
    final streak = state.quizStreakDays;
    final best = state.bestResult;
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
                color: AppColors.accentFor(
                  Theme.of(context).brightness,
                ),
                child: const Icon(
                  Icons.local_fire_department,
                  size: 26,
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t('streak'),
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      storyDigits('$streak ${t('days')}', state.lang),
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                        color: AppColors.accentFor(
                          Theme.of(context).brightness,
                        ),
                        height: 1.2,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (state.totalQuizzes > 0) ...[
            const SizedBox(height: 14),
            Row(
              children: [
                _Stat(
                  label: t('bestScore'),
                  value: best == null
                      ? '—'
                      : storyDigits(
                          '${best.score} / ${best.total}', state.lang),
                ),
                _Stat(
                  label: t('avgScore'),
                  value: storyDigits(
                      '${state.averagePercent}%', state.lang),
                ),
                _Stat(
                  label: t('totalQuizzes'),
                  value: storyDigits(
                      '${state.totalQuizzes}', state.lang),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1),
            for (final r in state.quizHistory.take(5))
              Column(
                children: [
                  const SizedBox(height: 10),
                  Container(
                    height: 1,
                    color: Theme.of(context).brightness == Brightness.dark
                        ? AppColors.darkHairline
                        : AppColors.hairline,
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${r.mode == 'practice' ? t('practiceQuiz') : t('editionQuiz')} — ${formatEditionDate(r.editionDate, state.lang)}',
                          style: const TextStyle(fontSize: 14),
                        ),
                      ),
                      Text(
                        storyDigits(
                            '${r.score} / ${r.total}', state.lang),
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
          ] else ...[
            const SizedBox(height: 8),
            Text(
              t('noHistory'),
              style: TextStyle(
                fontSize: 14,
                color: AppColors.secondaryFor(
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;

  const _Stat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w800,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: AppColors.secondaryFor(
                Theme.of(context).brightness,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Phase 5: new-edition downloads. The index.json URL defaults to
/// Rudro's public GitHub Pages host (see
/// [EditionDownloadService.defaultIndexUrl]) and is shown in the
/// field; a URL saved here overrides it, and clearing the field
/// restores the default. The "check" button downloads any newer
/// edition (validated first, bundled editions always the fallback).
/// Every text has an explicit colour in both themes, and the hint
/// is Bengali — no Latin text renders here while the default URL
/// is in use beyond the URL itself.
class _DownloadCard extends StatefulWidget {
  final AppState state;

  const _DownloadCard({required this.state});

  @override
  State<_DownloadCard> createState() => _DownloadCardState();
}

class _DownloadCardState extends State<_DownloadCard> {
  final _controller = TextEditingController();
  String _statusKey = 'downloadNotSet';
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _loadUrl() async {
    final stored = await EditionDownloadService.getStoredIndexUrl();
    final url = await EditionDownloadService.getEffectiveIndexUrl();
    if (!mounted) return;
    // The field always shows the EFFECTIVE URL — the default Pages
    // URL when nothing is stored — so Rudro can see it and change it.
    _controller.text = url;
    setState(() {
      _statusKey = stored.isEmpty ? 'downloadDefault' : 'downloadSet';
    });
  }

  Future<void> _save() async {
    final url = _controller.text.trim();
    await EditionDownloadService.setStoredIndexUrl(url);
    if (!mounted) return;
    // Clearing the field restores the default: show it again.
    if (url.isEmpty) {
      _controller.text =
          await EditionDownloadService.getEffectiveIndexUrl();
    }
    setState(() {
      _statusKey = url.isEmpty ? 'downloadDefault' : 'downloadSaved';
    });
  }

  Future<void> _check() async {
    if (_checking) return;
    setState(() {
      _checking = true;
      _statusKey = 'downloadChecking';
    });
    final result = await refreshEditions(widget.state);
    if (!mounted) return;
    setState(() {
      _checking = false;
      if (result.notConfigured) {
        _statusKey = 'downloadNotSet';
      } else if (result.error != null) {
        _statusKey = 'downloadFailed';
      } else if (result.downloaded.isNotEmpty) {
        _statusKey = 'downloadFound';
      } else {
        _statusKey = 'downloadNone';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = widget.state.t;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final ink = dark ? AppColors.darkInk : AppColors.ink;
    final secondary = AppColors.secondaryFor(
      Theme.of(context).brightness,
    );
    return LearnSurface(
      margin: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            t('downloadHint'),
            style: TextStyle(fontSize: 13, height: 1.6, color: secondary),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            key: const ValueKey('download-url-field'),
            keyboardType: TextInputType.url,
            style: TextStyle(fontSize: 14, color: ink),
            decoration: InputDecoration(
              labelText: t('downloadUrlLabel'),
              labelStyle: TextStyle(color: secondary),
              hintText: t('downloadUrlLabel'),
              hintStyle: TextStyle(color: secondary),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: _save,
                  child: Text(t('downloadSave')),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: _checking ? null : _check,
                  child: Text(t('downloadCheck')),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(
                _statusKey == 'downloadFound'
                    ? Icons.check_circle
                    : _statusKey == 'downloadFailed'
                        ? Icons.cloud_off
                        : Icons.cloud_download_outlined,
                size: 18,
                color: secondary,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  t(_statusKey),
                  style: TextStyle(fontSize: 13, height: 1.5, color: ink),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
