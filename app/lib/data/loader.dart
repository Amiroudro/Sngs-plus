/// Loads the bundled editions (English source JSON + Bengali overlays)
/// from assets, then overlays any valid downloaded editions from the
/// app documents directory (Phase 5 — see
/// [EditionDownloadService]). The default index URL is Rudro's
/// public GitHub Pages host (see [EditionDownloadService.defaultIndexUrl]);
/// a URL stored in Profile overrides it. Downloaded editions override
/// the bundled edition with the same date; a newer downloaded edition
/// joins the list.
///
/// Adding a new edition:
/// 1. Drop `data-YYYY-MM-DD.json` into assets/editions/.
/// 2. Add its entry to assets/editions/index.json.
/// 3. Optionally add `bn-YYYY-MM-DD.json` with the same story ids / MCQ
///    numbers for the Bengali translation overlay.
/// The loader picks up any entry in index.json automatically.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../models.dart';
import '../services/edition_download_service.dart';
import '../state/app_state.dart';

class EditionLoadResult {
  final List<Edition> editions;
  final int correctConsecutive;
  final String? correctRule;

  const EditionLoadResult({
    required this.editions,
    required this.correctConsecutive,
    this.correctRule,
  });
}

Future<EditionLoadResult> loadEditions() async {
  final indexRaw = await rootBundle.loadString('assets/editions/index.json');
  final indexJson = jsonDecode(indexRaw) as Map<String, dynamic>;

  final entries = <EditionIndexEntry>[];
  final rawEntries = indexJson['editions'];
  if (rawEntries is List) {
    for (final e in rawEntries) {
      if (e is Map<String, dynamic>) {
        entries.add(EditionIndexEntry.fromJson(e));
      } else if (e is Map) {
        entries.add(EditionIndexEntry.fromJson(Map<String, dynamic>.from(e)));
      }
    }
  }

  final correctConsecutive = indexJson['correct_consecutive_editions'] is int
      ? indexJson['correct_consecutive_editions'] as int
      : 0;
  final correctRule = indexJson['correct_rule'] as String?;

  var editions = <Edition>[];
  for (final entry in entries) {
    final raw = await rootBundle.loadString('assets/editions/${entry.file}');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final edition = Edition.fromJson(data, statusOverride: entry.status);

    // Bengali overlay is optional: a missing overlay file simply means
    // the edition shows in English (with the language toggle).
    try {
      final bnRaw =
          await rootBundle.loadString('assets/editions/${entry.bnFile}');
      final bnJson = jsonDecode(bnRaw) as Map<String, dynamic>;
      final bnStories = bnJson['stories'];
      if (bnStories is Map) {
        for (final story in edition.stories) {
          final bs = bnStories[story.id];
          if (bs is Map<String, dynamic>) {
            story.bn = BnStory.fromJson(bs);
          } else if (bs is Map) {
            story.bn = BnStory.fromJson(Map<String, dynamic>.from(bs));
          }
        }
      }
      final bnMcqs = bnJson['mcqs'];
      if (bnMcqs is Map) {
        for (final mcq in edition.mcqs) {
          final bm = bnMcqs['${mcq.no}'];
          if (bm is Map<String, dynamic>) {
            mcq.bn = BnMcq.fromJson(bm);
          } else if (bm is Map) {
            mcq.bn = BnMcq.fromJson(Map<String, dynamic>.from(bm));
          }
        }
      }
    } catch (_) {
      // No Bengali overlay for this edition — English source is used.
    }

    editions.add(edition);
  }

  // Newest first.
  editions.sort((a, b) => b.date.compareTo(a.date));

  // Phase 5: downloaded editions (from the configured remote index)
  // override the bundled edition with the same date, and a newer
  // downloaded edition joins the list. Invalid files are ignored —
  // the bundled editions always remain the fallback.
  editions = mergeDownloadedEditions(
    editions,
    await loadDownloadedEditions(),
  );
  editions.sort((a, b) => b.date.compareTo(a.date));

  return EditionLoadResult(
    editions: editions,
    correctConsecutive: correctConsecutive,
    correctRule: correctRule,
  );
}

/// Merges downloaded editions over bundled ones: same date replaces,
/// a newer date joins. Pure (no I/O) so tests can check the preference
/// rule directly.
List<Edition> mergeDownloadedEditions(
  List<Edition> bundled,
  List<Edition> downloaded,
) {
  final out = [...bundled];
  for (final d in downloaded) {
    final i = out.indexWhere((e) => e.date == d.date);
    if (i >= 0) {
      out[i] = d;
    } else {
      out.add(d);
    }
  }
  return out;
}

/// Reads valid downloaded editions from the app documents directory
/// (see [EditionDownloadService.downloadedDir]). Never throws: a
/// missing directory, an unreadable file or an invalid edition simply
/// yields no entry. [downloadDirOverride] exists for tests.
Future<List<Edition>> loadDownloadedEditions({
  Directory? downloadDirOverride,
}) async {
  try {
    final Directory dir;
    if (downloadDirOverride != null) {
      dir = downloadDirOverride;
    } else {
      final base = await getApplicationDocumentsDirectory();
      dir = Directory(
        '${base.path}/${EditionDownloadService.downloadedDirName}',
      );
    }
    if (!await dir.exists()) return const [];
    final out = <Edition>[];
    await for (final f in dir.list()) {
      if (f is! File) continue;
      final name = f.path.split('/').last;
      if (!name.startsWith('data-') || !name.endsWith('.json')) continue;
      try {
        final json =
            jsonDecode(await f.readAsString()) as Map<String, dynamic>;
        final edition = validateDownloadedEdition(json);
        if (edition == null) continue;
        // Bengali overlay next to the download, same rule as bundled.
        try {
          final bnFile = File(
            '${dir.path}/bn-${edition.date}.json',
          );
          if (await bnFile.exists()) {
            final bnJson = jsonDecode(await bnFile.readAsString())
                as Map<String, dynamic>;
            final bnStories = bnJson['stories'];
            if (bnStories is Map) {
              for (final story in edition.stories) {
                final bs = bnStories[story.id];
                if (bs is Map<String, dynamic>) {
                  story.bn = BnStory.fromJson(bs);
                } else if (bs is Map) {
                  story.bn = BnStory.fromJson(
                    Map<String, dynamic>.from(bs),
                  );
                }
              }
            }
          }
        } catch (_) {
          // No / bad overlay — the edition still shows in English.
        }
        out.add(edition);
      } catch (_) {
        // Invalid downloaded file — ignored, never trusted.
      }
    }
    return out;
  } catch (_) {
    return const [];
  }
}

/// Phase 5: checks the configured remote index (the stored URL when
/// set, otherwise the default Pages URL) and reloads the editions
/// into [state], preferring downloaded files. Returns the check
/// result (an error when the check failed). Never throws: any failure
/// leaves the bundled editions exactly as they were.
///
/// [service] is injectable so tests can pass a fake fetcher; production
/// passes nothing and gets the real HttpClient service.
Future<EditionDownloadResult> refreshEditions(
  AppState state, {
  EditionDownloadService? service,
}) async {
  try {
    final bundledDates = state.editions.map((e) => e.date).toSet();
    final svc = service ?? EditionDownloadService();
    final result = await svc.checkForUpdates(
      bundledDates: bundledDates,
    );
    final loaded = await loadEditions();
    await state.setEditions(
      loaded.editions,
      loaded.correctConsecutive,
      loaded.correctRule,
    );
    return result;
  } catch (_) {
    return const EditionDownloadResult(error: 'network');
  }
}
