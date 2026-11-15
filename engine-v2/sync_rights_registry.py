#!/usr/bin/env python3
"""Export the latest SQLite publisher-rights reviews to the Engine JSON registry.

Dry-run by default. Use --write only after a human has reviewed the DB rows.
Run from repository root or engine-v2/:
  python engine-v2/sync_rights_registry.py --db database/sarangsho.db
  python engine-v2/sync_rights_registry.py --db database/sarangsho.db --write
"""
import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import rights_registry


def _domain(value):
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def _date_only(value):
    return str(value or "").strip()[:10]


def export_registry(db_path, registry_path=None, write=False, routes_path=None):
    """Apply latest DB reviews to rights and route ledgers; dry-run unless write=True."""
    registry_file = Path(registry_path) if registry_path else rights_registry.REGISTRY_PATH
    routes_file = (Path(routes_path) if routes_path else
                   registry_file.with_name("source_routes.json"))
    data = rights_registry.load_registry(registry_file)
    routes_data = (json.loads(routes_file.read_text(encoding="utf-8"))
                   if routes_file.exists() else None)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        columns = {row["name"] for row in conn.execute(
            "PRAGMA table_info(source_rights_reviews)"
        )}
        required = {
            "publisher_domain", "metadata_status", "metadata_scope",
            "metadata_evidence", "page_metadata_status", "page_metadata_scope",
            "page_metadata_evidence", "automated_processing_status",
            "automated_processing_scope", "automated_processing_evidence",
            "review_due_at", "rights_status", "licence_scope",
            "permission_evidence", "reviewed_at", "expires_at"
        }
        missing = required - columns
        if missing:
            raise RuntimeError(
                "database migration 003 is required; missing columns: "
                + ", ".join(sorted(missing))
            )
        rows = conn.execute("""
            SELECT s.name AS source_name, s.enabled AS source_enabled, r.*
            FROM source_rights_reviews r
            JOIN sources s ON s.id = r.source_id
            WHERE r.id = (
                SELECT r2.id
                FROM source_rights_reviews r2
                WHERE r2.source_id = r.source_id
                ORDER BY r2.reviewed_at DESC, r2.id DESC
                LIMIT 1
            )
            ORDER BY s.name
        """).fetchall()
    finally:
        conn.close()

    report = {"rows_seen": len(rows), "domains_updated": [], "unmapped": [],
              "sources_without_domain": [], "conflicts": [],
              "routes_ledger_updated": bool(routes_data)}
    assignments = {}
    conflicting_keys = set()
    for row in rows:
        domain = _domain(row["publisher_domain"])
        if not domain:
            report["sources_without_domain"].append(row["source_name"])
            continue
        keys = [key for key in data["publishers"]
                if key == domain or key.endswith("." + domain)]
        if not keys:
            report["unmapped"].append({"source": row["source_name"],
                                       "domain": domain})
            continue
        for key in keys:
            previous = assignments.get(key)
            if previous is not None and previous["id"] != row["id"]:
                conflicting_keys.add(key)
                report["conflicts"].append({
                    "registry_domain": key,
                    "sources": sorted({previous["source_name"], row["source_name"]})
                })
            else:
                assignments[key] = row

    for key, row in assignments.items():
        if key in conflicting_keys:
            continue
        record = data["publishers"][key]
        rights_status = row["rights_status"]
        metadata_status = row["metadata_status"]
        page_status = row["page_metadata_status"]
        processing_status = row["automated_processing_status"]
        if rights_status == "disabled":
            metadata_status = "restricted"
            page_status = "restricted"
            processing_status = "restricted"

        record["source_enabled"] = bool(row["source_enabled"])
        record["metadata_status"] = metadata_status or "pending"
        record["metadata_scope"] = row["metadata_scope"] or ""
        record["metadata_evidence"] = row["metadata_evidence"] or ""
        record["page_metadata_status"] = page_status or "pending"
        record["page_metadata_scope"] = row["page_metadata_scope"] or ""
        record["page_metadata_evidence"] = row["page_metadata_evidence"] or ""
        record["automated_processing_status"] = processing_status or "pending"
        record["automated_processing_scope"] = row["automated_processing_scope"] or ""
        record["automated_processing_evidence"] = row["automated_processing_evidence"] or ""
        record["body_status"] = "licensed" if rights_status == "licensed" else "not_permitted"
        record["body_scope"] = row["licence_scope"] or ""
        record["body_evidence"] = row["permission_evidence"] or ""
        record["reviewed_at"] = _date_only(row["reviewed_at"])
        record["review_due_at"] = _date_only(row["review_due_at"])
        record["expires_at"] = _date_only(row["expires_at"])
        record["database_source_name"] = row["source_name"]
    report["domains_updated"] = sorted(
        key for key in assignments if key not in conflicting_keys
    )
    if routes_data is not None:
        route_by_host = {item["host"]: item for item in routes_data.get("sources", [])}
        for key in report["domains_updated"]:
            route = route_by_host.get(key)
            if route is None:
                continue
            source = data["publishers"][key]
            route["source_enabled"] = source.get("source_enabled") is True
            route["metadata_status"] = source.get("metadata_status", "pending")
            route["page_metadata_status"] = source.get("page_metadata_status", "pending")
            route["automated_processing_status"] = source.get(
                "automated_processing_status", "pending")
            route["body_status"] = source.get("body_status", "not_permitted")
        routes_data["counts"]["enabled"] = sum(
            1 for item in routes_data.get("sources", [])
            if item.get("source_enabled") is True)
    if write and report["conflicts"]:
        raise RuntimeError(
            "conflicting database reviews map to the same registry domain; "
            "resolve the source records before writing")
    if write:
        registry_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        report["written_to"] = str(registry_file)
        if routes_data is not None:
            routes_file.write_text(
                json.dumps(routes_data, ensure_ascii=False, indent=2) + "\\n",
                encoding="utf-8"
            )
            report["routes_written_to"] = str(routes_file)
    else:
        report["written_to"] = None
    return data, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--registry", default=None,
                        help="Optional JSON registry path (defaults to state/source_rights.json)")
    parser.add_argument("--routes", default=None,
                        help="Optional route ledger path (defaults beside the registry)")
    parser.add_argument("--write", action="store_true",
                        help="Write changes to the JSON registry; otherwise dry-run")
    args = parser.parse_args()
    _, report = export_registry(args.db, args.registry, args.write, args.routes)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
