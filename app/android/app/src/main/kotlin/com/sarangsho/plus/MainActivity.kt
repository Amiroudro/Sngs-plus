package com.sarangsho.plus

import android.content.Intent
import android.speech.tts.TextToSpeech
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.util.Locale

class MainActivity : FlutterActivity() {
    private val channel = "com.sarangsho.plus/share"

    // --- Text-to-speech (Phase 3): the word speaker button. Android's
    // own TextToSpeech engine, no plugin, no download, no network.
    // The engine initialises asynchronously; the first speak waits
    // for it and answers its Result from the init callback.
    private val ttsChannel = "com.sarangsho.plus/tts"
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    private var pendingSpeak: Pair<String, MethodChannel.Result>? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        setupShareChannel(flutterEngine)
        setupTtsChannel(flutterEngine)
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }

    private fun speakNow(text: String): Boolean {
        return try {
            val engine = tts ?: return false
            engine.speak(
                text,
                TextToSpeech.QUEUE_FLUSH,
                null,
                "word-${System.currentTimeMillis()}",
            ) == TextToSpeech.SUCCESS
        } catch (e: Exception) {
            false
        }
    }

    private fun setupTtsChannel(flutterEngine: FlutterEngine) {
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, ttsChannel)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "speak" -> {
                        val text = call.argument<String>("text") ?: ""
                        if (text.isBlank()) {
                            result.success(false)
                            return@setMethodCallHandler
                        }
                        if (ttsReady) {
                            result.success(speakNow(text))
                        } else if (tts == null) {
                            pendingSpeak = text to result
                            tts = TextToSpeech(applicationContext) { status ->
                                if (status == TextToSpeech.SUCCESS) {
                                    val lang = tts?.setLanguage(Locale.US)
                                    if (lang == TextToSpeech.LANG_MISSING_DATA ||
                                        lang == TextToSpeech.LANG_NOT_SUPPORTED
                                    ) {
                                        ttsReady = false
                                        pendingSpeak?.second?.success(false)
                                        pendingSpeak = null
                                    } else {
                                        // Slightly slower than 1.0: the
                                        // listener is a learner, not a race.
                                        tts?.setSpeechRate(0.9f)
                                        tts?.setPitch(1.0f)
                                        ttsReady = true
                                        val pending = pendingSpeak
                                        pendingSpeak = null
                                        pending?.second?.success(
                                            speakNow(pending.first),
                                        )
                                    }
                                } else {
                                    pendingSpeak?.second?.success(false)
                                    pendingSpeak = null
                                }
                            }
                        } else {
                            // Init still in progress: drop the older
                            // request and keep the newest one.
                            pendingSpeak?.second?.success(false)
                            pendingSpeak = text to result
                        }
                    }

                    "stop" -> {
                        tts?.stop()
                        result.success(null)
                    }

                    else -> result.notImplemented()
                }
            }
    }

    private fun setupShareChannel(flutterEngine: FlutterEngine) {
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    // App-private cache dir, for the rendered share image.
                    "getCacheDir" -> result.success(cacheDir.absolutePath)

                    "shareImage" -> {
                        val path = call.argument<String>("path")
                        val text = call.argument<String>("text") ?: ""
                        if (path == null) {
                            result.success(false)
                            return@setMethodCallHandler
                        }
                        try {
                            val uri = FileProvider.getUriForFile(
                                this,
                                "$packageName.fileprovider",
                                File(path),
                            )
                            val intent = Intent(Intent.ACTION_SEND).apply {
                                type = "image/png"
                                putExtra(Intent.EXTRA_STREAM, uri)
                                putExtra(Intent.EXTRA_TEXT, text)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }
                            startActivity(
                                Intent.createChooser(intent, null),
                            )
                            result.success(true)
                        } catch (e: Exception) {
                            result.success(false)
                        }
                    }

                    "shareText" -> {
                        val text = call.argument<String>("text") ?: ""
                        try {
                            val intent = Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, text)
                            }
                            startActivity(
                                Intent.createChooser(intent, null),
                            )
                            result.success(true)
                        } catch (e: Exception) {
                            result.success(false)
                        }
                    }

                    else -> result.notImplemented()
                }
            }
    }
}
