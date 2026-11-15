/// The six reading sections. Edition 2 already uses these names as its
/// story categories; Edition 1 uses long free-text categories, which are
/// grouped into the same six by the keyword rules in [sectionFor].
///
/// Grouping rules (checked in order). They are deliberately keyword-based
/// and documented, so the APK builder can verify every Edition 1 story
/// lands in the section below:
///
/// * exact six-section name -> itself
/// * contains "banking" -> Economy & Banking
/// * contains "international" -> World
/// * contains "technology" or "science" -> Technology
/// * contains "economy", "trade", "finance", "tax", "industrial" or
///   "infrastructure" -> Economy & Banking
/// * contains "labour" or "migration" -> Jobs & Education
/// * contains "renewable" or "climate" -> Bangladesh
/// * contains "history" or "governance" -> Bangladesh
/// * anything else -> Bangladesh
///
/// Resulting Edition 1 mapping (verified by tools/check_data.py):
/// * Bangladesh: CA01 (history/governance), CA13 (renewable energy)
/// * Economy & Banking: CA02, CA03, CA04, CA05, CA06, CA07, CA08, CA09, CA12
/// * World: CA14, CA15
/// * Technology: CA10
/// * Jobs & Education: CA11
/// * Politics: (none in Edition 1)
library;

const List<String> sixSections = [
  'Bangladesh',
  'Economy & Banking',
  'World',
  'Politics',
  'Technology',
  'Jobs & Education',
];

const Map<String, String> sectionNamesBn = {
  'Bangladesh': 'বাংলাদেশ',
  'Economy & Banking': 'অর্থনীতি ও ব্যাংকিং',
  'World': 'বিশ্ব',
  'Politics': 'রাজনীতি',
  'Technology': 'প্রযুক্তি',
  'Jobs & Education': 'চাকরি ও শিক্ষা',
};

String sectionName(String section, String lang) {
  if (lang != 'bn') return section;
  // Bangla fallback for an unmapped category: never leak the raw
  // English section name into Bengali UI (Phase 4).
  return sectionNamesBn[section] ?? 'বাংলাদেশ';
}

/// Bengali name for an MCQ's English section, as stored in the edition
/// data ('Current Affairs', 'Vocabulary', 'Phrases' — note the data
/// also uses the variants 'Current affairs' and 'Phrase').
///
/// Unlike [sectionName], the fallback returns the input unchanged: a
/// practice mistake's section is already a localised type label
/// (e.g. 'প্রতিশব্দ'), so an unmapped value is localised text, not an
/// English leak. Routing MCQ sections through [sectionName] would be
/// wrong — 'Vocabulary' is not a story section and would fall back to
/// 'বাংলাদেশ'.
String mcqSectionName(String section, String lang) {
  if (lang != 'bn') return section;
  return switch (section) {
    'Current Affairs' || 'Current affairs' => 'সাম্প্রতিক ঘটনা',
    'Vocabulary' => 'শব্দ',
    'Phrases' || 'Phrase' => 'শব্দবন্ধ',
    _ => section,
  };
}

String sectionFor(String category) {
  if (sixSections.contains(category)) return category;
  final c = category.toLowerCase();
  if (c.contains('banking')) return 'Economy & Banking';
  if (c.contains('international')) return 'World';
  if (c.contains('technology') || c.contains('science')) {
    return 'Technology';
  }
  if (c.contains('economy') ||
      c.contains('trade') ||
      c.contains('finance') ||
      c.contains('tax') ||
      c.contains('industrial') ||
      c.contains('infrastructure')) {
    return 'Economy & Banking';
  }
  if (c.contains('labour') || c.contains('migration')) {
    return 'Jobs & Education';
  }
  if (c.contains('renewable') || c.contains('climate')) {
    return 'Bangladesh';
  }
  if (c.contains('history') || c.contains('governance')) {
    return 'Bangladesh';
  }
  return 'Bangladesh';
}
