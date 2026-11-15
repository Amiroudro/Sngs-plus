/// App-wide state: language (Bengali default), theme, selected edition,
/// bookmarks, quiz history, mistakes deck, reviewed revision words.
/// Everything persists locally with shared_preferences. No account, no
/// network, no tracking.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models.dart';
import '../services/app_update_service.dart';

class Mistake {
  final String editionDate;
  final int mcqNo;
  final String question;
  final String chosen;
  final String correct;
  final String? explanation;
  final String section;
  final bool isPractice;

  const Mistake({
    required this.editionDate,
    required this.mcqNo,
    required this.question,
    required this.chosen,
    required this.correct,
    this.explanation,
    required this.section,
    this.isPractice = false,
  });

  Map<String, dynamic> toJson() => {
        'editionDate': editionDate,
        'mcqNo': mcqNo,
        'question': question,
        'chosen': chosen,
        'correct': correct,
        'explanation': explanation,
        'section': section,
        'isPractice': isPractice,
      };

  factory Mistake.fromJson(Map<String, dynamic> json) {
    return Mistake(
      editionDate: json['editionDate'] as String? ?? '',
      mcqNo: json['mcqNo'] is int
          ? json['mcqNo'] as int
          : int.tryParse('${json['mcqNo']}') ?? 0,
      question: json['question'] as String? ?? '',
      chosen: json['chosen'] as String? ?? '',
      correct: json['correct'] as String? ?? '',
      explanation: json['explanation'] as String?,
      section: json['section'] as String? ?? '',
      isPractice: json['isPractice'] as bool? ?? false,
    );
  }
}

class QuizResult {
  final String editionDate;
  final String mode; // 'edition' or 'practice'
  final int score;
  final int total;
  final String timestamp;

  const QuizResult({
    required this.editionDate,
    required this.mode,
    required this.score,
    required this.total,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
        'editionDate': editionDate,
        'mode': mode,
        'score': score,
        'total': total,
        'timestamp': timestamp,
      };

  factory QuizResult.fromJson(Map<String, dynamic> json) {
    return QuizResult(
      editionDate: json['editionDate'] as String? ?? '',
      mode: json['mode'] as String? ?? 'edition',
      score: json['score'] is int
          ? json['score'] as int
          : int.tryParse('${json['score']}') ?? 0,
      total: json['total'] is int
          ? json['total'] as int
          : int.tryParse('${json['total']}') ?? 0,
      timestamp: json['timestamp'] as String? ?? '',
    );
  }
}

class AppState extends ChangeNotifier {
  static const _kLang = 'lang';
  static const _kDark = 'dark_mode';
  static const _kEdition = 'selected_edition';
  static const _kBookmarkedStories = 'bookmarks_stories';
  static const _kBookmarkedWords = 'bookmarks_words';
  static const _kMistakes = 'mistakes';
  static const _kQuizHistory = 'quiz_history';
  static const _kReviewedRevision = 'reviewed_revision';
  static const _kFontScale = 'font_scale';
  static const _kRecentSearches = 'recent_searches';
  static const _kReadStories = 'read_stories';
  static const _kRecallKnown = 'recall_known';
  static const _kRecallUnknown = 'recall_unknown';
  static const _kWordKnown = 'word_known';
  static const _kWordDue = 'word_unknown_due';

  SharedPreferences? _prefs;

  /// 'bn' is the default language. The toggle in Settings can switch to
  /// 'en', but the app always starts in Bengali.
  String lang = 'bn';
  bool darkMode = false;

  /// In-app font-size multiplier (0.9 / 1.0 / 1.15 / 1.3). It scales the
  /// system text size, so accessibility settings are respected, not
  /// replaced. Default 1.0.
  double fontScale = 1.0;
  String? selectedEditionDate;

  /// Recent search queries, newest first, max 8.
  final List<String> recentSearches = [];

  final Set<String> bookmarkedStories = {};
  final Set<String> bookmarkedWords = {};
  final List<Mistake> mistakes = [];
  final List<QuizResult> quizHistory = [];
  final Set<String> reviewedRevision = {};

  /// Stories the reader marked "পড়া হয়েছে" (story screen bottom bar).
  final Set<String> readStories = {};

  /// Story self-test (cloze) results, per card: keys are
  /// "editionDate:storyId:cloze0" etc. A card is in exactly one set.
  final Set<String> recallKnown = {};
  final Set<String> recallUnknown = {};

  /// Word SRS (Phase 3): per-word জানি / জানি না, keyed by
  /// "editionDate:headword" (same key scheme as bookmarks).
  /// Known words stay out of revision. Unknown words carry a due
  /// date and a stage: stage 1 -> due in 1 day, stage 2 -> 3 days,
  /// stage 3 -> 7 days (later "জানি না" taps stay at 7 days).
  final Set<String> wordKnown = {};

  /// Unknown-word due dates: key -> 'yyyy-MM-dd'.
  final Map<String, String> wordDueDates = {};

  /// Unknown-word stages: key -> 1, 2 or 3.
  final Map<String, int> wordUnknownStages = {};

  List<Edition> editions = [];
  int correctConsecutive = 0;
  String? correctRule;

  /// A newer app version advertised by GitHub (see
  /// services/app_update_service.dart). Null when up to date or
  /// when the check could not run. Shown as a banner on Home.
  UpdateInfo? availableUpdate;

  /// Records a newer version (or clears it); notifies listeners.
  void setAvailableUpdate(UpdateInfo? info) {
    availableUpdate = info;
    notifyListeners();
  }

  /// Hides the update banner for this session (it returns on the
  /// next launch while a newer version is still available).
  void dismissUpdate() {
    availableUpdate = null;
    notifyListeners();
  }

  Edition? get selectedEdition {
    if (editions.isEmpty) return null;
    if (selectedEditionDate == null) return editions.first;
    return editions.firstWhere(
      (e) => e.date == selectedEditionDate,
      orElse: () => editions.first,
    );
  }

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    lang = _prefs!.getString(_kLang) ?? 'bn';
    darkMode = _prefs!.getBool(_kDark) ?? false;
    fontScale = _prefs!.getDouble(_kFontScale) ?? 1.0;
    recentSearches.addAll(_prefs!.getStringList(_kRecentSearches) ?? const []);
    selectedEditionDate = _prefs!.getString(_kEdition);
    bookmarkedStories
        .addAll(_prefs!.getStringList(_kBookmarkedStories) ?? const []);
    bookmarkedWords
        .addAll(_prefs!.getStringList(_kBookmarkedWords) ?? const []);
    reviewedRevision
        .addAll(_prefs!.getStringList(_kReviewedRevision) ?? const []);
    readStories.addAll(_prefs!.getStringList(_kReadStories) ?? const []);
    recallKnown.addAll(_prefs!.getStringList(_kRecallKnown) ?? const []);
    recallUnknown.addAll(_prefs!.getStringList(_kRecallUnknown) ?? const []);
    wordKnown.addAll(_prefs!.getStringList(_kWordKnown) ?? const []);
    for (final raw in _prefs!.getStringList(_kWordDue) ?? const []) {
      try {
        final m = jsonDecode(raw) as Map<String, dynamic>;
        final key = m['k'] as String?;
        final due = m['due'] as String?;
        final stage = m['stage'] is int
            ? m['stage'] as int
            : int.tryParse('${m['stage']}');
        if (key != null && due != null && stage != null) {
          wordDueDates[key] = due;
          wordUnknownStages[key] = stage;
        }
      } catch (_) {}
    }
    for (final raw in _prefs!.getStringList(_kMistakes) ?? const []) {
      try {
        mistakes.add(Mistake.fromJson(jsonDecode(raw) as Map<String, dynamic>));
      } catch (_) {}
    }
    for (final raw in _prefs!.getStringList(_kQuizHistory) ?? const []) {
      try {
        quizHistory
            .add(QuizResult.fromJson(jsonDecode(raw) as Map<String, dynamic>));
      } catch (_) {}
    }
    notifyListeners();
  }

  /// Loads a new edition list. The app always shows the newest
  /// available edition: whenever the newest date in the list is
  /// newer than the current selection (or there is no selection, or
  /// the selected date is gone), the selection moves to the newest
  /// and is persisted. A refresh that brings in today's edition
  /// therefore switches the screen to it on its own — the reader
  /// never has to pick the new day by hand. Within one session the
  /// date picker still lets the reader browse older editions; the
  /// next load or refresh returns to the newest.
  Future<void> setEditions(
      List<Edition> loaded, int correct, String? rule) async {
    editions = loaded;
    correctConsecutive = correct;
    correctRule = rule;
    String? newest;
    for (final e in editions) {
      if (newest == null || e.date.compareTo(newest) > 0) {
        newest = e.date;
      }
    }
    if (newest == null) {
      selectedEditionDate = null;
    } else if (selectedEditionDate == null ||
        !editions.any((e) => e.date == selectedEditionDate) ||
        selectedEditionDate!.compareTo(newest) < 0) {
      selectedEditionDate = newest;
      await _prefs?.setString(_kEdition, newest);
    }
    notifyListeners();
  }

  Future<void> setLang(String value) async {
    lang = value;
    await _prefs?.setString(_kLang, value);
    notifyListeners();
  }

  Future<void> setDarkMode(bool value) async {
    darkMode = value;
    await _prefs?.setBool(_kDark, value);
    notifyListeners();
  }

  Future<void> setFontScale(double value) async {
    fontScale = value;
    await _prefs?.setDouble(_kFontScale, value);
    notifyListeners();
  }

  Future<void> addRecentSearch(String query) async {
    final q = query.trim();
    if (q.isEmpty) return;
    recentSearches.remove(q);
    recentSearches.insert(0, q);
    if (recentSearches.length > 8) {
      recentSearches.removeRange(8, recentSearches.length);
    }
    await _prefs?.setStringList(_kRecentSearches, recentSearches);
    notifyListeners();
  }

  Future<void> clearRecentSearches() async {
    recentSearches.clear();
    await _prefs?.setStringList(_kRecentSearches, const []);
    notifyListeners();
  }

  // --- Quiz stats (computed from the saved quiz history only) ----------

  int get totalQuizzes => quizHistory.length;

  /// Best result by score ratio (ties: the most recent one).
  QuizResult? get bestResult {
    if (quizHistory.isEmpty) return null;
    QuizResult? best;
    for (final r in quizHistory) {
      if (r.total == 0) continue;
      if (best == null || r.score / r.total > best.score / best.total) {
        best = r;
      }
    }
    return best;
  }

  /// Mean score ratio across all saved quizzes, as a whole percent.
  int get averagePercent {
    final valid = quizHistory.where((r) => r.total > 0).toList();
    if (valid.isEmpty) return 0;
    var sum = 0.0;
    for (final r in valid) {
      sum += r.score / r.total;
    }
    return (sum / valid.length * 100).round();
  }

  /// Consecutive days with at least one quiz, ending today (or
  /// yesterday when today has no quiz yet — the streak is still alive).
  int get quizStreakDays {
    if (quizHistory.isEmpty) return 0;
    final days = <DateTime>{};
    for (final r in quizHistory) {
      final dt = DateTime.tryParse(r.timestamp);
      if (dt != null) days.add(DateTime(dt.year, dt.month, dt.day));
    }
    final now = DateTime.now();
    var day = DateTime(now.year, now.month, now.day);
    if (!days.contains(day)) {
      day = day.subtract(const Duration(days: 1));
    }
    var streak = 0;
    while (days.contains(day)) {
      streak++;
      day = day.subtract(const Duration(days: 1));
    }
    return streak;
  }

  Future<void> selectEdition(String date) async {
    selectedEditionDate = date;
    await _prefs?.setString(_kEdition, date);
    notifyListeners();
  }

  String storyKey(String editionDate, String storyId) =>
      '$editionDate:$storyId';
  String wordKey(String editionDate, String headword) =>
      '$editionDate:$headword';

  bool isStoryBookmarked(String editionDate, String storyId) =>
      bookmarkedStories.contains(storyKey(editionDate, storyId));

  bool isWordBookmarked(String editionDate, String headword) =>
      bookmarkedWords.contains(wordKey(editionDate, headword));

  Future<void> toggleStoryBookmark(String editionDate, String storyId) async {
    final key = storyKey(editionDate, storyId);
    if (bookmarkedStories.contains(key)) {
      bookmarkedStories.remove(key);
    } else {
      bookmarkedStories.add(key);
    }
    await _prefs?.setStringList(
        _kBookmarkedStories, bookmarkedStories.toList());
    notifyListeners();
  }

  Future<void> toggleWordBookmark(String editionDate, String headword) async {
    final key = wordKey(editionDate, headword);
    if (bookmarkedWords.contains(key)) {
      bookmarkedWords.remove(key);
    } else {
      bookmarkedWords.add(key);
    }
    await _prefs?.setStringList(_kBookmarkedWords, bookmarkedWords.toList());
    notifyListeners();
  }

  Future<void> addMistakes(List<Mistake> newMistakes) async {
    // Avoid exact duplicates from retaking the same quiz.
    for (final m in newMistakes) {
      final exists = mistakes.any((e) =>
          e.editionDate == m.editionDate &&
          e.mcqNo == m.mcqNo &&
          e.question == m.question &&
          e.isPractice == m.isPractice);
      if (!exists) mistakes.add(m);
    }
    await _prefs?.setStringList(
        _kMistakes, mistakes.map((m) => jsonEncode(m.toJson())).toList());
    notifyListeners();
  }

  Future<void> clearMistakes() async {
    mistakes.clear();
    await _prefs?.setStringList(_kMistakes, const []);
    notifyListeners();
  }

  Future<void> recordQuizResult(QuizResult result) async {
    quizHistory.insert(0, result);
    if (quizHistory.length > 50) {
      quizHistory.removeRange(50, quizHistory.length);
    }
    await _prefs?.setStringList(
        _kQuizHistory, quizHistory.map((r) => jsonEncode(r.toJson())).toList());
    notifyListeners();
  }

  Future<void> toggleReviewedRevision(
      String editionDate, String headword) async {
    final key = wordKey(editionDate, headword);
    if (reviewedRevision.contains(key)) {
      reviewedRevision.remove(key);
    } else {
      reviewedRevision.add(key);
    }
    await _prefs?.setStringList(_kReviewedRevision, reviewedRevision.toList());
    notifyListeners();
  }

  bool isRevisionReviewed(String editionDate, String headword) =>
      reviewedRevision.contains(wordKey(editionDate, headword));

  // --- Story read state + self-test (Phase 2 story screen) ----------

  bool isStoryRead(String editionDate, String storyId) =>
      readStories.contains(storyKey(editionDate, storyId));

  Future<void> toggleStoryRead(String editionDate, String storyId) async {
    final key = storyKey(editionDate, storyId);
    if (readStories.contains(key)) {
      readStories.remove(key);
    } else {
      readStories.add(key);
    }
    await _prefs?.setStringList(_kReadStories, readStories.toList());
    notifyListeners();
  }

  String recallKey(String editionDate, String storyId, int index) =>
      '$editionDate:$storyId:cloze$index';

  /// Self-test result for one cloze card: true = "জানি",
  /// false = "জানি না", null = not answered yet.
  bool? recallResult(String editionDate, String storyId, int index) {
    final key = recallKey(editionDate, storyId, index);
    if (recallKnown.contains(key)) return true;
    if (recallUnknown.contains(key)) return false;
    return null;
  }

  Future<void> setRecallResult(
    String editionDate,
    String storyId,
    int index,
    bool known,
  ) async {
    final key = recallKey(editionDate, storyId, index);
    if (known) {
      recallKnown.add(key);
      recallUnknown.remove(key);
    } else {
      recallUnknown.add(key);
      recallKnown.remove(key);
    }
    await _prefs?.setStringList(_kRecallKnown, recallKnown.toList());
    await _prefs?.setStringList(_kRecallUnknown, recallUnknown.toList());
    notifyListeners();
  }

  // --- Word SRS: জানি / জানি না + 1 / 3 / 7-day revision (Phase 3) ---

  /// "জানি না" intervals by stage: 1st tap -> 1 day, 2nd -> 3 days,
  /// 3rd and later -> 7 days.
  static const List<int> unknownIntervalsDays = [1, 3, 7];

  /// Self-test result for one word: true = "জানি", false = "জানি না",
  /// null = not answered yet.
  bool? wordResult(String editionDate, String headword) {
    final key = wordKey(editionDate, headword);
    if (wordKnown.contains(key)) return true;
    if (wordDueDates.containsKey(key)) return false;
    return null;
  }

  /// Due date ('yyyy-MM-dd') for a "জানি না" word, or null.
  String? wordDueDate(String editionDate, String headword) =>
      wordDueDates[wordKey(editionDate, headword)];

  /// Current unknown stage (1-3) for a "জানি না" word, or 0.
  int wordUnknownStage(String editionDate, String headword) =>
      wordUnknownStages[wordKey(editionDate, headword)] ?? 0;

  static String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  static DateTime _dateOnly(DateTime d) => DateTime(d.year, d.month, d.day);

  Future<void> _persistWordSrs() async {
    await _prefs?.setStringList(_kWordKnown, wordKnown.toList());
    await _prefs?.setStringList(
      _kWordDue,
      wordDueDates.entries
          .map((e) => jsonEncode({
                'k': e.key,
                'due': e.value,
                'stage': wordUnknownStages[e.key] ?? 1,
              }))
          .toList(),
    );
  }

  /// Records a জানি / জানি না answer. "জানি" clears any due date,
  /// so the word stays out of revision. "জানি না" advances the
  /// stage (1 -> 2 -> 3, capped) and sets the next due date that
  /// many days after [now] (default: today).
  Future<void> setWordResult(
    String editionDate,
    String headword,
    bool known, {
    DateTime? now,
  }) async {
    final key = wordKey(editionDate, headword);
    if (known) {
      wordKnown.add(key);
      wordDueDates.remove(key);
      wordUnknownStages.remove(key);
    } else {
      final stage = ((wordUnknownStages[key] ?? 0) + 1).clamp(1, 3);
      final interval =
          unknownIntervalsDays[(stage - 1).clamp(0, 2)];
      final due = _dateOnly(now ?? DateTime.now())
          .add(Duration(days: interval));
      wordKnown.remove(key);
      wordDueDates[key] = _isoDate(due);
      wordUnknownStages[key] = stage;
    }
    await _persistWordSrs();
    notifyListeners();
  }

  /// True when a "জানি না" word's due date is today or past.
  bool isWordDue(String editionDate, String headword, {DateTime? now}) {
    final due = wordDueDate(editionDate, headword);
    if (due == null) return false;
    final dt = DateTime.tryParse(due);
    if (dt == null) return false;
    return !_dateOnly(dt).isAfter(_dateOnly(now ?? DateTime.now()));
  }

  /// This edition's words due for revision: "জানি না" words whose
  /// due date is today or past. Overdue first (earliest due date),
  /// then alphabetically. "জানি" words and never-answered words are
  /// never in this list. This is the PER-EDITION pool; the revision
  /// tab shows [dueRevisionWords], the same rule across the last 7
  /// editions (Phase 5).
  List<VocabWord> dueWordsFor(Edition edition, {DateTime? now}) {
    final seen = <String>{};
    final due = <VocabWord>[];
    for (final w in [...edition.words, ...edition.revisionWords]) {
      if (!seen.add(w.headword)) continue;
      if (isWordDue(edition.date, w.headword, now: now)) due.add(w);
    }
    due.sort((a, b) {
      final da = wordDueDate(edition.date, a.headword) ?? '';
      final db = wordDueDate(edition.date, b.headword) ?? '';
      final byDate = da.compareTo(db);
      if (byDate != 0) return byDate;
      return a.headword.compareTo(b.headword);
    });
    return due;
  }

  /// Phase 5: the revision window is the 7 newest editions by
  /// edition_date. Words from older editions are out of revision
  /// (their SRS state is kept — nothing is deleted — they simply
  /// stop appearing until a newer edition re-uses the word).
  static const int revisionWindowEditions = 7;

  List<Edition> get revisionWindow {
    final sorted = [...editions]
      ..sort((a, b) => b.date.compareTo(a.date));
    return sorted.take(revisionWindowEditions).toList();
  }

  /// Due revision words across the last 7 editions, each with the
  /// edition it belongs to (the SRS key is editionDate:headword, so
  /// the edition is needed to open the word and to read its due
  /// date). Same rules as [dueWordsFor]: only "জানি না" words whose
  /// due date is today or past; "জানি" words and never-answered
  /// words never appear. Overdue first (earliest due date), then
  /// newest edition, then alphabetically. Per-edition
  /// revision_words lists still feed the pool through
  /// [dueWordsFor], unchanged.
  List<({Edition edition, VocabWord word})> dueRevisionWords(
      {DateTime? now}) {
    final out = <({Edition edition, VocabWord word, String due})>[];
    for (final edition in revisionWindow) {
      for (final word in dueWordsFor(edition, now: now)) {
        out.add((
          edition: edition,
          word: word,
          due: wordDueDate(edition.date, word.headword) ?? '',
        ));
      }
    }
    out.sort((a, b) {
      final byDue = a.due.compareTo(b.due);
      if (byDue != 0) return byDue;
      final byEdition = b.edition.date.compareTo(a.edition.date);
      if (byEdition != 0) return byEdition;
      return a.word.headword.compareTo(b.word.headword);
    });
    return out
        .map((e) => (edition: e.edition, word: e.word))
        .toList();
  }

  Story? findStory(String editionDate, String storyId) {
    for (final e in editions) {
      if (e.date != editionDate) continue;
      for (final s in e.stories) {
        if (s.id == storyId) return s;
      }
    }
    return null;
  }

  VocabWord? findWord(String editionDate, String headword) {
    for (final e in editions) {
      if (e.date != editionDate) continue;
      for (final w in [...e.words, ...e.revisionWords]) {
        if (w.headword == headword) return w;
      }
    }
    return null;
  }

  Edition? findEdition(String date) {
    for (final e in editions) {
      if (e.date == date) return e;
    }
    return null;
  }
}
