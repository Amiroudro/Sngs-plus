/// Story screen layout derivation (Phase 2, mockup image-6).
///
/// Pure Dart: turns one [Story] into the structured sections of the
/// redesigned story screen. No widgets, no invented content — every
/// string below is extracted from the edition data verbatim, or a
/// mechanical split / truncation of it. The screen renders exactly
/// what this file derives; nothing is rewritten.
///
/// Rules (from the Phase 2 brief):
/// * one-liner = first sentence of the summary, max 20 words.
/// * tiles = figures + exam_facts split on ';', max 4, no duplicates,
///   no tile whose text already appears in the one-liner or a bullet.
/// * bullets = remaining summary sentences, 2–3.
/// * why = the story's why_it_matters (first sentence), else one
///   specific sentence derived from the summary, else hidden.
/// * Q→A and cloze cards derive from the story's own tile facts only;
///   when a story cannot yield a clean pair, the section is hidden
///   rather than invented.
/// * the bar chart appears only when 3+ comparable numbers share one
///   unit in the figures.
/// * the collapsed section holds the full summary, people and sources.
library;

import '../models.dart';

/// Bengali danda — the sentence terminator in the Bengali data.
/// (NOT U+09E4 — that was the v1.2.1 bug.)
const String danda = '।';

bool _isDigit(String c) {
  final code = c.codeUnitAt(0);
  return (code >= 0x30 && code <= 0x39) ||
      (code >= 0x09E6 && code <= 0x09EF); // Bangla digits ০–৯
}

/// Bangla digits ০–৯, index = Latin digit value.
const String _banglaDigits = '০১২৩৪৫৬৭৮৯';

/// Converts Bangla digits in [text] back to Latin digits, so number
/// parsing works on the Phase 4 Bengali data ("১,৩৫০ কোটি টাকা" parses
/// as 1350) exactly as it did on the old Latin-digit data.
String _latinizeDigits(String text) {
  final out = StringBuffer();
  for (var i = 0; i < text.length; i++) {
    final code = text.codeUnitAt(i);
    if (code >= 0x09E6 && code <= 0x09EF) {
      out.write(_banglaDigits.indexOf(text[i]).toString());
    } else {
      out.write(text[i]);
    }
  }
  return out.toString();
}

/// True when [text] contains any digit, Latin or Bangla.
bool _hasDigit(String text) =>
    RegExp(r'[0-9০-৯]').hasMatch(text);

/// Digit characters for number-phrase patterns: Latin 0-9 and Bangla
/// ০-৯. Always used inside a character class: `[$_d]`, `[$_d,]`.
const String _d = '0-9০-৯';

/// Splits [text] into sentences on the Bengali danda, Latin '.', '?'
/// and '!'. A '.' between two digits (e.g. 51.62) is not a sentence
/// end. The terminator stays attached to its sentence.
List<String> splitSentences(String text) {
  final out = <String>[];
  final t = text.trim();
  var start = 0;
  for (var i = 0; i < t.length; i++) {
    final c = t[i];
    final isTerm = c == danda || c == '.' || c == '?' || c == '!';
    if (!isTerm) continue;
    if (c == '.' &&
        i > 0 &&
        i + 1 < t.length &&
        _isDigit(t[i - 1]) &&
        _isDigit(t[i + 1])) {
      continue;
    }
    final sentence = t.substring(start, i + 1).trim();
    if (sentence.isNotEmpty) out.add(sentence);
    start = i + 1;
  }
  final tail = t.substring(start).trim();
  if (tail.isNotEmpty) out.add(tail);
  return out;
}

/// First sentence of [text], or the whole text when there is no
/// terminator.
String firstSentence(String text) {
  final sentences = splitSentences(text);
  return sentences.isEmpty ? text.trim() : sentences.first;
}

/// Everything after the first sentence, or '' when there is only one.
String restOf(String text) {
  final first = firstSentence(text.trim());
  if (first.length >= text.trim().length) return '';
  return text.trim().substring(first.length).trim();
}

int wordCount(String text) =>
    text.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;

/// Truncates [text] to at most [maxWords] words, adding '…' when cut.
String capWords(String text, int maxWords) {
  final words = text.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
  if (words.length <= maxWords) return text.trim();
  return '${words.take(maxWords).join(' ')}…';
}

/// Normalised text for dedup: lowercase, punctuation and extra
/// whitespace removed. Digits are kept, so two facts that differ only
/// in their number are NOT treated as duplicates.
String normalizeFact(String text) {
  return text
      .toLowerCase()
      .replaceAll(RegExp(r'[^\p{L}\p{M}\p{N}\s]', unicode: true), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();
}

// ---------------------------------------------------------------------------
// Numbers
// ---------------------------------------------------------------------------

/// Words that may follow a number as its unit. Anything else after a
/// number stays part of the label (e.g. "177 factories shut" ->
/// value "177", label "factories shut").
const Set<String> _measureUnits = {
  'percent',
  'শতাংশ',
  'billion',
  'বিলিয়ন',
  'million',
  'মিলিয়ন',
  'thousand',
  'bn',
  'mn',
  'কোটি',
  'লাখ',
  'হাজার',
  'টাকা',
  'taka',
  'dollars',
  'dollar',
};

const List<String> _monthWords = [
  'january',
  'february',
  'march',
  'april',
  'may',
  'june',
  'july',
  'august',
  'september',
  'october',
  'november',
  'december',
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

/// A number as it appears in the data: optional currency prefix,
/// a number or a range ("2-3", "২০০–৩০০"), and an optional measure unit.
/// Digits may be Latin (English data) or Bangla (Phase 4 Bengali data).
/// A range separator may be a hyphen or an en/em dash: the Phase 4
/// converter writes Bengali ranges with '–' ("২০০–৩০০ কোটি টাকা"), and
/// the chart/tiles must still read the unit after the range.
final RegExp _numberRe = RegExp(
  '(Tk|৳|\\\$)?\\s*[$_d][$_d,]*(?:\\.[$_d]+)?(?:\\s*[-–—]\\s*[$_d][$_d,]*(?:\\.[$_d]+)?)?'
  r'(?:\s*(?:percent|শতাংশ|billion|বিলিয়ন|million|মিলিয়ন|thousand|bn|mn|কোটি|লাখ|হাজার|টাকা|taka|dollars?))?(?:\s*(?:টাকা|ডলার|taka|dollars?))?',
);

/// Digits only (a single number or a range) inside a number phrase.
final RegExp _digitsRe = RegExp(
  '[$_d][$_d,]*(?:\\.[$_d]+)?(?:\\s*[-–—]\\s*[$_d][$_d,]*(?:\\.[$_d]+)?)?',
);

/// The first usable number phrase in [text], or null. A match is
/// rejected when it is a time ("3:45pm"), part of a date ("1 November
/// 2026"), or a bare year standing alone — those are not tile values.
({String phrase, int start, int end, double value})? firstNumber(String text) {
  for (final m in _numberRe.allMatches(text)) {
    final phrase = m.group(0)!.trim();
    // A time, not a value.
    if (m.end < text.length && text[m.end] == ':') continue;
    // A date ("1 November 2026") or a bare year: not a value.
    // The month may sit before the number ("November 2026") or
    // after it ("1 November 2026").
    final after = text.substring(m.end).trimLeft();
    final nextWord =
        after.split(RegExp(r'[\s,;()]+')).firstOrNull?.toLowerCase() ?? '';
    if (_monthWords.contains(nextWord)) continue;
    final before = text.substring(0, m.start).trimRight();
    final prevWord =
        before.split(RegExp(r'[\s,;()]+')).lastOrNull?.toLowerCase() ?? '';
    if (_monthWords.contains(prevWord)) continue;
    if (RegExp(r'^[0-9০-৯]{4}$').hasMatch(phrase) && nextWord.isEmpty) continue;
    final value = _numberValue(phrase);
    if (value == null) continue;
    return (phrase: phrase, start: m.start, end: m.end, value: value);
  }
  return null;
}

/// Numeric value of a number phrase; a range ("2-3") becomes its
/// midpoint (the display keeps the original "2-3" text). Bangla digits
/// are normalised to Latin before parsing ("১,৩৫০" -> 1350).
double? _numberValue(String phrase) {
  final nums = RegExp(r'[0-9০-৯][0-9০-৯,]*(?:\.[0-9০-৯]+)?')
      .allMatches(phrase)
      .map((m) => double.tryParse(
          _latinizeDigits(m.group(0)!).replaceAll(',', '')))
      .whereType<double>()
      .toList();
  if (nums.isEmpty) return null;
  if (nums.length == 1) return nums.first;
  return (nums.first + nums.last) / 2;
}

/// Unit key for comparability: currency prefix + measure unit, both
/// lowercased (e.g. "tk|বিলিয়ন", "$|billion", "|percent"). The prefix
/// recognises the Bengali forms too: "টাকা"/"৳" is taka, "ডলার" is
/// dollars — so the Phase 4 Bengali figures group exactly like the
/// English ones did.
String? numberUnit(String phrase) {
  final lower = phrase.toLowerCase();
  var prefix = '';
  if (lower.contains('tk') ||
      lower.contains('৳') ||
      lower.contains('টাকা')) {
    prefix = 'tk';
  } else if (lower.contains('\$') || lower.contains('ডলার')) {
    prefix = '\$';
  }
  for (final unit in _measureUnits) {
    if (lower.contains(unit)) return '$prefix|$unit';
  }
  return null;
}

/// Display form of a unit key ("tk|বিলিয়ন" -> "Tk বিলিয়ন" in English,
/// "টাকা বিলিয়ন" in Bengali; "$|বিলিয়ন" -> "$ বিলিয়ন" / "ডলার বিলিয়ন").
/// The 'Tk' literal must never leak into Bengali UI (Phase 4) except
/// for the single allowlisted FactTile.original slot, which this
/// function does not render.
String unitDisplay(String unitKey, {String lang = 'en'}) {
  final parts = unitKey.split('|');
  final prefix = parts[0];
  final unit = parts.length > 1 ? parts[1] : '';
  final shown = switch (prefix) {
    'tk' => lang == 'bn' ? 'টাকা' : 'Tk',
    '\$' => lang == 'bn' ? 'ডলার' : '\$',
    _ => '',
  };
  return [shown, unit].where((s) => s.isNotEmpty).join(' ');
}

// ---------------------------------------------------------------------------
// Tiles
// ---------------------------------------------------------------------------

/// One "মনে রাখুন" fact tile. [label] is the small grey context,
/// [value] the large bold fact, [original] the tiny grey English
/// figure (Bengali mode only), [isNumeric] whether the value is a
/// number (accent-coloured) or text (ink).
class FactTile {
  final String label;
  final String value;
  final String? original;
  final bool isNumeric;

  const FactTile({
    required this.label,
    required this.value,
    this.original,
    required this.isNumeric,
  });
}

String _cleanLabel(String text) {
  var t = text
      .replaceAll(RegExp(r'^[\s,;:()\-–—]+'), '')
      .replaceAll(RegExp(r'[\s,;:()\-–—]+$'), '')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();
  return t;
}

/// Parses one fact item (a ';'-separated fragment of figures or
/// exam_facts) into a tile. Returns null when the item cannot become
/// a clean tile. [englishItem] is the same-index item from the
/// English source, used for the tiny original figure.
FactTile? parseTile(String item, String? englishItem) {
  var text = item.trim().replaceAll(RegExp(r'[।.]+$'), '').trim();
  if (text.isEmpty) return null;

  String label = '';
  String value;

  // 1. Parenthetical: "value (label)" — the period in parens.
  final paren = RegExp(r'^(.*?)\s*\(([^()]*)\)\s*$').firstMatch(text);
  if (paren != null &&
      paren.group(1)!.trim().isNotEmpty &&
      paren.group(2)!.trim().isNotEmpty) {
    value = paren.group(1)!.trim();
    label = _cleanLabel(paren.group(2)!);
  } else {
    // 2. Colon: "label: value" (short left side only).
    final colon = text.indexOf(':');
    if (colon > 0) {
      final left = text.substring(0, colon).trim();
      final right = text.substring(colon + 1).trim();
      if (wordCount(left) <= 6 && right.isNotEmpty) {
        label = left;
        value = right;
      } else {
        value = text;
      }
    } else {
      value = text;
    }
    // 3. Number: value = the number phrase, label = the rest.
    if (label.isEmpty) {
      final num = firstNumber(text);
      if (num != null) {
        value = num.phrase;
        final rest =
            '${text.substring(0, num.start)} ${text.substring(num.end)}'
                .trim();
        label = capWords(_cleanLabel(rest), 6);
        if (label.isEmpty) {
          value = text;
          label = '';
        }
      } else if (wordCount(text) <= 8) {
        value = text;
        label = '';
      } else {
        return null;
      }
    }
  }

  // Tiny original English figure (Bengali mode only): the number
  // phrase of the same-index English item, abbreviated like the
  // mockup ("Tk 13.5 bn").
  String? original;
  if (englishItem != null) {
    final enNum = firstNumber(englishItem);
    if (enNum != null) {
      original = enNum.phrase
          .replaceAll('billion', 'bn')
          .replaceAll('million', 'mn');
    }
  }

  return FactTile(
    label: label,
    value: value,
    original: original,
    isNumeric: _hasDigit(value),
  );
}

// ---------------------------------------------------------------------------
// Chart
// ---------------------------------------------------------------------------

class ChartBar {
  final String label;
  final double value;
  final String display;

  const ChartBar({
    required this.label,
    required this.value,
    required this.display,
  });
}

class ChartData {
  final String title;
  final List<ChartBar> bars;

  const ChartData({required this.title, required this.bars});
}

/// Builds the small bar chart from the figures items: 3+ comparable
/// numbers (same unit) become bars. Returns null otherwise. [lang]
/// controls the title's currency word ('Tk' in English, 'টাকা' in
/// Bengali — never 'Tk' in Bengali UI).
ChartData? buildChart(List<String> figureItems, String lang) {
  // unit key -> list of (item, number, label)
  final groups = <String, List<({String item, double value, String display, String label})>>{};
  for (final item in figureItems) {
    final tile = parseTile(item, null);
    if (tile == null) continue;
    // The chart works on the tile's value phrase, so a range keeps
    // its "2-3" display while the bar height uses the midpoint.
    final num = firstNumber(tile.value);
    if (num == null) continue;
    final unit = numberUnit(num.phrase);
    if (unit == null) continue;
    groups.putIfAbsent(unit, () => []).add((
      item: item,
      value: num.value,
      display: num.phrase,
      label: tile.label,
    ));
  }
  String? bestUnit;
  for (final entry in groups.entries) {
    if (entry.value.length < 3) continue;
    if (bestUnit == null || entry.value.length > groups[bestUnit]!.length) {
      bestUnit = entry.key;
    }
  }
  if (bestUnit == null) return null;
  final rows = groups[bestUnit]!;
  // Title: a word that appears before the number in every item
  // ("দৈনিক" in the QR figures) + the unit; otherwise the unit alone.
  String? commonWord;
  final firstWords = <String?>[];
  for (final row in rows) {
    final num = firstNumber(row.item);
    if (num == null) {
      firstWords.add(null);
      continue;
    }
    final before = row.item.substring(0, num.start).trim();
    firstWords.add(before.split(RegExp(r'\s+')).lastOrNull);
  }
  if (firstWords.every((w) => w != null && w == firstWords.first)) {
    commonWord = firstWords.first;
  }
  final title = commonWord != null
      ? '$commonWord (${unitDisplay(bestUnit, lang: lang)})'
      : unitDisplay(bestUnit, lang: lang);
  return ChartData(
    title: title,
    bars: rows
        .map(
          (r) => ChartBar(
            label: r.label.isEmpty ? r.display : r.label,
            value: r.value,
            display: r.display,
          ),
        )
        .toList(),
  );
}

// ---------------------------------------------------------------------------
// Q&A and cloze (recall tests, derived from the tile facts only)
// ---------------------------------------------------------------------------

class QaPair {
  final String question;
  final String answer;

  const QaPair({required this.question, required this.answer});
}

class ClozeCard {
  /// Sentence with '______' where the answer was blanked.
  final String text;

  /// The blanked-out value (digits only, e.g. "13.5").
  final String answer;

  const ClozeCard({required this.text, required this.answer});
}

/// Words that mark a label as a time period ("মে মাসের শেষ"). A
/// period cannot make a clean "কত?" question, so such tiles are
/// skipped for Q→A (the tile itself still shows).
const List<String> _timeWords = [
  'মাস',
  'সপ্তাহ',
  'বছর',
  'দিন',
  'ঘণ্টা',
  'সকাল',
  'বিকেল',
  'রাত',
  'week',
  'month',
  'year',
  'day',
  'morning',
  'evening',
  'night',
];

bool _isTimeLabel(String label) {
  final lower = label.toLowerCase();
  return _timeWords.any((w) => lower.contains(w)) ||
      _monthWords.any((w) => lower.contains(w));
}

/// 1–2 question → answer rows. Two sources, both mechanical:
/// (1) tiles — a numeric value asks "কত?", any other labelled value
/// asks "কী?"; (2) definition-shaped exam facts — an item whose first
/// two words name a subject that also appears in the headline or the
/// key people ("বাংলা QR কী?" -> its definition). Conservative by
/// design: a tile or item that cannot make a clean question is
/// skipped, and the section hides when nothing qualifies.
List<QaPair> buildQa(
  List<FactTile> tiles,
  Story story,
  String lang,
) {
  final out = <QaPair>[];
  final seen = <String>{};
  void add(String question, String answer) {
    if (out.length >= 2) return;
    if (answer.isEmpty || wordCount(answer) > 14) return;
    if (!seen.add(normalizeFact(question))) return;
    out.add(QaPair(question: question, answer: answer));
  }

  for (final tile in tiles) {
    if (out.length >= 2) break;
    final label = tile.label.trim();
    if (label.isEmpty || wordCount(label) > 6) continue;
    if (_hasDigit(label)) continue;
    if (_isTimeLabel(label)) continue;
    final answer = tile.value.trim();
    if (answer.isEmpty || wordCount(answer) > 10) continue;
    final question = lang == 'bn'
        ? (tile.isNumeric ? '$label কত?' : '$label কী?')
        : 'What is $label?';
    add(question, answer);
  }

  // Definition-shaped exam facts: "বাংলা QR <definition…>".
  if (out.length < 2) {
    final headlineNorm = normalizeFact(story.headlineIn(lang));
    final peopleNorm = normalizeFact(story.peopleIn(lang) ?? '');
    for (final raw in splitList(story.factsIn(lang))) {
      if (out.length >= 2) break;
      final item = raw.trim().replaceAll(RegExp(r'[।.]+$'), '').trim();
      if (item.isEmpty) continue;
      if (_hasDigit(item)) continue;
      final words = item.split(RegExp(r'\s+'));
      if (words.length < 9 || words.length > 20) continue;
      final subject = words.take(2).join(' ');
      final subjectNorm = normalizeFact(subject);
      if (!headlineNorm.contains(subjectNorm) &&
          !peopleNorm.contains(subjectNorm)) {
        continue;
      }
      final rest = words.skip(2).join(' ').trim();
      if (wordCount(rest) < 5 || wordCount(rest) > 14) continue;
      final question =
          lang == 'bn' ? '$subject কী?' : 'What is $subject?';
      add(question, rest);
    }
  }
  return out;
}

/// 2 fill-in-the-blank cards: a fact sentence with its first number
/// blanked out. The blank covers the digits only, so the currency,
/// unit and context stay visible ("দৈনিক ______ কোটি টাকা").
List<ClozeCard> buildCloze(List<String> factItems) {
  final out = <ClozeCard>[];
  for (final raw in factItems) {
    if (out.length >= 2) break;
    final item = raw.trim().replaceAll(RegExp(r'[।.]+$'), '').trim();
    if (item.isEmpty) continue;
    final num = firstNumber(item);
    if (num == null) continue;
    // Blank the digits span inside the number phrase, not the
    // currency prefix or the unit.
    final digitsMatch = _digitsRe.firstMatch(num.phrase);
    if (digitsMatch == null) continue;
    final digits = digitsMatch.group(0)!.trim();
    final blankStart = num.start + digitsMatch.start;
    final blankEnd = num.start + digitsMatch.end;
    final blanked =
        '${item.substring(0, blankStart)}______${item.substring(blankEnd)}'
            .replaceAll(RegExp(r'\s+'), ' ')
            .trim();
    if (wordCount(blanked.replaceAll('______', '')) < 4) continue;
    if (out.any((c) => normalizeFact(c.answer) == normalizeFact(digits))) {
      continue;
    }
    out.add(ClozeCard(text: blanked, answer: digits));
  }
  return out;
}

// ---------------------------------------------------------------------------
// Why it matters
// ---------------------------------------------------------------------------

const List<String> _importanceCuesBn = [
  'গুরুত্ব',
  'তাৎপর্য',
  'প্রভাব',
  'সুযোগ',
  'ঝুঁকি',
  'পরীক্ষা',
  'শিক্ষা',
];

const List<String> _importanceCuesEn = [
  'important',
  'significance',
  'impact',
  'crucial',
  'matters',
  'exam',
];

/// One sentence, specific to this story — or null (the section hides).
String? deriveWhy(
  Story story,
  String lang,
  String oneLiner,
  List<String> bullets,
) {
  final why = story.whyIn(lang)?.trim();
  if (why != null && why.isNotEmpty) {
    final first = firstSentence(why);
    // A why that merely repeats the one-liner adds nothing.
    if (normalizeFact(first) == normalizeFact(oneLiner)) return null;
    return first;
  }
  // Fall back to the last summary sentence that carries an
  // importance cue — and is not already shown as a bullet.
  final cues = lang == 'bn' ? _importanceCuesBn : _importanceCuesEn;
  final sentences = splitSentences(story.summaryIn(lang));
  for (final s in sentences.reversed) {
    final lower = s.toLowerCase();
    if (!cues.any((c) => lower.contains(c))) continue;
    if (normalizeFact(s) == normalizeFact(oneLiner)) continue;
    if (bullets.any((b) => normalizeFact(b) == normalizeFact(s))) continue;
    return s;
  }
  return null;
}

// ---------------------------------------------------------------------------
// The whole layout
// ---------------------------------------------------------------------------

class StoryLayout {
  /// First sentence of the summary, max 20 words.
  final String oneLiner;

  /// Remaining summary sentences, 2–3 short bullets.
  final List<String> bullets;

  /// One story-specific sentence, or null (section hides).
  final String? whySentence;

  /// Max 4 fact tiles, figures first.
  final List<FactTile> tiles;

  /// Bar chart when 3+ comparable numbers share a unit, else null.
  final ChartData? chart;

  /// 1–2 exam Q→A rows, or empty (section hides).
  final List<QaPair> qa;

  /// Fill-in-the-blank cards, or empty (section hides).
  final List<ClozeCard> cloze;

  /// Full summary (collapsed section).
  final String fullSummary;

  /// Key people / organisations (collapsed section).
  final List<String> people;

  /// Sources (collapsed section).
  final List<SourceRef> sources;

  const StoryLayout({
    required this.oneLiner,
    required this.bullets,
    required this.whySentence,
    required this.tiles,
    required this.chart,
    required this.qa,
    required this.cloze,
    required this.fullSummary,
    required this.people,
    required this.sources,
  });
}

/// Derives the full story-screen layout from one story's data.
/// Nothing here invents content: every string comes from the data.
/// Phase 5: when the story carries the authored fields (one_liner,
/// key_facts, what_happened, exam_qa, recall_cards, detail) those
/// are read first; every section falls back to the old mechanical
/// derivation from summary / exam_facts / figures when a field is
/// absent, so old edition files render exactly as before.
StoryLayout buildStoryLayout(Story story, String lang) {
  final summary = story.summaryIn(lang);
  final sentences = splitSentences(summary);

  // One-liner: authored first, else the first summary sentence.
  final authoredOneLiner = story.oneLinerIn(lang)?.trim();
  final oneLiner = authoredOneLiner != null && authoredOneLiner.isNotEmpty
      ? capWords(authoredOneLiner, 20)
      : (sentences.isEmpty ? '' : capWords(sentences.first, 20));

  // Bullets: authored "কী ঘটেছে" first, else remaining sentences.
  final authoredBullets = story.whatHappenedIn(lang);
  final bullets = <String>[];
  if (authoredBullets.isNotEmpty) {
    // Authored bullets restate the lead verbatim in the data (e.g.
    // bn 2026-11-17 CA01: what_happened[0] == the one-liner), so
    // skip any bullet whose normalized text equals the one-liner or
    // an earlier bullet — the mechanical branch below already dedups
    // this way (see deriveWhy). The edition data is never edited for
    // this: restating the lead is legitimate authored content.
    final oneLinerNorm = normalizeFact(oneLiner);
    for (final b in authoredBullets) {
      if (bullets.length >= 3) break;
      final trimmed = b.trim();
      if (trimmed.isEmpty) continue;
      final norm = normalizeFact(trimmed);
      if (norm == oneLinerNorm) continue;
      if (bullets.any((e) => normalizeFact(e) == norm)) continue;
      bullets.add(trimmed);
    }
  } else {
    for (final s in sentences.skip(1)) {
      if (bullets.length >= 3) break;
      if (wordCount(s) > 28) {
        final splitAt = _splitLongSentence(s);
        for (final part in splitAt) {
          if (bullets.length >= 3) break;
          if (part.trim().isNotEmpty) bullets.add(part.trim());
        }
      } else {
        bullets.add(s);
      }
    }
  }

  // Tiles: figures first, then exam facts; deduped, and never a fact
  // already stated in the one-liner or a bullet (checked as a
  // substring: a tile whose words already appear in order in the
  // shown text adds nothing).
  final figureItems = splitList(story.figuresIn(lang));
  final factItems = splitList(story.factsIn(lang));
  final figureItemsEn = splitList(story.figures);
  final factItemsEn = splitList(story.examFacts);
  final shownTexts = <String>{
    normalizeFact(oneLiner),
    for (final b in bullets) normalizeFact(b),
  };
  bool alreadyShown(String norm) =>
      norm.isEmpty || shownTexts.any((t) => t.contains(norm));
  final tiles = <FactTile>[];
  void addTile(FactTile tile) {
    final tileNorm = normalizeFact('${tile.label} ${tile.value}');
    if (alreadyShown(tileNorm)) return;
    if (tiles.any(
      (t) => normalizeFact('${t.label} ${t.value}') == tileNorm,
    )) {
      return;
    }
    shownTexts.add(tileNorm);
    tiles.add(tile);
  }

  // Authored key facts become tiles directly (max 4); the `original`
  // slot carries the fact's own English figure in Bengali mode.
  final authoredFacts = story.keyFactsIn(lang);
  final keyFactItems = <String>[];
  if (authoredFacts.isNotEmpty) {
    for (final f in authoredFacts) {
      if (tiles.length >= 4) break;
      if (f.value.trim().isEmpty) continue;
      keyFactItems.add(
        f.label.trim().isEmpty ? f.value : '${f.label}: ${f.value}',
      );
      addTile(
        FactTile(
          label: f.label,
          value: f.value,
          original: lang == 'bn' ? f.original : null,
          isNumeric: _hasDigit(f.value),
        ),
      );
    }
  } else {
    void addTiles(
      List<String> items,
      List<String> itemsEn,
    ) {
      for (var i = 0; i < items.length && tiles.length < 4; i++) {
        final item = items[i];
        if (alreadyShown(normalizeFact(item))) continue;
        final englishItem = lang == 'bn' && i < itemsEn.length
            ? itemsEn[i]
            : null;
        final tile = parseTile(item, englishItem);
        if (tile == null) continue;
        addTile(tile);
      }
    }

    addTiles(figureItems, figureItemsEn);
    addTiles(factItems, factItemsEn);
  }

  // The bar chart stays derived from the figures (old field): the
  // authored key facts are at most 4 mixed-unit facts, so they
  // rarely form a 3+ comparable group — feeding them to the chart
  // halved chart coverage (14 -> 7 stories). Figures are retained
  // in the data, so the chart is unchanged from Phase 4.
  final chart = buildChart(figureItems, lang);
  final authoredQa = story.examQaIn(lang);
  final qa = authoredQa.isNotEmpty
      ? authoredQa
          .take(2)
          .map((e) => QaPair(question: e.q, answer: e.a))
          .toList()
      : buildQa(tiles, story, lang);
  final authoredCloze = story.recallCardsIn(lang);
  final cloze = authoredCloze.isNotEmpty
      ? authoredCloze
          .take(2)
          .map((c) => ClozeCard(text: c.cloze, answer: c.answer))
          .toList()
      : buildCloze([...keyFactItems, ...figureItems, ...factItems]);
  final why = deriveWhy(story, lang, oneLiner, bullets);

  return StoryLayout(
    oneLiner: oneLiner,
    bullets: bullets,
    whySentence: why,
    tiles: tiles,
    chart: chart,
    qa: qa,
    cloze: cloze,
    fullSummary: story.detailIn(lang) ?? summary,
    people: splitList(story.peopleIn(lang)),
    sources: story.sources,
  );
}

/// Splits a long sentence at the first ';' or ',' after the 15th word,
/// so a bullet never becomes a paragraph. Words are never changed.
List<String> _splitLongSentence(String sentence) {
  final matches = RegExp(r'\S+').allMatches(sentence).toList();
  if (matches.length <= 28) return [sentence];
  final after15 = matches[15].start; // start of the 16th word
  for (var i = after15; i < sentence.length; i++) {
    if (sentence[i] == ';' || sentence[i] == ',') {
      return [
        sentence.substring(0, i + 1).trim(),
        sentence.substring(i + 1).trim(),
      ];
    }
  }
  return [sentence];
}
