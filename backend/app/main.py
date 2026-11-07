from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sarangsho Plus API",
    version="0.1.0",
    description="Backend foundation for the Sarangsho Plus bilingual news platform.",
)

# Local development only. Restrict this list to the deployed frontend origin before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "project": "sarangsho-plus", "stage": "foundation"}

@app.get("/api/v1/briefing")
def briefing():
    return {
        "status": "demo",
        "message": "Live collection is not connected yet.",
        "stories": [],
    }
