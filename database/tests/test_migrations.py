import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA = ROOT / "database" / "schema.sql"
MIGRATION = ROOT / "database" / "migrations" / "001_study_and_verification_layer.sql"


class StudyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(BASE_SCHEMA.read_text(encoding="utf-8"))
        self.db.executescript(MIGRATION.read_text(encoding="utf-8"))

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
            "editorial_corrections",
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

    def test_invalid_question_language_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO questions (language, question_type, stem) "
                "VALUES ('fr', 'mcq', 'Invalid language')"
            )


if __name__ == "__main__":
    unittest.main()
