#!/usr/bin/env python3
"""Validate the machine-readable publisher feed-route audit ledger."""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ledger = json.loads((ROOT / "state" / "source_routes.json").read_text(encoding="utf-8"))
rights = json.loads((ROOT / "state" / "source_rights.json").read_text(encoding="utf-8"))


def main():
    sources = ledger["sources"]
    counts = ledger["counts"]
    assert len(sources) == counts["host_records"] == 55
    assert len({row["host"] for row in sources}) == 55
    assert {row["host"] for row in sources} == set(rights["publishers"])
    assert counts["route_leads"] == sum(bool(row["feed_url_lead"]) for row in sources) == 8
    assert counts["directly_verified"] == 0
    assert counts["enabled"] == 0
    terms_reviewed = [
        row for row in sources
        if row.get("terms_status") not in {
            "", "not_reviewed_or_not_recorded", "not_located",
        }
    ]
    assert len(terms_reviewed) == 12
    for row in terms_reviewed:
        assert row.get("terms_url", "").startswith("https://")
        assert "permission" not in row["terms_status"] or "permission_granted" not in row["terms_status"]
        assert row["source_enabled"] is False

    collector_routes = ledger["collector_route_inventory"]
    assert len(collector_routes) == counts["collector_route_records"] == 19
    for route in collector_routes:
        assert route["evidence_date"] == "2026-11-15"
        assert route["evidence_environment"] == "original_engine_development_vm"
        assert route["deployment_environment_verified"] is False
        assert route["current_reachability"] == "not_verified"
        assert route["robots_status"] == "not_rechecked_for_deployment"
        assert route["rights_approved"] is False
        assert route["source_enabled"] is False
        assert route["url"].startswith("https://")
        host = (urlparse(route["url"]).hostname or "").lower()
        host = host[4:] if host.startswith("www.") else host
        assert host in rights["publishers"], (route["publisher"], host)
        assert route["route_type"] in {
            "rss", "news_sitemap", "news_sitemap_template",
            "sitemap_index", "sitemap", "section_page", "homepage_probe",
        }
    for row in sources:
        assert row["source_enabled"] is False, row["host"]
        assert row["direct_fetch_status"] == "not_verified_in_deployment_environment"
        assert row["body_status"] == "not_permitted"
        assert row["source_enabled"] == rights["publishers"][row["host"]]["source_enabled"]
        assert row["body_status"] == rights["publishers"][row["host"]]["body_status"]
        assert row["metadata_status"] == rights["publishers"][row["host"]]["metadata_status"]
        assert row["page_metadata_status"] == rights["publishers"][row["host"]]["page_metadata_status"]
        assert row["automated_processing_status"] == rights["publishers"][row["host"]]["automated_processing_status"]
        assert row["automated_processing_status"] != "approved", row["host"]
        if row["feed_url_lead"]:
            assert row["feed_route_status"] in {
                "third_party_directory_lead_not_directly_verified",
                "rss_content_type_seen_payload_unparsed",
            }
    print("PASS: 55-host route ledger is consistent, default-deny, and does not overstate feed verification")


if __name__ == "__main__":
    main()
