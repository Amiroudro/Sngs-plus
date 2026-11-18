/// Story screen golden screenshots (2.0): the top of the story in
/// every banner/state combination, plus the module mid-section.
///
/// Light + dark, small phone (390x844), and 200% text scale. First
/// run creates the goldens:
///   flutter test test/story_screen_golden_test.dart --update-goldens
/// Then READ every PNG in test/goldens/story/ yourself and fix any
/// overflow, invisible text or clipped label before reporting.
/// These tests assert no overflow (takeException null) as well as the
/// golden match, so a later visual regression fails loudly.
///
/// States:
/// * v2 fixture (spec-exact, all 11 sections) with a failing image
///   URL -> typographic banner. This asynchronous network-failure
///   fallback is layout-checked rather than pixel-golden tested.
/// * v2 fixture with the image mocked (1x1 PNG via the debug hook)
///   -> image banner + attribution bar.
/// * real v1 renovated story (1 Nov) -> exam-notes shape, fallback.
/// * Edition 11 story (17 Nov, no module) -> no module section.
/// The converted v2 editions had not landed when these goldens were
/// made; the fixture stands in for them exactly to the spec.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/screens/story_detail_screen.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;
late List<Edition> bundledEditions;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

/// The 11-section module, exactly to LEARNING_MODULE_MODEL_V2.md.
/// (Same fixture as story_screen_v2_test.dart, kept in sync.)
Map<String, dynamic> _v2ModuleJson() {
  return {
    'hero': {
      'figure': '৬.৫৩%',
      'label': 'জুলাই–অক্টোবরে এডিপি বাস্তবায়নের হার',
    },
    'news_summary': {
      'text':
          'জুলাই–অক্টোবরে বার্ষিক উন্নয়ন কর্মসূচির বাস্তবায়ন হার ৬.৫৩ শতাংশে নেমেছে, যা এযাবৎকালের সর্বনিম্ন।',
      'source': {
        'publication': 'The Business Standard',
        'date': '2026-11-15',
        'url': 'https://www.tbsnews.net/economy/adp-implementation-6853',
      },
    },
    'verified_facts': [
      {
        'label': 'বাস্তবায়ন হার',
        'value': '৬.৫৩%',
        'date': '১৫ নভেম্বর ২০২৬',
        'source': 'TBS',
      },
      {
        'label': 'ব্যয়',
        'value': '২০,১৬০ কোটি টাকা',
        'date': '১৫ নভেম্বর ২০২৬',
        'source': 'TBS',
      },
    ],
    'topic_gk': {
      'intro': 'এডিপি হলো সরকারের বার্ষিক উন্নয়ন কর্মসূচি।',
      'tables': [
        {
          'title': 'ADP at a glance',
          'rows': [
            {'label': 'পূর্ণরূপ', 'value': 'Annual Development Programme'},
          ],
        },
      ],
      'distinctions': [
        {
          'a': 'ADP',
          'b': 'RADP',
          'points': ['এডিপি বছরের শুরুতে অনুমোদিত হয়।', 'আরএডিপি সংশোধিত রূপ।'],
        },
      ],
      'sources': [
        {'name': 'Banglapedia — ADP', 'url': 'https://en.banglapedia.org/'},
      ],
    },
    'institutions': [
      {
        'name': 'Planning Commission',
        'full_name': 'পরিকল্পনা কমিশন',
        'role': 'এডিপি প্রণয়ন করে।',
        'source': 'plancomm.gov.bd',
      },
      {
        'name': 'ECNEC',
        'full_name': 'জাতীয় অর্থনৈতিক পরিষদের নির্বাহী কমিটি',
        'role': 'বড় প্রকল্প অনুমোদন দেয়।',
      },
    ],
    'extra_knowledge': [
      {
        'term': 'Public Investment',
        'meaning': 'সরকারি বিনিয়োগ।',
        'source': 'Banglapedia',
      },
      {
        'term': 'PIM',
        'full_name': 'Public Investment Management',
        'meaning': 'সরকারি বিনিয়োগ ব্যবস্থাপনা।',
      },
    ],
    'mcq_practice': [
      {
        'question': 'জুলাই–অক্টোবরে এডিপি বাস্তবায়নের হার কত?',
        'options': ['৫.৫৩%', '৬.৫৩%', '৭.৫৩%', '৮.৫৩%'],
        'correct': 1,
        'explanation': 'জুলাই–অক্টোবরে হার ৬.৫৩ শতাংশ।',
      },
    ],
    'written_prep': {
      'short': {
        'question': 'এডিপি কীভাবে প্রণয়ন হয়?',
        'outline': ['পরিকল্পনা কমিশন খসড়া তৈরি করে।', 'এনইসি অনুমোদন দেয়।'],
      },
      'analytical': {
        'question': 'এডিপি বাস্তবায়ন কম হলে অর্থনীতিতে কী প্রভাব পড়ে?',
        'outline': ['প্রকল্প বিলম্বিত হয়।', 'কর্মসংস্থান কমে।', 'প্রবৃদ্ধি মন্থর হয়।'],
      },
    },
    'vocabulary': [
      {
        'word': 'implementation',
        'meaning_bn': 'বাস্তবায়ন',
        'example': 'The implementation of the ADP slowed down.',
        'synonyms': ['execution', 'carrying out'],
        'antonyms': ['neglect'],
      },
    ],
    'revision': {
      'flashcards': [
        {'q': 'এডিপি বাস্তবায়নের হার কত?', 'a': '৬.৫৩%।'},
      ],
      'next_revision': ['এডিপি কী?'],
    },
    'deep_prep': [
      'বাংলাদেশের উন্নয়ন পরিকল্পনার ইতিহাস',
      'পঞ্চবার্ষিক পরিকল্পনা',
    ],
  };
}

Map<String, dynamic> _v2StoryJson({String? imageUrl}) {
  return {
    'id': 'CA03',
    'headline': 'এডিপি বাস্তবায়ন সর্বনিম্ন ৬.৫৩ শতাংশে',
    'category': 'Economy & Banking',
    'event_date': '2026-11-15',
    'article_date': '2026-11-15',
    'summary': 'জুলাই–অক্টোবরে এডিপি বাস্তবায়ন ৬.৫৩ শতাংশ।',
    'why_it_matters': 'পরীক্ষায় আসার মতো সংখ্যা।',
    'exam_facts': 'বাস্তবায়ন হার ৬.৫৩ শতাংশ।',
    'exam_relevance': 'High',
    'key_people': '',
    'figures': '৬.৫৩%',
    'sources': [
      {
        'publication': 'The Business Standard',
        'headline': 'ADP implementation hits record low',
        'date': '2026-11-15',
        'url': 'https://www.tbsnews.net/economy/adp-implementation-6853',
      },
    ],
    if (imageUrl != null) 'image_url': imageUrl,
    'one_liner': 'এডিপি বাস্তবায়ন ৬.৫৩ শতাংশে নেমেছে।',
    'key_facts': [
      {'label': 'হার', 'value': '৬.৫৩%', 'original': '6.53%'},
    ],
    'what_happened': ['জুলাই–অক্টোবরে বাস্তবায়ন কমেছে।'],
    'exam_qa': [
      {'q': 'বাস্তবায়ন হার কত?', 'a': '৬.৫৩%।'},
      {'q': 'কোন সংবাদপত্রে এসেছে?', 'a': 'দ্য বিজনেস স্ট্যান্ডার্ড।'},
    ],
    'recall_cards': [
      {'cloze': 'বাস্তবায়ন হার ______ শতাংশ।', 'answer': '৬.৫৩'},
    ],
    'keywords': ['এডিপি'],
    'detail': 'বিস্তারিত সারাংশ।',
    'learning_module': _v2ModuleJson(),
  };
}

Edition _editionFor(Story story) {
  return Edition(
    date: '2026-11-17',
    stories: [story],
    words: const [],
    revisionWords: const [],
    phrases: const [],
    mcqs: const [],
    sources: const [],
    counts: const {},
  );
}

class _MockImageResponse extends Stream<List<int>>
    implements HttpClientResponse {
  static final _bytes = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  );

  @override
  StreamSubscription<List<int>> listen(
    void Function(List<int> event)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) =>
      Stream<List<int>>.value(_bytes).listen(
        onData,
        onError: onError,
        onDone: onDone,
        cancelOnError: cancelOnError,
      );

  @override
  int get statusCode => 200;

  @override
  int get contentLength => _bytes.length;

  @override
  HttpClientResponseCompressionState get compressionState =>
      HttpClientResponseCompressionState.notCompressed;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _MockImageRequest implements HttpClientRequest {
  @override
  Future<HttpClientResponse> close() async => _MockImageResponse();

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _MockImageClient implements HttpClient {
  @override
  Future<HttpClientRequest> getUrl(Uri url) async => _MockImageRequest();

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  setUpAll(() async {
    // Flutter widget tests use the test font unless app fonts are loaded
    // explicitly. Load the same bundled Bengali families used by the app
    // before capturing story goldens, otherwise Bengali glyphs render as
    // missing-glyph boxes and the screenshots do not represent the app.
    final hindSiliguri = FontLoader('HindSiliguri')
      ..addFont(rootBundle.load('assets/fonts/HindSiliguri-Regular.ttf'))
      ..addFont(rootBundle.load('assets/fonts/HindSiliguri-Bold.ttf'));
    await hindSiliguri.load();

    final notoSerifBengali = FontLoader('NotoSerifBengali')
      ..addFont(rootBundle.load('assets/fonts/NotoSerifBengali-Bold.ttf'));
    await notoSerifBengali.load();

    SharedPreferences.setMockInitialValues({});
    sharedState = AppState();
    await sharedState.init();
    bundledEditions = (await loadEditions()).editions;
  });

  Future<void> shot(
    WidgetTester tester,
    String name,
    Edition edition,
    Story story, {
    bool dark = false,
    double textScale = 1.0,
    String? scrollTo,
    bool compareGolden = true,
  }) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
        child: MaterialApp(
          theme: buildLightTheme(),
          darkTheme: buildDarkTheme(),
          themeMode: dark ? ThemeMode.dark : ThemeMode.light,
          home: StoryDetailScreen(
            edition: edition,
            story: story,
            state: sharedState,
          ),
        ),
      ),
    );
    await _pump(tester);
    // The banner image (when mocked) finishes on real async, not
    // fake test time: let it land before the screenshot, or the
    // golden captures the loading placeholder instead of the image.
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 500));
    });
    await _pump(tester, steps: 5);
    if (scrollTo != null) {
      await tester.scrollUntilVisible(find.text(scrollTo), 500);
      await _pump(tester, steps: 5);
    }
    expect(tester.takeException(), isNull);
    if (compareGolden) {
      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('goldens/story/$name.png'),
      );
    }
  }

  Story v2Story({String? imageUrl}) =>
      Story.fromJson(_v2StoryJson(imageUrl: imageUrl));

  group('story goldens', () {
    testWidgets('v2 fallback light small', (t) async {
      final story = v2Story(imageUrl: 'https://127.0.0.1:1/banner.jpg');
      await shot(t, 'story_v2_fallback_light_small', _editionFor(story), story,
        compareGolden: false);
    });
    testWidgets('v2 fallback dark small', (t) async {
      final story = v2Story(imageUrl: 'https://127.0.0.1:1/banner.jpg');
      await shot(
        t,
        'story_v2_fallback_dark_small',
        _editionFor(story),
        story,
        dark: true,
        compareGolden: false);
    });
    testWidgets('v2 fallback light 200pct', (t) async {
      final story = v2Story(imageUrl: 'https://127.0.0.1:1/banner.jpg');
      await shot(
        t,
        'story_v2_fallback_light_200pct',
        _editionFor(story),
        story,
        textScale: 2.0,
        compareGolden: false);
    });
    testWidgets('v2 image light small', (t) async {
      debugNetworkImageHttpClientProvider = () => _MockImageClient();
      addTearDown(() => debugNetworkImageHttpClientProvider = null);
      final story =
          v2Story(imageUrl: 'https://cdn.example.com/banner.jpg');
      await shot(t, 'story_v2_image_light_small', _editionFor(story), story);
      debugNetworkImageHttpClientProvider = null;
    });
    testWidgets('v2 image light 200pct', (t) async {
      // The two-row attribution bar at 200%: credit wraps, the
      // open-original button wraps, nothing overflows.
      debugNetworkImageHttpClientProvider = () => _MockImageClient();
      addTearDown(() => debugNetworkImageHttpClientProvider = null);
      final story =
          v2Story(imageUrl: 'https://cdn.example.com/banner.jpg');
      await shot(
        t,
        'story_v2_image_light_200pct',
        _editionFor(story),
        story,
        textScale: 2.0,
      );
      debugNetworkImageHttpClientProvider = null;
    });
    testWidgets('v2 module mid light small', (t) async {
      final story = v2Story();
      await shot(
        t,
        'story_v2_module_light_small',
        _editionFor(story),
        story,
        scrollTo: 'এমসিকিউ অনুশীলন',
      );
    });
    testWidgets('v2 module mid dark small', (t) async {
      final story = v2Story();
      await shot(
        t,
        'story_v2_module_dark_small',
        _editionFor(story),
        story,
        dark: true,
        scrollTo: 'প্রতিষ্ঠানসমূহ',
      );
    });
    testWidgets('converted v2 light small', (t) async {
      // A real converted story (1 Nov, renovation_format
      // "learning-module-v2"): institutions + extra knowledge as
      // their own sections, news source as an object, list MCQs.
      final file = File('../editions/data-2026-11-01.json');
      final data =
          jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      final edition = Edition.fromJson(data);
      await shot(
        t,
        'story_v2_converted_light_small',
        edition,
        edition.stories.first,
      );
    });
    testWidgets('no-module light small', (t) async {
      final edition =
          bundledEditions.firstWhere((e) => e.date == '2026-11-17');
      await shot(
        t,
        'story_nomodule_light_small',
        edition,
        edition.stories.first,
      );
    });
    testWidgets('no-module dark 200pct', (t) async {
      final edition =
          bundledEditions.firstWhere((e) => e.date == '2026-11-17');
      await shot(
        t,
        'story_nomodule_dark_200pct',
        edition,
        edition.stories.first,
        dark: true,
        textScale: 2.0,
      );
    });
  });
}
