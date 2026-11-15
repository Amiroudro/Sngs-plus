#!/usr/bin/env python3
"""SQLite-to-JSON rights sync tests. Run from engine-v2/."""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))
import rights_registry  # noqa: E402
from sync_rights_registry import export_registry  # noqa: E402


def _record():
    return {
        "publisher": "Example News",
        "source_enabled": False,
        "metadata_status": "pending", "metadata_scope": "", "metadata_evidence": "",
        "page_metadata_status": "pending", "page_metadata_scope": "",
        "page_metadata_evidence": "",
        "automated_processing_status": "pending",
        "automated_processing_scope": "", "automated_processing_evidence": "",
        "body_status": "not_permitted", "body_scope": "", "body_evidence": "",
        "reviewed_at": "", "review_due_at": "", "expires_at": ""
    }


def _make_database(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((ROOT / "database/schema.sql").read_text(encoding="utf-8"))
    for name in (
        "001_study_and_verification_layer.sql",
        "002_rights_translation_exam_assessment.sql",
        "003_operational_rights_registry_sync.sql",
    ):
        db.executescript(
            (ROOT / "database/migrations" / name).read_text(encoding="utf-8"))
    db.execute(
        "INSERT INTO sources (name, homepage_url) VALUES (?, ?)",
        ("Example News", "https://example.com/")
    )
    source_id = db.execute(
        "SELECT id FROM sources WHERE name='Example News'"
    ).fetchone()[0]
    db.commit()
    return db, source_id


def _insert_review(db, source_id, body="rss_headlines_only",
                   page="pending", processing="approved", metadata="approved"):
    db.execute(
        "INSERT INTO source_rights_reviews "
        "(source_id, publisher_domain, rights_status, licence_scope, permission_evidence, "
        "metadata_status, metadata_scope, metadata_evidence, page_metadata_status, "
        "page_metadata_scope, page_metadata_evidence, automated_processing_status, "
        "automated_processing_scope, automated_processing_evidence, review_due_at) "
        "VALUES (?, 'example.com', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now', '+30 days'))",
        (source_id, body,
         "article body licence" if body == "licensed" else "",
         "written body permission" if body == "licensed" else "",
         metadata, "headline, canonical URL and publication date", "terms or permission",
         page, "canonical page headline" if page == "approved" else "",
         "page extraction permission" if page == "approved" else "",
         processing, "automated classification and study summaries" if processing == "approved" else "",
         "automated processing permission" if processing == "approved" else "")
    )
    db.commit()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        db_path = tmp / "rights.sqlite"
        registry_path = tmp / "source_rights.json"
        initial = {"version": 1, "policy": {"discovery_hosts": []},
                   "publishers": {"example.com": _record(),
                                  "news.example.com": _record()}}
        registry_path.write_text(json.dumps(initial), encoding="utf-8")
        db, source_id = _make_database(db_path)
        try:
            _insert_review(db, source_id)
            db.execute("UPDATE sources SET enabled=1 WHERE id=?", (source_id,))
            db.commit()

            # Dry-run produces the correct export but leaves the JSON unchanged.
            dry_data, dry_report = export_registry(db_path, registry_path, write=False)
            assert dry_report["domains_updated"] == ["example.com", "news.example.com"]
            assert dry_data["publishers"]["example.com"]["metadata_status"] == "approved"
            assert json.loads(registry_path.read_text())["publishers"]["example.com"]["metadata_status"] == "pending"
            print("PASS: dry-run sync maps latest DB metadata/AI grants without writing")

            export_registry(db_path, registry_path, write=True)
            current = rights_registry.load_registry(registry_path)
            assert rights_registry.metadata_decision("https://www.example.com/story", current)[0]
            assert rights_registry.body_decision("https://example.com/story", current)[0] is False
            assert rights_registry.page_metadata_decision("https://example.com/story", current)[0] is False
            assert rights_registry.metadata_decision("https://news.example.com/story", current)[0]
            print("PASS: metadata-only DB grant reaches Engine registry without body/page permission")

            _insert_review(db, source_id, body="licensed", page="approved")
            db.execute(
                "UPDATE sources SET collection_mode='article_body', "
                "article_page_fetch_enabled=1 WHERE id=?", (source_id,))
            db.commit()
            export_registry(db_path, registry_path, write=True)
            current = rights_registry.load_registry(registry_path)
            assert rights_registry.body_decision("https://example.com/story", current)[0]
            assert rights_registry.page_metadata_decision("https://example.com/story", current)[0]
            print("PASS: separately approved page and body rights sync to Engine registry")

            _insert_review(db, source_id, body="permission_required",
                           page="restricted", processing="restricted",
                           metadata="restricted")
            export_registry(db_path, registry_path, write=True)
            current = rights_registry.load_registry(registry_path)
            assert rights_registry.metadata_decision("https://example.com/story", current)[0] is False
            assert rights_registry.body_decision("https://example.com/story", current)[0] is False
            print("PASS: latest restrictive DB review revokes prior JSON permissions")

            db.execute(
                "INSERT INTO sources (name, homepage_url) VALUES (?, ?)",
                ("Duplicate domain source", "https://example.com/duplicate")
            )
            duplicate_id = db.execute(
                "SELECT id FROM sources WHERE name='Duplicate domain source'"
            ).fetchone()[0]
            _insert_review(db, duplicate_id, body="rss_headlines_only")
            _, conflict_report = export_registry(db_path, registry_path, write=False)
            assert conflict_report["conflicts"]
            before = registry_path.read_text(encoding="utf-8")
            try:
                export_registry(db_path, registry_path, write=True)
            except RuntimeError as exc:
                assert "conflicting database reviews" in str(exc)
            else:
                raise AssertionError("conflicting source rows must block registry writes")
            assert registry_path.read_text(encoding="utf-8") == before
            print("PASS: conflicting DB sources cannot silently overwrite a publisher registry entry")
        finally:
            db.close()


if __name__ == "__main__":
    main()
