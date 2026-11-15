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
    return sorted(
        [entry for entry in entries if isinstance(entry, dict)],
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

    bn_path = BANGLA_EDITIONS_DIR / f"bn-{edition_date}.json"
    bangla = _read_json(bn_path) if bn_path.is_file() else None
    return {"edition": edition, "bangla": bangla, "index_entry": entry}
