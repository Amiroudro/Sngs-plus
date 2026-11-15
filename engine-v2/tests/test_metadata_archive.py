#!/usr/bin/env python3
"""Metadata-only archive tests. Run from engine-v2/."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from run_v2 import _metadata_only_record  # noqa: E402


def main():
    decision = {"id": "a017"}
    article = {
        "id": "a017",
        "title": "Example headline",
        "source": "Example News",
        "url": "https://example.com/story",
        "published": "2026-11-16T08:00:00+06:00",
        "summary": "A short publisher-provided feed summary.",
        "body_error": "rights registry: article-body licence is not approved",
    }
    item = _metadata_only_record(decision, article)
    assert item["id"] == "a017"
    assert item["headline"] == article["title"]
    assert "rss_summary" not in item
    assert item["archive_status"] == "metadata_only_body_not_licensed"
    assert item["study_note_status"] == "not_generated"
    assert "body_text" not in item and "facts" not in item
    assert "summary" not in item

    blocked = _metadata_only_record(
        decision, {**article, "body_error": "robots.txt disallows"})
    assert blocked["archive_status"] == "body_blocked_by_robots"

    failed = _metadata_only_record(
        decision, {**article, "body_error": "connection reset"})
    assert failed["archive_status"] == "body_fetch_failed"
    print("PASS: bodyless kept stories retain source metadata without fabricated study notes")


if __name__ == "__main__":
    main()
