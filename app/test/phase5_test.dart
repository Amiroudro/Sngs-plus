/// Phase 5 unit tests (no widgets): new story fields, the 7-edition
/// revision window, the edition-download service (mocked fetcher,
/// never the real network), and the loader's downloaded-over-bundled
/// preference. Run with `flutter test test/phase5_test.dart`.
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/data/story_layout.dart';
import 'package:sarangsho_plus/models.dart';
import 'package:sarangsho_plus/services/edition_download_service.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// A story JSON with the Phase 5 fields filled in.
Map<String, dynamic> newFieldStoryJson() => {
      'id': 'CA99',
      'headline': 'Test headline',
      'category': 'Bangladesh',
      'summary':
          'First summary sentence here. Second summary sentence here. Third one too.',
      'why_it_matters': 'Why this matters for the exam.',
      'exam_facts': 'Old fact one; Old fact two.',
      'figures': 'Old figure 100 items shipped across regions.',
      'sources': [],
      'one_liner': 'Authored one-liner, short and exact.',
      'key_facts': [
        {'label': 'Authored label', 'value': '৫০০ কোটি টাকা', 'original': 'Tk 5 bn'},
        {'label': 'Second', 'value': '৭৫ শতাংশ'},
      ],
      'what_happened': ['Authored bullet one.', 'Authored bullet two.'],
      'exam_qa': [
        {'q': 'Authored question?', 'a': 'Authored answer.'},
      ],
      'recall_cards': [
        {'cloze': 'The value was ______ কোটি টাকা.', 'answer': '৫০০'},
      ],
      'keywords': ['test', 'bangladesh'],
      'detail': 'Authored full detail text.',
    };

/// A minimal valid edition JSON for a given date.
Map<String, dynamic> editionJson(String date, {String headline = 'H'}) => {
      'edition_date': date,
      'stories': [
        {
          'id': 'S01',
          'headline': headline,
          'category': 'Bangladesh',
          'summary': 'Summary.',
          'sources': [],
        },
      ],
      'words': [],
      'phrases': [],
      'mcqs': [],
    };

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('compact edition index parsing', () {
    test('derives bundled English and Bangla filenames from the date', () {
      final entry = EditionIndexEntry.fromJson({
        'edition_date': '2026-11-15',
        'status': 'published',
      });
      expect(entry.date, '2026-11-15');
      expect(entry.file, 'data-2026-11-15.json');
      expect(entry.bnFile, 'bn-2026-11-15.json');
    });

    test('preserves an explicit filename from the remote index', () {
      final entry = EditionIndexEntry.fromJson({
        'edition_date': '2026-11-15',
        'file': 'data-custom.json',
        'status': 'published',
      });
      expect(entry.file, 'data-custom.json');
      expect(entry.bnFile, 'bn-custom.json');
    });

    test('missing date and filename remain empty', () {
      final entry = EditionIndexEntry.fromJson({'status': 'published'});
      expect(entry.date, '');
      expect(entry.file, '');
    });
  });

  group('phase5: new story fields', () {
    test('parses all new fields', () {
      final story = Story.fromJson(newFieldStoryJson());
      expect(story.oneLiner, 'Authored one-liner, short and exact.');
      expect(story.keyFacts.length, 2);
      expect(story.keyFacts.first.label, 'Authored label');
      expect(story.keyFacts.first.value, '৫০০ কোটি টাকা');
      expect(story.keyFacts.first.original, 'Tk 5 bn');
      expect(story.whatHappened,
          ['Authored bullet one.', 'Authored bullet two.']);
      expect(story.examQa.length, 1);
      expect(story.examQa.first.q, 'Authored question?');
      expect(story.recallCards.first.answer, '৫০০');
      expect(story.keywords, ['test', 'bangladesh']);
      expect(story.detail, 'Authored full detail text.');
    });

    test('old files without the fields parse with empty defaults', () {
      final story = Story.fromJson({
        'id': 'CA01',
        'headline': 'Old headline',
        'category': 'Bangladesh',
        'summary': 'Old summary.',
        'sources': [],
      });
      expect(story.oneLiner, isNull);
      expect(story.keyFacts, isEmpty);
      expect(story.whatHappened, isEmpty);
      expect(story.examQa, isEmpty);
      expect(story.recallCards, isEmpty);
      expect(story.keywords, isEmpty);
      expect(story.detail, isNull);
      // And the layout still derives everything from the old fields.
      final layout = buildStoryLayout(story, 'en');
      expect(layout.oneLiner, 'Old summary.');
      expect(layout.fullSummary, 'Old summary.');
    });

    test('Bengali overlay new fields parse, English falls back', () {
      final bn = BnStory.fromJson({
        'headline': 'বাংলা শিরোনাম',
        'one_liner': 'বাংলা এক লাইন।',
        'key_facts': [
          {'label': 'বাংলা লেবেল', 'value': '১০০ কোটি টাকা'},
        ],
        'what_happened': ['বাংলা বুলেট।'],
      });
      expect(bn.oneLiner, 'বাংলা এক লাইন।');
      expect(bn.keyFacts!.first.value, '১০০ কোটি টাকা');
      expect(bn.examQa, isNull);
      expect(bn.detail, isNull);
    });

    test('layout reads authored fields when present', () {
      final story = Story.fromJson(newFieldStoryJson());
      final layout = buildStoryLayout(story, 'en');
      expect(layout.oneLiner, 'Authored one-liner, short and exact.');
      expect(layout.bullets,
          ['Authored bullet one.', 'Authored bullet two.']);
      expect(layout.tiles.length, 2);
      expect(layout.tiles.first.label, 'Authored label');
      expect(layout.tiles.first.value, '৫০০ কোটি টাকা');
      expect(layout.qa.length, 1);
      expect(layout.qa.first.question, 'Authored question?');
      expect(layout.qa.first.answer, 'Authored answer.');
      expect(layout.cloze.length, 1);
      expect(layout.cloze.first.text,
          'The value was ______ কোটি টাকা.');
      expect(layout.cloze.first.answer, '৫০০');
      expect(layout.fullSummary, 'Authored full detail text.');
    });

    test('empty new fields count as absent (2 Nov CA04 shape)', () {
      // The data carries empty new fields by design on some stories:
      // one_liner "", key_facts [], what_happened [], exam_qa [],
      // recall_cards [], keywords ["jobs & education"] and NO detail
      // key at all. The layout must derive from the old fields, and
      // the collapsed section must show the summary, not "".
      final story = Story.fromJson({
        'id': 'CA04',
        'headline': 'Empty fields headline',
        'category': 'Jobs & Education',
        'summary':
            'First summary sentence here. Second summary sentence here.',
        'why_it_matters': 'Why it matters.',
        'exam_facts': 'Old fact one; Old fact two.',
        'figures': 'Old figure 100 items shipped across regions.',
        'sources': [],
        'one_liner': '',
        'key_facts': [],
        'what_happened': [],
        'exam_qa': [],
        'recall_cards': [],
        'keywords': ['jobs & education'],
      });
      expect(story.oneLinerIn('en'), isNull);
      expect(story.detailIn('en'), isNull);
      expect(story.keyFactsIn('en'), isEmpty);
      expect(story.examQaIn('en'), isEmpty);
      expect(story.recallCardsIn('en'), isEmpty);
      final layout = buildStoryLayout(story, 'en');
      expect(layout.oneLiner, 'First summary sentence here.');
      expect(layout.bullets, ['Second summary sentence here.']);
      expect(layout.tiles, isNotEmpty);
      expect(layout.fullSummary, isNotEmpty);
      expect(
        layout.fullSummary,
        'First summary sentence here. Second summary sentence here.',
      );
    });

    test('layout falls back per-section when only some fields exist', () {
      final json = newFieldStoryJson()
        ..remove('key_facts')
        ..remove('exam_qa')
        ..remove('recall_cards');
      final story = Story.fromJson(json);
      final layout = buildStoryLayout(story, 'en');
      // Authored sections stay authored…
      expect(layout.oneLiner, 'Authored one-liner, short and exact.');
      expect(layout.bullets, ['Authored bullet one.', 'Authored bullet two.']);
      expect(layout.fullSummary, 'Authored full detail text.');
      // …while the missing ones derive from the old fields.
      expect(layout.tiles, isNotEmpty);
      expect(layout.qa, isNotEmpty);
      expect(layout.cloze, isNotEmpty);
    });
  });

  group('phase5: revision window (last 7 editions)', () {
    late AppState state;
    late List<Edition> editions;

    Edition fakeEdition(String date, String headword) => Edition(
          date: date,
          stories: const [],
          words: [VocabWord(headword: headword)],
          revisionWords: const [],
          phrases: const [],
          mcqs: const [],
          sources: const [],
          counts: const {},
        );

    setUp(() async {
      SharedPreferences.setMockInitialValues({});
      state = AppState();
      await state.init();
      editions = [
        for (var i = 1; i <= 8; i++)
          fakeEdition(
            '2026-11-0$i',
            ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',
             'golf', 'hotel'][i - 1],
          ),
      ];
      await state.setEditions(editions, 0, null);
    });

    test('7-editions-back boundary: in-window due, out-of-window out',
        () async {
      // alpha (1 Nov, 8 editions back from 8 Nov): unknown on 1 Nov,
      // due 2 Nov — due, but outside the 7-edition window.
      await state.setWordResult(
        '2026-11-01', 'alpha', false, now: DateTime(2026, 11, 1),
      );
      // bravo (2 Nov, exactly 7 editions back): unknown on 2 Nov,
      // due 3 Nov — due AND inside the window.
      await state.setWordResult(
        '2026-11-02', 'bravo', false, now: DateTime(2026, 11, 2),
      );
      // hotel (8 Nov): unknown today, due tomorrow — not due yet.
      await state.setWordResult(
        '2026-11-08', 'hotel', false, now: DateTime(2026, 11, 8),
      );
      // golf (7 Nov): marked known — never in revision.
      await state.setWordResult('2026-11-07', 'golf', true);

      final due = state.dueRevisionWords(now: DateTime(2026, 11, 8));
      final words = due.map((e) => e.word.headword).toList();
      expect(words, contains('bravo'));
      expect(words, isNot(contains('alpha')),
          reason: '1 Nov is 8 editions back — outside the window');
      expect(words, isNot(contains('hotel')),
          reason: 'due tomorrow, not today');
      expect(words, isNot(contains('golf')), reason: 'marked known');
      // The per-edition method is unchanged: alpha IS due for 1 Nov.
      expect(
        state.dueWordsFor(editions[0], now: DateTime(2026, 11, 8))
            .map((w) => w.headword),
        contains('alpha'),
      );
      // The window itself is the 7 newest dates.
      expect(
        state.revisionWindow.map((e) => e.date).toList(),
        [
          '2026-11-08', '2026-11-07', '2026-11-06', '2026-11-05',
          '2026-11-04', '2026-11-03', '2026-11-02',
        ],
      );
    });

    test('overdue first across editions, revision words still feed the pool',
        () async {
      // charlie (3 Nov) unknown 1 Nov -> due 2 Nov (most overdue).
      await state.setWordResult(
        '2026-11-03', 'charlie', false, now: DateTime(2026, 11, 1),
      );
      // bravo (2 Nov) unknown 2 Nov -> due 3 Nov.
      await state.setWordResult(
        '2026-11-02', 'bravo', false, now: DateTime(2026, 11, 2),
      );
      final due = state.dueRevisionWords(now: DateTime(2026, 11, 8));
      expect(
        due.map((e) => e.word.headword).toList(),
        ['charlie', 'bravo'],
        reason: 'earliest due date first, across editions',
      );
      expect(due.first.edition.date, '2026-11-03');
    });
  });

  group('phase5: download service', () {
    late Directory tempDir;

    setUp(() async {
      SharedPreferences.setMockInitialValues({});
      tempDir = await Directory.systemTemp.createTemp('sp5-download-');
    });

    tearDown(() async {
      if (await tempDir.exists()) await tempDir.delete(recursive: true);
    });

    test('no stored URL: the default Pages URL is used, no throw',
        () async {
      var calls = 0;
      var indexFetchedFrom = '';
      final service = EditionDownloadService(
        fetcher: (url) async {
          calls++;
          if (url.toString() == EditionDownloadService.defaultIndexUrl) {
            indexFetchedFrom = url.toString();
          }
          // Index listing only already-bundled dates: nothing new.
          return jsonEncode({
            'editions': [
              {
                'edition_date': '2026-11-08',
                'file': 'data-2026-11-08.json',
              },
            ],
          });
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl('');
      expect(
        await EditionDownloadService.getEffectiveIndexUrl(),
        EditionDownloadService.defaultIndexUrl,
      );
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.notConfigured, isFalse);
      expect(result.error, isNull);
      expect(indexFetchedFrom, EditionDownloadService.defaultIndexUrl);
      // Index + the newest entry's re-fetch (same-date corrections
      // must land); the body here is the index JSON, so it fails
      // validation and nothing is saved.
      expect(calls, 2);
      expect(result.downloaded, isEmpty);
    });

    test('a stored URL overrides the default', () async {
      const indexUrl = 'https://example.com/editions/index.json';
      var fetchedUrl = '';
      final service = EditionDownloadService(
        fetcher: (url) async {
          fetchedUrl = url.toString();
          return jsonEncode({'editions': []});
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      expect(
        await EditionDownloadService.getEffectiveIndexUrl(),
        indexUrl,
      );
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, isNull);
      expect(fetchedUrl, indexUrl);
      expect(
        fetchedUrl,
        isNot(EditionDownloadService.defaultIndexUrl),
      );
    });

    test('downloads + validates + saves a newer edition', () async {
      const indexUrl = 'https://example.com/editions/index.json';
      final edition = editionJson('2026-11-09', headline: 'New story');
      final service = EditionDownloadService(
        fetcher: (url) async {
          if (url.toString() == indexUrl) {
            return jsonEncode({
              'editions': [
                {
                  'edition_date': '2026-11-09',
                  'file': 'data-2026-11-09.json',
                  'status': 'published',
                },
              ],
            });
          }
          if (url.toString().endsWith('data-2026-11-09.json')) {
            return jsonEncode(edition);
          }
          throw const HttpException('404'); // no bn overlay offered
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, isNull);
      expect(result.downloaded, ['2026-11-09']);
      final saved = File(
        '${tempDir.path}/downloaded_editions/data-2026-11-09.json',
      );
      expect(await saved.exists(), isTrue);
      final parsed = jsonDecode(await saved.readAsString());
      expect(parsed['stories'][0]['headline'], 'New story');
    });

    test('invalid edition JSON is rejected and never saved', () async {
      const indexUrl = 'https://example.com/editions/index.json';
      final service = EditionDownloadService(
        fetcher: (url) async {
          if (url.toString() == indexUrl) {
            return jsonEncode({
              'editions': [
                {'edition_date': '2026-11-09', 'file': 'data-2026-11-09.json'},
              ],
            });
          }
          // Missing the 'mcqs' list: invalid.
          return jsonEncode({
            'edition_date': '2026-11-09',
            'stories': [],
            'words': [],
            'phrases': [],
          });
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.downloaded, isEmpty);
      expect(
        await File('${tempDir.path}/downloaded_editions/data-2026-11-09.json')
            .exists(),
        isFalse,
      );
    });

    test('non-newest bundled dates are skipped, not fetched', () async {
      var fileFetches = 0;
      const indexUrl = 'https://example.com/editions/index.json';
      final service = EditionDownloadService(
        fetcher: (url) async {
          if (url.toString() == indexUrl) {
            return jsonEncode({
              'editions': [
                {'edition_date': '2026-11-07', 'file': 'data-2026-11-07.json'},
                {'edition_date': '2026-11-08', 'file': 'data-2026-11-08.json'},
              ],
            });
          }
          fileFetches++;
          return ''; // invalid body: the newest re-fetch fails, nothing saved
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-07', '2026-11-08'},
      );
      expect(result.downloaded, isEmpty);
      expect(result.skipped, ['2026-11-07', '2026-11-08']);
      // Only the newest entry (2026-11-08) was re-fetched, so a
      // same-date correction to it would land; the older one was
      // never touched.
      expect(fileFetches, 1);
    });

    test('re-downloads the newest edition when its content changed',
        () async {
      const indexUrl = 'https://example.com/editions/index.json';
      final dir = Directory('${tempDir.path}/downloaded_editions');
      await dir.create(recursive: true);
      final savedFile = File('${dir.path}/data-2026-11-09.json');
      await savedFile.writeAsString(
        jsonEncode(editionJson('2026-11-09', headline: 'Old story')),
      );
      final service = EditionDownloadService(
        fetcher: (url) async {
          if (url.toString() == indexUrl) {
            return jsonEncode({
              'editions': [
                {
                  'edition_date': '2026-11-09',
                  'file': 'data-2026-11-09.json',
                },
              ],
            });
          }
          if (url.toString().endsWith('data-2026-11-09.json')) {
            return jsonEncode(
              editionJson('2026-11-09', headline: 'Corrected story'),
            );
          }
          throw const HttpException('404'); // no bn overlay offered
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, isNull);
      expect(result.downloaded, ['2026-11-09']);
      final parsed = jsonDecode(await savedFile.readAsString());
      expect(parsed['stories'][0]['headline'], 'Corrected story');
    });

    test('identical newest content is not reported as downloaded',
        () async {
      const indexUrl = 'https://example.com/editions/index.json';
      final edition = editionJson('2026-11-09', headline: 'Same story');
      final dir = Directory('${tempDir.path}/downloaded_editions');
      await dir.create(recursive: true);
      final savedFile = File('${dir.path}/data-2026-11-09.json');
      await savedFile.writeAsString(jsonEncode(edition));
      var fileFetches = 0;
      final service = EditionDownloadService(
        fetcher: (url) async {
          if (url.toString() == indexUrl) {
            return jsonEncode({
              'editions': [
                {
                  'edition_date': '2026-11-09',
                  'file': 'data-2026-11-09.json',
                },
              ],
            });
          }
          if (url.toString().endsWith('data-2026-11-09.json')) {
            fileFetches++;
            return jsonEncode(edition);
          }
          throw const HttpException('404'); // no bn overlay offered
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(indexUrl);
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, isNull);
      expect(fileFetches, 1); // re-fetched (it is the newest) ...
      expect(result.downloaded, isEmpty); // ... but identical, so not saved
      expect(result.skipped, ['2026-11-09']);
    });

    test('network failure: error result, no throw, nothing saved',
        () async {
      final service = EditionDownloadService(
        fetcher: (url) async =>
            throw const SocketException('no connection'),
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl(
        'https://example.com/editions/index.json',
      );
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, 'network');
      expect(result.downloaded, isEmpty);
      expect(await tempDir.list().toList(), isEmpty);
    });

    test('bad URL is reported, not fetched', () async {
      var calls = 0;
      final service = EditionDownloadService(
        fetcher: (url) async {
          calls++;
          return '';
        },
        documentsDir: () async => tempDir,
      );
      await EditionDownloadService.setStoredIndexUrl('not a url at all');
      final result = await service.checkForUpdates(
        bundledDates: {'2026-11-08'},
      );
      expect(result.error, 'bad_url');
      expect(calls, 0);
    });

    test('validateDownloadedEdition rejects missing keys', () {
      expect(validateDownloadedEdition({}), isNull);
      expect(
        validateDownloadedEdition({
          'edition_date': '2026-11-09',
          'stories': [],
          'words': [],
          'phrases': [],
        }),
        isNull,
        reason: 'mcqs missing',
      );
      expect(
        validateDownloadedEdition(editionJson('2026-11-09')),
        isNotNull,
      );
    });
  });

  group('phase5: newest edition is always selected', () {
    test('setEditions switches a stored older selection to the newest',
        () async {
      SharedPreferences.setMockInitialValues({});
      final state = AppState();
      await state.init();
      final old = [
        Edition.fromJson(editionJson('2026-11-08')),
        Edition.fromJson(editionJson('2026-11-07')),
      ];
      await state.setEditions(old, 0, null);
      expect(state.selectedEditionDate, '2026-11-08');
      // The reader browses back to an older edition...
      await state.selectEdition('2026-11-07');
      expect(state.selectedEditionDate, '2026-11-07');
      // ...then a refresh brings in a newer one: the screen switches.
      final newer = [
        Edition.fromJson(editionJson('2026-11-09')),
        Edition.fromJson(editionJson('2026-11-08')),
        Edition.fromJson(editionJson('2026-11-07')),
      ];
      await state.setEditions(newer, 0, null);
      expect(state.selectedEditionDate, '2026-11-09');
      expect(state.selectedEdition!.date, '2026-11-09');
    });

    test('setEditions returns to the newest even without a new arrival',
        () async {
      SharedPreferences.setMockInitialValues({});
      final state = AppState();
      await state.init();
      final editions = [
        Edition.fromJson(editionJson('2026-11-08')),
        Edition.fromJson(editionJson('2026-11-07')),
      ];
      await state.setEditions(editions, 0, null);
      await state.selectEdition('2026-11-07');
      // Next load (e.g. a restart) with the same list: back to newest.
      await state.setEditions(editions, 0, null);
      expect(state.selectedEditionDate, '2026-11-08');
    });

    test('the newest selection is persisted across AppState loads',
        () async {
      SharedPreferences.setMockInitialValues({});
      final first = AppState();
      await first.init();
      await first.setEditions([
        Edition.fromJson(editionJson('2026-11-08')),
        Edition.fromJson(editionJson('2026-11-07')),
      ], 0, null);
      await first.selectEdition('2026-11-07');
      await first.setEditions([
        Edition.fromJson(editionJson('2026-11-09')),
        Edition.fromJson(editionJson('2026-11-08')),
        Edition.fromJson(editionJson('2026-11-07')),
      ], 0, null);
      // A fresh AppState over the same prefs reads the newest selection.
      final second = AppState();
      await second.init();
      expect(second.selectedEditionDate, '2026-11-09');
    });
  });

  group('phase5: loader merge', () {
    test('downloaded edition overrides bundled, newer one joins', () {
      final bundled = [
        Edition.fromJson(editionJson('2026-11-08', headline: 'Bundled')),
        Edition.fromJson(editionJson('2026-11-07', headline: 'Old')),
      ];
      final downloaded = [
        Edition.fromJson(editionJson('2026-11-08', headline: 'Downloaded')),
        Edition.fromJson(editionJson('2026-11-09', headline: 'Brand new')),
      ];
      final merged = mergeDownloadedEditions(bundled, downloaded);
      expect(merged.length, 3);
      expect(
        merged.firstWhere((e) => e.date == '2026-11-08')
            .stories.first.headline,
        'Downloaded',
      );
      expect(
        merged.firstWhere((e) => e.date == '2026-11-09')
            .stories.first.headline,
        'Brand new',
      );
      expect(
        merged.firstWhere((e) => e.date == '2026-11-07')
            .stories.first.headline,
        'Old',
      );
    });

    test('loadDownloadedEditions reads valid files, ignores invalid ones',
        () async {
      final dir = await Directory.systemTemp.createTemp('sp5-loader-');
      try {
        final sub = Directory('${dir.path}/downloaded_editions');
        await sub.create(recursive: true);
        await File('${sub.path}/data-2026-11-09.json').writeAsString(
          jsonEncode(editionJson('2026-11-09')),
        );
        await File('${sub.path}/data-2026-11-10.json').writeAsString(
          '{"edition_date": "2026-11-10"}', // invalid: lists missing
        );
        await File('${sub.path}/notes.txt').writeAsString('not an edition');
        final loaded = await loadDownloadedEditions(
          downloadDirOverride: sub,
        );
        expect(loaded.map((e) => e.date).toList(), ['2026-11-09']);
      } finally {
        await dir.delete(recursive: true);
      }
    });

    test('refreshEditions picks up a newer edition from the default URL',
        () async {
      SharedPreferences.setMockInitialValues({});
      final tempDir = await Directory.systemTemp.createTemp('sp5-refresh-');
      try {
        final state = AppState();
        await state.init();
        final result = await loadEditions();
        await state.setEditions(
          result.editions,
          result.correctConsecutive,
          result.correctRule,
        );
        // Bundled editions run 2026-11-01..13; the fake server offers
        // 2026-11-16 through the DEFAULT Pages URL.
        final bundledDates = state.editions.map((e) => e.date).toSet();
        expect(bundledDates, contains('2026-11-13'));
        expect(bundledDates, isNot(contains('2026-11-16')));
        final edition = editionJson('2026-11-16', headline: 'Fresh story');
        var indexFetches = 0;
        final service = EditionDownloadService(
          fetcher: (url) async {
            if (url.toString() ==
                EditionDownloadService.defaultIndexUrl) {
              indexFetches++;
              return jsonEncode({
                'editions': [
                  {
                    'edition_date': '2026-11-16',
                    'file': 'data-2026-11-16.json',
                    'status': 'published',
                  },
                ],
              });
            }
            if (url.toString().endsWith('data-2026-11-16.json')) {
              return jsonEncode(edition);
            }
            throw const HttpException('404'); // no bn overlay offered
          },
          documentsDir: () async => tempDir,
        );
        final check = await refreshEditions(state, service: service);
        expect(check.error, isNull);
        expect(indexFetches, 1);
        expect(check.downloaded, ['2026-11-16']);
        final saved = File(
          '${tempDir.path}/downloaded_editions/data-2026-11-16.json',
        );
        expect(await saved.exists(), isTrue);
        final parsed = jsonDecode(await saved.readAsString());
        expect(parsed['stories'][0]['headline'], 'Fresh story');
        // In this test the fake service writes to a temp dir, so the
        // reload inside refreshEditions (which reads the real
        // documents dir) cannot see the new file yet. In production
        // the service writes to the real documents dir, so the same
        // refreshEditions call reloads and the new edition appears
        // in state immediately.
        expect(state.editions.map((e) => e.date), isNot(contains('2026-11-16')));
      } finally {
        await tempDir.delete(recursive: true);
      }
    });

    test('refreshEditions: failed check leaves bundled editions unchanged',
        () async {
      SharedPreferences.setMockInitialValues({});
      final state = AppState();
      await state.init();
      final result = await loadEditions();
      await state.setEditions(
        result.editions,
        result.correctConsecutive,
        result.correctRule,
      );
      final before = state.editions.map((e) => e.date).toList();
      final service = EditionDownloadService(
        fetcher: (url) async =>
            throw const SocketException('no connection'),
        documentsDir: () async =>
            Directory.systemTemp.createTemp('sp5-refresh-fail-'),
      );
      final check = await refreshEditions(state, service: service);
      expect(check.error, 'network');
      expect(state.editions.map((e) => e.date).toList(), before);
    });
  });
}
