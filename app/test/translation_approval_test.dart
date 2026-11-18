import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/data/loader.dart';
import 'package:sarangsho_plus/models.dart';

void main() {
  late Edition edition;

  setUp(() {
    edition = Edition(
      date: '2026-11-17',
      stories: [
        Story(
          id: 'CA01',
          headline: 'A test story',
          category: 'Bangladesh',
          summary: 'A test summary',
          sources: const [],
        ),
        Story(
          id: 'CA02',
          headline: 'Another test story',
          category: 'World',
          summary: 'Another test summary',
          sources: const [],
        ),
      ],
      words: const [],
      revisionWords: const [],
      phrases: const [],
      mcqs: const [],
      sources: const [],
      counts: const {},
    );
  });

  test('requires explicit approval for every story', () {
    final approved = {
      'CA01': {'translation_status': 'approved'},
      'CA02': {'translation_status': 'approved'},
    };
    expect(isBanglaOverlayApprovedForEdition(edition, approved), isTrue);
  });

  test('needs_review is not approval', () {
    final pending = {
      'CA01': {'translation_status': 'approved'},
      'CA02': {'translation_status': 'needs_review'},
    };
    expect(isBanglaOverlayApprovedForEdition(edition, pending), isFalse);
  });

  test('automated checks are not approval', () {
    final automated = {
      'CA01': {'translation_status': 'automated_checks_passed'},
      'CA02': {'translation_status': 'automated_checks_passed'},
    };
    expect(isBanglaOverlayApprovedForEdition(edition, automated), isFalse);
  });

  test('missing and extra story overlays fail closed', () {
    expect(
      isBanglaOverlayApprovedForEdition(edition, {
        'CA01': {'translation_status': 'approved'},
      }),
      isFalse,
    );
    expect(
      isBanglaOverlayApprovedForEdition(edition, {
        'CA01': {'translation_status': 'approved'},
        'CA02': {'translation_status': 'approved'},
        'CA03': {'translation_status': 'approved'},
      }),
      isFalse,
    );
  });

  test('list-shaped overlays are not accepted by the current contract', () {
    expect(
      isBanglaOverlayApprovedForEdition(edition, [
        {'id': 'CA01', 'translation_status': 'approved'},
        {'id': 'CA02', 'translation_status': 'approved'},
      ]),
      isFalse,
    );
  });
}
