/// Self-update tests (2013): the GitHub version check. The service
/// uses an injected fetcher — no test ever touches the real network.
/// Run with `flutter test test/app_update_test.dart`.
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/services/app_update_service.dart';

/// A version.json body advertising the given code, name and URL.
String versionJson({
  required int code,
  String name = '1.2.1',
  String url = 'https://github.com/Amiroudro/sarangsho-plus-editions/releases/download/v1.2.1/app-release.apk',
  String? notes,
}) {
  final m = <String, dynamic>{
    'latest_version_code': code,
    'latest_version_name': name,
    'apk_url': url,
  };
  if (notes != null) m['notes'] = notes;
  return jsonEncode(m);
}

void main() {
  group('app update: parseVersionFile', () {
    test('parses a well-formed version file', () {
      final info = AppUpdateService.parseVersionFile(
        versionJson(code: 2014, notes: 'Auto-switch fix.'),
      );
      expect(info, isNotNull);
      expect(info!.versionCode, 2014);
      expect(info.versionName, '1.2.1');
      expect(info.apkUrl, contains('app-release.apk'));
      expect(info.notes, 'Auto-switch fix.');
    });

    test('accepts the version code as a string', () {
      final info = AppUpdateService.parseVersionFile(
        '{"latest_version_code": "2014", '
        '"latest_version_name": "1.2.1", '
        '"apk_url": "https://example.com/app.apk"}',
      );
      expect(info, isNotNull);
      expect(info!.versionCode, 2014);
    });

    test('rejects a missing version code', () {
      expect(
        AppUpdateService.parseVersionFile(
          '{"latest_version_name": "1.2.1", '
          '"apk_url": "https://example.com/app.apk"}',
        ),
        isNull,
      );
    });

    test('rejects a missing or non-http apk url', () {
      expect(
        AppUpdateService.parseVersionFile(
          versionJson(code: 2014, url: ''),
        ),
        isNull,
      );
      expect(
        AppUpdateService.parseVersionFile(
          versionJson(code: 2014, url: 'ftp://example.com/app.apk'),
        ),
        isNull,
      );
      expect(
        AppUpdateService.parseVersionFile(
          '{"latest_version_code": 2014, '
          '"latest_version_name": "1.2.1"}',
        ),
        isNull,
      );
    });

    test('rejects malformed JSON and non-object bodies', () {
      expect(AppUpdateService.parseVersionFile('not json'), isNull);
      expect(AppUpdateService.parseVersionFile('[1, 2, 3]'), isNull);
      expect(AppUpdateService.parseVersionFile(''), isNull);
    });
  });

  group('app update: checkForUpdate', () {
    test('returns the info when a newer version is advertised', () async {
      final svc = AppUpdateService(
        fetcher: (_) async => versionJson(code: 2014),
      );
      final info = await svc.checkForUpdate();
      expect(info, isNotNull);
      expect(info!.versionCode, 2014);
    });

    test('returns null when the advertised version is this build', () async {
      final svc = AppUpdateService(
        fetcher: (_) async =>
            versionJson(code: AppUpdateService.currentVersionCode),
      );
      expect(await svc.checkForUpdate(), isNull);
    });

    test('returns null when the advertised version is older', () async {
      final svc = AppUpdateService(
        fetcher: (_) async => versionJson(code: 2012),
      );
      expect(await svc.checkForUpdate(), isNull);
    });

    test('returns null when the fetch fails', () async {
      final svc = AppUpdateService(
        fetcher: (_) async => throw Exception('no network'),
      );
      expect(await svc.checkForUpdate(), isNull);
    });

    test('returns null on a malformed version file', () async {
      final svc = AppUpdateService(
        fetcher: (_) async => 'not json',
      );
      expect(await svc.checkForUpdate(), isNull);
    });

    test('current version code is 2013 (pubspec 1.2.1+2013)', () {
      expect(AppUpdateService.currentVersionCode, 2013);
    });
  });
}
