/// Exam-pattern logic for the word section and the practice quiz.
///
/// HONESTY RULE (from the task): a previous-exam reference is shown ONLY
/// when it is verified in the edition data or in the engine's
/// PAST_QUESTION_PATTERNS.md
/// (~/workspace/english-daily-ai/claude-project/PAST_QUESTION_PATTERNS.md).
/// No "asked in 43rd BCS" claim is ever invented.
///
/// What that file actually verifies:
/// * Question types: synonym/antonym (most frequent), idioms & phrases,
///   phrasal verbs, one-word substitution, spelling, fill in the blank
///   (preposition/article/verb form), analogy (Bank, IBA-style).
/// * Topic families that generate the most vocab: Economy & banking
///   (inflation, deficit, remittance, monetary policy, fiscal, subsidy,
///   austerity); Governance (accountability, transparency, bureaucracy,
///   judiciary); International (diplomacy, bilateral, sanction, treaty,
///   summit); Environment (climate, emission, renewable, adaptation);
///   Social (disparity, migration, labour unrest, gender equality).
/// * One explicit previous-question family: "mitigate/mitigation"
///   (Bank previous-question family).
///
/// Only five headwords in the two bundled editions match those verified
/// families. Every other word honestly shows "no specific previous-exam
/// reference". The exam-type chips for a word (item 11 of the word
/// section) are DERIVED from the question-type list above plus the word's
/// own data fields — e.g. a word with synonyms fits synonym questions;
/// a word with a definition fits one-word substitution. Nothing else.
library;

import 'dart:math';

import '../models.dart';

/// Verified pattern notes, keyed by lowercase headword. Source:
/// PAST_QUESTION_PATTERNS.md (see the file header). The Bengali text
/// states the family; it never claims a specific exam year or sitting.
const Map<String, String> verifiedExamPatterns = {
  // Governance family: "bureaucracy" is listed.
  'bureaucratic': 'শাসন শব্দ-পরিবার।',
  // International family: "bilateral" and "sanction" are listed.
  'bilateral': 'আন্তর্জাতিক শব্দ-পরিবার।',
  'sanction': 'আন্তর্জাতিক শব্দ-পরিবার।',
  // Environment family: "adaptation" is listed.
  'adaptation': 'পরিবেশ শব্দ-পরিবার।',
  // Explicit Bank previous-question family named in the file.
  'mitigation': 'ব্যাংকের আগের প্রশ্নের পরিবার।',
};

/// Exam question types a word fits, derived from the question-type list
/// in PAST_QUESTION_PATTERNS.md and the word's own data. Labels are
/// Bengali (the UI language); the English type name is kept in brackets
/// so the mapping stays checkable.
List<String> examTypesFor(VocabWord word, Edition edition) {
  final types = <String>[
    'অর্থ (meaning)',
    'বানান (spelling)',
    'পদ (part of speech)',
    // Every word has an English definition, so every word can be asked
    // as a one-word substitution ("a sum of money paid on retirement"
    // = gratuity). That is a format derivation, not a data claim.
    'এক শব্দে প্রকাশ (one-word substitution)',
  ];
  if (word.hasSynonyms) {
    types.add('প্রতিশব্দ (synonym)');
    // A word with a synonym pair can appear in an analogy item.
    types.add('উপমা (analogy)');
  }
  if (word.hasAntonyms) types.add('বিপরীত শব্দ (antonym)');
  if (word.wordFamily.length >= 2) {
    types.add('বিভিন্ন পদ হিসেবে ব্যবহার (parts of speech)');
  }
  if (word.hasCollocations) {
    types.add('শূন্যস্থান পূরণ / উপযুক্ত শব্দবন্ধ (fill in the blank)');
  }
  if (edition.relatedPhrasesFor(word).isNotEmpty) {
    types.add('idiom / phrase / group verb');
  }
  return types;
}

// ---------------------------------------------------------------------------
// Practice questions generated from the edition's word data.
// ---------------------------------------------------------------------------

/// One generated practice question. Clearly labelled in the UI as
/// practice generated from the edition words — never confused with the
/// edition's own 25 MCQs.
class PracticeQuestion {
  final String type; // synonym | antonym | spelling | analogy
  final String question;
  final List<String> options;
  final int correctIndex;
  final String explanation;
  final String sourceWord;

  const PracticeQuestion({
    required this.type,
    required this.question,
    required this.options,
    required this.correctIndex,
    required this.explanation,
    required this.sourceWord,
  });
}

List<String> _shuffled(List<String> items, Random rng) {
  final copy = List<String>.of(items);
  copy.shuffle(rng);
  return copy;
}

/// Builds up to 10 synonym, 10 antonym, 10 spelling and 5 analogy
/// practice questions from [edition]'s words. Deterministic: the same
/// edition always produces the same set (seeded by the edition date),
/// so results are reproducible and checkable.
List<PracticeQuestion> buildPracticeQuestions(Edition edition) {
  final rng = Random(edition.date.hashCode);
  final out = <PracticeQuestion>[];
  final words = edition.words.where((w) => w.headword.isNotEmpty).toList();

  // Pool of first-synonyms / first-antonyms for distractors.
  final synonymPool = <String, String>{};
  final antonymPool = <String, String>{};
  for (final w in words) {
    if (w.synonyms.isNotEmpty) synonymPool[w.headword] = w.synonyms.first;
    if (w.antonyms.isNotEmpty) antonymPool[w.headword] = w.antonyms.first;
  }

  List<String> distractors(
      Map<String, String> pool, String excludeWord, String correct) {
    final others = pool.entries
        .where((e) => e.key != excludeWord && e.value != correct)
        .map((e) => e.value)
        .toSet()
        .toList();
    others.shuffle(rng);
    return others.take(3).toList();
  }

  // --- Synonym practice ---
  final synWords = words.where((w) => w.synonyms.isNotEmpty).toList()
    ..shuffle(rng);
  for (final w in synWords.take(10)) {
    final correct = w.synonyms.first;
    final d = distractors(synonymPool, w.headword, correct);
    if (d.length < 3) continue;
    final options = _shuffled([correct, ...d], rng);
    out.add(PracticeQuestion(
      type: 'synonym',
      question: "'${w.headword}' শব্দের প্রতিশব্দ কোনটি?",
      options: options,
      correctIndex: options.indexOf(correct),
      explanation: "'${w.headword}' শব্দের প্রতিশব্দ: $correct। "
          "বাংলা অর্থ: ${w.banglaMeaning ?? '—'}।",
      sourceWord: w.headword,
    ));
  }

  // --- Antonym practice ---
  final antWords = words.where((w) => w.antonyms.isNotEmpty).toList()
    ..shuffle(rng);
  for (final w in antWords.take(10)) {
    final correct = w.antonyms.first;
    final d = distractors(antonymPool, w.headword, correct);
    if (d.length < 3) continue;
    final options = _shuffled([correct, ...d], rng);
    out.add(PracticeQuestion(
      type: 'antonym',
      question: "'${w.headword}' শব্দের বিপরীত শব্দ কোনটি?",
      options: options,
      correctIndex: options.indexOf(correct),
      explanation: "'${w.headword}' শব্দের বিপরীত শব্দ: $correct। "
          "বাংলা অর্থ: ${w.banglaMeaning ?? '—'}।",
      sourceWord: w.headword,
    ));
  }

  // --- Spelling practice: the correct headword plus three mechanical
  // misspellings (swap adjacent letters / drop a letter / double one).
  // The misspellings are generated, never taken from any source.
  final spellWords = words.where((w) => w.headword.length >= 5).toList()
    ..shuffle(rng);
  for (final w in spellWords.take(10)) {
    final bad = misspellings(w.headword, rng);
    if (bad.length < 3) continue;
    final options = _shuffled([w.headword, ...bad.take(3)], rng);
    out.add(PracticeQuestion(
      type: 'spelling',
      question: '\'${w.banglaMeaning ?? w.headword}\' — সঠিক বানান কোনটি?',
      options: options,
      correctIndex: options.indexOf(w.headword),
      explanation: 'সঠিক বানান: ${w.headword}।',
      sourceWord: w.headword,
    ));
  }

  // --- Analogy practice: A : synonym(A) :: B : synonym(B).
  // Built only from word:synonym pairs that exist in the data.
  final pairWords = words.where((w) => w.synonyms.isNotEmpty).toList()
    ..shuffle(rng);
  if (pairWords.length >= 2) {
    var made = 0;
    for (var i = 0; i + 1 < pairWords.length && made < 5; i += 2) {
      final a = pairWords[i];
      final b = pairWords[i + 1];
      final correct = b.synonyms.first;
      final d = distractors(synonymPool, b.headword, correct)
          .where((x) => x != a.synonyms.first)
          .toList();
      if (d.length < 3) continue;
      final options = _shuffled([correct, ...d], rng);
      out.add(PracticeQuestion(
        type: 'analogy',
        question: '${a.headword} : ${a.synonyms.first} :: ${b.headword} : ?',
        options: options,
        correctIndex: options.indexOf(correct),
        explanation: "'${a.headword}' শব্দের প্রতিশব্দ ${a.synonyms.first}; "
            "তেমনি '${b.headword}' শব্দের প্রতিশব্দ $correct।",
        sourceWord: b.headword,
      ));
      made++;
    }
  }

  out.shuffle(rng);
  return out;
}

/// Three mechanical misspellings of [word]. Pure string operations:
/// swap two adjacent interior letters, drop one interior letter, and
/// double one interior letter. Results are guaranteed distinct from the
/// word itself and from each other; an empty list is returned when a
/// word is too short to misspell three different ways.
List<String> misspellings(String word, Random rng) {
  final out = <String>{};
  final letters = word.split('');
  if (letters.length < 5) return const [];

  // Swap an adjacent pair (not the first two, to keep it non-trivial).
  for (var attempt = 0; attempt < 8 && out.isEmpty; attempt++) {
    final i = 2 + rng.nextInt(letters.length - 3);
    if (letters[i] == letters[i + 1]) continue;
    final copy = List<String>.of(letters);
    final tmp = copy[i];
    copy[i] = copy[i + 1];
    copy[i + 1] = tmp;
    out.add(copy.join());
  }
  // Drop one interior letter.
  for (var attempt = 0; attempt < 8 && out.length < 2; attempt++) {
    final i = 1 + rng.nextInt(letters.length - 2);
    final copy = List<String>.of(letters)..removeAt(i);
    out.add(copy.join());
  }
  // Double one interior letter.
  for (var attempt = 0; attempt < 8 && out.length < 3; attempt++) {
    final i = 1 + rng.nextInt(letters.length - 2);
    final copy = List<String>.of(letters)..insert(i, letters[i]);
    out.add(copy.join());
  }
  out.remove(word);
  return out.toList();
}
