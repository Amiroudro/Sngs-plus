/// Data models for Sarangsho Plus.
///
/// Everything is parsed from the bundled edition JSON files
/// (assets/editions/data-YYYY-MM-DD.json) plus the Bengali translation
/// overlays (assets/editions/bn-YYYY-MM-DD.json). No network, no invented
/// content: a field that is missing in the source stays missing here and
/// the UI says so in Bengali instead of fabricating a value.
library;

/// Returns [v] as a String, or null when [v] is null.
String? asStr(dynamic v) {
  if (v == null) return null;
  if (v is String) return v;
  return v.toString();
}

/// Splits a ';'-separated field into trimmed, non-empty items.
List<String> splitList(String? raw) {
  if (raw == null || raw.trim().isEmpty) return const [];
  return raw
      .split(';')
      .map((e) => e.trim())
      .where((e) => e.isNotEmpty)
      .toList();
}

/// True when a text field is present and meaningful.
/// The data uses the literal text "No direct antonym" for words that have
/// no antonym; that counts as absent, not as an antonym.
bool hasValue(String? v) {
  if (v == null) return false;
  final t = v.trim();
  if (t.isEmpty) return false;
  final lower = t.toLowerCase();
  if (lower == 'no direct antonym' ||
      lower == 'none' ||
      lower == 'n/a' ||
      lower == 'not applicable') {
    return false;
  }
  return true;
}

class SourceRef {
  final String? id;
  final String publication;
  final String headline;
  final String? date;
  final String? url;

  const SourceRef({
    this.id,
    required this.publication,
    required this.headline,
    this.date,
    this.url,
  });

  factory SourceRef.fromJson(Map<String, dynamic> json) {
    return SourceRef(
      id: asStr(json['id'] ?? json['Source ID']),
      publication: asStr(json['publication'] ??
              json['Publication / organisation'] ??
              json['Publication']) ??
          '',
      headline: asStr(json['headline'] ??
              json['Headline / report'] ??
              json['Headline']) ??
          '',
      date: asStr(json['date'] ?? json['Publication date']),
      url: asStr(json['url'] ?? json['Direct URL']),
    );
  }
}

/// Bengali translation of one story's text fields.
/// All figures, dates and proper nouns inside these strings were kept
/// exactly as in the English source; only the connecting language was
/// translated. A null field means "no Bengali translation supplied" and
/// the UI falls back to the English source text.
class BnStory {
  final String? headline;
  final String? summary;
  final String? whyItMatters;
  final String? examFacts;
  final String? keyPeople;
  final String? figures;

  /// Phase 5 fields (optional — an overlay without them behaves
  /// exactly like the old overlay and the UI falls back).
  final String? oneLiner;
  final List<KeyFact>? keyFacts;
  final List<String>? whatHappened;
  final List<ExamQa>? examQa;
  final List<RecallCard>? recallCards;
  final List<String>? keywords;
  final String? detail;

  const BnStory({
    this.headline,
    this.summary,
    this.whyItMatters,
    this.examFacts,
    this.keyPeople,
    this.figures,
    this.oneLiner,
    this.keyFacts,
    this.whatHappened,
    this.examQa,
    this.recallCards,
    this.keywords,
    this.detail,
  });

  factory BnStory.fromJson(Map<String, dynamic> json) {
    return BnStory(
      headline: asStr(json['headline']),
      summary: asStr(json['summary']),
      whyItMatters: asStr(json['why_it_matters']),
      examFacts: asStr(json['exam_facts']),
      keyPeople: asStr(json['key_people']),
      figures: asStr(json['figures']),
      oneLiner: asStr(json['one_liner']),
      keyFacts: parseKeyFacts(json['key_facts']),
      whatHappened: parseStringList(json['what_happened']),
      examQa: parseExamQa(json['exam_qa']),
      recallCards: parseRecallCards(json['recall_cards']),
      keywords: parseStringList(json['keywords']),
      detail: asStr(json['detail']),
    );
  }
}

/// One "মনে রাখুন" fact (Phase 5 story field `key_facts`):
/// a label, its value, and the original English figure for the tiny
/// original slot in Bengali mode. All three come from the data.
class KeyFact {
  final String label;
  final String value;
  final String? original;

  const KeyFact({required this.label, required this.value, this.original});

  factory KeyFact.fromJson(Map<String, dynamic> json) {
    return KeyFact(
      label: asStr(json['label']) ?? '',
      value: asStr(json['value']) ?? '',
      original: asStr(json['original']),
    );
  }
}

/// One exam Q→A row (Phase 5 story field `exam_qa`).
class ExamQa {
  final String q;
  final String a;

  const ExamQa({required this.q, required this.a});

  factory ExamQa.fromJson(Map<String, dynamic> json) {
    return ExamQa(
      q: asStr(json['q']) ?? '',
      a: asStr(json['a']) ?? '',
    );
  }
}

/// One fill-in-the-blank recall card (Phase 5 story field
/// `recall_cards`): the sentence with the blank already in it, and
/// the answer that fills it.
class RecallCard {
  final String cloze;
  final String answer;

  const RecallCard({required this.cloze, required this.answer});

  factory RecallCard.fromJson(Map<String, dynamic> json) {
    return RecallCard(
      cloze: asStr(json['cloze']) ?? '',
      answer: asStr(json['answer']) ?? '',
    );
  }
}

/// Parses a JSON list of strings (or null / anything else) into a
/// list, dropping empty items. Null-safe: missing fields yield null
/// so the caller can fall back to the old fields.
List<String>? parseStringList(dynamic raw) {
  if (raw is! List) return null;
  final out = <String>[];
  for (final item in raw) {
    final s = asStr(item);
    if (s != null && s.trim().isNotEmpty) out.add(s);
  }
  return out;
}

/// Parses a JSON list of {label, value, original} maps, or null when
/// the field is absent / not a list.
List<KeyFact>? parseKeyFacts(dynamic raw) {
  if (raw is! List) return null;
  final out = <KeyFact>[];
  for (final item in raw) {
    if (item is Map<String, dynamic>) {
      out.add(KeyFact.fromJson(item));
    } else if (item is Map) {
      out.add(KeyFact.fromJson(Map<String, dynamic>.from(item)));
    }
  }
  return out;
}

/// Parses a JSON list of {q, a} maps, or null when absent.
List<ExamQa>? parseExamQa(dynamic raw) {
  if (raw is! List) return null;
  final out = <ExamQa>[];
  for (final item in raw) {
    if (item is Map<String, dynamic>) {
      out.add(ExamQa.fromJson(item));
    } else if (item is Map) {
      out.add(ExamQa.fromJson(Map<String, dynamic>.from(item)));
    }
  }
  return out;
}

/// Parses a JSON list of {cloze, answer} maps, or null when absent.
List<RecallCard>? parseRecallCards(dynamic raw) {
  if (raw is! List) return null;
  final out = <RecallCard>[];
  for (final item in raw) {
    if (item is Map<String, dynamic>) {
      out.add(RecallCard.fromJson(item));
    } else if (item is Map) {
      out.add(RecallCard.fromJson(Map<String, dynamic>.from(item)));
    }
  }
  return out;
}

/// Bengali translation of one MCQ's text fields. The correct-answer key
/// always comes from the English source data, never from the overlay.
class BnMcq {
  final String? question;
  final Map<String, String>? options;
  final String? explanation;

  const BnMcq({this.question, this.options, this.explanation});

  factory BnMcq.fromJson(Map<String, dynamic> json) {
    Map<String, String>? opts;
    final raw = json['options'];
    if (raw is Map) {
      opts = {
        for (final e in raw.entries) e.key.toString(): e.value.toString(),
      };
    }
    return BnMcq(
      question: asStr(json['question']),
      options: opts,
      explanation: asStr(json['explanation']),
    );
  }
}

class Story {
  final String id;
  final String headline;
  final String category;
  final String? eventDate;
  final String? articleDate;
  final String summary;
  final String? whyItMatters;
  final String? examFacts;
  final String? examRelevance;
  final String? keyPeople;
  final String? figures;
  final List<SourceRef> sources;

  /// Phase 5 fields. ALL OPTIONAL: an old edition file without them
  /// parses exactly as before (null / empty) and the story screen
  /// falls back to the old fields (summary / exam_facts / figures).
  /// * [oneLiner] — the authored one-line summary (≤20 words).
  /// * [keyFacts] — the authored "মনে রাখুন" fact tiles.
  /// * [whatHappened] — the authored "কী ঘটেছে" bullets.
  /// * [examQa] — the authored "পরীক্ষায় যেভাবে আসে" Q→A rows.
  /// * [recallCards] — the authored "নিজেকে যাচাই করুন" cloze cards.
  /// * [keywords] — search / grouping keywords (parsed, not shown).
  /// * [detail] — the fuller detail text for the collapsed section.
  final String? oneLiner;
  final List<KeyFact> keyFacts;
  final List<String> whatHappened;
  final List<ExamQa> examQa;
  final List<RecallCard> recallCards;
  final List<String> keywords;
  final String? detail;

  /// Bengali overlay, if one was bundled for this edition.
  BnStory? bn;

  Story({
    required this.id,
    required this.headline,
    required this.category,
    this.eventDate,
    this.articleDate,
    required this.summary,
    this.whyItMatters,
    this.examFacts,
    this.examRelevance,
    this.keyPeople,
    this.figures,
    required this.sources,
    this.bn,
    this.oneLiner,
    this.keyFacts = const [],
    this.whatHappened = const [],
    this.examQa = const [],
    this.recallCards = const [],
    this.keywords = const [],
    this.detail,
  });

  factory Story.fromJson(Map<String, dynamic> json) {
    final srcs = <SourceRef>[];
    final raw = json['sources'];
    if (raw is List) {
      for (final s in raw) {
        if (s is Map<String, dynamic>) {
          srcs.add(SourceRef.fromJson(s));
        } else if (s is Map) {
          srcs.add(SourceRef.fromJson(Map<String, dynamic>.from(s)));
        }
      }
    }
    return Story(
      id: asStr(json['id']) ?? '',
      headline: asStr(json['headline']) ?? '',
      category: asStr(json['category']) ?? '',
      eventDate: asStr(json['event_date']),
      articleDate: asStr(json['article_date']),
      summary: asStr(json['summary']) ?? '',
      whyItMatters: asStr(json['why_it_matters']),
      examFacts: asStr(json['exam_facts']),
      examRelevance: asStr(json['exam_relevance']),
      keyPeople: asStr(json['key_people']),
      figures: asStr(json['figures']),
      sources: srcs,
      oneLiner: asStr(json['one_liner']),
      keyFacts: parseKeyFacts(json['key_facts']) ?? const [],
      whatHappened: parseStringList(json['what_happened']) ?? const [],
      examQa: parseExamQa(json['exam_qa']) ?? const [],
      recallCards: parseRecallCards(json['recall_cards']) ?? const [],
      keywords: parseStringList(json['keywords']) ?? const [],
      detail: asStr(json['detail']),
    );
  }

  /// Display headline in the requested language ('bn' falls back to
  /// English when no Bengali translation exists for this story).
  String headlineIn(String lang) =>
      (lang == 'bn' ? bn?.headline : null) ?? headline;

  String summaryIn(String lang) =>
      (lang == 'bn' ? bn?.summary : null) ?? summary;

  String? whyIn(String lang) =>
      (lang == 'bn' ? bn?.whyItMatters : null) ?? whyItMatters;

  String? factsIn(String lang) =>
      (lang == 'bn' ? bn?.examFacts : null) ?? examFacts;

  String? peopleIn(String lang) =>
      (lang == 'bn' ? bn?.keyPeople : null) ?? keyPeople;

  String? figuresIn(String lang) =>
      (lang == 'bn' ? bn?.figures : null) ?? figures;

  /// Phase 5 field accessors. Bengali overlay wins when it carries
  /// the field (non-empty); otherwise the English source field; when
  /// neither exists the result is null / empty and the layout falls
  /// back to the old fields. EMPTY counts as absent: the data
  /// carries empty new fields by design on some stories (2 Nov CA04
  /// has one_liner "", key_facts [] and NO detail key at all), and an
  /// empty string must never blank a section that the old fields
  /// could have filled.
  String? oneLinerIn(String lang) {
    final bnOne = lang == 'bn' ? bn?.oneLiner : null;
    if (bnOne != null && bnOne.trim().isNotEmpty) return bnOne;
    if (oneLiner != null && oneLiner!.trim().isNotEmpty) return oneLiner;
    return null;
  }

  List<KeyFact> keyFactsIn(String lang) {
    if (lang == 'bn' && bn?.keyFacts != null && bn!.keyFacts!.isNotEmpty) {
      return bn!.keyFacts!;
    }
    return keyFacts;
  }

  List<String> whatHappenedIn(String lang) {
    if (lang == 'bn' &&
        bn?.whatHappened != null &&
        bn!.whatHappened!.isNotEmpty) {
      return bn!.whatHappened!;
    }
    return whatHappened;
  }

  List<ExamQa> examQaIn(String lang) {
    if (lang == 'bn' && bn?.examQa != null && bn!.examQa!.isNotEmpty) {
      return bn!.examQa!;
    }
    return examQa;
  }

  List<RecallCard> recallCardsIn(String lang) {
    if (lang == 'bn' &&
        bn?.recallCards != null &&
        bn!.recallCards!.isNotEmpty) {
      return bn!.recallCards!;
    }
    return recallCards;
  }

  String? detailIn(String lang) {
    final bnDetail = lang == 'bn' ? bn?.detail : null;
    if (bnDetail != null && bnDetail.trim().isNotEmpty) return bnDetail;
    if (detail != null && detail!.trim().isNotEmpty) return detail;
    return null;
  }

  /// The data carries NO numeric 0-100 score. `exam_relevance` is a
  /// free-text label ("High", "Medium", "High — ..."). This returns the
  /// level only: 'High', 'Medium', or null. Never invent a number.
  String? get relevanceLevel {
    final r = examRelevance;
    if (r == null) return null;
    if (r.startsWith('High')) return 'High';
    if (r.startsWith('Medium')) return 'Medium';
    if (r.startsWith('Low')) return 'Low';
    return null;
  }

  /// Publication names of this story's sources, for the card byline.
  List<String> get sourcePublications =>
      sources.map((s) => s.publication).toSet().toList();
}

/// One vocabulary word. Field names in the source JSON are long
/// ('Headword / phrase', 'Bangla phonetic', ...); they are mapped here.
class VocabWord {
  final String headword;
  final String? ipa;
  final String? banglaPhonetic;
  final String? partOfSpeech;
  final String? difficulty;
  final String? banglaMeaning;
  final String? englishDefinition;
  final String? synonymsRaw;
  final String? antonymsRaw;
  final String? wordFamilyRaw;
  final String? collocationsRaw;
  final String? example;
  final String? contextNote;
  final String? sourcePublication;
  final String? articleHeadline;
  final String? publicationDate;
  final String? sourceUrl;
  final String? bcsRelevance;
  final String? priority;
  final bool isRevision;

  const VocabWord({
    required this.headword,
    this.ipa,
    this.banglaPhonetic,
    this.partOfSpeech,
    this.difficulty,
    this.banglaMeaning,
    this.englishDefinition,
    this.synonymsRaw,
    this.antonymsRaw,
    this.wordFamilyRaw,
    this.collocationsRaw,
    this.example,
    this.contextNote,
    this.sourcePublication,
    this.articleHeadline,
    this.publicationDate,
    this.sourceUrl,
    this.bcsRelevance,
    this.priority,
    this.isRevision = false,
  });

  factory VocabWord.fromJson(Map<String, dynamic> json,
      {bool isRevision = false}) {
    return VocabWord(
      headword: asStr(json['Headword / phrase']) ?? '',
      ipa: asStr(json['IPA']),
      banglaPhonetic: asStr(json['Bangla phonetic']),
      partOfSpeech: asStr(json['Part of speech / type']),
      difficulty: asStr(json['Difficulty']),
      banglaMeaning: asStr(json['Bangla meaning']),
      englishDefinition: asStr(json['English definition']),
      synonymsRaw: asStr(json['Synonyms']),
      antonymsRaw: asStr(json['Antonyms']),
      wordFamilyRaw: asStr(json['Word family / derivatives']),
      collocationsRaw: asStr(json['Collocations / patterns']),
      example: asStr(json['Original example']),
      contextNote: asStr(json['Newspaper context note']),
      sourcePublication: asStr(json['Source publication']),
      articleHeadline: asStr(json['Article headline']),
      publicationDate: asStr(json['Publication date']),
      sourceUrl: asStr(json['Direct source URL']),
      bcsRelevance: asStr(json['BCS / Bank relevance']),
      priority: asStr(json['Priority']),
      isRevision: isRevision,
    );
  }

  List<String> get synonyms => splitList(synonymsRaw);
  List<String> get antonyms =>
      hasValue(antonymsRaw) ? splitList(antonymsRaw) : const [];
  List<String> get wordFamily => splitList(wordFamilyRaw);
  List<String> get collocations => splitList(collocationsRaw);

  bool get hasSynonyms => synonyms.isNotEmpty;
  bool get hasAntonyms => antonyms.isNotEmpty;
  bool get hasWordFamily => wordFamily.isNotEmpty;
  bool get hasCollocations => collocations.isNotEmpty;

  /// The word spelled out letter by letter, for the spelling row.
  List<String> get spellingLetters => headword.split('');

  /// Indexes of letters that are part of a doubled letter (e.g. the two
  /// 's' in "suppress"). Mechanical only — no claim about silent letters
  /// or other spelling traps, which the data does not supply.
  Set<int> get doubledLetterIndexes {
    final out = <int>{};
    final letters = headword.toLowerCase().split('');
    for (var i = 1; i < letters.length; i++) {
      if (letters[i] == letters[i - 1] && letters[i].trim().isNotEmpty) {
        out.add(i - 1);
        out.add(i);
      }
    }
    return out;
  }

  /// Longest common prefix (min 3 letters) shared by the headword and at
  /// least one of its derivatives. Mechanical morphology from the data's
  /// own word-family field — not a verified etymology.
  String? get commonStem {
    String? best;
    for (final form in wordFamily) {
      final a = headword.toLowerCase();
      final b = form.toLowerCase().trim();
      var i = 0;
      while (i < a.length && i < b.length && a[i] == b[i]) {
        i++;
      }
      if (i >= 3 && (best == null || i > best.length)) {
        best = headword.substring(0, i);
      }
    }
    return best;
  }
}

class Phrase {
  final String phrase;
  final String? type;
  final String? banglaMeaning;
  final String? englishExplanation;
  final String? usage;
  final String? example1;
  final String? example2;
  final String? collocationsRaw;
  final String? sourcePublication;
  final String? articleHeadline;
  final String? publicationDate;
  final String? sourceUrl;
  final String? examValue;

  const Phrase({
    required this.phrase,
    this.type,
    this.banglaMeaning,
    this.englishExplanation,
    this.usage,
    this.example1,
    this.example2,
    this.collocationsRaw,
    this.sourcePublication,
    this.articleHeadline,
    this.publicationDate,
    this.sourceUrl,
    this.examValue,
  });

  factory Phrase.fromJson(Map<String, dynamic> json) {
    return Phrase(
      phrase: asStr(json['Phrase']) ?? '',
      type: asStr(json['Type']),
      banglaMeaning: asStr(json['Bangla meaning']),
      englishExplanation: asStr(json['English explanation']),
      usage: asStr(json['Usage / register']),
      example1: asStr(json['Original example 1']),
      example2: asStr(json['Original example 2']),
      collocationsRaw: asStr(json['Common collocations / grammar pattern']),
      sourcePublication: asStr(json['Source publication']),
      articleHeadline: asStr(json['Article headline']),
      publicationDate: asStr(json['Publication date']),
      sourceUrl: asStr(json['Direct source URL']),
      examValue: asStr(json['Exam value']),
    );
  }

  List<String> get collocations => splitList(collocationsRaw);
}

class Mcq {
  final int no;
  final String section;
  final String question;
  final Map<String, String> options;
  final String correct;
  final String? explanation;
  final String? source;

  /// Bengali overlay, if bundled for this edition.
  BnMcq? bn;

  Mcq({
    required this.no,
    required this.section,
    required this.question,
    required this.options,
    required this.correct,
    this.explanation,
    this.source,
    this.bn,
  });

  factory Mcq.fromJson(Map<String, dynamic> json) {
    final opts = <String, String>{};
    final raw = json['options'];
    if (raw is Map) {
      for (final e in raw.entries) {
        opts[e.key.toString()] = e.value.toString();
      }
    } else if (raw is List) {
      const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
      for (var i = 0; i < raw.length && i < letters.length; i++) {
        opts[letters[i]] = raw[i].toString();
      }
    }
    return Mcq(
      no: json['no'] is int
          ? json['no'] as int
          : int.tryParse(asStr(json['no']) ?? '') ?? 0,
      section: asStr(json['section']) ?? '',
      question: asStr(json['question']) ?? '',
      options: opts,
      correct: asStr(json['correct']) ?? '',
      explanation: asStr(json['explanation']),
      source: asStr(json['source']),
    );
  }

  /// Option keys in A-B-C-D order.
  List<String> get optionKeys {
    final keys = options.keys.toList()..sort();
    return keys;
  }

  String questionIn(String lang) =>
      (lang == 'bn' ? bn?.question : null) ?? question;

  String optionIn(String lang, String key) {
    if (lang == 'bn') {
      final v = bn?.options?[key];
      if (v != null) return v;
    }
    return options[key] ?? '';
  }

  String? explanationIn(String lang) =>
      (lang == 'bn' ? bn?.explanation : null) ?? explanation;
}

class Edition {
  final String date;
  final String? day;
  final String? coverage;
  final String? status;
  final List<Story> stories;
  final List<VocabWord> words;
  final List<VocabWord> revisionWords;
  final List<Phrase> phrases;
  final List<Mcq> mcqs;
  final List<SourceRef> sources;
  final Map<String, int> counts;

  Edition({
    required this.date,
    this.day,
    this.coverage,
    this.status,
    required this.stories,
    required this.words,
    required this.revisionWords,
    required this.phrases,
    required this.mcqs,
    required this.sources,
    required this.counts,
  });

  factory Edition.fromJson(Map<String, dynamic> json,
      {String? statusOverride}) {
    List<T> parseList<T>(dynamic raw, T Function(Map<String, dynamic>) f) {
      final out = <T>[];
      if (raw is List) {
        for (final item in raw) {
          if (item is Map<String, dynamic>) {
            out.add(f(item));
          } else if (item is Map) {
            out.add(f(Map<String, dynamic>.from(item)));
          }
        }
      }
      return out;
    }

    final counts = <String, int>{};
    final rawCounts = json['counts'];
    if (rawCounts is Map) {
      for (final e in rawCounts.entries) {
        final n =
            e.value is int ? e.value as int : int.tryParse(e.value.toString());
        if (n != null) counts[e.key.toString()] = n;
      }
    }

    return Edition(
      date: asStr(json['edition_date']) ?? '',
      day: asStr(json['edition_day']),
      coverage: asStr(json['coverage']),
      status: statusOverride ?? asStr(json['status']),
      stories: parseList<Story>(json['stories'], Story.fromJson),
      words: parseList<VocabWord>(json['words'], (m) => VocabWord.fromJson(m)),
      revisionWords: parseList<VocabWord>(json['revision_words'],
          (m) => VocabWord.fromJson(m, isRevision: true)),
      phrases: parseList<Phrase>(json['phrases'], Phrase.fromJson),
      mcqs: parseList<Mcq>(json['mcqs'], Mcq.fromJson),
      sources: parseList<SourceRef>(json['sources'], SourceRef.fromJson),
      counts: counts,
    );
  }

  int get storyCount => counts['stories'] ?? stories.length;
  int get wordCount => counts['words'] ?? words.length;
  int get phraseCount => counts['phrases'] ?? phrases.length;
  int get mcqCount => counts['mcqs'] ?? mcqs.length;
  int get revisionCount =>
      counts['revision'] ?? counts['revision_words'] ?? revisionWords.length;
  int get sourceCount => counts['sources'] ?? sources.length;

  /// Phrases in this edition whose text contains the word's headword
  /// (or vice versa). Derived from the edition's own data only.
  List<Phrase> relatedPhrasesFor(VocabWord word) {
    final h = word.headword.toLowerCase().trim();
    if (h.isEmpty) return const [];
    return phrases.where((p) => p.phrase.toLowerCase().contains(h)).toList();
  }
}

class EditionIndexEntry {
  final String date;
  final String file;
  final String? status;
  final String? review;
  final String? coverage;

  const EditionIndexEntry({
    required this.date,
    required this.file,
    this.status,
    this.review,
    this.coverage,
  });

  factory EditionIndexEntry.fromJson(Map<String, dynamic> json) {
    return EditionIndexEntry(
      date: asStr(json['edition_date']) ?? '',
      file: asStr(json['file']) ?? '',
      status: asStr(json['status']),
      review: asStr(json['review']),
      coverage: asStr(json['coverage']),
    );
  }

  /// Bengali overlay filename for this edition, e.g.
  /// data-2026-11-07.json -> bn-2026-11-07.json
  String get bnFile => file.replaceFirst('data-', 'bn-');
}
