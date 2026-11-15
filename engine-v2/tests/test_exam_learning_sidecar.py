#!/usr/bin/env python3
"""Regression tests for the optional exam-learning edition sidecar."""
import unittest

import convert_to_app as converter


class ExamLearningSidecarTests(unittest.TestCase):
    def test_valid_sidecar_is_indexed_by_original_story_id(self):
        doc = {
            "edition_date": "2026-11-16",
            "stories": {
                "STORY-7": {
                    "en": {"concepts": [{"title": "ADP"}]},
                    "bn": {"concepts": [{"title": "এডিপি"}]},
                }
            },
        }
        stories = converter.validate_exam_learning_sidecar(doc, "2026-11-16")
        self.assertIn("STORY-7", stories)

    def test_wrong_date_is_rejected(self):
        with self.assertRaises(ValueError):
            converter.validate_exam_learning_sidecar(
                {"edition_date": "2026-11-15", "stories": {}},
                "2026-11-16",
            )

    def test_non_object_language_layer_is_rejected(self):
        with self.assertRaises(ValueError):
            converter.validate_exam_learning_sidecar(
                {"edition_date": "2026-11-16",
                 "stories": {"STORY-7": {"bn": ["not", "an", "object"]}}},
                "2026-11-16",
            )

    def test_learning_layers_attach_without_being_generated_or_changed(self):
        en = {"id": "CA01"}
        bn = {"id": "CA01", "translation_status": "needs_review"}
        source = {
            "STORY-7": {
                "en": {"concepts": [{"title": "Annual Development Programme"}]},
                "bn": {"concepts": [{"title": "বার্ষিক উন্নয়ন কর্মসূচি"}]},
            }
        }
        has_en, has_bn = converter.attach_exam_learning(en, bn, "STORY-7", source)
        self.assertTrue(has_en)
        self.assertTrue(has_bn)
        self.assertEqual(en["exam_learning"]["concepts"][0]["title"],
                         "Annual Development Programme")
        self.assertEqual(bn["exam_learning"]["concepts"][0]["title"],
                         "বার্ষিক উন্নয়ন কর্মসূচি")
        self.assertEqual(bn["translation_status"], "needs_review")

    def test_missing_story_entry_is_empty_and_non_fatal(self):
        en, bn = {"id": "CA01"}, {"id": "CA01"}
        self.assertEqual(
            converter.attach_exam_learning(en, bn, "UNKNOWN", {}),
            (False, False),
        )
        self.assertEqual(en["exam_learning"], {})
        self.assertEqual(bn["exam_learning"], {})


if __name__ == "__main__":
    unittest.main()
