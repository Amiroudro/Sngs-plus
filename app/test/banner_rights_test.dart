/// Publisher photos show only when a story is explicitly marked
/// `banner_rights: "approved"`. Everything else gets the generated
/// typographic banner.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/models.dart';

Story _story({String? imageUrl, String? bannerRights}) => Story(
      id: 'T1',
      headline: 'শিরোনাম',
      category: 'অর্থনীতি',
      summary: 'সারসংক্ষেপ।',
      sources: const [],
      imageUrl: imageUrl,
      bannerRights: bannerRights,
    );

void main() {
  const url = 'https://cdn.example.com/banner.jpg';

  test('image without banner_rights is not shown', () {
    expect(_story(imageUrl: url).bannerImageUrl, isNull);
  });

  test('pending or unknown rights are not shown', () {
    expect(_story(imageUrl: url, bannerRights: 'pending').bannerImageUrl,
        isNull);
    expect(_story(imageUrl: url, bannerRights: 'yes').bannerImageUrl,
        isNull);
  });

  test('approved rights show the image', () {
    expect(_story(imageUrl: url, bannerRights: 'approved').bannerImageUrl,
        url);
    expect(_story(imageUrl: url, bannerRights: ' Approved ').bannerImageUrl,
        url);
  });

  test('approved but no image is still the generated banner', () {
    expect(_story(bannerRights: 'approved').bannerImageUrl, isNull);
  });

  test('banner_rights is read from JSON', () {
    final s = Story.fromJson({
      'id': 'T2',
      'headline': 'H',
      'category': 'C',
      'summary': 'S',
      'sources': <dynamic>[],
      'image_url': url,
      'banner_rights': 'approved',
    });
    expect(s.bannerImageUrl, url);
  });
}
