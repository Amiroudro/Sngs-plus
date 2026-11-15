import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convert_to_app import build_editorial_story, build_story_fields


class TranslationApprovalGateTests(unittest.TestCase):
    def test_regular_story_overlay_starts_unreviewed(self):
        item = {
            "id": "CA01",
            "headline": "IMF board approves a $442 million tranche for Bangladesh",
            "topic_primary": "INT-ORG",
            "date": "2026-11-15",
            "facts_en": [{
                "what": "IMF board approves tranche",
                "value": "442",
                "unit": "million",
                "date": "2026-11-13",
                "quote": "The IMF board approved a $442 million tranche for Bangladesh."
            }],
            "fact_lines": ["আইএমএফ বোর্ড কিস্তি বাংলাদেশ: ৪৪২ মিলিয়ন"],
            "sources": [{"name": "Example Publisher", "url": "https://example.com/story"}],
        }
        _, bangla, _ = build_story_fields(item, {}, "2026-11-15", {})
        self.assertEqual(bangla["translation_status"], "needs_review")

    def test_editorial_overlay_also_starts_unreviewed(self):
        _, bangla, _ = build_editorial_story({
            "headline": "Editorial headline",
            "summary": "The writer argues for policy reform.",
            "source": "Example",
            "url": "https://example.com/editorial",
        }, "2026-11-15", "ED01")
        self.assertEqual(bangla["translation_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
