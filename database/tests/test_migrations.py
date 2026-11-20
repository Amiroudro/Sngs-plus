import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA = ROOT / "database" / "schema.sql"
MIGRATIONS = [ROOT / "database" / "migrations" / name for name in (
    "001_study_and_verification_layer.sql",
    "002_rights_translation_exam_assessment.sql",
    "003_operational_rights_registry_sync.sql",
    "004_event_intelligence.sql",
)]


class StudyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(BASE_SCHEMA.read_text(encoding="utf-8"))
        for migration in MIGRATIONS:
            self.db.executescript(migration.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()

    def test_expected_tables_exist(self):
        names = {
            row[0] for row in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        expected = {
            "source_checks", "fact_evidence", "questions", "question_options",
            "vocabulary_entries", "vocabulary_occurrences", "review_progress",
            "editorial_corrections", "source_rights_reviews", "article_localizations",
            "article_exam_assessments", "event_summary_versions",
            "event_timeline_entries", "event_article_perspectives",
            "perspective_fact_links", "event_summary_sources",
            "event_summary_facts",
        }
        self.assertTrue(expected.issubset(names), expected - names)

    def test_foreign_keys_and_question_options(self):
        self.db.execute(
            "INSERT INTO events (slug, status, importance_score) VALUES (?, ?, ?)",
            ("test-event", "developing", 8),
        )
        event_id = self.db.execute(
            "SELECT id FROM events WHERE slug='test-event'"
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO questions (event_id, language, question_type, stem) "
            "VALUES (?, 'en', 'mcq', 'Which institution issued the report?')",
            (event_id,),
        )
        question_id = self.db.execute(
            "SELECT id FROM questions"
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO question_options "
            "(question_id, option_key, option_text, is_correct) "
            "VALUES (?, 'A', 'Example institution', 1)",
            (question_id,),
        )
        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*) FROM question_options WHERE question_id=?",
                (question_id,),
            ).fetchone()[0],
            1,
        )


    def _insert_article(self):
        self.db.execute(
            "INSERT INTO sources (name, homepage_url) VALUES (?, ?)",
            ("Rights test publisher", "https://example.com"),
        )
        source_id = self.db.execute(
            "SELECT id FROM sources WHERE name='Rights test publisher'"
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO articles (source_id, canonical_url, original_title) "
            "VALUES (?, ?, ?)",
            (source_id, "https://example.com/story", "Test story"),
        )
        article_id = self.db.execute(
            "SELECT id FROM articles WHERE canonical_url='https://example.com/story'"
        ).fetchone()[0]
        return source_id, article_id

    def test_rights_review_is_auditable_and_status_is_constrained(self):
        source_id, _ = self._insert_article()
        self.db.execute(
            "INSERT INTO source_rights_reviews (source_id, rights_status, terms_url) "
            "VALUES (?, 'permission_required', 'https://example.com/terms')",
            (source_id,),
        )
        review_id = self.db.execute(
            "SELECT id FROM source_rights_reviews WHERE source_id=?",
            (source_id,),
        ).fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE source_rights_reviews SET reviewer_note='overwrite' WHERE id=?",
                (review_id,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "DELETE FROM source_rights_reviews WHERE id=?", (review_id,)
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE sources SET enabled=1 WHERE id=?", (source_id,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO sources (name, homepage_url, enabled) "
                "VALUES ('Unsafe source', 'https://unsafe.example', 1)"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO source_rights_reviews (source_id, rights_status) "
                "VALUES (?, 'probably_ok')",
                (source_id,),
            )

        # A body licence by itself is insufficient: metadata and automated
        # processing need their own permission records.
        self.db.execute(
            "INSERT INTO source_rights_reviews "
            "(source_id, rights_status, licence_scope, permission_evidence) "
            "VALUES (?, 'licensed', 'article body', 'Body licence only')",
            (source_id,),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE sources SET enabled=1 WHERE id=?", (source_id,))

        # A current metadata-only grant plus explicit automated-processing
        # scope is sufficient for metadata-only collection.
        self.db.execute(
            "INSERT INTO source_rights_reviews "
            "(source_id, publisher_domain, rights_status, metadata_status, "
            "metadata_scope, metadata_evidence, automated_processing_status, "
            "automated_processing_scope, automated_processing_evidence, review_due_at) "
            "VALUES (?, 'example.com', 'rss_headlines_only', 'approved', "
            "'headline, canonical URL and date', 'Terms URL', 'approved', "
            "'automated classification and study notes', 'Written permission', "
            "date('now', '+30 days'))",
            (source_id,),
        )
        self.db.execute("UPDATE sources SET enabled=1 WHERE id=?", (source_id,))
        enabled = self.db.execute(
            "SELECT enabled FROM sources WHERE id=?", (source_id,)
        ).fetchone()[0]
        self.assertEqual(enabled, 1)

        # Metadata permission does not allow article-body or article-page fetches.
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE sources SET collection_mode='article_body' WHERE id=?",
                (source_id,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE sources SET article_page_fetch_enabled=1 WHERE id=?",
                (source_id,),
            )

        # A new complete review unlocks the two separate capabilities.
        self.db.execute(
            "INSERT INTO source_rights_reviews "
            "(source_id, publisher_domain, rights_status, licence_scope, "
            "permission_evidence, metadata_status, metadata_scope, metadata_evidence, "
            "page_metadata_status, page_metadata_scope, page_metadata_evidence, "
            "automated_processing_status, automated_processing_scope, "
            "automated_processing_evidence, review_due_at) "
            "VALUES (?, 'example.com', 'licensed', 'article body and study summaries', "
            "'Written publisher licence', 'approved', 'headline and date', "
            "'Metadata permission', 'approved', 'canonical page headline', "
            "'Page metadata permission', 'approved', 'automated classification, "
            "extraction and summaries', 'AI processing permission', date('now', '+30 days'))",
            (source_id,),
        )
        self.db.execute(
            "UPDATE sources SET collection_mode='article_body' WHERE id=?",
            (source_id,),
        )
        self.db.execute(
            "UPDATE sources SET article_page_fetch_enabled=1 WHERE id=?",
            (source_id,),
        )
        modes = self.db.execute(
            "SELECT collection_mode, article_page_fetch_enabled FROM sources WHERE id=?",
            (source_id,),
        ).fetchone()
        self.assertEqual(tuple(modes), ("article_body", 1))

        # A later restrictive review immediately disables the source.
        self.db.execute(
            "INSERT INTO source_rights_reviews "
            "(source_id, publisher_domain, rights_status, metadata_status, "
            "automated_processing_status, review_due_at) "
            "VALUES (?, 'example.com', 'permission_required', 'restricted', "
            "'restricted', date('now', '+30 days'))",
            (source_id,),
        )
        enabled = self.db.execute(
            "SELECT enabled FROM sources WHERE id=?", (source_id,)
        ).fetchone()[0]
        self.assertEqual(enabled, 0)

    def test_localization_requires_review_by_default(self):
        _, article_id = self._insert_article()
        self.db.execute(
            "INSERT INTO article_localizations "
            "(article_id, language, headline, generation_method) "
            "VALUES (?, 'bn', 'পরীক্ষামূলক শিরোনাম', 'deterministic')",
            (article_id,),
        )
        status = self.db.execute(
            "SELECT quality_status FROM article_localizations WHERE article_id=?",
            (article_id,),
        ).fetchone()[0]
        self.assertEqual(status, "needs_review")

    def test_exam_relevance_is_separate_bounded_score(self):
        _, article_id = self._insert_article()
        self.db.execute(
            "INSERT INTO article_exam_assessments "
            "(article_id, exam_relevance_score, exam_relevance_reason, retention_status, topic_tags_json) "
            "VALUES (?, 8, 'Core public policy topic', 'full_note', '[\"BD-GOVERNANCE\"]')",
            (article_id,),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO article_exam_assessments "
                "(article_id, exam_relevance_score, exam_relevance_reason, retention_status) "
                "VALUES (?, 11, 'Out of range', 'full_note')",
                (article_id,),
            )

    def test_invalid_question_language_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO questions (language, question_type, stem) "
                "VALUES ('fr', 'mcq', 'Invalid language')"
            )



    def _insert_event(self, slug="event-intelligence-test"):
        self.db.execute(
            "INSERT INTO events (slug, status, importance_score) VALUES (?, 'developing', 8)",
            (slug,),
        )
        return self.db.execute(
            "SELECT id FROM events WHERE slug=?", (slug,)
        ).fetchone()[0]

    def test_three_summary_levels_are_versioned_and_review_gated(self):
        _, article_id = self._insert_article()
        event_id = self._insert_event()
        self.db.execute(
            "INSERT INTO facts (event_id, fact_text, fact_type, source_article_id) "
            "VALUES (?, 'Source-backed summary fact', 'reported', ?)",
            (event_id, article_id),
        )
        fact_id = self.db.execute(
            "SELECT id FROM facts WHERE event_id=?", (event_id,)
        ).fetchone()[0]
        for level in ("quick", "standard", "deep"):
            self.db.execute(
                "INSERT INTO event_summary_versions "
                "(event_id, language, summary_level, version, content, generation_method) "
                "VALUES (?, 'en', ?, 1, ?, 'deterministic')",
                (event_id, level, f"{level} summary"),
            )
        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*) FROM event_summary_versions "
                "WHERE event_id=? AND quality_status='needs_review'",
                (event_id,),
            ).fetchone()[0],
            3,
        )
        quick_id = self.db.execute(
            "SELECT id FROM event_summary_versions "
            "WHERE event_id=? AND summary_level='quick'",
            (event_id,),
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO event_summary_sources "
            "(summary_version_id, article_id, evidence_role) "
            "VALUES (?, ?, 'primary')",
            (quick_id, article_id),
        )
        self.db.execute(
            "INSERT INTO event_summary_facts (summary_version_id, fact_id, relation) "
            "VALUES (?, ?, 'uses')",
            (quick_id, fact_id),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO event_summary_sources "
                "(summary_version_id, article_id) VALUES (?, 999999)",
                (quick_id,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO event_summary_versions "
                "(event_id, language, summary_level, version, content) "
                "VALUES (?, 'en', 'quick', 1, 'duplicate version')",
                (event_id,),
            )
        summary_id = self.db.execute(
            "SELECT id FROM event_summary_versions WHERE event_id=? AND summary_level='quick'",
            (event_id,),
        ).fetchone()[0]
        self.db.execute(
            "UPDATE event_summary_versions SET quality_status='approved' WHERE id=?",
            (summary_id,),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE event_summary_versions SET content='silent rewrite' WHERE id=?",
                (summary_id,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "DELETE FROM event_summary_versions WHERE id=?", (summary_id,)
            )
        self.db.execute(
            "INSERT INTO event_summary_versions "
            "(event_id, language, summary_level, version, content) "
            "VALUES (?, 'en', 'quick', 2, 'corrected version')",
            (event_id,),
        )

    def test_timeline_requires_source_and_preserves_approved_history(self):
        _, article_id = self._insert_article()
        event_id = self._insert_event("timeline-test")
        self.db.execute(
            "INSERT INTO event_timeline_entries "
            "(event_id, source_article_id, entry_type, title, description, "
            "occurred_at, reported_at, chronology_precision, verification_status) "
            "VALUES (?, ?, 'announcement', 'Announcement', 'Source-backed event', "
            "'2026-11-18', '2026-11-18T10:00:00Z', 'date_only', 'single_source')",
            (event_id, article_id),
        )
        entry_id = self.db.execute(
            "SELECT id FROM event_timeline_entries WHERE event_id=?", (event_id,)
        ).fetchone()[0]
        self.db.execute(
            "UPDATE event_timeline_entries SET publication_status='approved' WHERE id=?",
            (entry_id,),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE event_timeline_entries SET description='rewritten' WHERE id=?",
                (entry_id,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "DELETE FROM event_timeline_entries WHERE id=?", (entry_id,)
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO event_timeline_entries "
                "(event_id, source_article_id, entry_type, title, description) "
                "VALUES (?, 999999, 'development', 'Orphan', 'No source')",
                (event_id,),
            )

    def test_multiple_perspectives_link_to_shared_facts(self):
        source_id, article_one = self._insert_article()
        self.db.execute(
            "INSERT INTO sources (name, homepage_url) VALUES (?, ?)",
            ("Second perspective publisher", "https://second.example"),
        )
        second_source = self.db.execute(
            "SELECT id FROM sources WHERE name='Second perspective publisher'"
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO articles (source_id, canonical_url, original_title) "
            "VALUES (?, ?, ?)",
            (second_source, "https://second.example/story", "Second coverage"),
        )
        article_two = self.db.execute(
            "SELECT id FROM articles WHERE canonical_url='https://second.example/story'"
        ).fetchone()[0]
        event_id = self._insert_event("perspectives-test")
        self.db.executemany(
            "INSERT INTO event_articles (event_id, article_id) VALUES (?, ?)",
            [(event_id, article_one), (event_id, article_two)],
        )
        self.db.execute(
            "INSERT INTO facts (event_id, fact_text, fact_type, source_article_id) "
            "VALUES (?, 'Shared reported fact', 'reported', ?)",
            (event_id, article_one),
        )
        fact_id = self.db.execute(
            "SELECT id FROM facts WHERE event_id=?", (event_id,)
        ).fetchone()[0]
        self.db.executemany(
            "INSERT INTO event_article_perspectives "
            "(event_id, article_id, framing, emphasis, quality_status) "
            "VALUES (?, ?, ?, ?, 'approved')",
            [(event_id, article_one, "Public service framing", "Policy detail"),
             (event_id, article_two, "Economic framing", "Cost impact")],
        )
        perspective_ids = [
            row[0] for row in self.db.execute(
                "SELECT id FROM event_article_perspectives WHERE event_id=? ORDER BY id",
                (event_id,),
            ).fetchall()
        ]
        self.assertEqual(len(perspective_ids), 2)
        self.db.executemany(
            "INSERT INTO perspective_fact_links "
            "(perspective_id, fact_id, relation, verification_status) "
            "VALUES (?, ?, 'reports', 'reviewed')",
            [(perspective_ids[0], fact_id), (perspective_ids[1], fact_id)],
        )
        self.assertEqual(
            self.db.execute(
                "SELECT COUNT(*) FROM perspective_fact_links WHERE fact_id=?",
                (fact_id,),
            ).fetchone()[0],
            2,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE event_article_perspectives SET framing='silent rewrite' WHERE id=?",
                (perspective_ids[0],),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "DELETE FROM event_article_perspectives WHERE id=?",
                (perspective_ids[0],),
            )

if __name__ == "__main__":
    unittest.main()
