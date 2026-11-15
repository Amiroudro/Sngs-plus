/// Unit tests for the Phase 4 Bangla formatting utility.
/// Pure-Dart checks only (no widgets, no assets) — run with
/// `flutter test test/bangla_format_test.dart`.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/utils/bangla_format.dart';

void main() {
  group('toBanglaDigits', () {
    test('converts every Latin digit', () {
      expect(toBanglaDigits('0123456789'), '০১২৩৪৫৬৭৮৯');
    });

    test('converts digits inside mixed text, keeps the rest', () {
      expect(toBanglaDigits('Tk 13.5 bn'), 'Tk ১৩.৫ bn');
      expect(toBanglaDigits('2 December 2026'), '২ December ২০২৬');
      expect(toBanglaDigits('৩ / ১৪'), '৩ / ১৪');
    });

    test('keeps Western comma grouping', () {
      expect(toBanglaDigits('1,350'), '১,৩৫০');
      expect(toBanglaDigits('99,999'), '৯৯,৯৯৯');
      expect(toBanglaDigits('1,121.49'), '১,১২১.৪৯');
    });

    test('empty and digit-free text pass through', () {
      expect(toBanglaDigits(''), '');
      expect(toBanglaDigits('নভেম্বর'), 'নভেম্বর');
    });
  });

  group('formatBanglaDate', () {
    test('all 12 months', () {
      const expected = [
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
      for (var m = 1; m <= 12; m++) {
        expect(
          formatBanglaDate(DateTime(2026, m, 15)),
          '১৫ ${expected[m - 1]} ২০২৬',
        );
      }
    });

    test('ISO string and DateTime agree; day and year are Bangla digits',
        () {
      expect(formatBanglaDate('2026-11-07'), '৭ নভেম্বর ২০২৬');
      expect(formatBanglaDate(DateTime(2026, 11, 7)), '৭ নভেম্বর ২০২৬');
      expect(formatBanglaDate('2026-01-01'), '১ জানুয়ারি ২০২৬');
      expect(formatBanglaDate('2026-12-31'), '৩১ ডিসেম্বর ২০২৬');
    });

    test('invalid input throws ArgumentError', () {
      expect(() => formatBanglaDate('not a date'), throwsArgumentError);
      expect(() => formatBanglaDate(20261107), throwsArgumentError);
    });
  });

  group('formatBanglaDateWithWeekday', () {
    test('all 7 weekdays (1–7 Nov 2026 = Sun–Sat)', () {
      // Weekdays verified against the real calendar: 1 Nov 2026 is a
      // Sunday, so 7 Nov 2026 is a Saturday — NOT Friday. (An early
      // brief said "শুক্রবার, ৭ নভেম্বর ২০২৬"; that weekday was wrong.)
      const expected = [
        'রবিবার, ১ নভেম্বর ২০২৬',
        'সোমবার, ২ নভেম্বর ২০২৬',
        'মঙ্গলবার, ৩ নভেম্বর ২০২৬',
        'বুধবার, ৪ নভেম্বর ২০২৬',
        'বৃহস্পতিবার, ৫ নভেম্বর ২০২৬',
        'শুক্রবার, ৬ নভেম্বর ২০২৬',
        'শনিবার, ৭ নভেম্বর ২০২৬',
      ];
      for (var d = 1; d <= 7; d++) {
        expect(
          formatBanglaDateWithWeekday('2026-11-0$d'),
          expected[d - 1],
        );
      }
    });

    test('accepts a DateTime too', () {
      expect(
        formatBanglaDateWithWeekday(DateTime(2026, 11, 8)),
        'রবিবার, ৮ নভেম্বর ২০২৬',
      );
    });
  });

  group('formatMoney', () {
    test('below 1 lakh: plain টাকা', () {
      expect(formatMoney(300), '৩০০ টাকা');
      expect(formatMoney(99999), '৯৯,৯৯৯ টাকা');
      expect(formatMoney(0), '০ টাকা');
    });

    test('1 lakh threshold: লাখ', () {
      expect(formatMoney(100000), '১ লাখ টাকা');
      expect(formatMoney(4250000), '৪২.৫ লাখ টাকা');
      expect(formatMoney(250000), '২.৫ লাখ টাকা');
    });

    test('1 crore threshold: কোটি', () {
      expect(formatMoney(10000000), '১ কোটি টাকা');
      expect(formatMoney(13500000000), '১,৩৫০ কোটি টাকা');
      expect(formatMoney(11214900000), '১,১২১.৪৯ কোটি টাকা');
    });

    test('decimals are trimmed, not padded', () {
      expect(formatMoney(1000000), '১০ লাখ টাকা');
      expect(formatMoney(1500000), '১৫ লাখ টাকা');
      expect(formatMoney(105000), '১.০৫ লাখ টাকা');
    });

    test('accepts int and double', () {
      expect(formatMoney(300.0), '৩০০ টাকা');
      expect(formatMoney(42.5), '৪২.৫ টাকা');
    });

    test('a foreign-currency original is NOT converted', () {
      // 13.5 billion USD must never become "১,৩৫০ কোটি টাকা".
      expect(
        formatMoney(13500000000, original: r'$13.5 billion'),
        r'$13.5 billion',
      );
      expect(
        formatMoney(300000000, original: r'$300 million'),
        r'$300 million',
      );
    });

    test('a taka original is ignored and the BDT amount is formatted',
        () {
      expect(
        formatMoney(13500000000, original: 'Tk 13.5 bn'),
        '১,৩৫০ কোটি টাকা',
      );
    });
  });

  group('containsLatinDigits', () {
    test('positive and negative cases', () {
      expect(containsLatinDigits('১২৩'), isFalse);
      expect(containsLatinDigits('abc'), isFalse);
      expect(containsLatinDigits('abc123'), isTrue);
      expect(containsLatinDigits('১২3'), isTrue);
      expect(containsLatinDigits('2 December'), isTrue);
    });
  });

  group('containsEnglishMonth', () {
    test('full names and abbreviations', () {
      for (final month in [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Sept',
        'Oct',
        'Nov',
        'Dec',
      ]) {
        expect(containsEnglishMonth('7 $month 2026'), isTrue,
            reason: month);
      }
    });

    test('negative cases', () {
      expect(containsEnglishMonth('৭ নভেম্বর ২০২৬'), isFalse);
      expect(containsEnglishMonth('নভেম্বর'), isFalse);
      // Lowercase may/march are verbs, not months.
      expect(containsEnglishMonth('it may stay vacant'), isFalse);
      expect(containsEnglishMonth('soldiers march on'), isFalse);
      // ...but capitalised May/March are months.
      expect(containsEnglishMonth('May 2026'), isTrue);
      expect(containsEnglishMonth('March 2026'), isTrue);
      expect(containsEnglishMonth('maybe'), isFalse);
    });
  });

  group('containsTk', () {
    test('positive cases — including the one allowlisted slot', () {
      // "Tk 13.5 bn" MUST be detected, so the validator can allowlist
      // exactly that one occurrence rather than the detector missing it.
      expect(containsTk('Tk 13.5 bn'), isTrue);
      expect(containsTk('Tk200 কোটি'), isTrue);
      expect(containsTk('Tk'), isTrue);
      expect(containsTk('বেতন Tk 7,500 থেকে'), isTrue);
    });

    test('negative cases', () {
      expect(containsTk('১,৩৫০ কোটি টাকা'), isFalse);
      expect(containsTk('৳১,৩৫০'), isFalse);
      expect(containsTk('টাকা'), isFalse);
      expect(containsTk('taka'), isFalse);
    });
  });

  group('containsHyphenSuffix', () {
    test('Latin word + hyphen + Bangla ending', () {
      for (final text in [
        'QR-এর মাধ্যমে',
        'TIB-এর নির্বাহী',
        'BGB-এর মোট',
        '7 November-এর ঘটনা',
        'BCS/Bank-এর নিয়ম',
        'Kagoj.ai-এর আগে',
        'COP31-এর সম্মেলন',
        'OC-সহ 6 জন',
        'Mackenzie-কে গ্রেপ্তার',
        'Malindi-র কাছে',
        'Antalya-তে সম্মেলন',
      ]) {
        expect(containsHyphenSuffix(text), isTrue, reason: text);
      }
    });

    test('dollar figures with a Bengali unit', () {
      expect(containsHyphenSuffix(r'$300 মিলিয়ন'), isTrue);
      expect(containsHyphenSuffix(r'US$113.44 বিলিয়ন'), isTrue);
      expect(containsHyphenSuffix(r'US$28.2–31.7 বিলিয়ন'), isTrue);
    });

    test('negative cases', () {
      // Bengali–Bengali hyphen is fine.
      expect(containsHyphenSuffix('কিলোওয়াট-ঘণ্টায়'), isFalse);
      expect(containsHyphenSuffix('পিয়ার-টু-পিয়ার'), isFalse);
      // Digit ranges are not hyphen-suffixes.
      expect(containsHyphenSuffix('2-3 বিলিয়ন'), isFalse);
      expect(containsHyphenSuffix('2,200-2,300 টাকা'), isFalse);
      // Latin word without a hyphenated Bangla ending is fine.
      expect(containsHyphenSuffix('BCS/Bank পরীক্ষা'), isFalse);
      expect(containsHyphenSuffix('QR কোড'), isFalse);
      expect(containsHyphenSuffix('Tk 13.5 bn'), isFalse);
    });
  });

  group('findBanglaViolations', () {
    test('returns every kind with correct spans', () {
      final violations = findBanglaViolations('2 December থেকে Tk 13.5 bn');
      expect(
        violations.map((v) => v.kind).toList(),
        [
          BanglaViolationKind.latinDigits, // '2'
          BanglaViolationKind.englishMonth, // 'December'
          BanglaViolationKind.tk, // 'Tk'
          BanglaViolationKind.latinDigits, // '13.5'
        ],
      );
      expect(violations.first.match, '2');
      expect(violations.first.start, 0);
      expect(violations[1].match, 'December');
    });

    test('overlapping kinds are kept separate', () {
      final violations = findBanglaViolations('November-এর ঘটনা');
      expect(
        violations.map((v) => v.kind).toSet(),
        {
          BanglaViolationKind.englishMonth,
          BanglaViolationKind.hyphenSuffix,
        },
      );
    });

    test('clean Bengali text has no violations', () {
      expect(findBanglaViolations('৭ নভেম্বর ২০২৬'), isEmpty);
      expect(
        findBanglaViolations('১,৩৫০ কোটি টাকা প্রকল্পের ব্যয়'),
        isEmpty,
      );
      expect(hasBanglaViolation('৭ নভেম্বর ২০২৬'), isFalse);
      expect(hasBanglaViolation('2 December'), isTrue);
    });

    test('finder helpers return the matched strings', () {
      expect(findLatinDigitRuns('a 2 b 13.5'), ['2', '13.5']);
      expect(findEnglishMonths('2 November, 31 December'), [
        'November',
        'December',
      ]);
      expect(findTkOccurrences('Tk200, Tk 13.5'), ['Tk', 'Tk']);
      expect(
        findHyphenSuffixMatches('QR-এর, US\$300 মিলিয়ন'),
        ['QR-এর', r'US$300 মিলিয়ন'],
      );
    });
  });
}
