#!/usr/bin/env python3
"""Validate the machine-readable publisher feed-route audit ledger."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ledger = json.loads((ROOT / "state" / "source_routes.json").read_text(encoding="utf-8"))


def main():
    sources = ledger["sources"]
    counts = ledger["counts"]
    assert len(sources) == counts["host_records"] == 55
    assert len({row["host"] for row in sources}) == 55
    assert counts["route_leads"] == sum(bool(row["feed_url_lead"]) for row in sources) == 8
    assert counts["directly_verified"] == 0
    assert counts["enabled"] == 0
    for row in sources:
        assert row["source_enabled"] is False, row["host"]
        assert row["direct_fetch_status"] == "not_verified_in_deployment_environment"
        assert row["body_status"] == "not_permitted"
        if row["feed_url_lead"]:
            assert row["feed_route_status"] in {
                "third_party_directory_lead_not_directly_verified",
                "rss_content_type_seen_payload_unparsed",
            }
    print("PASS: 55-host route ledger is consistent, default-deny, and does not overstate feed verification")


if __name__ == "__main__":
    main()
