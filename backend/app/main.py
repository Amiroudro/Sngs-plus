import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .edition_store import EditionNotFound, list_editions, load_edition

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

    if language == "bn" and result["bangla"] is not None:
        data = result["bangla"]
        resolved_language = "bn"
    else:
        data = result["edition"]
        resolved_language = "en"

    return {
        "status": "published",
        "edition_date": edition_date,
        "language": resolved_language,
        "fallback_language": "en" if language == "bn" and resolved_language == "en" else None,
        "data": data,
        "stories": data.get("stories", []),
    }
