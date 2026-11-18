/// Story screen, learning-module-v2 (confirmed 2026-11-18).
///
/// Three data shapes, three screen states:
/// * v2 fixture built exactly to LEARNING_MODULE_MODEL_V2.md — all 11
///   sections, source as an object, list MCQ options with an int
///   `correct`, GK tables, a/b distinctions, institutions and
///   extra-knowledge as their own sections, list synonyms/antonyms.
/// * a real v1 renovated file (renovated-editions/data-2026-11-01.json)
///   — `exam_notes` still present, plain-string news source, map-keyed
///   MCQ options — must render without changes.
/// * Edition 11 (17 Nov, bundled) — NO learning_module at all — the
///   story renders with the existing sections only.
///
/// Banner states: image URL that loads (mock HTTP returns a 1x1 PNG)
/// shows the image + attribution + tap-to-open; an image URL that
/// fails (connection refused) and a story with no image both show the
/// typographic banner, with the headline exactly once. Light + dark +
/// 200% text, no overflow anywhere.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/screens/story_detail_screen.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

late AppState sharedState;

/// Bundled editions, loaded in setUpAll (real async). Awaiting an
/// asset load inside a testWidgets body hangs the fake-async zone
/// (see widget_test.dart), so no test awaits loadEditions() directly.
late List<Edition> bundledEditions;

Future<void> _pump(WidgetTester tester, {int steps = 40}) async {
  for (var i = 0; i < steps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Future<void> _pumpStory(
  WidgetTester tester,
  Edition edition,
  Story story, {
  bool dark = false,
  double textScale = 1.0,
}) async {
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
}

/// The 11-section module, exactly to the v2 spec. The ADP story
/// (Edition 11 CA03) is the model's golden test case.
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
      {
        'question': 'এডিপি কী?',
        'options': ['বার্ষিক উন্নয়ন কর্মসূচি', 'রাজস্ব নীতি', 'মুদ্রানীতি', 'বাণিজ্য নীতি'],
        'correct': 0,
        'explanation': 'এডিপি হলো বার্ষিক উন্নয়ন কর্মসূচি।',
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

/// A 1x1 transparent PNG, served for every HTTP request while the
/// override is installed — the story banner's image branch loads
/// without touching the network.
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
    SharedPreferences.setMockInitialValues({});
    sharedState = AppState();
    await sharedState.init();
    bundledEditions = (await loadEditions()).editions;
  });

  group('v2 model parsing', () {
    test('all 11 sections parse from the spec-exact fixture', () {
      final module = LearningModule.fromJson(_v2ModuleJson());
      expect(module.heroFigure, '৬.৫৩%');
      expect(module.heroLabel, contains('এডিপি'));
      expect(module.newsSummary, contains('৬.৫৩'));
      expect(module.newsSourceObj, isNotNull);
      expect(module.newsSourceObj!.publication, 'The Business Standard');
      expect(module.newsSourceObj!.date, '2026-11-15');
      expect(
        module.newsSourceObj!.url,
        'https://www.tbsnews.net/economy/adp-implementation-6853',
      );
      expect(module.verifiedFacts, hasLength(2));
      expect(module.verifiedFacts[0].label, 'বাস্তবায়ন হার');
      expect(module.verifiedFacts[0].date, '১৫ নভেম্বর ২০২৬');
      expect(module.topicGk, isNotNull);
      expect(module.topicGk!.tables, hasLength(1));
      expect(module.topicGk!.tables[0].title, 'ADP at a glance');
      expect(module.topicGk!.tables[0].rows[0].value,
          'Annual Development Programme');
      expect(module.topicGk!.distinctions, hasLength(1));
      expect(module.topicGk!.distinctions[0].a, 'ADP');
      expect(module.topicGk!.distinctions[0].b, 'RADP');
      expect(module.topicGk!.distinctions[0].points, hasLength(2));
      expect(module.institutions, hasLength(2));
      expect(module.institutions[0].name, 'Planning Commission');
      expect(module.institutions[0].role, 'এডিপি প্রণয়ন করে।');
      expect(module.institutions[1].fullName, contains('নির্বাহী কমিটি'));
      expect(module.extraKnowledge, hasLength(2));
      expect(module.extraKnowledge[0].term, 'Public Investment');
      expect(module.extraKnowledge[1].fullName,
          'Public Investment Management');
      expect(module.mcqPractice, hasLength(2));
      // List options + int correct normalise to A–D keys.
      expect(module.mcqPractice[0].options['B'], '৬.৫৩%');
      expect(module.mcqPractice[0].correct, 'B');
      expect(module.mcqPractice[1].correct, 'A');
      expect(module.mcqPractice[0].explanation, contains('৬.৫৩'));
      expect(module.writtenPrep, hasLength(2));
      expect(module.writtenPrep[0].isAnalytical, isFalse);
      expect(module.writtenPrep[1].isAnalytical, isTrue);
      expect(module.writtenPrep[1].outline, hasLength(3));
      expect(module.vocabulary, hasLength(1));
      expect(module.vocabulary[0].synonyms, ['execution', 'carrying out']);
      expect(module.vocabulary[0].antonyms, ['neglect']);
      expect(module.vocabulary[0].banglaMeaning, 'বাস্তবায়ন');
      expect(module.revision, isNotNull);
      expect(module.revision!.flashcards, hasLength(1));
      expect(module.revision!.nextRevision, ['এডিপি কী?']);
      expect(module.deepPrep, hasLength(2));
      // exam_notes is dropped in v2.
      expect(module.examNotes, isNull);
      expect(module.examNotesMarker, isNull);
    });

    test('v1 map-keyed MCQs and string synonyms still parse', () {
      final module = LearningModule.fromJson({
        'hero': {'figure': '৩০,০০০ টাকা', 'label': 'দাবি করা মজুরি'},
        'news_summary': 'পুরোনো আকারের সারাংশ।',
        'mcq_practice': [
          {
            'question': 'প্রশ্ন?',
            'options': {'A': 'ক', 'B': 'খ'},
            'correct': 'A',
            'explanation': 'ব্যাখ্যা।',
          },
        ],
        'vocabulary': [
          {
            'word': 'disruption',
            'bangla_meaning': 'বিঘ্ন',
            'synonym': 'interruption; disturbance',
            'antonym': 'continuity',
          },
        ],
        'exam_notes': {
          'points': ['পুরোনো নোট।'],
        },
      });
      expect(module.newsSummary, 'পুরোনো আকারের সারাংশ।');
      expect(module.newsSourceObj, isNull);
      expect(module.mcqPractice[0].options['A'], 'ক');
      expect(module.mcqPractice[0].correct, 'A');
      expect(module.vocabulary[0].synonyms,
          ['interruption', 'disturbance']);
      expect(module.examNotes, isNotNull);
      expect(module.examNotes!.bullets, ['পুরোনো নোট।']);
    });

    test('every story in all 16 converted v2 files parses', () {
      var stories = 0;
      for (var day = 1; day <= 16; day++) {
        final dd = day.toString().padLeft(2, '0');
        final file = File(
          '../editions/data-2026-11-$dd.json',
        );
        expect(file.existsSync(), isTrue, reason: file.path);
        final data =
            jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
        expect(data['renovation_format'], 'learning-module-v2',
            reason: file.path);
        final edition = Edition.fromJson(data);
        for (final story in edition.stories) {
          stories++;
          final m = story.learningModule;
          expect(m, isNotNull, reason: '${edition.date} ${story.id}');
          expect(m!.heroFigure, isNotNull,
              reason: '${edition.date} ${story.id}');
          // v2 news source is always an explicit object.
          expect(m.newsSourceObj, isNotNull,
              reason: '${edition.date} ${story.id}');
          expect(m.newsSourceObj!.publication, isNotEmpty);
          // 4 MCQs per story, list options + int correct in the file.
          expect(m.mcqPractice, hasLength(4),
              reason: '${edition.date} ${story.id}');
          expect(m.mcqPractice[0].options, hasLength(4));
          expect(m.mcqPractice[0].correct, isNotEmpty);
          // exam_notes is dropped in v2.
          expect(m.examNotes, isNull, reason: '${edition.date} ${story.id}');
          expect(m.examNotesMarker, isNull);
        }
      }
      expect(stories, 225);
    });

    test('converted v2 shape: sections are list-or-marker, never invented',
        () {
      // Institutions / extra knowledge / topic GK are a list, an
      // empty list (section omitted), or the unverified-marker
      // string — never anything else. 60 stories carry an empty
      // institutions list; 6 carry a marker per section.
      var emptyInstitutions = 0;
      var emptyExtra = 0;
      var markers = 0;
      for (var day = 1; day <= 16; day++) {
        final dd = day.toString().padLeft(2, '0');
        final file = File(
          '../editions/data-2026-11-$dd.json',
        );
        final data =
            jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
        final edition = Edition.fromJson(data);
        for (final story in edition.stories) {
          final m = story.learningModule!;
          if (m.institutions.isEmpty && m.institutionsMarker == null) {
            emptyInstitutions++;
          }
          if (m.extraKnowledge.isEmpty && m.extraKnowledgeMarker == null) {
            emptyExtra++;
          }
          if (m.topicGkMarker != null ||
              m.institutionsMarker != null ||
              m.extraKnowledgeMarker != null) {
            markers++;
          }
          // topic_gk keeps its v1 inner shape: intro/facts/
          // distinctions {title, text}/sources — never tables.
          if (m.topicGk != null) {
            expect(m.topicGk!.tables, isEmpty,
                reason: '${edition.date} ${story.id}');
          }
        }
      }
      expect(emptyInstitutions, 60);
      expect(emptyExtra, 2);
      expect(markers, greaterThan(0));
    });
  });

  group('story screen — v2 fixture', () {
    testWidgets('typographic fallback: headline once, all 11 sections',
        (tester) async {
      final story = Story.fromJson(
        _v2StoryJson(imageUrl: 'https://127.0.0.1:1/banner.jpg'),
      );
      await _pumpStory(tester, _editionFor(story), story);
      // Image fails (connection refused) -> typographic banner.
      await _pump(tester, steps: 10);
      expect(find.text('এডিপি বাস্তবায়ন সর্বনিম্ন ৬.৫৩ শতাংশে'),
          findsOneWidget);
      expect(find.text('৬.৫৩%'), findsWidgets);
      expect(find.text('শেখার মডিউল'), findsOneWidget);
      expect(find.text('সংবাদ'), findsOneWidget);
      expect(find.textContaining('The Business Standard'), findsWidgets);
      // No image branch: no attribution bar, no open-original button.
      expect(find.text('মূল সংবাদ খুলুন'), findsNothing);
      for (final heading in [
        'যাচাইকৃত তথ্য',
        'বিষয়ভিত্তিক সাধারণ জ্ঞান',
        'প্রতিষ্ঠানসমূহ',
        'আরও জানুন',
        'এমসিকিউ অনুশীলন',
        'লিখিত প্রস্তুতি',
        'শব্দভান্ডার',
        'পুনরালোচনা',
        'গভীর প্রস্তুতি',
      ]) {
        await tester.scrollUntilVisible(find.text(heading), 500);
        expect(find.text(heading), findsOneWidget, reason: heading);
      }
      // v2-only content renders.
      await tester.scrollUntilVisible(
          find.text('Planning Commission (পরিকল্পনা কমিশন)'), 500);
      expect(find.text('এডিপি প্রণয়ন করে।'), findsOneWidget);
      expect(find.text('ADP — RADP'), findsOneWidget);
      expect(find.text('ADP at a glance'), findsOneWidget);
      await tester.scrollUntilVisible(find.text('implementation'), 500);
      expect(find.textContaining('execution; carrying out'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('MCQ tap reveals the answer + explanation', (tester) async {
      final story = Story.fromJson(_v2StoryJson());
      await _pumpStory(tester, _editionFor(story), story);
      await tester.scrollUntilVisible(
          find.text('জুলাই–অক্টোবরে এডিপি বাস্তবায়নের হার কত?'), 500);
      // Option A ('৫.৫৩%') is unique to this MCQ; tapping the wrong
      // answer still reveals the correct answer + explanation.
      await tester.tap(find.text('৫.৫৩%'));
      await _pump(tester, steps: 5);
      expect(find.text('জুলাই–অক্টোবরে হার ৬.৫৩ শতাংশ।'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('banner image loads: attribution + tap-to-open',
        (tester) async {
      // NetworkImage caches one shared HttpClient per process, created
      // at the first image load (the binding's 400-mock in earlier
      // tests) — so a zone override cannot reach it. The debug hook
      // is the supported way to supply the client in tests.
      debugNetworkImageHttpClientProvider = () => _MockImageClient();
      addTearDown(() => debugNetworkImageHttpClientProvider = null);
      final story = Story.fromJson(
        _v2StoryJson(imageUrl: 'https://cdn.example.com/banner.jpg'),
      );
      await _pumpStory(tester, _editionFor(story), story);
      await _pump(tester, steps: 10);
      // Image branch: attribution bar with the publication, and the
      // open-original action. The headline stays below the banner.
      expect(find.text('ছবি: The Business Standard'), findsOneWidget);
      expect(find.text('মূল সংবাদ খুলুন'), findsOneWidget);
      expect(find.text('এডিপি বাস্তবায়ন সর্বনিম্ন ৬.৫৩ শতাংশে'),
          findsOneWidget);
      expect(tester.takeException(), isNull);
      // Reset inside the body: the framework checks painting debug
      // variables before tearDown callbacks run.
      debugNetworkImageHttpClientProvider = null;
    });

    testWidgets('v2 dark + 200% text: no overflow', (tester) async {
      final story = Story.fromJson(_v2StoryJson());
      await _pumpStory(
        tester,
        _editionFor(story),
        story,
        dark: true,
        textScale: 2.0,
      );
      await tester.scrollUntilVisible(find.text('গভীর প্রস্তুতি'), 800);
      await tester.scrollUntilVisible(
          find.text('বাংলাদেশের উন্নয়ন পরিকল্পনার ইতিহাস'), 500);
      expect(tester.takeException(), isNull);
    });
  });

  group('story screen — converted and no-module', () {
    testWidgets('converted story renders (institutions + extra, no exam notes)',
        (tester) async {
      final file = File('../editions/data-2026-11-01.json');
      final data =
          jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      expect(data['renovation_format'], 'learning-module-v2');
      final edition = Edition.fromJson(data);
      final story = edition.stories.first;
      expect(story.learningModule, isNotNull);
      expect(story.learningModule!.examNotes, isNull);
      await _pumpStory(tester, edition, story);
      await tester.scrollUntilVisible(find.text('প্রতিষ্ঠানসমূহ'), 500);
      expect(find.text('প্রতিষ্ঠানসমূহ'), findsOneWidget);
      await tester.scrollUntilVisible(find.text('আরও জানুন'), 500);
      expect(find.text('আরও জানুন'), findsOneWidget);
      expect(find.text('পরীক্ষার নোট'), findsNothing);
      await tester.scrollUntilVisible(find.text('গভীর প্রস্তুতি'), 800);
      expect(tester.takeException(), isNull);
    });

    testWidgets('converted story with no institutions omits the section',
        (tester) async {
      final file = File('../editions/data-2026-11-03.json');
      final data =
          jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
      final edition = Edition.fromJson(data);
      final story = edition.stories.first;
      expect(story.learningModule!.institutions, isEmpty);
      expect(story.learningModule!.institutionsMarker, isNull);
      await _pumpStory(tester, edition, story);
      expect(find.text('প্রতিষ্ঠানসমূহ'), findsNothing);
      await tester.scrollUntilVisible(find.text('আরও জানুন'), 800);
      expect(find.text('আরও জানুন'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('Edition 11 story (no module) renders as before',
        (tester) async {
      final edition =
          bundledEditions.firstWhere((e) => e.date == '2026-11-17');
      final story = edition.stories.first;
      expect(story.learningModule, isNull);
      await _pumpStory(tester, edition, story);
      expect(find.text('শেখার মডিউল'), findsNothing);
      expect(find.text(story.headlineIn('bn')), findsOneWidget);
      await tester.scrollUntilVisible(
          find.text('পুরো সারাংশ ও সূত্র দেখুন'), 500);
      expect(tester.takeException(), isNull);
    });

    testWidgets('Edition 11 story dark + 200%: no overflow',
        (tester) async {
      final edition =
          bundledEditions.firstWhere((e) => e.date == '2026-11-17');
      final story = edition.stories.first;
      await _pumpStory(
        tester,
        edition,
        story,
        dark: true,
        textScale: 2.0,
      );
      await tester.scrollUntilVisible(
          find.text('পুরো সারাংশ ও সূত্র দেখুন'), 800);
      expect(tester.takeException(), isNull);
    });
  });
}
