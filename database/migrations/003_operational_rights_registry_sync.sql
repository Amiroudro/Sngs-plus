PRAGMA foreign_keys = ON;

-- Keep the application rights ledger expressive enough to drive the
-- Engine's separate metadata, page extraction, AI processing and body gates.
ALTER TABLE sources ADD COLUMN collection_mode TEXT NOT NULL DEFAULT 'metadata_only'
  CHECK (collection_mode IN ('metadata_only', 'article_body'));
ALTER TABLE sources ADD COLUMN article_page_fetch_enabled INTEGER NOT NULL DEFAULT 0
  CHECK (article_page_fetch_enabled IN (0, 1));

ALTER TABLE source_rights_reviews ADD COLUMN publisher_domain TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN metadata_status TEXT NOT NULL DEFAULT 'pending'
  CHECK (metadata_status IN ('pending', 'approved', 'restricted'));
ALTER TABLE source_rights_reviews ADD COLUMN metadata_scope TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN metadata_evidence TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN page_metadata_status TEXT NOT NULL DEFAULT 'pending'
  CHECK (page_metadata_status IN ('pending', 'approved', 'restricted'));
ALTER TABLE source_rights_reviews ADD COLUMN page_metadata_scope TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN page_metadata_evidence TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN automated_processing_status TEXT NOT NULL DEFAULT 'pending'
  CHECK (automated_processing_status IN ('pending', 'approved', 'restricted'));
ALTER TABLE source_rights_reviews ADD COLUMN automated_processing_scope TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN automated_processing_evidence TEXT;
ALTER TABLE source_rights_reviews ADD COLUMN review_due_at TEXT;

CREATE INDEX IF NOT EXISTS idx_source_rights_domain_review
  ON source_rights_reviews(publisher_domain, reviewed_at DESC, id DESC);

-- Rights reviews are an audit ledger. Corrections must be new rows, never
-- edits or deletions of the prior decision.
CREATE TRIGGER IF NOT EXISTS trg_source_rights_reviews_no_update
BEFORE UPDATE ON source_rights_reviews
BEGIN
  SELECT RAISE(ABORT, 'rights reviews are append-only; insert a new review');
END;

CREATE TRIGGER IF NOT EXISTS trg_source_rights_reviews_no_delete
BEFORE DELETE ON source_rights_reviews
BEGIN
  SELECT RAISE(ABORT, 'rights reviews are append-only');
END;

-- Metadata-only is the least-privilege default. A current metadata grant and
-- a separate automated-processing grant are required to enable any source.
DROP TRIGGER IF EXISTS trg_sources_enable_requires_license;
CREATE TRIGGER trg_sources_enable_requires_metadata_and_processing
BEFORE UPDATE OF enabled ON sources
WHEN NEW.enabled = 1
AND NOT EXISTS (
  SELECT 1
  FROM source_rights_reviews r
  WHERE r.source_id = NEW.id
    AND r.id = (
      SELECT id FROM source_rights_reviews
      WHERE source_id = NEW.id
      ORDER BY reviewed_at DESC, id DESC
      LIMIT 1
    )
    AND r.rights_status <> 'disabled'
    AND r.metadata_status = 'approved'
    AND length(trim(coalesce(r.metadata_scope, ''))) > 0
    AND length(trim(coalesce(r.metadata_evidence, ''))) > 0
    AND r.automated_processing_status = 'approved'
    AND length(trim(coalesce(r.automated_processing_scope, ''))) > 0
    AND length(trim(coalesce(r.automated_processing_evidence, ''))) > 0
    AND r.review_due_at IS NOT NULL
    AND date(r.review_due_at) >= date('now')
    AND date(r.reviewed_at) <= date('now')
    AND (r.expires_at IS NULL OR date(r.expires_at) >= date('now'))
)
BEGIN
  SELECT RAISE(ABORT, 'source needs current metadata and automated-processing permission');
END;

-- Article-body collection needs an additional, explicit body licence.
CREATE TRIGGER IF NOT EXISTS trg_sources_body_mode_requires_license
BEFORE UPDATE OF enabled, collection_mode ON sources
WHEN NEW.enabled = 1
AND NEW.collection_mode = 'article_body'
AND NOT EXISTS (
  SELECT 1
  FROM source_rights_reviews r
  WHERE r.source_id = NEW.id
    AND r.id = (
      SELECT id FROM source_rights_reviews
      WHERE source_id = NEW.id
      ORDER BY reviewed_at DESC, id DESC
      LIMIT 1
    )
    AND r.rights_status = 'licensed'
    AND length(trim(coalesce(r.licence_scope, ''))) > 0
    AND length(trim(coalesce(r.permission_evidence, ''))) > 0
    AND r.metadata_status = 'approved'
    AND r.automated_processing_status = 'approved'
    AND length(trim(coalesce(r.automated_processing_scope, ''))) > 0
    AND length(trim(coalesce(r.automated_processing_evidence, ''))) > 0
    AND r.review_due_at IS NOT NULL
    AND date(r.review_due_at) >= date('now')
    AND date(r.reviewed_at) <= date('now')
    AND (r.expires_at IS NULL OR date(r.expires_at) >= date('now'))
)
BEGIN
  SELECT RAISE(ABORT, 'article-body mode needs a current documented body licence');
END;

-- Article-page title extraction is separately gated; a feed permission does
-- not silently authorise fetching the publisher's article page.
CREATE TRIGGER IF NOT EXISTS trg_sources_page_fetch_requires_permission
BEFORE UPDATE OF enabled, article_page_fetch_enabled ON sources
WHEN NEW.enabled = 1
AND NEW.article_page_fetch_enabled = 1
AND NOT EXISTS (
  SELECT 1
  FROM source_rights_reviews r
  WHERE r.source_id = NEW.id
    AND r.id = (
      SELECT id FROM source_rights_reviews
      WHERE source_id = NEW.id
      ORDER BY reviewed_at DESC, id DESC
      LIMIT 1
    )
    AND r.page_metadata_status = 'approved'
    AND length(trim(coalesce(r.page_metadata_scope, ''))) > 0
    AND length(trim(coalesce(r.page_metadata_evidence, ''))) > 0
    AND r.automated_processing_status = 'approved'
    AND length(trim(coalesce(r.automated_processing_scope, ''))) > 0
    AND length(trim(coalesce(r.automated_processing_evidence, ''))) > 0
    AND r.review_due_at IS NOT NULL
    AND date(r.review_due_at) >= date('now')
    AND date(r.reviewed_at) <= date('now')
    AND (r.expires_at IS NULL OR date(r.expires_at) >= date('now'))
)
BEGIN
  SELECT RAISE(ABORT, 'article-page fetch needs current page-metadata and automated-processing permission');
END;

-- A new restrictive or expired review automatically disables an enabled
-- source. The Engine's JSON runtime gate independently checks every run.
CREATE TRIGGER IF NOT EXISTS trg_rights_review_disables_invalid_source
AFTER INSERT ON source_rights_reviews
WHEN EXISTS (
  SELECT 1 FROM sources s
  WHERE s.id = NEW.source_id
    AND s.enabled = 1
    AND (
      NEW.rights_status = 'disabled'
      OR NEW.metadata_status <> 'approved'
      OR length(trim(coalesce(NEW.metadata_scope, ''))) = 0
      OR length(trim(coalesce(NEW.metadata_evidence, ''))) = 0
      OR NEW.automated_processing_status <> 'approved'
      OR length(trim(coalesce(NEW.automated_processing_scope, ''))) = 0
      OR length(trim(coalesce(NEW.automated_processing_evidence, ''))) = 0
      OR NEW.review_due_at IS NULL
      OR date(NEW.review_due_at) < date('now')
      OR (NEW.expires_at IS NOT NULL AND date(NEW.expires_at) < date('now'))
      OR (s.collection_mode = 'article_body' AND (
        NEW.rights_status <> 'licensed'
        OR length(trim(coalesce(NEW.licence_scope, ''))) = 0
        OR length(trim(coalesce(NEW.permission_evidence, ''))) = 0
      ))
      OR (s.article_page_fetch_enabled = 1 AND (
        NEW.page_metadata_status <> 'approved'
        OR length(trim(coalesce(NEW.page_metadata_scope, ''))) = 0
        OR length(trim(coalesce(NEW.page_metadata_evidence, ''))) = 0
      ))
    )
)
BEGIN
  UPDATE sources SET enabled = 0 WHERE id = NEW.source_id;
END;
