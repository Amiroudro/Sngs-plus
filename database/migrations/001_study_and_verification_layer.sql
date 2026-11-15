PRAGMA foreign_keys = ON;

-- Source health and coverage history. A failed fetch is recorded, never
-- silently treated as a publisher with no news.
CREATE TABLE IF NOT EXISTS source_checks (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  method TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'ok', 'empty', 'blocked', 'robots_disallowed', 'timeout',
    'http_error', 'parse_error', 'unreachable', 'disabled'
  )),
  items_found INTEGER NOT NULL DEFAULT 0 CHECK (items_found >= 0),
  latest_published_at TEXT,
  error_detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_source_checks_source_time
  ON source_checks(source_id, checked_at DESC);

-- Multiple pieces of evidence may support or contradict one fact.
-- The fact's original article remains separately traceable.
CREATE TABLE IF NOT EXISTS fact_evidence (
  id INTEGER PRIMARY KEY,
  fact_id INTEGER NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
  article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
  evidence_type TEXT NOT NULL CHECK (evidence_type IN (
    'reported_support', 'primary_confirmation', 'independent_corroboration',
    'contradiction', 'context'
  )),
  quote_or_reference TEXT NOT NULL,
  source_url TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (verification_status IN (
      'unreviewed', 'supports', 'partly_supports', 'contradicts', 'inconclusive'
    )),
  checked_at TEXT,
  reviewer_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_fact_evidence_fact
  ON fact_evidence(fact_id);

-- Structured exam questions with options stored separately so the app can
-- shuffle answer positions without changing the canonical answer.
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY,
  event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
  language TEXT NOT NULL CHECK (language IN ('en', 'bn')),
  question_type TEXT NOT NULL CHECK (question_type IN (
    'mcq', 'short', 'analytical', 'recall'
  )),
  stem TEXT NOT NULL,
  answer_text TEXT,
  explanation TEXT,
  difficulty TEXT CHECK (difficulty IN ('basic', 'intermediate', 'advanced')),
  exam_track TEXT NOT NULL DEFAULT 'general'
    CHECK (exam_track IN ('general', 'bcs', 'bank', 'government', 'other')),
  source_fact_id INTEGER REFERENCES facts(id) ON DELETE SET NULL,
  quality_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (quality_status IN ('needs_review', 'approved', 'rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS question_options (
  id INTEGER PRIMARY KEY,
  question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  option_key TEXT NOT NULL,
  option_text TEXT NOT NULL,
  is_correct INTEGER NOT NULL DEFAULT 0 CHECK (is_correct IN (0, 1)),
  UNIQUE(question_id, option_key)
);
CREATE INDEX IF NOT EXISTS idx_questions_event
  ON questions(event_id, quality_status);

-- Reusable vocabulary entries and the article contexts that justify them.
CREATE TABLE IF NOT EXISTS vocabulary_entries (
  id INTEGER PRIMARY KEY,
  lemma TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'bn')),
  part_of_speech TEXT,
  ipa TEXT,
  bn_phonetic TEXT,
  meaning_bn TEXT,
  definition_en TEXT,
  synonyms_json TEXT NOT NULL DEFAULT '[]',
  antonyms_json TEXT NOT NULL DEFAULT '[]',
  word_family_json TEXT NOT NULL DEFAULT '[]',
  collocations_json TEXT NOT NULL DEFAULT '[]',
  UNIQUE(lemma, language)
);
CREATE TABLE IF NOT EXISTS vocabulary_occurrences (
  id INTEGER PRIMARY KEY,
  vocabulary_id INTEGER NOT NULL REFERENCES vocabulary_entries(id) ON DELETE CASCADE,
  article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
  event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
  source_sentence TEXT,
  source_url TEXT,
  published_at TEXT,
  UNIQUE(vocabulary_id, article_id, source_sentence)
);
CREATE INDEX IF NOT EXISTS idx_vocab_occurrences_vocab
  ON vocabulary_occurrences(vocabulary_id);

-- Per-learner review state. learner_id is an app-generated opaque identifier;
-- no email, phone number or real-world identity is stored here.
CREATE TABLE IF NOT EXISTS review_progress (
  id INTEGER PRIMARY KEY,
  learner_id TEXT NOT NULL,
  question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
  vocabulary_id INTEGER REFERENCES vocabulary_entries(id) ON DELETE CASCADE,
  due_at TEXT NOT NULL,
  interval_days INTEGER NOT NULL DEFAULT 1 CHECK (interval_days > 0),
  repetitions INTEGER NOT NULL DEFAULT 0 CHECK (repetitions >= 0),
  last_result TEXT CHECK (last_result IN ('correct', 'incorrect', 'skipped')),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (
    (question_id IS NOT NULL AND vocabulary_id IS NULL) OR
    (question_id IS NULL AND vocabulary_id IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS idx_review_due
  ON review_progress(learner_id, due_at);

-- Append-only editorial corrections. Published facts and summaries should
-- be corrected with an audit trail rather than silently overwritten.
CREATE TABLE IF NOT EXISTS editorial_corrections (
  id INTEGER PRIMARY KEY,
  event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
  article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
  field_name TEXT NOT NULL,
  previous_value TEXT,
  corrected_value TEXT NOT NULL,
  reason TEXT NOT NULL,
  source_url TEXT,
  corrected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
