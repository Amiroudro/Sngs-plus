/// Highlights the matching part of a search result in the brand colour.
/// Used by the search screen so the user sees WHY a result matched.
library;

import 'package:flutter/material.dart';

import 'app_theme.dart';

class HighlightText extends StatelessWidget {
  final String text;
  final String query;
  final TextStyle? style;
  final int? maxLines;

  const HighlightText({
    super.key,
    required this.text,
    required this.query,
    this.style,
    this.maxLines,
  });

  @override
  Widget build(BuildContext context) {
    final base = style ?? AppType.body;
    final q = query.trim();
    if (q.isEmpty) {
      return Text(text, style: base, maxLines: maxLines);
    }
    final lower = text.toLowerCase();
    final needle = q.toLowerCase();
    final spans = <TextSpan>[];
    var start = 0;
    var idx = lower.indexOf(needle, start);
    if (idx < 0) {
      return Text(text, style: base, maxLines: maxLines);
    }
    while (idx >= 0) {
      if (idx > start) {
        spans.add(TextSpan(text: text.substring(start, idx)));
      }
      spans.add(
        TextSpan(
          text: text.substring(idx, idx + needle.length),
          style: TextStyle(
            fontWeight: FontWeight.w800,
            color: AppColors.accentFor(
              Theme.of(context).brightness,
            ),
          ),
        ),
      );
      start = idx + needle.length;
      idx = lower.indexOf(needle, start);
    }
    if (start < text.length) {
      spans.add(TextSpan(text: text.substring(start)));
    }
    return RichText(
      text: TextSpan(style: base, children: spans),
      maxLines: maxLines,
      overflow: TextOverflow.ellipsis,
    );
  }
}
