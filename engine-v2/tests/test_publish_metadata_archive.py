import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from publish_v2 import metadata_archive_validation_error


class MetadataArchivePublishGateTests(unittest.TestCase):
    def setUp(self):
        self.document = {
            "date": "2026-11-16",
            "record_type": "metadata_only",
            "study_notes_available": False,
            "items": [{
                "id": "MO01",
                "headline": "Headline",
                "source": "Publisher",
                "url": "https://example.com/story",
                "published": "2026-11-16T08:00:00+06:00",
                "archive_status": "metadata_only_body_not_licensed",
                "study_note_status": "not_generated",
            }],
        }

    def test_valid_metadata_only_archive_passes(self):
        self.assertEqual(
            metadata_archive_validation_error(self.document, "2026-11-16"), ""
        )

    def test_wrong_date_fails(self):
        self.assertIn(
            "schema/date",
            metadata_archive_validation_error(self.document, "2026-11-15"),
        )

    def test_body_or_study_fields_fail_closed(self):
        self.document["items"][0]["body_text"] = "must not be published"
        self.assertIn(
            "invalid fields",
            metadata_archive_validation_error(self.document, "2026-11-16"),
        )

    def test_unknown_archive_status_fails(self):
        self.document["items"][0]["archive_status"] = "approved"
        self.assertIn(
            "invalid fields",
            metadata_archive_validation_error(self.document, "2026-11-16"),
        )

    def test_extra_top_level_fields_fail(self):
        self.document["debug"] = "unexpected"
        self.assertIn(
            "unexpected top-level",
            metadata_archive_validation_error(self.document, "2026-11-16"),
        )


if __name__ == "__main__":
    unittest.main()
