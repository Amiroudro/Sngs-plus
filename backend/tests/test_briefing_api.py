import unittest
from unittest.mock import patch

from backend.app import main


class BriefingApiTests(unittest.TestCase):
    def test_bangla_id_keyed_overlay_returns_ordered_story_list(self):
        english = [
            {"id": "CA01", "headline": "English headline", "summary": "English summary",
             "category": "Bangladesh", "article_date": "2026-11-15",
             "sources": [{"publication": "Publisher", "url": "https://example.com/a"}]},
            {"id": "CA02", "headline": "Second story", "summary": "Second summary"},
        ]
        bangla = {
            "edition_date": "2026-11-15",
            "stories": {
                "CA01": {"headline": "বাংলা শিরোনাম", "summary": "বাংলা সারাংশ", "translation_status": "approved"},
                "CA02": {"headline": "দ্বিতীয় সংবাদ", "summary": "দ্বিতীয় সারাংশ", "translation_status": "approved"},
            },
        }
        loaded = {"edition": {"edition_date": "2026-11-15", "stories": english},
                  "bangla": bangla, "index_entry": {"edition_date": "2026-11-15"}}
        with patch.object(main, "list_editions", return_value=[{"edition_date": "2026-11-15"}]), \
             patch.object(main, "load_edition", return_value=loaded):
            payload = main.briefing("bn")

        self.assertEqual(payload["language"], "bn")
        self.assertIsNone(payload["fallback_language"])
        self.assertIsInstance(payload["stories"], list)
        self.assertEqual([s["id"] for s in payload["stories"]], ["CA01", "CA02"])
        self.assertEqual(payload["stories"][0]["headline"], "বাংলা শিরোনাম")
        self.assertEqual(payload["stories"][0]["category"], "Bangladesh")
        self.assertEqual(payload["stories"][0]["sources"][0]["url"], "https://example.com/a")

    def test_bangla_list_overlay_is_supported(self):
        english = [{"id": "CA01", "headline": "English", "summary": "Base"}]
        loaded = {"edition": {"stories": english},
                  "bangla": {"stories": [{"id": "CA01", "summary": "বাংলা", "translation_status": "approved"}]}}
        with patch.object(main, "list_editions", return_value=[{"edition_date": "2026-11-15"}]), \
             patch.object(main, "load_edition", return_value=loaded):
            payload = main.briefing("bn")
        self.assertEqual(payload["stories"][0]["summary"], "বাংলা")
        self.assertEqual(payload["stories"][0]["headline"], "English")

    def test_unreviewed_bangla_overlay_falls_back_to_english(self):
        english = [{"id": "CA01", "headline": "English", "summary": "Base"}]
        loaded = {"edition": {"stories": english},
                  "bangla": {"stories": {"CA01": {
                      "headline": "শিরোনাম", "summary": "যান্ত্রিক রূপান্তর",
                      "translation_status": "needs_review"
                  }}}}
        with patch.object(main, "list_editions", return_value=[{"edition_date": "2026-11-15"}]), \
             patch.object(main, "load_edition", return_value=loaded):
            payload = main.briefing("bn")
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["fallback_language"], "en")
        self.assertEqual(payload["stories"], english)

    def test_missing_bangla_overlay_falls_back_to_english(self):
        english = [{"id": "CA01", "headline": "English", "summary": "Base"}]
        loaded = {"edition": {"stories": english}, "bangla": None}
        with patch.object(main, "list_editions", return_value=[{"edition_date": "2026-11-15"}]), \
             patch.object(main, "load_edition", return_value=loaded):
            payload = main.briefing("bn")
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["fallback_language"], "en")
        self.assertEqual(payload["stories"], english)


if __name__ == "__main__":
    unittest.main()
