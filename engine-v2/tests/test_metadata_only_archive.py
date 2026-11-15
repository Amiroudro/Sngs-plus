#!/usr/bin/env python3
"""Metadata-only archive safety tests. Run from engine-v2/."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from run_v2 import _metadata_only_record  # noqa: E402


def main():
    record = _metadata_only_record(
        {"id": "a001"},
        {
            "id": "a001",
            "title": "A source-grounded headline",
            "source": "Example News",
            "url": "https://example.com/news/1",
            "published": "2026-11-16T08:00:00+06:00",
            "summary": "This is an RSS excerpt and must not enter the archive.",
            "body_error": "rights registry: article-body licence is not approved"
        }
    )
    assert record["archive_status"] == "metadata_only_body_not_licensed"
    assert record["study_note_status"] == "not_generated"
    assert record["headline"] == "A source-grounded headline"
    assert record["source"] == "Example News"
    assert record["url"] == "https://example.com/news/1"
    assert record["published"] == "2026-11-16T08:00:00+06:00"
    forbidden = {
        "body_text", "rss_summary", "facts", "facts_raw", "translation",
        "questions", "mcq", "study_note"
    }
    assert forbidden.isdisjoint(record)
    print("PASS: metadata-only archive preserves bibliographic fields without excerpts or generated study content")

    blocked = _metadata_only_record(
        {"id": "a002"},
        {"url": "https://example.com/news/2", "body_error": "robots.txt disallows"}
    )
    assert blocked["archive_status"] == "body_blocked_by_robots"
    assert blocked["study_note_status"] == "not_generated"
    print("PASS: robots-blocked body is archived as metadata-only, not presented as a study note")


if __name__ == "__main__":
    main()
