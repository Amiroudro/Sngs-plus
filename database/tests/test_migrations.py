import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA = ROOT / "database" / "schema.sql"
MIGRATIONS = [ROOT / "database" / "migrations" / name for name in (
    "001_study_and_verification_layer.sql",
    "002_rights_translation_exam_assessment.sql",
    "003_operational_rights_registry_sync.sql",
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
            "article_exam_assessments",
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


if __name__ == "__main__":
    unittest.main()
