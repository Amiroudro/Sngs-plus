import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .edition_store import (EditionNotFound, list_editions, load_edition,\n                            search_metadata_archive)

app = FastAPI(
    title="Sarangsho Plus API",
    version="0.2.0",
    description="Read-only API for human-published Sarangsho Plus editions.",
)

# Local development only. Restrict this list to the deployed frontend origin before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "SARANGSHO_CORS_ORIGINS",
        "http://localhost:4321,http://127.0.0.1:4321",
    ).split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _merge_bangla_stories(english_stories, bangla_stories):
    """Return an ordered story list with Bangla fields overlaid by story ID.

    The v2 converter stores Bangla stories as an ID-keyed object, while
    the English edition stores an ordered list. Older app-format editions
    may instead provide a Bangla list, so both shapes are accepted.
    """
    if not isinstance(english_stories, list) or not english_stories:
        return []
    if isinstance(bangla_stories, dict):
        overlays = bangla_stories
    elif isinstance(bangla_stories, list):
        overlays = {
            story.get("id"): story for story in bangla_stories
            if isinstance(story, dict) and story.get("id")
        }
    else:
        return []

    merged = []
    for story in english_stories:
        if not isinstance(story, dict):
            continue
        overlay = overlays.get(story.get("id"))
        # A mechanical conversion is not a reviewed translation. Require
        # an explicit per-story approval before any Bangla fields are shown.
        if not isinstance(overlay, dict) or overlay.get("translation_status") != "approved":
            return []
        merged.append({**story, **overlay, "id": story.get("id")})
    return merged


@app.get("/health")
def health():
    editions = list_editions()
    return {
        "status": "ok",
        "project": "sarangsho-plus",
        "stage": "edition-api" if editions else "foundation",
        "published_editions": len(editions),
    }


@app.get("/api/v1/editions")
def editions():
    entries = list_editions()
    return {
        "status": "ready" if entries else "demo",
        "count": len(entries),
        "editions": entries,
    }


@app.get("/api/v1/editions/{edition_date}")
def edition_detail(edition_date: str):
    try:
        return load_edition(edition_date)
    except EditionNotFound:
        raise HTTPException(status_code=404, detail="Edition not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/v1/briefing")
def briefing(language: str = Query(default="en", pattern="^(en|bn)$")):
    entries = list_editions()
    if not entries:
        return {
            "status": "demo",
            "message": "No human-published edition is available yet.",
            "edition_date": None,
            "language": language,
            "stories": [],
        }

    edition_date = entries[0].get("edition_date", "")
    try:
        result = load_edition(edition_date)
    except (EditionNotFound, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Latest edition unavailable: {exc}")

    english_data = result["edition"]
    english_stories = english_data.get("stories", [])
    bangla_data = result.get("bangla")
    stories = english_stories
    data = english_data
    resolved_language = "en"

    if language == "bn" and isinstance(bangla_data, dict):
        bangla_stories = _merge_bangla_stories(
            english_stories, bangla_data.get("stories")
        )
        if bangla_stories and any(
            story != english for story, english in zip(bangla_stories, english_stories)
        ):
            stories = bangla_stories
            data = bangla_data
            resolved_language = "bn"

    return {
        "status": "published",
        "edition_date": edition_date,
        "language": resolved_language,
        "fallback_language": "en" if language == "bn" and resolved_language == "en" else None,
        "data": data,
        "stories": stories,
    }


@app.get("/api/v1/archive")
def metadata_archive(
    q: str = Query(default="", max_length=160),
    source: str = Query(default="", max_length=100),
    limit: int = Query(default=30, ge=1, le=100),
):
    """Search the published metadata-only archive, never article bodies."""
    try:
        result = search_metadata_archive(q, source, limit)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail=f"Archive unavailable: {exc}")
    return {
        "status": "ready" if result["total"] else "empty",
        "record_type": "metadata_only",
        "study_notes_available": False,
        **result,
    }
