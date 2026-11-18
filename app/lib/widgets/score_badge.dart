/// Relevance mark for a story row / detail page.
///
/// The edition data carries NO numeric 0-100 score. `exam_relevance`
/// is a free-text label ("High", "Medium", "High — ..."). This shows
/// the level only, as plain text — no pill, no star, no tint:
/// `● উচ্চ` (pink) / `● মাধ্যমিক` (neutral) / `● কম` (faint).
/// When a story has no relevance label at all, it renders nothing.
/// The full raw label stays available as a tooltip.
library;

import 'package:flutter/material.dart';

import '../models.dart';
import '../state/app_state.dart';
import 'app_theme.dart';

class RelevanceMark extends StatelessWidget {
  final Story story;
  final AppState state;

  /// When true, append the remainder of the raw label after the level
  /// word (e.g. "High — World Bank…" -> "— World Bank…"), as on the
  /// detail page. Default false (rows show the level only).
  final bool showDetail;

  const RelevanceMark({
    super.key,
    required this.story,
    required this.state,
    this.showDetail = false,
  });

  @override
  Widget build(BuildContext context) {
    final strings = state.strings;
    final level = story.relevanceLevel;
    if (level == null) return const SizedBox.shrink();
    final label = switch (level) {
      'High' => strings['relevanceHigh'] ?? 'High',
      'Medium' => strings['relevanceMedium'] ?? 'Medium',
      _ => strings['relevanceLow'] ?? 'Low',
    };
    final brightness = Theme.of(context).brightness;
    final color = switch (level) {
      'High' => AppColors.accentFor(brightness),
      'Medium' => AppColors.secondaryFor(brightness),
      _ => AppColors.faintFor(brightness),
    };
    var text = '● $label';
    if (showDetail) {
      final raw = story.examRelevance ?? '';
      final rest = raw
          .replaceFirst(RegExp('^(High|Medium|Low)\\s*[—\\-]?\\s*'), '')
          .trim();
      if (rest.isNotEmpty) {
        text = '● $label — $rest';
      }
    }
    return Tooltip(
      message: story.examRelevance ?? label,
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }
}
