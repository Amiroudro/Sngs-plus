"""Read-only access to human-published Sarangsho Plus editions."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EDITIONS_DIR = PROJECT_ROOT / "editions"
BANGLA_EDITIONS_DIR = PROJECT_ROOT / "app" / "assets" / "editions"
METADATA_ARCHIVE_DIR = EDITIONS_DIR
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class EditionNotFound(FileNotFoundError):
    """Raised when an edition is not indexed or its published file is absent."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Could not read valid edition JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return value


def load_index() -> dict[str, Any]:
    path = EDITIONS_DIR / "index.json"
    if not path.exists():
        return {"correct_consecutive_editions": 0, "editions": []}
    index = _read_json(path)
    if not isinstance(index.get("editions"), list):
        raise ValueError("Edition index must contain an 'editions' list")
    return index


def list_editions() -> list[dict[str, Any]]:
    entries = load_index()["editions"]
    # The index is the publication registry, but require its explicit
    # published state too so staged/draft entries can never appear.
    return sorted(
        [
            entry for entry in entries
            if isinstance(entry, dict) and entry.get("status") == "published"
        ],
        key=lambda entry: str(entry.get("edition_date", "")),
        reverse=True,
    )


def load_edition(edition_date: str) -> dict[str, Any]:
    if not DATE_RE.fullmatch(edition_date):
        raise ValueError("edition_date must use YYYY-MM-DD")
    try:
        date.fromisoformat(edition_date)
    except ValueError as exc:
        raise ValueError("edition_date is not a valid calendar date") from exc

    entry = next(
        (item for item in list_editions()
         if item.get("edition_date") == edition_date),
        None,
    )
    if entry is None:
        raise EditionNotFound(edition_date)

    # Only allow the exact date-derived filename, never arbitrary index paths.
    filename = entry.get("file")
    expected = f"data-{edition_date}.json"
    if filename != expected:
        raise ValueError(f"Edition index filename must be {expected}")

    data_path = EDITIONS_DIR / expected
    if not data_path.is_file():
        raise EditionNotFound(f"Published edition file missing: {expected}")
    edition = _read_json(data_path)
    if edition.get("edition_date") != edition_date:
        raise ValueError("Edition file date does not match its index entry")
    if edition.get("status") != "published":
        raise ValueError("Indexed edition file is not marked published")

    bn_path = BANGLA_EDITIONS_DIR / f"bn-{edition_date}.json"
    bangla = _read_json(bn_path) if bn_path.is_file() else None
    return {"edition": edition, "bangla": bangla, "index_entry": entry}


def load_metadata_archive(edition_date: str) -> list[dict[str, Any]]:
    """Load the metadata-only archive for a published date.

    Publication is gated by the normal edition index. Staged files and
    archives for draft/unindexed dates are never exposed.
    """
    load_edition(edition_date)  # validates date and human-published status
    path = METADATA_ARCHIVE_DIR / f"metadata-only-{edition_date}.json"
    if not path.is_file():
        return []
    archive = _read_json(path)
    if archive.get("date") != edition_date:
        raise ValueError("Metadata archive date does not match its filename")
    items = archive.get("items", [])
    if not isinstance(items, list):
        raise ValueError("Metadata archive must contain an 'items' list")

    allowed_statuses = {
        "metadata_only_body_not_licensed",
        "body_blocked_by_robots",
        "no_direct_article_url",
        "body_fetch_failed",
    }
    safe_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("archive_status") not in allowed_statuses:
            continue
        if item.get("study_note_status") != "not_generated":
            continue
        # Explicit field allowlist prevents body text or generated study
        # material from leaking into this metadata-only endpoint.
        safe_items.append({
            key: item.get(key, "")
            for key in ("id", "headline", "source", "url", "published",
                        "archive_status", "study_note_status")
        })
    return safe_items


def search_metadata_archive(query: str = "", source: str = "",
                            limit: int = 30) -> dict[str, Any]:
    """Search metadata-only records from published editions only."""
    q = query.strip().casefold()
    publisher = source.strip().casefold()
    matches = []
    for entry in list_editions():
        edition_date = str(entry.get("edition_date", ""))
        try:
            items = load_metadata_archive(edition_date)
        except EditionNotFound:
            continue
        for item in items:
            haystack = " ".join((item.get("headline", ""),
                                 item.get("source", ""),
                                 item.get("url", ""))).casefold()
            if q and q not in haystack:
                continue
            if publisher and publisher not in item.get("source", "").casefold():
                continue
            matches.append({**item, "edition_date": edition_date,
                            "record_type": "metadata_only"})
    matches.sort(key=lambda item: (
        str(item.get("published", "")), item.get("edition_date", "")
    ), reverse=True)
    return {"total": len(matches), "items": matches[:limit]}
