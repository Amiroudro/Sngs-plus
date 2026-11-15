/// Sharing without any new dependency: a minimal MethodChannel to the
/// native share sheet (ACTION_SEND). No share plugin is used — the
/// lightest free option is no plugin at all, and this keeps the APK
/// small. Implemented in MainActivity (Kotlin) + FileProvider.
library;

import 'package:flutter/services.dart';

class ShareService {
  static const _channel = MethodChannel('com.sarangsho.plus/share');

  /// App-private cache directory, for writing a rendered share image.
  static Future<String?> cacheDir() async {
    try {
      return await _channel.invokeMethod<String>('getCacheDir');
    } catch (_) {
      return null;
    }
  }

  /// Share an image file through the system share sheet.
  static Future<bool> shareImage(String path, String text) async {
    try {
      final ok = await _channel.invokeMethod<bool>(
        'shareImage',
        {'path': path, 'text': text},
      );
      return ok ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Share plain text through the system share sheet.
  static Future<bool> shareText(String text) async {
    try {
      final ok = await _channel.invokeMethod<bool>(
        'shareText',
        {'text': text},
      );
      return ok ?? false;
    } catch (_) {
      return false;
    }
  }
}
