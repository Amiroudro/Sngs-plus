/// Standalone Phase 4 (Authentic Bengali) validator.
///
///     dart tools/validate_bangla.dart [--write-snapshot]
///
/// Fails (exit code 1, listing every violation as `file:line`) when it
/// finds Latin digits, English months, `Tk`, or hyphen-suffixed Latin
/// words in Bengali text. Pure Dart — no Flutter imports — and it reuses
/// the detectors in `lib/utils/bangla_format.dart` verbatim.
///
/// What is scanned (and why):
/// (a) the `stringsBn` map in `lib/data/strings.dart` — every UI string
///     shown in Bengali mode. (The English map is never scanned: it is
///     English by design.)
/// (b) every `bn-*.json` file in `assets/editions/` — every string value
///     (stories + MCQs). The `note` provenance field is excluded: it is
///     never displayed.
/// (c) `data-*.json`, fallback-aware, exactly as `lib/data/loader.dart`
///     merges the overlay (`models.dart`: `headlineIn` / `summaryIn` /
///     `whyIn` / `factsIn` / `peopleIn` / `figuresIn` and the MCQ
///     `questionIn` / `optionIn` / `explanationIn` fall back to the
///     English source when the Bengali overlay lacks that field):
///     an English story/MCQ field is scanned ONLY when the overlay for
///     that story/MCQ lacks it. Plus the Bengali fields that have no
///     overlay at all: words' / revision words' `Bangla meaning` and
///     `Bangla phonetic`, and phrases' `Bangla meaning`.
///     NOT scanned: English definitions, newspaper examples, source
///     publication names/headlines, URLs, `edition_day` / `coverage`
///     metadata — English by design or never rendered as Bengali text.
///
/// Allowlist: `tools/validate_bangla_allowlist.json`. An entry
/// suppresses a violation only when the violation's match lies inside
/// an occurrence of the entry's `substring` in the same scanned string
/// in the same file. `code-slot` entries suppress nothing (they
/// document the one runtime `Tk` rendering, which lives in .dart code
/// this script does not scan).
///
/// `--write-snapshot` writes `tools/validate_bangla_snapshot.json`
/// (per-file, per-kind counts of unsuppressed violations). The Flutter
/// test `test/bangla_validator_test.dart` compares its live in-process
/// scan against that snapshot, so the suite stays green while the
/// Phase 4 data conversion is in progress and fails if a new violation
/// slips in. After the conversion, regenerate the snapshot (all counts
/// become 0) and this script becomes the strict gate: exit 0.
library;

import 'dart:convert';
import 'dart:io';

import 'package:sarangsho_plus/utils/bangla_format.dart';

/// One violation found by the scan, with everything needed to report
/// it and to test it against the allowlist.
class FoundViolation {
  final String file;
  final int line;
  final String location;
  final BanglaViolationKind kind;
  final String match;
  final String value;
  final int matchStart;
  final int matchEnd;

  const FoundViolation({
    required this.file,
    required this.line,
    required this.location,
    required this.kind,
    required this.match,
    required this.value,
    required this.matchStart,
    required this.matchEnd,
  });
}

class _AllowlistEntry {
  final String? file;
  final String? substring;
  final String kind;
  final String reason;
  int suppressed = 0;

  _AllowlistEntry({
    required this.file,
    required this.substring,
    required this.kind,
    required this.reason,
  });
}

/// One scanned string value, with its location for reporting.
class _ScannedValue {
  final String file;
  final int line;
  final String location;
  final String value;

  const _ScannedValue({
    required this.file,
    required this.line,
    required this.location,
    required this.value,
  });
}

/// Returns the 1-based line containing [encoded], searching [lines] in
/// order and skipping lines already used for the same encoded value.
int _findLine(
  List<String> lines,
  Map<String, List<int>> used,
  String encoded,
) {
  final usedLines = used.putIfAbsent(encoded, () => <int>[]);
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].contains(encoded) && !usedLines.contains(i + 1)) {
      usedLines.add(i + 1);
      return i + 1;
    }
  }
  return 1;
}

/// Walks decoded JSON, calling [onString] for every string leaf with a
/// dotted path like `stories.CA04.headline` or `mcqs.16.options.B`.
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

// ---------------------------------------------------------------------------
// (a) stringsBn
// ---------------------------------------------------------------------------

/// A Dart string literal found while scanning: its decoded [value] and
/// the 1-based [line] it starts on.
class _DartLiteral {
  final String value;
  final int line;

  const _DartLiteral(this.value, this.line);
}

/// Scans the `stringsBn` map block in `lib/data/strings.dart` and
/// returns its entries as (key, value, line-of-value).
List<({String key, String value, int line})> _parseStringsBn(String src) {
  final start = src.indexOf('stringsBn = {');
  if (start < 0) throw StateError('stringsBn map not found in strings.dart');
  var i = src.indexOf('{', start);
  var depth = 0;
  final literals = <_DartLiteral>[];
  var line = 1 + '\n'.allMatches(src.substring(0, i)).length;

  String readLiteral() {
    final quote = src[i];
    final startLine = line;
    final buf = StringBuffer();
    i++; // opening quote
    while (i < src.length) {
      final c = src[i];
      if (c == '\n') line++;
      if (c == '\\' && i + 1 < src.length) {
        final next = src[i + 1];
        if (next == 'u' && i + 2 < src.length && src[i + 2] == '{') {
          final close = src.indexOf('}', i + 3);
          final hex = src.substring(i + 3, close);
          buf.write(String.fromCharCode(int.parse(hex, radix: 16)));
          i = close + 1;
        } else if (next == 'u' && i + 5 < src.length) {
          buf.write(String.fromCharCode(
              int.parse(src.substring(i + 2, i + 6), radix: 16)));
          i += 6;
        } else {
          buf.write(switch (next) {
            'n' => '\n',
            'r' => '\r',
            't' => '\t',
            _ => next,
          });
          i += 2;
        }
        continue;
      }
      if (c == quote) {
        i++;
        return buf.toString();
      }
      buf.write(c);
      i++;
    }
    throw StateError('Unterminated string literal at line $startLine');
  }

  while (i < src.length) {
    final c = src[i];
    if (c == '\n') {
      line++;
      i++;
      continue;
    }
    // Skip //-comments outside strings.
    if (c == '/' && i + 1 < src.length && src[i + 1] == '/') {
      while (i < src.length && src[i] != '\n') {
        i++;
      }
      continue;
    }
    if (c == '{') {
      depth++;
      i++;
      continue;
    }
    if (c == '}') {
      depth--;
      i++;
      if (depth == 0) break;
      continue;
    }
    if (c == "'" || c == '"') {
      final literalLine = line;
      final value = readLiteral();
      literals.add(_DartLiteral(value, literalLine));
      continue;
    }
    i++;
  }

  // Literals arrive as key, value, key, value, ... — stringsBn has no
  // adjacent-literal values, so each value is exactly one literal.
  final out = <({String key, String value, int line})>[];
  var j = 0;
  while (j + 1 < literals.length) {
    final key = literals[j];
    final value = literals[j + 1];
    out.add((key: key.value, value: value.value, line: value.line));
    j += 2;
  }
  return out;
}

List<_ScannedValue> _scanStringsBn(String appRoot) {
  const path = 'lib/data/strings.dart';
  final src = File('$appRoot/$path').readAsStringSync();
  return [
    for (final e in _parseStringsBn(src))
      _ScannedValue(
        file: path,
        line: e.line,
        location: "stringsBn['${e.key}']",
        value: e.value,
      ),
  ];
}

// ---------------------------------------------------------------------------
// (b) bn-*.json
// ---------------------------------------------------------------------------

List<_ScannedValue> _scanBnJson(File file, String relPath) {
  final raw = file.readAsStringSync();
  final lines = raw.split('\n');
  final used = <String, List<int>>{};
  final decoded = jsonDecode(raw);
  final out = <_ScannedValue>[];
  _walkJson(decoded, '', (path, value) {
    // Metadata, never displayed as Bengali text: the ISO edition date,
    // the language tag, and the provenance note.
    if (path == 'note' || path == 'edition_date' || path == 'language') {
      return;
    }
    out.add(_ScannedValue(
      file: relPath,
      line: _findLine(lines, used, jsonEncode(value)),
      location: path,
      value: value,
    ));
  });
  return out;
}

// ---------------------------------------------------------------------------
// (c) data-*.json, fallback-aware
// ---------------------------------------------------------------------------

const List<String> _storyFields = [
  'headline',
  'summary',
  'why_it_matters',
  'exam_facts',
  'key_people',
  'figures',
];

List<_ScannedValue> _scanDataJson(
  File dataFile,
  String relPath,
  Map<String, dynamic>? bn,
) {
  final raw = dataFile.readAsStringSync();
  final lines = raw.split('\n');
  final used = <String, List<int>>{};
  final decoded = jsonDecode(raw) as Map<String, dynamic>;
  final out = <_ScannedValue>[];

  void add(String location, String value) {
    out.add(_ScannedValue(
      file: relPath,
      line: _findLine(lines, used, jsonEncode(value)),
      location: location,
      value: value,
    ));
  }

  bool bnHas(Map<String, dynamic>? overlay, String field) {
    final v = overlay?[field];
    return v is String && v.trim().isNotEmpty;
  }

  final bnStories = bn?['stories'];
  final stories = decoded['stories'];
  if (stories is List) {
    for (final story in stories) {
      if (story is! Map) continue;
      final id = story['id']?.toString() ?? '?';
      final overlay = bnStories is Map ? bnStories[id] : null;
      final overlayMap = overlay is Map<String, dynamic>
          ? overlay
          : overlay is Map
              ? Map<String, dynamic>.from(overlay)
              : null;
      for (final field in _storyFields) {
        if (bnHas(overlayMap, field)) continue;
        final v = story[field];
        if (v is String && v.trim().isNotEmpty) {
          add(
            'stories.$id.$field (fallback: no Bengali overlay)',
            v,
          );
        }
      }
    }
  }

  final bnMcqs = bn?['mcqs'];
  final mcqs = decoded['mcqs'];
  if (mcqs is List) {
    for (final mcq in mcqs) {
      if (mcq is! Map) continue;
      final no = mcq['no']?.toString() ?? '?';
      final overlay = bnMcqs is Map ? bnMcqs[no] : null;
      final overlayMap = overlay is Map<String, dynamic>
          ? overlay
          : overlay is Map
              ? Map<String, dynamic>.from(overlay)
              : null;
      if (!bnHas(overlayMap, 'question')) {
        final v = mcq['question'];
        if (v is String && v.trim().isNotEmpty) {
          add('mcqs.$no.question (fallback: no Bengali overlay)', v);
        }
      }
      final options = mcq['options'];
      final bnOptions = overlayMap?['options'];
      if (options is Map) {
        for (final e in options.entries) {
          final key = e.key.toString();
          final bnValue =
              bnOptions is Map ? bnOptions[key] : null;
          if (bnValue is String && bnValue.trim().isNotEmpty) continue;
          final v = e.value;
          if (v is String && v.trim().isNotEmpty) {
            add(
              'mcqs.$no.options.$key (fallback: no Bengali overlay)',
              v,
            );
          }
        }
      }
      if (!bnHas(overlayMap, 'explanation')) {
        final v = mcq['explanation'];
        if (v is String && v.trim().isNotEmpty) {
          add('mcqs.$no.explanation (fallback: no Bengali overlay)', v);
        }
      }
    }
  }

  // Bengali fields with no overlay at all: word / phrase meanings.
  for (final listName in ['words', 'revision_words']) {
    final words = decoded[listName];
    if (words is List) {
      for (var i = 0; i < words.length; i++) {
        final w = words[i];
        if (w is! Map) continue;
        for (final field in ['Bangla meaning', 'Bangla phonetic']) {
          final v = w[field];
          if (v is String && v.trim().isNotEmpty) {
            add('$listName[$i].$field', v);
          }
        }
      }
    }
  }
  final phrases = decoded['phrases'];
  if (phrases is List) {
    for (var i = 0; i < phrases.length; i++) {
      final p = phrases[i];
      if (p is! Map) continue;
      final v = p['Bangla meaning'];
      if (v is String && v.trim().isNotEmpty) {
        add('phrases[$i].Bangla meaning', v);
      }
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

String _excerpt(String value, int start, int end) {
  final from = start - 30 < 0 ? 0 : start - 30;
  final to = end + 30 > value.length ? value.length : end + 30;
  final piece = value.substring(from, to).replaceAll('\n', ' ');
  return '${from > 0 ? '…' : ''}$piece${to < value.length ? '…' : ''}';
}

void main(List<String> args) {
  var writeSnapshot = false;
  for (final arg in args) {
    if (arg == '--write-snapshot') {
      writeSnapshot = true;
    } else {
      stderr.writeln('Usage: dart tools/validate_bangla.dart '
          '[--write-snapshot]');
      exit(2);
    }
  }

  final scriptFile = File(Platform.script.toFilePath());
  var appRoot = scriptFile.parent.parent.path;
  if (!File('$appRoot/tools/validate_bangla_allowlist.json').existsSync()) {
    appRoot = Directory.current.path;
  }
  final allowlistFile =
      File('$appRoot/tools/validate_bangla_allowlist.json');
  if (!allowlistFile.existsSync()) {
    stderr.writeln('Allowlist not found: ${allowlistFile.path}');
    exit(2);
  }

  final allowlistJson =
      jsonDecode(allowlistFile.readAsStringSync()) as Map<String, dynamic>;
  final entries = <_AllowlistEntry>[];
  final rawEntries = allowlistJson['entries'];
  if (rawEntries is List) {
    for (final e in rawEntries) {
      if (e is! Map) continue;
      entries.add(_AllowlistEntry(
        file: e['file'] as String?,
        substring: e['substring'] as String?,
        kind: (e['kind'] as String?) ?? 'unknown',
        reason: (e['reason'] as String?) ?? '',
      ));
    }
  }

  // --- Collect every scanned string value. ---
  final values = <_ScannedValue>[];
  values.addAll(_scanStringsBn(appRoot));
  final editionsDir = Directory('$appRoot/assets/editions');
  final bnFiles = editionsDir
      .listSync()
      .whereType<File>()
      .where((f) => f.path.endsWith('.json'))
      .where((f) {
        final name = f.uri.pathSegments.last;
        return name.startsWith('bn-');
      })
      .toList()
    ..sort((a, b) => a.path.compareTo(b.path));
  final dataFiles = editionsDir
      .listSync()
      .whereType<File>()
      .where((f) => f.path.endsWith('.json'))
      .where((f) {
        final name = f.uri.pathSegments.last;
        return name.startsWith('data-');
      })
      .toList()
    ..sort((a, b) => a.path.compareTo(b.path));

  for (final f in bnFiles) {
    final name = f.uri.pathSegments.last;
    values.addAll(_scanBnJson(f, 'assets/editions/$name'));
  }
  for (final f in dataFiles) {
    final name = f.uri.pathSegments.last;
    final bnName = name.replaceFirst('data-', 'bn-');
    final bnFile = File('${editionsDir.path}/$bnName');
    Map<String, dynamic>? bn;
    if (bnFile.existsSync()) {
      final decoded = jsonDecode(bnFile.readAsStringSync());
      if (decoded is Map<String, dynamic>) {
        bn = decoded;
      } else if (decoded is Map) {
        bn = Map<String, dynamic>.from(decoded);
      }
    }
    values.addAll(_scanDataJson(f, 'assets/editions/$name', bn));
  }

  // --- Run the detectors; suppress allowlisted spans. ---
  final violations = <FoundViolation>[];
  var suppressedCount = 0;
  final suppressedByFile = <String, int>{};
  for (final scanned in values) {
    for (final v in findBanglaViolations(scanned.value)) {
      var suppressed = false;
      for (final entry in entries) {
        final substring = entry.substring;
        if (entry.file == null ||
            substring == null ||
            entry.file != scanned.file) {
          continue;
        }
        var searchFrom = 0;
        while (true) {
          final at = scanned.value.indexOf(substring, searchFrom);
          if (at < 0) break;
          if (v.start >= at && v.end <= at + substring.length) {
            suppressed = true;
            entry.suppressed++;
            break;
          }
          searchFrom = at + 1;
        }
        if (suppressed) break;
      }
      if (suppressed) {
        suppressedCount++;
        suppressedByFile.update(
          scanned.file,
          (n) => n + 1,
          ifAbsent: () => 1,
        );
        continue;
      }
      violations.add(FoundViolation(
        file: scanned.file,
        line: scanned.line,
        location: scanned.location,
        kind: v.kind,
        match: v.match,
        value: scanned.value,
        matchStart: v.start,
        matchEnd: v.end,
      ));
    }
  }

  violations.sort((a, b) {
    final byFile = a.file.compareTo(b.file);
    if (byFile != 0) return byFile;
    final byLine = a.line.compareTo(b.line);
    if (byLine != 0) return byLine;
    final byLoc = a.location.compareTo(b.location);
    if (byLoc != 0) return byLoc;
    return a.matchStart.compareTo(b.matchStart);
  });

  for (final v in violations) {
    stdout.writeln(
      '${v.file}:${v.line}: [${v.kind.name}] ${v.location} — '
      '"${v.match}" in "${_excerpt(v.value, v.matchStart, v.matchEnd)}"',
    );
  }

  final byKind = <String, int>{};
  final byFile = <String, int>{};
  for (final v in violations) {
    byKind.update(v.kind.name, (n) => n + 1, ifAbsent: () => 1);
    byFile.update(v.file, (n) => n + 1, ifAbsent: () => 1);
  }

  stdout.writeln('---');
  stdout.writeln('Scanned ${values.length} Bengali-display strings in '
      '${bnFiles.length + dataFiles.length} edition files + stringsBn.');
  stdout.writeln('Violations: ${violations.length} '
      '(by kind: $byKind; by file: $byFile).');
  stdout.writeln('Suppressed by allowlist: $suppressedCount '
      '(by file: $suppressedByFile).');
  for (final entry in entries) {
    stdout.writeln('Allowlist [${entry.kind}] '
        '${entry.file ?? entry.substring ?? ''}'
        '${entry.substring != null ? ' :: "${entry.substring}"' : ''}'
        ' — suppressed ${entry.suppressed}.');
  }

  if (writeSnapshot) {
    final snapshot = <String, dynamic>{
      'generated_by': 'dart tools/validate_bangla.dart --write-snapshot',
      'note': 'Per-file, per-kind counts of UNSUPPRESSED violations, plus '
          'suppressed counts. test/bangla_validator_test.dart compares its '
          'live in-process scan against these numbers. Regenerate after '
          'converting data; when Phase 4 conversion is complete every '
          'violations count here is 0 and the script exits 0.',
      'violations': {
        for (final file in byFile.keys)
          file: {
            for (final kind in byKind.keys)
              if (violations.any(
                  (v) => v.file == file && v.kind.name == kind))
                kind: violations
                    .where((v) => v.file == file && v.kind.name == kind)
                    .length,
          },
      },
      'suppressed': suppressedByFile,
      'totals': {
        'violations': violations.length,
        'suppressed': suppressedCount,
      },
    };
    File('$appRoot/tools/validate_bangla_snapshot.json')
        .writeAsStringSync(
      const JsonEncoder.withIndent('  ').convert(snapshot),
    );
    stdout.writeln('Snapshot written to tools/validate_bangla_snapshot.json.');
  }

  if (violations.isEmpty) {
    stdout.writeln('PASS: no Bangla violations.');
    exit(0);
  } else {
    stdout.writeln(
      'FAIL: ${violations.length} Bangla violation(s). '
      'Fix the data (see lib/utils/bangla_format.dart) or, only with a '
      'written reason, add an allowlist entry.',
    );
    exit(1);
  }
}
