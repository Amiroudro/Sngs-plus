PRAGMA foreign_keys = ON;

-- Append-only publisher rights reviews. The latest row for a source is its
-- current operational rights state; earlier rows remain available for audit.
CREATE TABLE IF NOT EXISTS source_rights_reviews (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  rights_status TEXT NOT NULL CHECK (rights_status IN (
    'unknown', 'rss_headlines_only', 'permission_required', 'licensed', 'disabled'
  )),
  terms_url TEXT,
  licence_scope TEXT,
  permission_evidence TEXT,
  reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  reviewer_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_source_rights_latest
  ON source_rights_reviews(source_id, reviewed_at DESC, id DESC);

-- A generated translation or summary is not reader-ready until reviewed.
-- Keep the original article and its URL as the canonical source record.
CREATE TABLE IF NOT EXISTS article_localizations (
  id INTEGER PRIMARY KEY,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  language TEXT NOT NULL CHECK (language IN ('en', 'bn')),
  headline TEXT,
  summary TEXT,
  key_facts_json TEXT NOT NULL DEFAULT '[]',
  generation_method TEXT NOT NULL CHECK (generation_method IN (
    'human', 'llm', 'deterministic', 'imported'
  )),
  quality_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (quality_status IN ('needs_review', 'approved', 'rejected')),
  reviewer_note TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(article_id, language)
);
CREATE INDEX IF NOT EXISTS idx_localizations_review
  ON article_localizations(quality_status, language);

-- Exam value is independent from Engine v2's 0-3 processing score.
CREATE TABLE IF NOT EXISTS article_exam_assessments (
  id INTEGER PRIMARY KEY,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  exam_relevance_score INTEGER NOT NULL
    CHECK (exam_relevance_score BETWEEN 0 AND 10),
  exam_relevance_reason TEXT NOT NULL,
  exam_tracks_json TEXT NOT NULL DEFAULT '[]',
  retention_status TEXT NOT NULL CHECK (retention_status IN (
    'full_note', 'short_note', 'archive_only'
  )),
  review_required INTEGER NOT NULL DEFAULT 0 CHECK (review_required IN (0, 1)),
  review_reason TEXT,
  assessed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(article_id)
);
CREATE INDEX IF NOT EXISTS idx_exam_assessments_score
  ON article_exam_assessments(exam_relevance_score DESC, assessed_at DESC);
