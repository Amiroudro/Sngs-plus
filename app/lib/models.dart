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

  /// Banner image URL (og:image) captured for the source article —
  /// the URL only, never a downloaded file. Null/empty when the
  /// article has none (the story screen shows its typographic
  /// banner instead).
  final String? imageUrl;

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
    this.imageUrl,
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
      imageUrl: asStr(json['image_url']),
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

/// One source reference inside a learning module (GK / exam notes):
/// a named source with a link. Only what the JSON carries — never invented.
class LmSource {
  final String name;
  final String? url;

  const LmSource({required this.name, this.url});

  factory LmSource.fromJson(Map<String, dynamic> json) {
    return LmSource(
      name: asStr(json['name']) ?? '',
      url: asStr(json['url']),
    );
  }
}

/// Parses a JSON list of {name, url} maps, or empty when absent.
List<LmSource> parseLmSources(dynamic raw) {
  if (raw is! List) return const [];
  final out = <LmSource>[];
  for (final item in raw) {
    if (item is Map<String, dynamic>) {
      out.add(LmSource.fromJson(item));
    } else if (item is Map) {
      out.add(LmSource.fromJson(Map<String, dynamic>.from(item)));
    }
  }
  return out;
}

/// One fact row in a learning module. Two shapes occur in the data:
/// `{label, value, source}` (a labelled figure) and `{fact, source}`
/// (a free fact sentence). The `{fact, from}` / `{fact, source_field}`
/// variants carry internal provenance, not a displayable source — the
/// parser keeps only the `source` key, never `from` / `source_field`.
/// The v2 model adds an optional `date` (verified-facts rows carry
/// the fact's date, e.g. "১৫ নভেম্বর ২০২৬").
class LmFact {
  final String? label;
  final String value;
  final String? source;
  final String? date;

  const LmFact({this.label, required this.value, this.source, this.date});

  factory LmFact.fromJson(dynamic raw) {
    if (raw is String) return LmFact(value: raw);
    if (raw is Map<String, dynamic>) {
      if (raw['label'] != null) {
        return LmFact(
          label: asStr(raw['label']),
          value: asStr(raw['value']) ?? '',
          source: asStr(raw['source']),
          date: asStr(raw['date']),
        );
      }
      return LmFact(
        value: asStr(raw['fact']) ?? '',
        source: asStr(raw['source']),
        date: asStr(raw['date']),
      );
    }
    if (raw is Map) {
      return LmFact.fromJson(Map<String, dynamic>.from(raw));
    }
    return const LmFact(value: '');
  }
}

/// The news source of a v2 `news_summary`: an explicit object
/// `{publication, date, url}` so the app can render it as a link
/// line. The v1 shape (a plain source string) is kept separately in
/// [LearningModule.newsSource].
class LmNewsSource {
  final String? publication;
  final String? date;
  final String? url;

  const LmNewsSource({this.publication, this.date, this.url});

  factory LmNewsSource.fromJson(Map<String, dynamic> json) {
    return LmNewsSource(
      publication: asStr(json['publication']),
      date: asStr(json['date']),
      url: asStr(json['url']),
    );
  }

  bool get isEmpty =>
      (publication == null || publication!.trim().isEmpty) &&
      (date == null || date!.trim().isEmpty) &&
      (url == null || url!.trim().isEmpty);
}

/// One table inside a v2 `topic_gk` lesson: a title plus
/// label/value rows (rendered like fact rows).
class LmGkTable {
  final String? title;
  final List<LmFact> rows;

  const LmGkTable({this.title, this.rows = const []});

  factory LmGkTable.fromJson(Map<String, dynamic> json) {
    return LmGkTable(
      title: asStr(json['title']),
      rows: (json['rows'] is List)
          ? (json['rows'] as List).map(LmFact.fromJson).toList()
          : const [],
    );
  }
}

/// One institution in a v2 module (its OWN section, section 5):
/// name + one-line role + the source the role is stated in.
class LmInstitution {
  final String name;
  final String? fullName;
  final String? role;
  final String? source;

  const LmInstitution({
    required this.name,
    this.fullName,
    this.role,
    this.source,
  });

  factory LmInstitution.fromJson(Map<String, dynamic> json) {
    return LmInstitution(
      name: asStr(json['name']) ?? '',
      fullName: asStr(json['full_name']),
      role: asStr(json['role']),
      source: asStr(json['source']),
    );
  }
}

/// One related concept in a v2 module (its OWN section, section 6):
/// term + one-line meaning + source.
class LmExtraTerm {
  final String term;
  final String? fullName;
  final String? meaning;
  final String? source;

  const LmExtraTerm({
    required this.term,
    this.fullName,
    this.meaning,
    this.source,
  });

  factory LmExtraTerm.fromJson(Map<String, dynamic> json) {
    return LmExtraTerm(
      term: asStr(json['term']) ?? '',
      fullName: asStr(json['full_name']),
      meaning: asStr(json['meaning']),
      source: asStr(json['source']),
    );
  }
}

/// One "পার্থক্য" (distinction) row: either a plain string or
/// `{title, text}` (v1), or the v2 shape `{a, b, points: [...]}` —
/// two things compared, with the differences as bullet points.
class LmDistinction {
  final String? title;
  final String text;
  final String? a;
  final String? b;
  final List<String> points;

  const LmDistinction({
    this.title,
    required this.text,
    this.a,
    this.b,
    this.points = const [],
  });

  factory LmDistinction.fromJson(dynamic raw) {
    if (raw is String) return LmDistinction(text: raw);
    if (raw is Map<String, dynamic>) {
      return LmDistinction(
        title: asStr(raw['title']),
        text: asStr(raw['text']) ?? '',
        a: asStr(raw['a']),
        b: asStr(raw['b']),
        points: parseStringList(raw['points']) ?? const [],
      );
    }
    if (raw is Map) {
      return LmDistinction.fromJson(Map<String, dynamic>.from(raw));
    }
    return const LmDistinction(text: '');
  }

  bool get isComparison =>
      a != null && a!.trim().isNotEmpty && b != null && b!.trim().isNotEmpty;
}

/// The topic-GK lesson of a learning module (section 3). GK facts and
/// news facts stay separate: this block's sources are the authoritative
/// GK sources, shown under this section only. The v2 model adds
/// `tables` (titled label/value tables) alongside the flat facts.
class LmTopicGk {
  final String? title;
  final String? intro;
  final List<LmFact> facts;
  final List<LmGkTable> tables;
  final List<LmDistinction> distinctions;
  final List<LmSource> sources;

  const LmTopicGk({
    this.title,
    this.intro,
    this.facts = const [],
    this.tables = const [],
    this.distinctions = const [],
    this.sources = const [],
  });

  factory LmTopicGk.fromJson(Map<String, dynamic> json) {
    return LmTopicGk(
      title: asStr(json['title']),
      intro: asStr(json['intro'] ?? json['text']),
      facts: (json['facts'] is List)
          ? (json['facts'] as List).map(LmFact.fromJson).toList()
          : const [],
      tables: (json['tables'] is List)
          ? (json['tables'] as List)
              .whereType<Map>()
              .map((m) => LmGkTable.fromJson(
                  m is Map<String, dynamic>
                      ? m
                      : Map<String, dynamic>.from(m)))
              .toList()
          : const [],
      distinctions: (json['distinctions'] is List)
          ? (json['distinctions'] as List)
              .map(LmDistinction.fromJson)
              .toList()
          : const [],
      sources: parseLmSources(json['sources']),
    );
  }
}

/// The BCS/Bank exam notes of a learning module (section 4). The data
/// carries the notes under several list keys (`notes`, `points`,
/// `key_points`, `institutions`) plus an optional intro paragraph
/// (`text`); all lists are rendered as bullets in that order.
class LmExamNotes {
  final String? intro;
  final List<String> bullets;
  final List<LmSource> sources;

  const LmExamNotes({
    this.intro,
    this.bullets = const [],
    this.sources = const [],
  });

  factory LmExamNotes.fromJson(Map<String, dynamic> json) {
    final bullets = <String>[];
    for (final key in ['notes', 'points', 'key_points', 'institutions']) {
      bullets.addAll(parseStringList(json[key]) ?? const []);
    }
    return LmExamNotes(
      intro: asStr(json['text']),
      bullets: bullets,
      sources: parseLmSources(json['sources']),
    );
  }
}

/// One MCQ in the module's practice set (section 5). Two shapes
/// occur in the data:
/// * v1: options keyed A–D (`{"A": ..., "B": ...}`), `correct` the key.
/// * v2 (LEARNING_MODULE_MODEL_V2.md): options as a plain list and
///   `correct` the 0-based index. Both normalise to A–D keys here,
///   so the widget never cares which shape arrived.
/// An optional `no` number is ignored.
class LmMcq {
  final String question;
  final Map<String, String> options;
  final String correct;
  final String? explanation;

  const LmMcq({
    required this.question,
    required this.options,
    required this.correct,
    this.explanation,
  });

  factory LmMcq.fromJson(Map<String, dynamic> json) {
    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
    final opts = <String, String>{};
    final raw = json['options'];
    if (raw is List) {
      for (var i = 0; i < raw.length && i < letters.length; i++) {
        opts[letters[i]] = asStr(raw[i]) ?? '';
      }
    } else if (raw is Map) {
      final entries = raw.entries.toList();
      final numericKeys = entries.every(
        (e) => int.tryParse(e.key.toString()) != null,
      );
      for (var i = 0; i < entries.length && i < letters.length; i++) {
        final key = numericKeys
            ? letters[int.tryParse(entries[i].key.toString()) ?? i]
            : entries[i].key.toString();
        opts[key] = entries[i].value.toString();
      }
    }
    var correct = asStr(json['correct']) ?? '';
    final correctIndex = json['correct'] is int
        ? json['correct'] as int
        : int.tryParse(correct);
    if (correctIndex != null &&
        correctIndex >= 0 &&
        correctIndex < letters.length) {
      correct = letters[correctIndex];
    }
    return LmMcq(
      question: asStr(json['question']) ?? '',
      options: opts,
      correct: correct,
      explanation: asStr(json['explanation']),
    );
  }

  /// Option keys in A-B-C-D order.
  List<String> get optionKeys {
    final keys = options.keys.toList()..sort();
    return keys;
  }
}

/// One written-prep question (section 6): short or analytical, with a
/// model-answer outline. The data carries three shapes:
/// * a list of `{question, outline|model_outline|model_answer_outline,
///   type?}` — `type` may be missing, English (`short`/`analytical`)
///   or Bengali (`সংক্ষিপ্ত প্রশ্ন` / `বিশ্লেষণধর্মী প্রশ্ন` …);
/// * a map `{short: {question, outline}, analytical: {...}}`;
/// * a flat map `{short_question, short_outline, analytical_question,
///   analytical_outline}`.
/// All three normalise to the same list, short first.
class LmWrittenItem {
  final bool isAnalytical;
  final String question;
  final List<String> outline;

  const LmWrittenItem({
    required this.isAnalytical,
    required this.question,
    this.outline = const [],
  });

  static bool _isAnalytical(String? type, String question, int index) {
    final t = (type ?? '').trim();
    if (t.contains('বিশ্লেষণ') || t == 'analytical') return true;
    if (t.contains('সংক্ষিপ্ত') || t == 'short') return false;
    if (question.contains('(বিশ্লেষণধর্মী')) return true;
    if (question.contains('(সংক্ষিপ্ত')) return false;
    return index != 0;
  }

  static List<LmWrittenItem> parseList(dynamic raw) {
    if (raw is List) {
      final out = <LmWrittenItem>[];
      for (var i = 0; i < raw.length; i++) {
        final item = raw[i];
        if (item is! Map) continue;
        final m = item is Map<String, dynamic>
            ? item
            : Map<String, dynamic>.from(item);
        final question = asStr(m['question']) ?? '';
        if (question.trim().isEmpty) continue;
        out.add(LmWrittenItem(
          isAnalytical:
              _isAnalytical(asStr(m['type']), question, out.length),
          question: question,
          outline: parseStringList(m['outline'] ??
                  m['model_outline'] ??
                  m['model_answer_outline']) ??
              const [],
        ));
      }
      return out;
    }
    if (raw is Map<String, dynamic> || raw is Map) {
      final m = raw is Map<String, dynamic>
          ? raw
          : Map<String, dynamic>.from(raw);
      LmWrittenItem? nested(String key, bool analytical) {
        final v = m[key];
        if (v is! Map) return null;
        final q = asStr(v['question']) ?? '';
        if (q.trim().isEmpty) return null;
        return LmWrittenItem(
          isAnalytical: analytical,
          question: q,
          outline: parseStringList(v['outline'] ??
                  v['model_outline'] ??
                  v['model_answer_outline']) ??
              const [],
        );
      }

      final out = <LmWrittenItem>[];
      final shortNested = nested('short', false);
      if (shortNested != null) out.add(shortNested);
      final analyticalNested = nested('analytical', true);
      if (analyticalNested != null) out.add(analyticalNested);
      if (out.isNotEmpty) return out;
      final shortQ = asStr(m['short_question']);
      if (shortQ != null && shortQ.trim().isNotEmpty) {
        out.add(LmWrittenItem(
          isAnalytical: false,
          question: shortQ,
          outline: parseStringList(m['short_outline']) ?? const [],
        ));
      }
      final analyticalQ = asStr(m['analytical_question']);
      if (analyticalQ != null && analyticalQ.trim().isNotEmpty) {
        out.add(LmWrittenItem(
          isAnalytical: true,
          question: analyticalQ,
          outline: parseStringList(m['analytical_outline']) ?? const [],
        ));
      }
      return out;
    }
    return const [];
  }
}

/// One vocabulary word in the module (section 7). Synonyms and
/// antonyms arrive as a ';'-separated string (v1) or a list (v2);
/// both normalise to lists. The Bengali meaning key is
/// `bangla_meaning` (v1) or `meaning_bn` (v2).
class LmVocab {
  final String word;
  final String? banglaMeaning;
  final String? example;
  final List<String> synonyms;
  final List<String> antonyms;

  const LmVocab({
    required this.word,
    this.banglaMeaning,
    this.example,
    this.synonyms = const [],
    this.antonyms = const [],
  });

  static List<String> _wordList(dynamic raw) {
    if (raw is List) {
      return [
        for (final item in raw)
          if (asStr(item) != null && asStr(item)!.trim().isNotEmpty)
            asStr(item)!.trim(),
      ];
    }
    return splitList(asStr(raw));
  }

  /// The v1 ';'-separated spellings, for callers that need the old
  /// string shape (e.g. the Phase 4 English-content exemption set).
  String? get synonym => synonyms.isEmpty ? null : synonyms.join('; ');
  String? get antonym => antonyms.isEmpty ? null : antonyms.join('; ');

  factory LmVocab.fromJson(Map<String, dynamic> json) {
    return LmVocab(
      word: asStr(json['word']) ?? '',
      banglaMeaning:
          asStr(json['bangla_meaning'] ?? json['meaning_bn'] ?? json['meaning']),
      example: asStr(json['example']),
      synonyms: _wordList(json['synonyms'] ?? json['synonym']),
      antonyms: _wordList(json['antonyms'] ?? json['antonym']),
    );
  }
}

/// The revision block (section 8): flashcards + next-revision
/// questions. Flashcard keys are `{q, a}` or `{question, answer}`.
class LmRevision {
  final List<ExamQa> flashcards;
  final List<String> nextRevision;

  const LmRevision({
    this.flashcards = const [],
    this.nextRevision = const [],
  });

  factory LmRevision.fromJson(Map<String, dynamic> json) {
    final cards = <ExamQa>[];
    final raw = json['flashcards'];
    if (raw is List) {
      for (final item in raw) {
        if (item is! Map) continue;
        final m = item is Map<String, dynamic>
            ? item
            : Map<String, dynamic>.from(item);
        final q = asStr(m['q'] ?? m['question']) ?? '';
        final a = asStr(m['a'] ?? m['answer']) ?? '';
        if (q.trim().isEmpty && a.trim().isEmpty) continue;
        cards.add(ExamQa(q: q, a: a));
      }
    }
    return LmRevision(
      flashcards: cards,
      nextRevision: parseStringList(json['next_revision']) ?? const [],
    );
  }
}

/// The learning module of a story — the 11-section model
/// (LEARNING_MODULE_MODEL_V2.md, confirmed 2026-11-18), rendered
/// in order: hero, news_summary, verified_facts, topic_gk,
/// institutions, extra_knowledge, mcq_practice, written_prep,
/// vocabulary, revision, deep_prep. All fields are optional: a story
/// without a module parses with [Story.learningModule] null and the
/// story screen renders exactly as before. The 16 renovated editions
/// carry the v1 shape (8 sections, `exam_notes` instead of the two
/// new sections, plain-string `news_summary` source, map-keyed MCQ
/// options, string synonyms) — the parser accepts both shapes and
/// the UI renders whatever keys a file carries. `topic_gk` /
/// `exam_notes` / `institutions` / `extra_knowledge` may be the
/// literal unverified marker string instead of content — the parser
/// keeps the marker text and the UI shows it instead of content.
/// Nothing is invented: a missing part renders nothing.
class LearningModule {
  final String? heroFigure;
  final String? heroLabel;
  final String? heroNote;
  final String? heroSource;
  final String? newsSummary;
  final String? newsSource;
  final LmNewsSource? newsSourceObj;
  final List<LmFact> verifiedFacts;
  final LmTopicGk? topicGk;
  final String? topicGkMarker;
  final LmExamNotes? examNotes;
  final String? examNotesMarker;
  final List<LmInstitution> institutions;
  final String? institutionsMarker;
  final List<LmExtraTerm> extraKnowledge;
  final String? extraKnowledgeMarker;
  final List<LmMcq> mcqPractice;
  final List<LmWrittenItem> writtenPrep;
  final List<LmVocab> vocabulary;
  final LmRevision? revision;
  final List<String> deepPrep;

  const LearningModule({
    this.heroFigure,
    this.heroLabel,
    this.heroNote,
    this.heroSource,
    this.newsSummary,
    this.newsSource,
    this.newsSourceObj,
    this.verifiedFacts = const [],
    this.topicGk,
    this.topicGkMarker,
    this.examNotes,
    this.examNotesMarker,
    this.institutions = const [],
    this.institutionsMarker,
    this.extraKnowledge = const [],
    this.extraKnowledgeMarker,
    this.mcqPractice = const [],
    this.writtenPrep = const [],
    this.vocabulary = const [],
    this.revision,
    this.deepPrep = const [],
  });

  factory LearningModule.fromJson(Map<String, dynamic> json) {
    String? newsSummary;
    String? newsSource;
    LmNewsSource? newsSourceObj;
    final rawSummary = json['news_summary'];
    if (rawSummary is String) {
      newsSummary = rawSummary;
    } else if (rawSummary is Map<String, dynamic>) {
      newsSummary = asStr(rawSummary['text']);
      final src = rawSummary['source'];
      if (src is Map<String, dynamic>) {
        newsSourceObj = LmNewsSource.fromJson(src);
      } else if (src is Map) {
        newsSourceObj = LmNewsSource.fromJson(
          Map<String, dynamic>.from(src),
        );
      } else {
        newsSource = asStr(src ?? rawSummary['source_line']);
      }
    } else if (rawSummary is Map) {
      final m = Map<String, dynamic>.from(rawSummary);
      newsSummary = asStr(m['text']);
      final src = m['source'];
      if (src is Map<String, dynamic>) {
        newsSourceObj = LmNewsSource.fromJson(src);
      } else if (src is Map) {
        newsSourceObj = LmNewsSource.fromJson(
          Map<String, dynamic>.from(src),
        );
      } else {
        newsSource = asStr(src ?? m['source_line']);
      }
    }

    LmTopicGk? topicGk;
    String? topicGkMarker;
    final rawGk = json['topic_gk'];
    if (rawGk is String) {
      topicGkMarker = rawGk;
    } else if (rawGk is Map<String, dynamic>) {
      topicGk = LmTopicGk.fromJson(rawGk);
    } else if (rawGk is Map) {
      topicGk = LmTopicGk.fromJson(Map<String, dynamic>.from(rawGk));
    }

    LmExamNotes? examNotes;
    String? examNotesMarker;
    final rawNotes = json['exam_notes'];
    if (rawNotes is String) {
      examNotesMarker = rawNotes;
    } else if (rawNotes is Map<String, dynamic>) {
      examNotes = LmExamNotes.fromJson(rawNotes);
    } else if (rawNotes is Map) {
      examNotes = LmExamNotes.fromJson(Map<String, dynamic>.from(rawNotes));
    }

    List<LmInstitution> institutions = const [];
    String? institutionsMarker;
    final rawInst = json['institutions'];
    if (rawInst is String) {
      institutionsMarker = rawInst;
    } else if (rawInst is List) {
      institutions = [
        for (final item in rawInst)
          if (item is Map<String, dynamic>)
            LmInstitution.fromJson(item)
          else if (item is Map)
            LmInstitution.fromJson(Map<String, dynamic>.from(item)),
      ];
    }

    List<LmExtraTerm> extraKnowledge = const [];
    String? extraKnowledgeMarker;
    final rawExtra = json['extra_knowledge'];
    if (rawExtra is String) {
      extraKnowledgeMarker = rawExtra;
    } else if (rawExtra is List) {
      extraKnowledge = [
        for (final item in rawExtra)
          if (item is Map<String, dynamic>)
            LmExtraTerm.fromJson(item)
          else if (item is Map)
            LmExtraTerm.fromJson(Map<String, dynamic>.from(item)),
      ];
    }

    final hero = json['hero'];
    final heroMap = hero is Map<String, dynamic>
        ? hero
        : hero is Map
            ? Map<String, dynamic>.from(hero)
            : null;

    List<LmMcq> mcqs = const [];
    final rawMcqs = json['mcq_practice'];
    if (rawMcqs is List) {
      mcqs = [
        for (final item in rawMcqs)
          if (item is Map<String, dynamic>)
            LmMcq.fromJson(item)
          else if (item is Map)
            LmMcq.fromJson(Map<String, dynamic>.from(item)),
      ];
    }

    List<LmVocab> vocab = const [];
    final rawVocab = json['vocabulary'];
    if (rawVocab is List) {
      vocab = [
        for (final item in rawVocab)
          if (item is Map<String, dynamic>)
            LmVocab.fromJson(item)
          else if (item is Map)
            LmVocab.fromJson(Map<String, dynamic>.from(item)),
      ];
    }

    LmRevision? revision;
    final rawRevision = json['revision'];
    if (rawRevision is Map<String, dynamic>) {
      revision = LmRevision.fromJson(rawRevision);
    } else if (rawRevision is Map) {
      revision = LmRevision.fromJson(Map<String, dynamic>.from(rawRevision));
    }

    return LearningModule(
      heroFigure: asStr(heroMap?['figure']),
      heroLabel: asStr(heroMap?['label']),
      heroNote: asStr(heroMap?['note']),
      heroSource: asStr(heroMap?['source']),
      newsSummary: newsSummary,
      newsSource: newsSource,
      newsSourceObj: newsSourceObj,
      verifiedFacts: (json['verified_facts'] is List)
          ? (json['verified_facts'] as List).map(LmFact.fromJson).toList()
          : const [],
      topicGk: topicGk,
      topicGkMarker: topicGkMarker,
      examNotes: examNotes,
      examNotesMarker: examNotesMarker,
      institutions: institutions,
      institutionsMarker: institutionsMarker,
      extraKnowledge: extraKnowledge,
      extraKnowledgeMarker: extraKnowledgeMarker,
      mcqPractice: mcqs,
      writtenPrep: LmWrittenItem.parseList(json['written_prep']),
      vocabulary: vocab,
      revision: revision,
      deepPrep: parseStringList(json['deep_prep']) ?? const [],
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
  /// * [learningModule] — the 8-part learning module (2026-11-17
  ///   renovation, learning-module-v1). Null when the edition predates
  ///   the renovation; the story screen then renders as before.
  /// * [imageUrl] — the source article's og:image URL (Step 1 v2.3.0),
  ///   the URL only, never a downloaded file. Empty/absent when the
  ///   article has none; the story screen shows its typographic
  ///   banner instead.
  final String? oneLiner;
  final List<KeyFact> keyFacts;
  final List<String> whatHappened;
  final List<ExamQa> examQa;
  final List<RecallCard> recallCards;
  final List<String> keywords;
  final String? detail;
  final LearningModule? learningModule;
  final String? imageUrl;

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
    this.learningModule,
    this.imageUrl,
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
      imageUrl: asStr(json['image_url']),
      learningModule: json['learning_module'] is Map<String, dynamic>
          ? LearningModule.fromJson(
              json['learning_module'] as Map<String, dynamic>)
          : json['learning_module'] is Map
              ? LearningModule.fromJson(
                  Map<String, dynamic>.from(json['learning_module'] as Map))
              : null,
    );
  }

  /// Banner image URL for the story screen: the source article's
  /// og:image (URL only, hotlinked from the publisher, never
  /// downloaded). Null when the story carries none — the screen
  /// shows its typographic banner instead.
  String? get bannerImageUrl {
    final u = imageUrl ?? bn?.imageUrl;
    if (u == null || u.trim().isEmpty) return null;
    return u.trim();
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

  /// True when a Bangla overlay exists but the edition has not passed
  /// explicit human approval. In that case the loader keeps the English
  /// source and the UI explains why.
  bool banglaPendingReview;

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
    this.banglaPendingReview = false,
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
