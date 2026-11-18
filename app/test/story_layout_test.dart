/// Unit tests for the Phase 2 story-layout derivation.
/// Pure Dart, no widgets. Runs against the real bundled editions.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'fixtures/approved_bn_qr_story.dart';
import 'package:sarangsho_plus/data/story_layout.dart';
import 'package:sarangsho_plus/state/app_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppState state;

  setUpAll(() async {
    SharedPreferences.setMockInitialValues({});
    state = AppState();
    await state.init();
    final result = await loadEditions();
    await state.setEditions(
      result.editions,
      result.correctConsecutive,
      result.correctRule,
    );

    // Bengali rendering uses a synthetic reviewed fixture below; bundled
    // unapproved overlays remain blocked by the production loader.
  });

  test('sentence splitting honours the Bengali danda', () {
    expect(
      splitSentences('প্রথম বাক্য। দ্বিতীয় বাক্য। তৃতীয়।'),
      ['প্রথম বাক্য।', 'দ্বিতীয় বাক্য।', 'তৃতীয়।'],
    );
    // A '.' inside a number is not a sentence end.
    expect(firstSentence('হার 51.62 শতাংশ। পরের বাক্য।'), 'হার 51.62 শতাংশ।');
    expect(splitSentences('One. Two. Three.'), ['One.', 'Two.', 'Three.']);
  });

  test('one-liner is at most 20 words for every story, both languages', () {
    for (final edition in state.editions) {
      for (final story in edition.stories) {
        for (final lang in ['bn', 'en']) {
          final layout = buildStoryLayout(story, lang);
          expect(
            wordCount(layout.oneLiner),
            lessThanOrEqualTo(20),
            reason: '${edition.date} ${story.id} ($lang): '
                '"${layout.oneLiner}"',
          );
          expect(layout.oneLiner, isNotEmpty);
        }
      }
    }
  });

  test('tiles are at most 4, unique, and never repeat a shown fact', () {
    var total = 0;
    for (final edition in state.editions) {
      for (final story in edition.stories) {
        for (final lang in ['bn', 'en']) {
          final layout = buildStoryLayout(story, lang);
          total++;
          expect(layout.tiles.length, lessThanOrEqualTo(4));
          final seen = <String>{};
          for (final tile in layout.tiles) {
            final norm = normalizeFact('${tile.label} ${tile.value}');
            expect(seen.add(norm), isTrue,
                reason: 'duplicate tile in ${story.id} ($lang)');
            expect(
              normalizeFact(layout.oneLiner).contains(norm) ||
                  layout.bullets.any(
                    (b) => normalizeFact(b).contains(norm),
                  ),
              isFalse,
              reason: 'tile repeats a shown fact in ${story.id} ($lang): '
                  '"${tile.label} ${tile.value}"',
            );
          }
          // Bullets never repeat the one-liner.
          for (final b in layout.bullets) {
            expect(normalizeFact(b), isNot(normalizeFact(layout.oneLiner)));
          }
          expect(layout.bullets.length, lessThanOrEqualTo(3));
        }
      }
    }
    // Total is stories × 2 languages; derive the story count from the
    // bundled data (161 after Editions 9–11 Nov 2026) instead of
    // hardcoding it, so the next published edition does not break this.
    final storyCount =
        state.editions.fold<int>(0, (n, e) => n + e.stories.length);
    expect(total, storyCount * 2);
  });

  test('cloze cards blank a number and keep the answer', () {
    for (final edition in state.editions) {
      for (final story in edition.stories) {
        final layout = buildStoryLayout(story, 'bn');
        expect(layout.cloze.length, lessThanOrEqualTo(2));
        for (final card in layout.cloze) {
          expect(card.text, contains('______'));
          expect(card.answer, isNotEmpty);
          expect(
            RegExp(r'[0-9০-৯]').hasMatch(card.answer),
            isTrue,
            reason: '${edition.date} ${story.id}: cloze answer "${card.answer}"',
          );
          // The blanked sentence still has context around the blank.
          expect(wordCount(card.text.replaceAll('______', '')), greaterThanOrEqualTo(4));
        }
      }
    }
  });

  test('Q&A rows are clean questions with real answers', () {
    for (final edition in state.editions) {
      for (final story in edition.stories) {
        final layout = buildStoryLayout(story, 'bn');
        expect(layout.qa.length, lessThanOrEqualTo(2));
        for (final pair in layout.qa) {
          expect(pair.question, endsWith('?'));
          expect(pair.answer, isNotEmpty);
          // Restored full-sentence Q&A (2026-11-17 exam_qa restore)
          // run to 22 words; the cap only guards against runaway
          // text, not against a proper question.
          expect(wordCount(pair.question), lessThanOrEqualTo(25));
        }
      }
    }
  });

  test('a reviewed Bengali QR fixture gets the mockup layout', () {
    final story = createApprovedBanglaQrStory();
    final layout = buildStoryLayout(story, 'bn');

    expect(layout.oneLiner, startsWith('বাংলা কিউআর লেনদেনের দৈনিক পরিমাণ'));
    expect(layout.tiles.length, greaterThanOrEqualTo(3));
    // The chart: three comparable daily figures, now in authentic
    // Bengali (Phase 4: "Tk 13.5 billion" -> "১,৩৫০ কোটি টাকা").
    expect(layout.chart, isNotNull);
    expect(layout.chart!.bars.length, 3);
    expect(
      layout.chart!.bars.map((b) => b.display),
      contains('১,৩৫০ কোটি টাকা'),
    );
    expect(layout.chart!.title, contains('টাকা'));
    expect(layout.chart!.title, isNot(contains('Tk')));
    // Tiles carry the tiny original English figure.
    expect(layout.tiles.any((t) => t.original != null), isTrue);
    // Cloze blanks a number from the figures.
    expect(layout.cloze, isNotEmpty);
    expect(layout.qa, isNotEmpty);
    expect(layout.whySentence, isNotNull);
    expect(layout.bullets.length, greaterThanOrEqualTo(2));
  });

  test('coverage: how many stories get tiles / chart / QA / cloze', () {
    var tiles = 0;
    var chart = 0;
    var qa = 0;
    var cloze = 0;
    var why = 0;
    var noTiles = <String>[];
    for (final edition in state.editions) {
      for (final story in edition.stories) {
        final layout = buildStoryLayout(story, 'bn');
        if (layout.tiles.isNotEmpty) {
          tiles++;
        } else {
          noTiles.add('${edition.date} ${story.id}');
        }
        if (layout.chart != null) chart++;
        if (layout.qa.isNotEmpty) qa++;
        if (layout.cloze.isNotEmpty) cloze++;
        if (layout.whySentence != null) why++;
      }
    }
    // Printed for the build report — these are coverage facts, not
    // pass/fail gates (a story with no clean tile simply hides it).
    // ignore: avoid_print
    print('stories=119 tiles=$tiles chart=$chart qa=$qa cloze=$cloze why=$why');
    // ignore: avoid_print
    print('no tiles: $noTiles');
    expect(tiles, greaterThan(100));
    expect(chart, greaterThan(10));
    expect(qa, greaterThan(80));
    expect(cloze, greaterThan(80));
    expect(why, greaterThan(100));
  });
}
