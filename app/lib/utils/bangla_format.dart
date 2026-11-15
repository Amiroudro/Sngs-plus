/// Phase 4 (Authentic Bengali) formatting + detection utilities.
///
/// Pure Dart — no Flutter imports — so the standalone validator script
/// (`tools/validate_bangla.dart`) can reuse this exact logic, and the
/// applying subagent can reuse it when converting the edition data.
///
/// What "authentic Bengali" means here:
/// * Latin digits 0–9 become Bangla digits ০–৯ (commas kept).
/// * Dates use Bangla month names with Bangla digits:
///   "৭ নভেম্বর ২০২৬", "শনিবার, ৭ নভেম্বর ২০২৬".
/// * Money uses কোটি (crore) / লাখ (lakh) / টাকা, never "Tk",
///   "billion" or "million" — except the single allowlisted slot:
///   the small grey original figure under fact tiles, which is
///   generated at runtime from the English source
///   (`lib/data/story_layout.dart`, `parseTile` -> `FactTile.original`)
///   and deliberately stays Latin ("Tk 13.5 bn", mockup image-6).
/// * No hyphenated Bangla endings on English words ("QR-এর",
///   "November-এর"), and no "$… মিলিয়ন/বিলিয়ন" figures.
///
/// NOTE on weekdays: 7 November 2026 is a Saturday (শনিবার), verified
/// against the real calendar — not Friday. Any brief or comment that
/// says otherwise is wrong; this file derives the weekday from the
/// date itself and never hard-codes one.
library;

/// Bangla digits ০–৯, index = Latin digit value.
const String _banglaDigits = '০১২৩৪৫৬৭৮৯';

/// Bangla month names, index 0 = January.
const List<String> banglaMonths = [
  'জানুয়ারি',
  'ফেব্রুয়ারি',
  'মার্চ',
  'এপ্রিল',
  'মে',
  'জুন',
  'জুলাই',
  'আগস্ট',
  'সেপ্টেম্বর',
  'অক্টোবর',
  'নভেম্বর',
  'ডিসেম্বর',
];

/// Bangla weekday names indexed by [DateTime.weekday] - 1
/// (Monday = 1 … Sunday = 7).
const List<String> banglaWeekdays = [
  'সোমবার',
  'মঙ্গলবার',
  'বুধবার',
  'বৃহস্পতিবার',
  'শুক্রবার',
  'শনিবার',
  'রবিবার',
];

/// Converts Latin digits 0–9 in [text] to Bangla digits ০–৯.
/// Everything else passes through untouched, so commas, decimal
/// points and mixed text are kept: `toBanglaDigits('1,350')` is
/// `'১,৩৫০'`, `toBanglaDigits('Tk 13.5 bn')` is `'Tk ১৩.৫ bn'`.
String toBanglaDigits(String text) {
  final out = StringBuffer();
  for (var i = 0; i < text.length; i++) {
    final code = text.codeUnitAt(i);
    if (code >= 0x30 && code <= 0x39) {
      out.write(_banglaDigits[code - 0x30]);
    } else {
      out.write(text[i]);
    }
  }
  return out.toString();
}

DateTime _asDateTime(Object date) {
  if (date is DateTime) return date;
  if (date is String) {
    final parsed = DateTime.tryParse(date);
    if (parsed != null) return parsed;
  }
  throw ArgumentError.value(
    date,
    'date',
    'Expected a DateTime or an ISO "YYYY-MM-DD" string.',
  );
}

/// Formats [date] (a [DateTime] or an ISO `"YYYY-MM-DD"` string) as
/// `"৭ নভেম্বর ২০২৬"` — Bangla day digits, Bangla month name, Bangla
/// year digits.
String formatBanglaDate(Object date) {
  final dt = _asDateTime(date);
  return '${toBanglaDigits(dt.day.toString())} '
      '${banglaMonths[dt.month - 1]} '
      '${toBanglaDigits(dt.year.toString())}';
}

/// Formats [date] (a [DateTime] or an ISO `"YYYY-MM-DD"` string) as
/// `"শনিবার, ৭ নভেম্বর ২০২৬"` — weekday derived from the date itself.
/// 7 November 2026 is a Saturday, so that date renders শনিবার.
String formatBanglaDateWithWeekday(Object date) {
  final dt = _asDateTime(date);
  return '${banglaWeekdays[dt.weekday - 1]}, ${formatBanglaDate(dt)}';
}

// ---------------------------------------------------------------------------
// Money (BDT only)
// ---------------------------------------------------------------------------

const double _oneLakh = 100000;
const double _oneCrore = 10000000;

/// Groups the integer part of a plain number string with Western
/// thousands separators: `'1350'` -> `'1,350'`, `'99999'` -> `'99,999'`.
String _groupWestern(String integerPart) {
  final digits = integerPart;
  if (digits.length <= 3) return digits;
  final out = StringBuffer();
  var first = digits.length % 3;
  if (first == 0) first = 3;
  out.write(digits.substring(0, first));
  for (var i = first; i < digits.length; i += 3) {
    out.write(',');
    out.write(digits.substring(i, i + 3));
  }
  return out.toString();
}

/// Formats a non-negative number with at most 2 decimals (trailing
/// zeros trimmed), Western comma grouping on the integer part, and
/// Bangla digits: `1350` -> `'১,৩৫০'`, `42.5` -> `'৪২.৫'`,
/// `1121.49` -> `'১,১২১.৪৯'`.
String _formatBanglaNumber(double value) {
  var text = value.toStringAsFixed(2);
  if (text.contains('.')) {
    text = text.replaceAll(RegExp(r'0+$'), '').replaceAll(RegExp(r'\.$'), '');
  }
  final parts = text.split('.');
  final grouped = _groupWestern(parts[0]);
  final withDecimals =
      parts.length > 1 ? '$grouped.${parts[1]}' : grouped;
  return toBanglaDigits(withDecimals);
}

String _formatScaled(double scaled, String unit) =>
    '${_formatBanglaNumber(scaled)} $unit';

/// True when [original] looks like a foreign-currency figure rather
/// than a taka figure: it mentions $, USD, billion/million (or bn/mn)
/// and does NOT mention Tk / ৳ / টাকা / কোটি / লাখ.
bool _looksForeign(String original) {
  final hasForeignMarker = original.contains('\$') ||
      original.contains('USD') ||
      RegExp(r'\b(?:billion|million|bn|mn)\b', caseSensitive: false)
          .hasMatch(original);
  if (!hasForeignMarker) return false;
  final hasTakaMarker = original.contains('Tk') ||
      original.contains('৳') ||
      original.contains('টাকা') ||
      original.contains('কোটি') ||
      original.contains('লাখ');
  return !hasTakaMarker;
}

/// Formats a BDT [amount] in authentic Bengali:
/// * >= 1 crore (10^7): `"১,৩৫০ কোটি টাকা"` for 13,500,000,000.
/// * >= 1 lakh (10^5): `"৪২.৫ লাখ টাকা"` for 4,250,000.
/// * below: `"৩০০ টাকা"` for 300, `"৯৯,৯৯৯ টাকা"` for 99999.
///
/// [original] is the English figure the amount came from, kept by the
/// caller for the small grey "original" slot under fact tiles. It is
/// NOT converted here: when it describes a foreign-currency amount
/// (e.g. `r'$13.5 billion'`), the amount must not be read as taka, so
/// [original] is returned unchanged. A taka original (e.g.
/// `'Tk 13.5 bn'`) is ignored and the BDT amount is formatted.
String formatMoney(num amount, {String? original}) {
  if (original != null && _looksForeign(original)) return original;
  final value = amount.toDouble();
  if (value < 0) return '-${formatMoney(-value)}';
  if (value >= _oneCrore) {
    return _formatScaled(value / _oneCrore, 'কোটি টাকা');
  }
  if (value >= _oneLakh) {
    return _formatScaled(value / _oneLakh, 'লাখ টাকা');
  }
  return '${_formatBanglaNumber(value)} টাকা';
}

// ---------------------------------------------------------------------------
// Detectors — what the validator flags in Bengali text
// ---------------------------------------------------------------------------

/// A single violation found in Bengali text: its [kind], the exact
/// [match], and its character span [start]/[end] inside the scanned
/// string (so the validator can suppress allowlisted spans exactly).
class BanglaViolation {
  final BanglaViolationKind kind;
  final String match;
  final int start;
  final int end;

  const BanglaViolation({
    required this.kind,
    required this.match,
    required this.start,
    required this.end,
  });

  @override
  String toString() => '${kind.name}: "$match" @$start..$end';
}

/// Kinds of non-authentic-Bengali content the validator flags.
enum BanglaViolationKind {
  /// Latin digits 0–9 (should be ০–৯).
  latinDigits,

  /// English month name, full or abbreviated.
  englishMonth,

  /// The literal `Tk` (should be টাকা / কোটি টাকা / লাখ টাকা,
  /// except the one allowlisted runtime slot).
  tk,

  /// A Latin word with a hyphenated Bangla ending (`QR-এর`,
  /// `November-এর`), or a `$… মিলিয়ন/বিলিয়ন` figure.
  hyphenSuffix,
}

/// Latin digit runs: `2`, `13.5`, `1,350`, `1,121.49`.
final RegExp _latinDigitRe = RegExp(r'\d[\d,]*(?:\.\d+)?');

/// English month names, full and abbreviated, matched
/// case-insensitively — except `May`, `March` and `Mar`, which are only
/// matched with a capital first letter: lowercase they are ordinary
/// verbs, not months.
final RegExp _englishMonthRe = RegExp(
  r'\b(?:January|February|April|June|July|August|September|October|'
  r'November|December|Jan|Feb|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b',
  caseSensitive: false,
);

/// `May` / `March` / `Mar` only with a capital first letter (see above).
final RegExp _englishMonthAmbiguousRe = RegExp(r'\b(?:May|March|Mar)\b');

Iterable<RegExpMatch> _englishMonthMatches(String text) =>
    _englishMonthRe.allMatches(text).followedBy(
      _englishMonthAmbiguousRe.allMatches(text),
    );

/// The literal `Tk`, not followed by another Latin letter, so
/// `Tk 13.5 bn` and `Tk200 কোটি` match but nothing else does.
/// (The Bengali taka sign ৳ is authentic and never matches.)
final RegExp _tkRe = RegExp(r'Tk(?![A-Za-z])');

/// Bangla suffixes that must never hang off a Latin word with a hyphen.
const List<String> _banglaSuffixes = [
  'এর',
  'গুলোর',
  'গুলো',
  'দের',
  'সহ',
  'থেকে',
  'জন্য',
  'মধ্যে',
  'দিয়ে',
  'পর',
  'আগে',
  'কে',
  'তে',
  'য়',
  'টি',
  'টা',
  'এ',
  'র',
];

final RegExp _hyphenSuffixRe = RegExp(
  "[A-Za-z][A-Za-z0-9./]*[-–](?:${_banglaSuffixes.join('|')})"
  r'(?![\u0980-\u09FF])',
);

/// A dollar figure kept in Latin form with a Bengali unit:
/// `$300 মিলিয়ন`, `US$113.44 বিলিয়ন`, `US$28.2–31.7 বিলিয়ন`
/// (ranges included — they occur in the data). (The digits are also
/// flagged as [BanglaViolationKind.latinDigits]; this kind names the
/// figure.)
final RegExp _dollarFigureRe = RegExp(
  r'(?:US)?\$\s*\d[\d,]*(?:\.\d+)?'
  r'(?:\s*[-–]\s*\d[\d,]*(?:\.\d+)?)?'
  r'\s*(?:মিলিয়ন|বিলিয়ন|কোটি|লাখ)',
);

/// All violations in [text], sorted by position. Overlapping matches
/// of different kinds are kept as separate violations (e.g.
/// `November-এর` is both an English month and a hyphen-suffix).
List<BanglaViolation> findBanglaViolations(String text) {
  final out = <BanglaViolation>[];
  void add(RegExp re, BanglaViolationKind kind) {
    for (final m in re.allMatches(text)) {
      out.add(BanglaViolation(
        kind: kind,
        match: m.group(0)!,
        start: m.start,
        end: m.end,
      ));
    }
  }

  add(_latinDigitRe, BanglaViolationKind.latinDigits);
  for (final m in _englishMonthMatches(text)) {
    out.add(BanglaViolation(
      kind: BanglaViolationKind.englishMonth,
      match: m.group(0)!,
      start: m.start,
      end: m.end,
    ));
  }
  add(_tkRe, BanglaViolationKind.tk);
  add(_hyphenSuffixRe, BanglaViolationKind.hyphenSuffix);
  add(_dollarFigureRe, BanglaViolationKind.hyphenSuffix);
  out.sort((a, b) {
    final byStart = a.start.compareTo(b.start);
    if (byStart != 0) return byStart;
    return a.kind.index.compareTo(b.kind.index);
  });
  return out;
}

/// True when [text] contains any Latin digit 0–9.
bool containsLatinDigits(String text) => _latinDigitRe.hasMatch(text);

/// True when [text] contains an English month name (January..December,
/// or Jan..Dec). Lowercase `may` / `march` / `mar` do not count (verbs).
bool containsEnglishMonth(String text) =>
    _englishMonthMatches(text).isNotEmpty;

/// True when [text] contains the literal `Tk` — including the one
/// allowlisted slot, `Tk 13.5 bn`, so the validator can allowlist
/// exactly that occurrence rather than the detector missing it.
bool containsTk(String text) => _tkRe.hasMatch(text);

/// True when [text] contains a Latin word with a hyphenated Bangla
/// ending (`QR-এর`, `November-এর`) or a `$… মিলিয়ন/বিলিয়ন` figure.
bool containsHyphenSuffix(String text) =>
    _hyphenSuffixRe.hasMatch(text) || _dollarFigureRe.hasMatch(text);

/// True when [text] has any violation (see [findBanglaViolations]).
bool hasBanglaViolation(String text) => findBanglaViolations(text).isNotEmpty;

/// The matched Latin digit runs in [text] (e.g. `['2', '13.5']`).
List<String> findLatinDigitRuns(String text) =>
    _latinDigitRe.allMatches(text).map((m) => m.group(0)!).toList();

/// The matched English month names in [text].
List<String> findEnglishMonths(String text) =>
    _englishMonthMatches(text).map((m) => m.group(0)!).toList();

/// The matched `Tk` occurrences in [text].
List<String> findTkOccurrences(String text) =>
    _tkRe.allMatches(text).map((m) => m.group(0)!).toList();

/// The matched hyphen-suffix / dollar-figure occurrences in [text].
List<String> findHyphenSuffixMatches(String text) => [
      ..._hyphenSuffixRe.allMatches(text).map((m) => m.group(0)!),
      ..._dollarFigureRe.allMatches(text).map((m) => m.group(0)!),
    ];
