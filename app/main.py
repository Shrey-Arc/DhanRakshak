import logging
from fastapi import FastAPI

from app.routers import auth, filing, documents, ml_results, finalize, dossier, reports, audit

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="DhanRakshak Backend", version="1.0.0")

app.include_router(auth.router)
app.include_router(filing.router)
app.include_router(documents.router)
app.include_router(ml_results.router)
app.include_router(finalize.router)
app.include_router(dossier.router)
app.include_router(reports.router)
app.include_router(audit.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
