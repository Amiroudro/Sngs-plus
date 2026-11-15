/// Downloads new editions from a remote index.json (Phase 5).
///
/// The URL is CONFIGURABLE, with a DEFAULT pointing at Rudro's
/// public GitHub Pages repo for editions:
/// https://amiroudro.github.io/sarangsho-plus-editions/editions/index.json
/// A URL stored in SharedPreferences (set in Profile) overrides the
/// default; clearing the stored URL restores the default. With the
/// default in place the app checks for new editions on launch and on
/// pull-to-refresh — no manual step needed.
///
/// Flow:
/// 1. Fetch the remote index.json (same shape as the bundled
///    assets/editions/index.json: {"editions": [{edition_date, file,
///    status, ...}]}).
/// 2. For each entry newer than the newest bundled edition, download
///    its file (relative URLs resolve against the index URL).
/// 2b. The NEWEST remote edition is always re-fetched, even when it
///    is already bundled or downloaded: a correction to today's
///    edition (same date, new content) must reach the phone, and the
///    loader prefers the downloaded copy over the bundled one.
///    Identical content is not rewritten and is not reported as
///    downloaded. Older entries are skipped once present, as before.
/// 3. Validate each download before saving: it must parse as JSON,
///    carry the required top-level keys, and parse through the same
///    [Edition.fromJson] the loader uses. Invalid downloads are
///    discarded, never saved.
/// 4. Valid editions are saved under the app documents directory
///    (`downloaded_editions/data-YYYY-MM-DD.json`, plus the Bengali
///    overlay `bn-YYYY-MM-DD.json` when the server offers one — a
///    missing overlay is fine, it is optional like the bundled one).
/// 5. [loadEditions] (loader.dart) prefers a downloaded edition over
///    the bundled one with the same date.
///
/// On ANY failure — no connection, bad URL, non-200, invalid JSON,
/// invalid edition — the check returns a failure result and the app
/// keeps showing the bundled editions. Nothing here ever throws to
/// the UI: [checkForUpdates] catches everything and reports it.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models.dart';

/// The fetch function, injectable so tests can use a fake instead of
/// the real network. The default uses dart:io HttpClient (no `http`
/// package dependency).
typedef EditionFetcher = Future<String> Function(Uri url);

/// Result of one update check. Never throws; inspect the fields.
class EditionDownloadResult {
  /// Dates of editions downloaded and saved in this check.
  final List<String> downloaded;

  /// Dates of remote editions skipped (already bundled / already
  /// downloaded / not newer).
  final List<String> skipped;

  /// Human-readable reason when the check could not run at all
  /// (no URL, bad URL, no connection, bad index). Null on success.
  final String? error;

  /// True when no index URL is configured at all. Unreachable in
  /// practice now that [getEffectiveIndexUrl] always falls back to
  /// the default Pages URL; kept so a check can still report it.
  final bool notConfigured;

  const EditionDownloadResult({
    this.downloaded = const [],
    this.skipped = const [],
    this.error,
    this.notConfigured = false,
  });

  bool get ok => error == null;
  bool get foundNew => downloaded.isNotEmpty;
}

/// Shape check for one downloaded edition file. The same strictness
/// the app applies when parsing bundled editions, plus the
/// requirements a remote file must meet before it is trusted:
/// * parses as a JSON object;
/// * carries `edition_date` (String) and the `stories`, `words`,
///   `phrases`, `mcqs` lists;
/// * parses through [Edition.fromJson] and the parsed date matches
///   `edition_date`.
/// Returns the parsed [Edition] on success, null on any failure.
Edition? validateDownloadedEdition(Map<String, dynamic> json) {
  try {
    final date = json['edition_date'];
    if (date is! String || date.isEmpty) return null;
    for (final key in ['stories', 'words', 'phrases', 'mcqs']) {
      if (json[key] is! List) return null;
    }
    final edition = Edition.fromJson(json);
    if (edition.date != date) return null;
    return edition;
  } catch (_) {
    return null;
  }
}

class EditionDownloadService {
  /// SharedPreferences key for the configurable index URL.
  static const prefsKey = 'edition_index_url';

  /// Default index URL (Rudro-approved 2026-11-12): the public
  /// GitHub Pages host for the published editions. Used whenever
  /// nothing is stored under [prefsKey]. The ONE place this URL
  /// lives — do not hard-code it anywhere else.
  static const defaultIndexUrl =
      'https://amiroudro.github.io/sarangsho-plus-editions/editions/index.json';

  /// Subdirectory of the app documents directory holding downloads.
  static const downloadedDirName = 'downloaded_editions';

  final EditionFetcher _fetch;

  /// Tests pass a fake fetcher and/or a temp directory; production
  /// uses the real HttpClient fetcher and the real documents dir.
  EditionDownloadService({
    EditionFetcher? fetcher,
    Future<Directory> Function()? documentsDir,
  })  : _fetch = fetcher ?? _httpFetch,
        _documentsDir = documentsDir;

  final Future<Directory> Function()? _documentsDir;

  /// Default fetcher: plain dart:io HttpClient, 15s timeouts.
  /// Non-200 is an error; the body is returned as text.
  static Future<String> _httpFetch(Uri url) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 15);
    try {
      final request = await client.getUrl(url);
      final response = await request.close().timeout(
            const Duration(seconds: 15),
          );
      if (response.statusCode != HttpStatus.ok) {
        throw HttpException(
          'HTTP ${response.statusCode} for $url',
          uri: url,
        );
      }
      return await response.transform(utf8.decoder).join().timeout(
            const Duration(seconds: 15),
          );
    } finally {
      client.close();
    }
  }

  // --- Configured URL (SharedPreferences) ----------------------------

  static Future<String> getStoredIndexUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(prefsKey) ?? '';
  }

  static Future<void> setStoredIndexUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(prefsKey, url.trim());
  }

  /// The URL actually used for update checks: the stored URL when
  /// one is set, otherwise the default Pages URL. Never empty.
  static Future<String> getEffectiveIndexUrl() async {
    final stored = await getStoredIndexUrl();
    return stored.isEmpty ? defaultIndexUrl : stored;
  }

  // --- Download directory --------------------------------------------

  Future<Directory> downloadedDir() async {
    final base = _documentsDir != null
        ? await _documentsDir()
        : await getApplicationDocumentsDirectory();
    final dir = Directory('${base.path}/$downloadedDirName');
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  /// Dates of editions already saved in the download directory
  /// (valid files only — an invalid file is ignored, never trusted).
  Future<Set<String>> downloadedDates() async {
    try {
      final dir = await downloadedDir();
      final out = <String>{};
      await for (final f in dir.list()) {
        if (f is! File) continue;
        final name = f.path.split('/').last;
        if (!name.startsWith('data-') || !name.endsWith('.json')) continue;
        try {
          final json =
              jsonDecode(await f.readAsString()) as Map<String, dynamic>;
          final edition = validateDownloadedEdition(json);
          if (edition != null) out.add(edition.date);
        } catch (_) {
          // Invalid saved file — ignored, never trusted.
        }
      }
      return out;
    } catch (_) {
      return {};
    }
  }

  /// Fetches the remote index, downloads any edition newer than the
  /// newest bundled date, validates and saves it. [bundledDates] are
  /// the dates of the bundled editions (the loader's index). The
  /// effective URL is used: a stored URL when set, otherwise the
  /// default Pages URL — so a check always runs. Never throws: every
  /// failure is reported in the returned result.
  Future<EditionDownloadResult> checkForUpdates({
    required Set<String> bundledDates,
  }) async {
    final url = await getEffectiveIndexUrl();
    if (url.isEmpty) {
      return const EditionDownloadResult(notConfigured: true);
    }
    final Uri indexUri;
    try {
      indexUri = Uri.parse(url);
      if (!indexUri.hasScheme ||
          (indexUri.scheme != 'http' && indexUri.scheme != 'https') ||
          indexUri.host.isEmpty) {
        return const EditionDownloadResult(error: 'bad_url');
      }
    } catch (_) {
      return const EditionDownloadResult(error: 'bad_url');
    }

    String indexRaw;
    try {
      indexRaw = await _fetch(indexUri).timeout(
        const Duration(seconds: 20),
      );
    } catch (_) {
      return const EditionDownloadResult(error: 'network');
    }

    final List<EditionIndexEntry> entries;
    try {
      final indexJson = jsonDecode(indexRaw) as Map<String, dynamic>;
      final raw = indexJson['editions'];
      if (raw is! List) {
        return const EditionDownloadResult(error: 'bad_index');
      }
      entries = raw
          .whereType<Map<String, dynamic>>()
          .map(EditionIndexEntry.fromJson)
          .toList();
    } catch (_) {
      return const EditionDownloadResult(error: 'bad_index');
    }

    final newestBundled = bundledDates.isEmpty
        ? ''
        : bundledDates.reduce((a, b) => a.compareTo(b) > 0 ? a : b);
    final newestRemote = entries.isEmpty
        ? ''
        : entries.map((e) => e.date).reduce(
              (a, b) => a.compareTo(b) > 0 ? a : b,
            );
    final already = await downloadedDates();
    final downloaded = <String>[];
    final skipped = <String>[];
    for (final entry in entries) {
      if (entry.date.isEmpty || entry.file.isEmpty) continue;
      // The newest remote edition is re-fetched even when already
      // present (see 2b above), so a same-date correction lands.
      // It is skipped only when the phone already holds a NEWER
      // edition than the remote index (stale index).
      final isNewestRefresh = entry.date == newestRemote &&
          entry.date.compareTo(newestBundled) >= 0;
      if (!isNewestRefresh &&
          (entry.date.compareTo(newestBundled) <= 0 ||
              bundledDates.contains(entry.date) ||
              already.contains(entry.date))) {
        skipped.add(entry.date);
        continue;
      }
      final outcome = await _downloadOne(indexUri, entry);
      if (outcome == _DownloadOutcome.saved) {
        downloaded.add(entry.date);
      } else {
        skipped.add(entry.date);
      }
    }
    return EditionDownloadResult(
      downloaded: downloaded,
      skipped: skipped,
    );
  }

  /// Downloads, validates and saves one edition (+ its Bengali
  /// overlay when the server offers one). Returns [saved] when new
  /// or changed content was written, [unchanged] when the server
  /// copy is byte-identical to the file already on disk, and
  /// [failed] on any failure; a failed download never leaves a
  /// file behind.
  Future<_DownloadOutcome> _downloadOne(
      Uri indexUri, EditionIndexEntry entry) async {
    try {
      final fileUri = indexUri.resolve(entry.file);
      final raw = await _fetch(fileUri).timeout(
        const Duration(seconds: 20),
      );
      final json = jsonDecode(raw);
      if (json is! Map<String, dynamic>) return _DownloadOutcome.failed;
      final edition = validateDownloadedEdition(json);
      if (edition == null || edition.date != entry.date) {
        return _DownloadOutcome.failed;
      }
      final dir = await downloadedDir();
      final file = File('${dir.path}/data-${edition.date}.json');
      var changed = false;
      try {
        final existing = await file.readAsString();
        if (existing != raw) {
          await file.writeAsString(raw);
          changed = true;
        }
      } catch (_) {
        // No usable file on disk yet — write it.
        await file.writeAsString(raw);
        changed = true;
      }
      // Bengali overlay: optional — a missing one is fine, the
      // edition still shows (in English, like a bundled edition
      // without an overlay). A bad overlay is discarded, never saved.
      // A changed overlay is written even when the English file was
      // already identical.
      try {
        final bnUri = indexUri.resolve(entry.bnFile);
        final bnRaw = await _fetch(bnUri).timeout(
          const Duration(seconds: 20),
        );
        final bnJson = jsonDecode(bnRaw);
        if (bnJson is Map<String, dynamic>) {
          final bnFile = File('${dir.path}/bn-${edition.date}.json');
          try {
            final existingBn = await bnFile.readAsString();
            if (existingBn != bnRaw) {
              await bnFile.writeAsString(bnRaw);
              changed = true;
            }
          } catch (_) {
            await bnFile.writeAsString(bnRaw);
            changed = true;
          }
        }
      } catch (_) {
        // No overlay — fine.
      }
      return changed ? _DownloadOutcome.saved : _DownloadOutcome.unchanged;
    } catch (_) {
      return _DownloadOutcome.failed;
    }
  }
}

/// Outcome of one edition download attempt (see [_downloadOne]).
enum _DownloadOutcome {
  /// New or changed content was written to disk.
  saved,

  /// The server copy is byte-identical to the file already on disk.
  unchanged,

  /// The download or validation failed; nothing was written.
  failed,
}
