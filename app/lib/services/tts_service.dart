/// Device text-to-speech for the word speaker button (Phase 3).
///
/// No plugin, no audio files, no network: [DeviceWordTts] speaks
/// through Android's own TextToSpeech engine via the MethodChannel
/// in MainActivity (`com.sarangsho.plus/tts`), the same channel
/// pattern the app already uses for sharing. A flutter_tts plugin
/// was tried first and dropped: its Gradle project needs AGP 8.13 +
/// Kotlin 2.2 artifacts that are not in this VM's Gradle cache and
/// cannot be downloaded through its proxy (connections reset), so
/// the build could not resolve them. The engine underneath is the
/// same Android TextToSpeech the plugin would have used.
///
/// Every failure — no engine, no English voice, no channel (other
/// platforms) — returns false instead of throwing, so the button
/// can show a short message and never crash. [WordTts] is an
/// interface so widget tests can inject a fake instead of a
/// platform channel.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

abstract class WordTts {
  /// Speaks [text] in English. Returns true when the engine accepted
  /// it, false when speaking is unavailable for any reason.
  Future<bool> speak(String text);

  /// Stops any speech in progress. Never throws.
  Future<void> stop();
}

class DeviceWordTts implements WordTts {
  static const _channel = MethodChannel('com.sarangsho.plus/tts');

  @override
  Future<bool> speak(String text) async {
    try {
      final ok = await _channel.invokeMethod<bool>('speak', {'text': text});
      return ok ?? false;
    } catch (e) {
      debugPrint('TTS unavailable: $e');
      return false;
    }
  }

  @override
  Future<void> stop() async {
    try {
      await _channel.invokeMethod<void>('stop');
    } catch (_) {
      // Stopping must never throw, even with no engine.
    }
  }
}
