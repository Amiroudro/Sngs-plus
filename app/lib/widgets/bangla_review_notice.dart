import 'package:flutter/material.dart';

/// Shown when a Bangla overlay is present but has not been explicitly
/// approved by an editor. The app then displays the original English
/// source rather than an unreviewed translation.
class BanglaReviewNotice extends StatelessWidget {
  const BanglaReviewNotice({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final textStyle = Theme.of(context).textTheme.bodySmall;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: colors.outlineVariant),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.translate_outlined,
            size: 18,
            color: colors.primary,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'এই সংস্করণের বাংলা অনুবাদ সম্পাদকীয় পর্যালোচনার অপেক্ষায়। '
              'আপাতত মূল ইংরেজি সংস্করণ দেখানো হচ্ছে।',
              style: textStyle,
            ),
          ),
        ],
      ),
    );
  }
}
