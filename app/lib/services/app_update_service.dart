/// Self-update check (2013): the app asks GitHub whether a newer
/// app version exists, and offers a one-tap update.
///
/// How it works: on launch the app fetches a small `version.json`
/// from the public GitHub Pages site
/// (https://amiroudro.github.io/sarangsho-plus-editions/app/version.json)
/// — the same free hosting as the editions feed. The file names the
/// latest version code and the APK download URL (a GitHub Release
/// asset). When the latest code is newer than this build's, the home
/// screen shows a banner; tapping Update opens the APK URL in the
/// browser, which downloads it and hands it to Android's installer.
/// The reader taps Install once. No APKs in chat any more.
///
/// What it does NOT do: app code cannot arrive through the editions
/// feed — only the news data flows that way. A new feature still
/// needs a new app version; this check only makes the app fetch that
/// version itself instead of waiting for a file in chat.
///
/// The check never blocks launch and never fails loudly: no network,
/// a bad file, or a missing field just means no banner. The banner
/// is dismissible for the session; it returns on the next launch
/// while a newer version is still available.
///
/// [currentVersionCode] MUST match pubspec.yaml's `version:
/// 1.2.1+NNNN` build number. tools/build_release.sh checks the two
/// agree and stops the build on a mismatch (a stale constant would
/// either spam the banner forever or never show it).
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// The fetch function, injectable so tests can use a fake instead of
/// the real network. Same pattern as EditionDownloadService.
typedef UpdateFetcher = Future<String> Function(Uri url);

/// A newer app version, as advertised by version.json.
class UpdateInfo {
  /// The advertised build number (pubspec +NNNN).
  final int versionCode;

  /// The advertised version name (e.g. "1.2.1").
  final String versionName;

  /// Where to download the APK (a GitHub Release asset URL).
  final String apkUrl;

  /// Short human-readable note about the release, if any.
  final String? notes;

  const UpdateInfo({
    required this.versionCode,
    required this.versionName,
    required this.apkUrl,
    this.notes,
  });
}

class AppUpdateService {
  /// This build's version code — keep in sync with pubspec.yaml.
  static const int currentVersionCode = 2013;

  /// The one place the version-file URL lives. version.json sits
  /// next to the editions feed on the same Pages site.
  static const String versionUrl =
      'https://amiroudro.github.io/sarangsho-plus-editions/app/version.json';

  final UpdateFetcher _fetch;

  /// Tests pass a fake fetcher; production uses the real HttpClient
  /// fetcher.
  const AppUpdateService({UpdateFetcher? fetcher})
      : _fetch = fetcher ?? _httpFetch;

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

  /// Parses version.json text into an [UpdateInfo], or null when the
  /// file is malformed or missing what a safe update needs. Never
  /// throws.
  static UpdateInfo? parseVersionFile(String raw) {
    try {
      final json = jsonDecode(raw);
      if (json is! Map<String, dynamic>) return null;
      final code = json['latest_version_code'];
      final codeInt = code is int
          ? code
          : (code is String ? int.tryParse(code) : null);
      if (codeInt == null) return null;
      final name = json['latest_version_name'];
      final url = json['apk_url'];
      if (name is! String || name.isEmpty) return null;
      if (url is! String || url.isEmpty) return null;
      final uri = Uri.tryParse(url);
      if (uri == null ||
          !uri.hasScheme ||
          (uri.scheme != 'http' && uri.scheme != 'https') ||
          uri.host.isEmpty) {
        return null;
      }
      final notes = json['notes'];
      return UpdateInfo(
        versionCode: codeInt,
        versionName: name,
        apkUrl: url,
        notes: notes is String && notes.isNotEmpty ? notes : null,
      );
    } catch (_) {
      return null;
    }
  }

  /// Fetches version.json and returns the [UpdateInfo] when a NEWER
  /// version than this build is advertised, null otherwise (up to
  /// date, unreachable, or a bad file). Never throws.
  Future<UpdateInfo?> checkForUpdate() async {
    try {
      final uri = Uri.parse(versionUrl);
      final raw = await _fetch(uri).timeout(
        const Duration(seconds: 20),
      );
      final info = parseVersionFile(raw);
      if (info == null) return null;
      if (info.versionCode <= currentVersionCode) return null;
      return info;
    } catch (_) {
      return null;
    }
  }
}
