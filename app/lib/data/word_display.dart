/// Display helpers for the Phase 3 word detail page (mockup image-7).
///
/// Pure functions over the word data — no widgets, no state — so they
/// are unit-testable. The data files are NOT edited (data fixes belong
/// to Phase 5); these helpers only normalise what the screen shows.
///
/// Capitalisation rule (one rule, every word): the English part of
/// speech is Title Case — first letter capital, rest lower — per
/// segment, joined with ' / '. The raw data mixes 'Noun', 'noun',
/// 'verb', 'Adjective', 'noun / verb', so the screen must never show
/// the raw string.
library;

import '../models.dart';
import 'strings.dart';

/// Title Case: first letter of each word capital, the rest lower.
/// 'noun' -> 'Noun'; 'SEE PRIOR ENTRY' -> 'See Prior Entry'.
String titleCase(String s) {
  return s.split(' ').map((w) {
    if (w.isEmpty) return w;
    return w[0].toUpperCase() + w.substring(1).toLowerCase();
  }).join(' ');
}

/// Splits 'Verb (past)' into ('Verb', 'past'); 'Noun' into
/// ('Noun', null). Plain index math, not a regex: the data
/// checker's paren-balance check counts brackets naively, and a
/// regex character class holding a close paren would throw it off.
(String base, String? note) _splitParen(String segment) {
  final open = segment.indexOf('(');
  if (open < 0) return (segment.trim(), null);
  final close = segment.indexOf(')', open + 1);
  if (close < 0) return (segment.trim(), null);
  return (
    segment.substring(0, open).trim(),
    segment.substring(open + 1, close).trim(),
  );
}

/// English part of speech for one '/'-segment, without its
/// parenthetical suffix. '(see prior entry)' is a data annotation,
/// not part of speech, so it is dropped; '(plural)' and '(past)'
/// describe the form, so they are kept, Title Cased.
String _segmentEn(String segment) {
  final (base, note) = _splitParen(segment);
  var out = titleCase(base);
  if (note != null) {
    final lower = note.toLowerCase();
    if (lower == 'plural' || lower == 'past') {
      out += ' (${titleCase(lower)})';
    }
    // Anything else ('see prior entry', ...) is dropped.
  }
  return out;
}

const Map<String, String> _posBn = {
  'noun': 'বিশেষ্য',
  'verb': 'ক্রিয়া',
  'adjective': 'বিশেষণ',
  'adverb': 'ক্রিয়াবিশেষণ',
  'preposition': 'অনুসর্গ',
  'pronoun': 'সর্বনাম',
  'conjunction': 'সংযোজক',
  'interjection': 'বিস্ময়সূচক',
  'article': 'নির্দেশক',
  'determiner': 'নির্ধারক',
};

const Map<String, String> _posSuffixBn = {
  'plural': 'বহুবচন',
  'past': 'অতীত',
};

/// Bengali part of speech for one '/'-segment. An unknown base word
/// falls back to its Title-Cased English form, so the row is never
/// empty or invented.
String _segmentBn(String segment) {
  final (base, note) = _splitParen(segment);
  var out = _posBn[base.toLowerCase()] ?? titleCase(base);
  if (note != null) {
    final bnNote = _posSuffixBn[note.toLowerCase()];
    if (bnNote != null) out += ' ($bnNote)';
  }
  return out;
}

/// 'noun / verb' -> 'Noun / Verb'; 'Noun' -> 'Noun';
/// 'Noun / adjective (see prior entry)' -> 'Noun / Adjective'.
/// Empty or missing input -> '' (the caller hides the row).
String normalizePosEn(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '';
  return raw
      .split('/')
      .map((s) => _segmentEn(s))
      .where((s) => s.isNotEmpty)
      .join(' / ');
}

/// 'noun / verb' -> 'বিশেষ্য / ক্রিয়া'; 'Noun' -> 'বিশেষ্য'.
String posBangla(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '';
  return raw
      .split('/')
      .map((s) => _segmentBn(s))
      .where((s) => s.isNotEmpty)
      .join(' / ');
}

/// 'বিশেষ্য' in Bengali mode, 'Noun' in English mode (mockup image-7
/// shows Bangla only in Bengali mode). Returns '' when the data has no
/// part of speech.
String posDisplay(String? raw, [String lang = 'bn']) {
  if (lang == 'en') return normalizePosEn(raw);
  return posBangla(raw);
}

/// Difficulty as a dot count (mockup: ●●●): Advanced 3,
/// Intermediate 2, Basic 1, Previously covered 1 (already learned,
/// so the lightest load). Unknown or missing -> 0.
int difficultyDots(String? difficulty) {
  return switch (difficulty?.trim()) {
    'Advanced' => 3,
    'Intermediate' => 2,
    'Basic' => 1,
    'Previously covered' => 1,
    _ => 0,
  };
}

/// The newspaper example with every case-insensitive occurrence of
/// the headword replaced by a blank, for the self-test hide toggle.
/// The headword itself is never changed — only the sentence copy.
String hideHeadwordIn(String sentence, String headword) {
  final h = headword.trim();
  if (h.isEmpty) return sentence;
  return sentence.replaceAll(
    RegExp(RegExp.escape(h), caseSensitive: false),
    '________',
  );
}

/// Source line under the newspaper sentence, e.g.
/// 'Prothom Alo English · ৭ নভেম্বর ২০২৬' (bn) /
/// 'Prothom Alo English · 7 November 2026' (en).
/// The raw publication date may carry a suffix
/// ('2026-11-05 (updated 2026-11-06)'); only the first ISO date is
/// used, always rendered as a real date, never raw. Returns null
/// when there is no publication and no date.
String? exampleSourceLine(VocabWord word, String lang) {
  final parts = <String>[];
  if (hasValue(word.sourcePublication)) parts.add(word.sourcePublication!);
  final raw = word.publicationDate ?? '';
  final m = RegExp(r'\d{4}-\d{2}-\d{2}').firstMatch(raw);
  if (m != null) {
    parts.add(storyDigits(formatEditionDate(m.group(0)!, lang), lang));
  }
  if (parts.isEmpty) return null;
  return parts.join(' · ');
}
