import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app import edition_store as store


class EditionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.editions = self.root / "editions"
        self.bn = self.root / "app" / "assets" / "editions"
        self.editions.mkdir(parents=True)
        self.bn.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_missing_index_is_empty(self):
        with patch.object(store, "EDITIONS_DIR", self.editions):
            self.assertEqual(store.list_editions(), [])

    def test_published_edition_and_bangla_overlay(self):
        day = "2026-11-15"
        entry = {"edition_date": day, "file": f"data-{day}.json"}
        self.write_json(self.editions / "index.json", {"editions": [entry]})
        self.write_json(self.editions / f"data-{day}.json", {
            "edition_date": day, "stories": [{"id": "CA01"}]
        })
        self.write_json(self.bn / f"bn-{day}.json", {
            "edition_date": day, "stories": [{"id": "CA01", "summary": "বাংলা"}]
        })
        with patch.object(store, "EDITIONS_DIR", self.editions), patch.object(
            store, "BANGLA_EDITIONS_DIR", self.bn
        ):
            result = store.load_edition(day)
        self.assertEqual(result["edition"]["stories"][0]["id"], "CA01")
        self.assertEqual(result["bangla"]["stories"][0]["summary"], "বাংলা")

    def test_rejects_path_traversal_filename(self):
        day = "2026-11-15"
        self.write_json(self.editions / "index.json", {
            "editions": [{"edition_date": day, "file": "../../secret.json"}]
        })
        with patch.object(store, "EDITIONS_DIR", self.editions):
            with self.assertRaises(ValueError):
                store.load_edition(day)

    def test_rejects_invalid_date(self):
        with patch.object(store, "EDITIONS_DIR", self.editions):
            with self.assertRaises(ValueError):
                store.load_edition("../latest")

    def test_unindexed_edition_is_not_served(self):
        self.write_json(self.editions / "index.json", {"editions": []})
        with patch.object(store, "EDITIONS_DIR", self.editions):
            with self.assertRaises(store.EditionNotFound):
                store.load_edition("2026-11-15")


if __name__ == "__main__":
    unittest.main()
