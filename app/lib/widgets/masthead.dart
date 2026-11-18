/// Masthead: red square logo + wordmark + tagline, dateline, counts,
/// edition switcher as a text button, search icon. 2px ink rule below.
///
/// Reusable top bar for news screens (MASTER.md §5.1). The edition
/// itself comes from [AppState.selectedEdition]; [greeting] is the
/// time-of-day greeting computed by the caller; [onEditionTap]
/// opens the edition switcher (a bottom sheet on Home).
/// The search icon navigates to [SearchScreen].
library;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../screens/search_screen.dart';
import '../state/app_state.dart';
import 'app_theme.dart';

class Masthead extends StatelessWidget {
  final AppState state;
  final String greeting;
  final VoidCallback onEditionTap;

  const Masthead({
    super.key,
    required this.state,
    required this.greeting,
    required this.onEditionTap,
  });

  @override
  Widget build(BuildContext context) {
    final edition = state.selectedEdition!;
    final lang = state.lang;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    color: primary,
                    alignment: Alignment.center,
                    child: const Text(
                      'সা',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        FittedBox(
                          alignment: Alignment.centerLeft,
                          fit: BoxFit.scaleDown,
                          child: Text(
                            state.t('appName'),
                            style: AppType.masthead,
                          ),
                        ),
                        Text(
                          state.t('appTagline'),
                          style: TextStyle(
                            fontSize: 12,
                            color: dark
                                ? AppColors.darkInkSecondary
                                : AppColors.inkSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: 48,
                    height: 48,
                    child: IconButton(
                      icon: const Icon(Icons.search),
                      tooltip: state.t('search'),
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => SearchScreen(state: state),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                formatEditionDateLong(edition.date, lang),
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 2),
              Wrap(
                spacing: 8,
                runSpacing: 2,
                children: [
                  Text(
                    greeting,
                    style: TextStyle(
                      fontSize: 13,
                      color: dark
                          ? AppColors.darkInkSecondary
                          : AppColors.inkSecondary,
                    ),
                  ),
                  Text(
                    storyDigits(
                      '${edition.storyCount} ${state.t('stories')} • '
                      '${edition.wordCount} ${state.t('words')} • '
                      '${edition.mcqCount} ${state.t('mcqs')}',
                      lang,
                    ),
                    style: TextStyle(
                      fontSize: 12,
                      color: dark ? AppColors.darkInkFaint : AppColors.inkFaint,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 16,
                runSpacing: 2,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.cloud_off_outlined, size: 14, color: accent),
                      const SizedBox(width: 4),
                      Flexible(
                        child: Text(
                          '${state.t('offline')} • ${state.t('downloaded')}',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: accent,
                          ),
                        ),
                      ),
                    ],
                  ),
                  InkWell(
                    onTap: onEditionTap,
                    child: Padding(
                      // 16px vertical: the switcher is a tap target
                      // and must clear the 44px floor (~47px total
                      // with the 13px label); 8px gave only ~31px.
                      padding: const EdgeInsets.symmetric(
                        vertical: 16,
                        horizontal: 4,
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Flexible(
                            child: Text(
                              '${state.t('edition')}: ${formatEditionDate(edition.date, lang)}',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: accent,
                              ),
                            ),
                          ),
                          Icon(
                            Icons.keyboard_arrow_down,
                            size: 18,
                            color: accent,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Container(
          height: 2,
          color: dark ? AppColors.darkInk : AppColors.ink,
        ),
      ],
    );
  }
}
