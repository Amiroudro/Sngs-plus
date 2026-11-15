/// In-process Phase 4 (Authentic Bengali) validator test.
///
/// APPROACH (see the task brief): the strict gate is the standalone
/// script `dart tools/validate_bangla.dart`, which fails (exit 1) on
/// ANY unsuppressed violation. This Flutter test runs the same checks
/// in-process — it imports the shared detectors from
/// `lib/utils/bangla_format.dart`, reads the same files (bundled
/// assets via `rootBundle`, falling back to `File`), and applies the
/// same allowlist span rule as the script — but it compares the live
/// counts against the checked-in snapshot
/// (`tools/validate_bangla_snapshot.json`) instead of demanding zero.
///
/// Why a snapshot: the edition data has not been converted yet
/// (3,106 violations at the time this test was written), so a strict
/// zero assertion would fail the whole suite until the applying agent
/// finishes the conversion. The snapshot keeps the suite green while
/// conversion is in progress AND fails the build if a violation slips
/// in (any new violation changes the live counts) or is fixed without
/// regenerating the snapshot. After the conversion, regenerate with
/// `dart tools/validate_bangla.dart --write-snapshot` — every count
/// becomes 0 and this test enforces zero from then on.
///
/// The one strict assertion that already holds today: `stringsBn`
/// must have zero violations (it is already clean).
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/strings.dart';
import 'package:sarangsho_plus/utils/bangla_format.dart';

/// Reads a bundled asset the way the app does, falling back to a plain
/// file read (the test working directory is the package root).
Future<String> _readAsset(String path) async {
  try {
    return await rootBundle.loadString(path);
  } catch (_) {
    return File(path).readAsStringSync();
  }
}

/// Every string leaf of decoded JSON, with a dotted path.
void _walkJson(
  dynamic node,
  String path,
  void Function(String path, String value) onString,
) {
  if (node is String) {
    onString(path, node);
  } else if (node is Map) {
    for (final e in node.entries) {
      final key = e.key.toString();
      _walkJson(e.value, path.isEmpty ? key : '$path.$key', onString);
    }
  } else if (node is List) {
    for (var i = 0; i < node.length; i++) {
      _walkJson(node[i], '$path[$i]', onString);
    }
  }
}

class _AllowlistEntry {
  final String? file;
  final String? substring;

  const _AllowlistEntry({required this.file, required this.substring});
}

/// A violation found in-process, kept with its scanned value so the
/// allowlist span rule can be checked exactly as the script does it.
class _LiveViolation {
  final String file;
  final String location;
  final BanglaViolation violation;
  final String value;

  const _LiveViolation({
    required this.file,
    required this.location,
    required this.violation,
    required this.value,
  });
}

const List<String> _storyFields = [
  'headline',
  'summary',
  'why_it_matters',
  'exam_facts',
  'key_people',
  'figures',
];

/// The full scan, mirroring `tools/validate_bangla.dart`:
/// (a) stringsBn, (b) every bn-*.json string except the metadata fields
/// `note` / `edition_date` / `language`, (c) data-*.json fallback-aware
/// (an English story/MCQ field only when the Bengali overlay lacks it)
/// plus words'/phrases' Bengali `Bangla meaning` / `Bangla phonetic`.
Future<
    ({
      List<_LiveViolation> violations,
      List<_LiveViolation> suppressed,
    })> _scanAll(List<_AllowlistEntry> allowlist) async {
  final violations = <_LiveViolation>[];
  final suppressed = <_LiveViolation>[];

  void check(String file, String location, String value) {
    for (final v in findBanglaViolations(value)) {
      final live = _LiveViolation(
        file: file,
        location: location,
        violation: v,
        value: value,
      );
      var isSuppressed = false;
      for (final entry in allowlist) {
        final substring = entry.substring;
        if (entry.file == null ||
            substring == null ||
            entry.file != file) {
          continue;
        }
        var from = 0;
        while (true) {
          final at = value.indexOf(substring, from);
          if (at < 0) break;
          if (v.start >= at && v.end <= at + substring.length) {
            isSuppressed = true;
            break;
          }
          from = at + 1;
        }
        if (isSuppressed) break;
      }
      (isSuppressed ? suppressed : violations).add(live);
    }
  }

  for (final e in stringsBn.entries) {
    check('lib/data/strings.dart', "stringsBn['${e.key}']", e.value);
  }

  final indexRaw = await _readAsset('assets/editions/index.json');
  final indexJson = jsonDecode(indexRaw) as Map<String, dynamic>;
  final files = <String>[];
  final rawEntries = indexJson['editions'];
  if (rawEntries is List) {
    for (final e in rawEntries) {
      if (e is Map) {
        final date = e['edition_date']?.toString() ?? '';
        final file = e['file'] as String? ??
            (date.isEmpty ? '' : 'data-$date.json');
        if (file.isNotEmpty) files.add(file);
      }
    }
  }

  for (final file in files) {
    final bnFile = file.replaceFirst('data-', 'bn-');
    final bnRaw = await _readAsset('assets/editions/$bnFile');
    final bn = jsonDecode(bnRaw) as Map<String, dynamic>;
    for (final section in ['stories', 'mcqs']) {
      final content = bn[section];
      if (content == null) continue;
      _walkJson(content, section, (path, value) {
        check('assets/editions/$bnFile', path, value);
      });
    }

    final dataRaw = await _readAsset('assets/editions/$file');
    final data = jsonDecode(dataRaw) as Map<String, dynamic>;
    bool bnHas(Map? overlay, String field) {
      final v = overlay?[field];
      return v is String && v.trim().isNotEmpty;
    }

    final bnStories = bn['stories'];
    final stories = data['stories'];
    if (stories is List) {
      for (final story in stories) {
        if (story is! Map) continue;
        final id = story['id']?.toString() ?? '?';
        final overlay = bnStories is Map ? bnStories[id] : null;
        for (final field in _storyFields) {
          if (bnHas(overlay, field)) continue;
          final v = story[field];
          if (v is String && v.trim().isNotEmpty) {
            check(
              'assets/editions/$file',
              'stories.$id.$field (fallback: no Bengali overlay)',
              v,
            );
          }
        }
      }
    }
    final bnMcqs = bn['mcqs'];
    final mcqs = data['mcqs'];
    if (mcqs is List) {
      for (final mcq in mcqs) {
        if (mcq is! Map) continue;
        final no = mcq['no']?.toString() ?? '?';
        final overlay = bnMcqs is Map ? bnMcqs[no] : null;
        if (!bnHas(overlay, 'question')) {
          final v = mcq['question'];
          if (v is String && v.trim().isNotEmpty) {
            check(
              'assets/editions/$file',
              'mcqs.$no.question (fallback: no Bengali overlay)',
              v,
            );
          }
        }
        final options = mcq['options'];
        final bnOptions = overlay is Map ? overlay['options'] : null;
        if (options is Map) {
          for (final e in options.entries) {
            final key = e.key.toString();
            final bnValue = bnOptions is Map ? bnOptions[key] : null;
            if (bnValue is String && bnValue.trim().isNotEmpty) continue;
            final v = e.value;
            if (v is String && v.trim().isNotEmpty) {
              check(
                'assets/editions/$file',
                'mcqs.$no.options.$key (fallback: no Bengali overlay)',
                v,
              );
            }
          }
        }
        if (!bnHas(overlay, 'explanation')) {
          final v = mcq['explanation'];
          if (v is String && v.trim().isNotEmpty) {
            check(
              'assets/editions/$file',
              'mcqs.$no.explanation (fallback: no Bengali overlay)',
              v,
            );
          }
        }
      }
    }
    for (final listName in ['words', 'revision_words']) {
      final words = data[listName];
      if (words is List) {
        for (var i = 0; i < words.length; i++) {
          final w = words[i];
          if (w is! Map) continue;
          for (final field in ['Bangla meaning', 'Bangla phonetic']) {
            final v = w[field];
            if (v is String && v.trim().isNotEmpty) {
              check('assets/editions/$file', '$listName[$i].$field', v);
            }
          }
        }
      }
    }
    final phrases = data['phrases'];
    if (phrases is List) {
      for (var i = 0; i < phrases.length; i++) {
        final p = phrases[i];
        if (p is! Map) continue;
        final v = p['Bangla meaning'];
        if (v is String && v.trim().isNotEmpty) {
          check('assets/editions/$file', 'phrases[$i].Bangla meaning', v);
        }
      }
    }
  }

  return (violations: violations, suppressed: suppressed);
}

Future<List<_AllowlistEntry>> _loadAllowlist() async {
  final raw =
      File('tools/validate_bangla_allowlist.json').readAsStringSync();
  final decoded = jsonDecode(raw) as Map<String, dynamic>;
  final out = <_AllowlistEntry>[];
  final entries = decoded['entries'];
  if (entries is List) {
    for (final e in entries) {
      if (e is! Map) continue;
      out.add(_AllowlistEntry(
        file: e['file'] as String?,
        substring: e['substring'] as String?,
      ));
    }
  }
  return out;
}

void main() {
  test('stringsBn has zero Bangla violations', () {
    final bad = <String>[];
    for (final e in stringsBn.entries) {
      final found = findBanglaViolations(e.value);
      if (found.isNotEmpty) {
        bad.add("${e.key}: ${found.map((v) => v.match).join(', ')}");
      }
    }
    expect(bad, isEmpty, reason: bad.join(' | '));
  });

  test('edition scan matches the checked-in snapshot', () async {
    final allowlist = await _loadAllowlist();
    final result = await _scanAll(allowlist);

    final liveViolations = <String, Map<String, int>>{};
    for (final v in result.violations) {
      final perKind = liveViolations.putIfAbsent(v.file, () => {});
      perKind.update(
        v.violation.kind.name,
        (n) => n + 1,
        ifAbsent: () => 1,
      );
    }
    final liveSuppressed = <String, int>{};
    for (final v in result.suppressed) {
      liveSuppressed.update(v.file, (n) => n + 1, ifAbsent: () => 1);
    }

    final snapshotRaw =
        File('tools/validate_bangla_snapshot.json').readAsStringSync();
    final snapshot = jsonDecode(snapshotRaw) as Map<String, dynamic>;
    final snapshotViolations =
        (snapshot['violations'] as Map<String, dynamic>).map(
      (file, kinds) => MapEntry(
        file,
        (kinds as Map<String, dynamic>)
            .map((kind, count) => MapEntry(kind, count as int)),
      ),
    );
    final snapshotSuppressed =
        (snapshot['suppressed'] as Map<String, dynamic>)
            .map((file, count) => MapEntry(file, count as int));

    expect(
      liveViolations,
      equals(snapshotViolations),
      reason: 'Live scan differs from tools/validate_bangla_snapshot.json. '
          'If data was converted (or a new violation slipped in), '
          'regenerate with: dart tools/validate_bangla.dart '
          '--write-snapshot',
    );
    expect(liveSuppressed, equals(snapshotSuppressed));
    expect(result.violations.length,
        (snapshot['totals'] as Map)['violations']);
    expect(result.suppressed.length,
        (snapshot['totals'] as Map)['suppressed']);
  });

  test('allowlist suppresses only the corrected HSC baseline date spans', () async {
    final allowlist = await _loadAllowlist();
    final result = await _scanAll(allowlist);
    const file = 'assets/editions/bn-2026-11-02.json';
    const spans = ['1 December', '1 December 2026', '1-31 December'];

    // The pending-fix entries must actually be doing work.
    final suppressedHere =
        result.suppressed.where((v) => v.file == file).length;
    expect(suppressedHere, greaterThan(0));

    // And no UNSUPPRESSED violation may sit inside an allowlisted span:
    // e.g. the '1' and 'December' of '1 December' must never be reported,
    // while the '31 December' results date (not allowlisted) still is.
    for (final v in result.violations) {
      if (v.file != file) continue;
      for (final span in spans) {
        var from = 0;
        while (true) {
          final at = v.value.indexOf(span, from);
          if (at < 0) break;
          expect(
            v.violation.start < at ||
                v.violation.end > at + span.length,
            isTrue,
            reason: 'Violation "${v.violation.match}" at '
                '${v.location} lies inside allowlisted "$span".',
          );
          from = at + 1;
        }
      }
    }
  });

  test('the one allowed Tk slot is code-generated, not data', () async {
    // No data file contains the literal 'Tk 13.5 bn': the small grey
    // original figure is generated at runtime in
    // lib/data/story_layout.dart (parseTile -> FactTile.original) from
    // the English source. If this test fails, a data file grew a
    // literal copy of the slot and the allowlist reasoning is wrong.
    final indexRaw = await _readAsset('assets/editions/index.json');
    final indexJson = jsonDecode(indexRaw) as Map<String, dynamic>;
    final rawEntries = indexJson['editions'];
    if (rawEntries is List) {
      for (final e in rawEntries) {
        if (e is Map && e['file'] is String) {
          final file = e['file'] as String;
          final bnFile = file.replaceFirst('data-', 'bn-');
          for (final name in [file, bnFile]) {
            final raw = await _readAsset('assets/editions/$name');
            expect(raw.contains('Tk 13.5 bn'), isFalse, reason: name);
          }
        }
      }
    }
  });
}
