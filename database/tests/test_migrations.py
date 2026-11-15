import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA = ROOT / "database" / "schema.sql"
MIGRATIONS = [ROOT / "database" / "migrations" / name for name in (
    "001_study_and_verification_layer.sql",
    "002_rights_translation_exam_assessment.sql",
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
        self.db.execute(
            "INSERT INTO source_rights_reviews "
            "(source_id, rights_status, licence_scope, permission_evidence) "
            "VALUES (?, 'licensed', 'article body and derivative study notes', "
            "'Written publisher permission on file')",
            (source_id,),
        )
        self.db.execute("UPDATE sources SET enabled=1 WHERE id=?", (source_id,))
        enabled = self.db.execute(
            "SELECT enabled FROM sources WHERE id=?", (source_id,)
        ).fetchone()[0]
        self.assertEqual(enabled, 1)

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
