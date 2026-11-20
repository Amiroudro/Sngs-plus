/// The engine copies one story-level source onto every institution /
/// extra-knowledge item. A source repeated on ALL items describes the
/// section, so it is shown once under the list instead of under each
/// item, where it would look like per-item evidence.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/screens/learning_module_section.dart';

void main() {
  group('sharedSectionSource', () {
    test('identical source on every item of a 2+ list is shared', () {
      expect(
        sharedSectionSource(['WTO — Aid-for-Trade', 'WTO — Aid-for-Trade']),
        'WTO — Aid-for-Trade',
      );
    });

    test('whitespace differences do not break sharing', () {
      expect(sharedSectionSource([' Banglapedia', 'Banglapedia ']),
          'Banglapedia');
    });

    test('mixed sources stay per-item', () {
      expect(sharedSectionSource(['plancomm.gov.bd', 'Banglapedia']), isNull);
    });

    test('one item missing a source stays per-item (existing fixtures)', () {
      expect(sharedSectionSource(['plancomm.gov.bd', null]), isNull);
      expect(sharedSectionSource(['plancomm.gov.bd', '']), isNull);
    });

    test('a single item is never treated as shared', () {
      expect(sharedSectionSource(['Banglapedia']), isNull);
    });

    test('empty list, empty or null sources are not shared', () {
      expect(sharedSectionSource(<String?>[]), isNull);
      expect(sharedSectionSource([null, null]), isNull);
      expect(sharedSectionSource(['', '']), isNull);
      expect(sharedSectionSource(['  ', '  ']), isNull);
    });
  });
}
