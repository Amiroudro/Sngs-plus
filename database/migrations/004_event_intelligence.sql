PRAGMA foreign_keys = ON;

-- Event Intelligence v1.
-- This migration adds structured records for three-level summaries,
-- chronological event timelines and source-by-source perspectives.
-- It does not modify the published-edition registry or edition JSON files.

ALTER TABLE events ADD COLUMN canonical_title TEXT;
ALTER TABLE events ADD COLUMN description TEXT;
ALTER TABLE events ADD COLUMN first_reported_at TEXT;
ALTER TABLE events ADD COLUMN last_activity_at TEXT;
ALTER TABLE events ADD COLUMN editorial_status TEXT NOT NULL DEFAULT 'needs_review'
  CHECK (editorial_status IN ('needs_review', 'approved', 'archived'));

-- Keep each summary level as its own versioned, reviewable record.
-- Existing summaries.short_summary remains untouched for backwards compatibility.
CREATE TABLE IF NOT EXISTS event_summary_versions (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  language TEXT NOT NULL CHECK (language IN ('en', 'bn')),
  summary_level TEXT NOT NULL CHECK (summary_level IN ('quick', 'standard', 'deep')),
  version INTEGER NOT NULL CHECK (version > 0),
  content TEXT NOT NULL CHECK (length(trim(content)) > 0),
  why_it_matters TEXT,
  context_note TEXT,
  quality_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (quality_status IN ('needs_review', 'approved', 'rejected')),
  generation_method TEXT NOT NULL DEFAULT 'human'
    CHECK (generation_method IN ('human', 'deterministic', 'llm', 'imported')),
  model_version TEXT,
  source_article_ids_json TEXT NOT NULL DEFAULT '[]',
  reviewer_note TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(event_id, language, summary_level, version)
);
CREATE INDEX IF NOT EXISTS idx_event_summaries_public
  ON event_summary_versions(event_id, language, summary_level, quality_status, version DESC);

-- Timeline entries require a traceable source article. The event date may be
-- unknown; published_at records when the source reported it, not when the
-- underlying event happened.
CREATE TABLE IF NOT EXISTS event_timeline_entries (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  source_article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
  entry_type TEXT NOT NULL CHECK (entry_type IN (
    'background', 'announcement', 'decision', 'incident', 'development',
    'response', 'outcome', 'correction'
  )),
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),
  description TEXT NOT NULL CHECK (length(trim(description)) > 0),
  occurred_at TEXT,
  reported_at TEXT,
  chronology_precision TEXT NOT NULL DEFAULT 'unknown'
    CHECK (chronology_precision IN ('exact', 'date_only', 'approximate', 'unknown')),
  verification_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (verification_status IN (
      'unreviewed', 'single_source', 'corroborated', 'primary_confirmed',
      'disputed', 'corrected'
    )),
  publication_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (publication_status IN ('needs_review', 'approved', 'rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(event_id, source_article_id, entry_type, title)
);
CREATE INDEX IF NOT EXISTS idx_event_timeline_order
  ON event_timeline_entries(event_id, occurred_at, reported_at, id);
CREATE INDEX IF NOT EXISTS idx_event_timeline_review
  ON event_timeline_entries(publication_status, verification_status);

-- One perspective record per article/event pair. This stores editorially
-- reviewed framing and emphasis, not an inferred political position.
CREATE TABLE IF NOT EXISTS event_article_perspectives (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE RESTRICT,
  framing TEXT,
  emphasis TEXT,
  distinctive_context TEXT,
  quality_status TEXT NOT NULL DEFAULT 'needs_review'
    CHECK (quality_status IN ('needs_review', 'approved', 'rejected')),
  generation_method TEXT NOT NULL DEFAULT 'human'
    CHECK (generation_method IN ('human', 'deterministic', 'llm', 'imported')),
  reviewer_note TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(event_id, article_id)
);
CREATE INDEX IF NOT EXISTS idx_event_perspectives_review
  ON event_article_perspectives(event_id, quality_status, article_id);

-- Connect each publication's treatment to a shared fact record. The relation
-- describes the article's evidentiary relationship, not whether the publisher
-- is politically aligned with a party or institution.
CREATE TABLE IF NOT EXISTS perspective_fact_links (
  id INTEGER PRIMARY KEY,
  perspective_id INTEGER NOT NULL
    REFERENCES event_article_perspectives(id) ON DELETE CASCADE,
  fact_id INTEGER NOT NULL REFERENCES facts(id) ON DELETE RESTRICT,
  relation TEXT NOT NULL CHECK (relation IN (
    'reports', 'supports', 'partly_supports', 'disputes', 'adds_context'
  )),
  evidence_note TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (verification_status IN (
      'unreviewed', 'reviewed', 'corroborated', 'disputed'
    )),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(perspective_id, fact_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_perspective_fact_fact
  ON perspective_fact_links(fact_id, verification_status);

-- Approved summary versions and perspectives are immutable. Corrections or
-- rewrites are new versions/records, preserving a reviewable audit trail.
CREATE TRIGGER IF NOT EXISTS trg_approved_summary_immutable
BEFORE UPDATE ON event_summary_versions
WHEN OLD.quality_status = 'approved'
BEGIN
  SELECT RAISE(ABORT, 'approved summary versions are immutable; insert a new version');
END;

CREATE TRIGGER IF NOT EXISTS trg_approved_timeline_immutable
BEFORE UPDATE ON event_timeline_entries
WHEN OLD.publication_status = 'approved'
BEGIN
  SELECT RAISE(ABORT, 'approved timeline entries are immutable; insert a corrected entry');
END;

CREATE TRIGGER IF NOT EXISTS trg_approved_perspective_immutable
BEFORE UPDATE ON event_article_perspectives
WHEN OLD.quality_status = 'approved'
BEGIN
  SELECT RAISE(ABORT, 'approved perspectives are immutable; create a new reviewed record');
END;
