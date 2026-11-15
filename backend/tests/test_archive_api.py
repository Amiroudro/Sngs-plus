import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.app import main


class MetadataArchiveApiTests(unittest.TestCase):
    def test_search_returns_explicit_metadata_only_contract(self):
        result_data = {
            "total": 1,
            "items": [{
                "headline": "Example headline",
                "source": "Example Daily",
                "record_type": "metadata_only",
            }],
        }
        with patch.object(main, "search_metadata_archive", return_value=result_data):
            result = main.metadata_archive(q="example", source="", limit=30)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["record_type"], "metadata_only")
        self.assertFalse(result["study_notes_available"])
        self.assertEqual(result["total"], 1)

    def test_empty_search_is_honest(self):
        with patch.object(
            main, "search_metadata_archive",
            return_value={"total": 0, "items": []},
        ):
            result = main.metadata_archive(q="missing", source="", limit=30)
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["items"], [])
        self.assertFalse(result["study_notes_available"])

    def test_store_failure_becomes_service_unavailable(self):
        with patch.object(
            main, "search_metadata_archive", side_effect=ValueError("bad archive")
        ):
            with self.assertRaises(HTTPException) as raised:
                main.metadata_archive(q="", source="", limit=30)
        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
