"""FastAPI application entrypoint."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import __version__
from .config import get_settings
from .report import docx_available, weasyprint_available
from .routes import audits, report, ws

# Single-page HTML UI (vanilla JS) — served same-origin so the dashboard, WebSocket
# progress and report exports all work without any CORS configuration.
_INDEX_HTML = Path(__file__).resolve().parents[2] / "frontend" / "index.html"

cfg = get_settings()

app = FastAPI(
    title="Website Audit & Recommendation System API",
    version=__version__,
    description="White-label SEO audit engine: crawl, analyse, and generate branded reports.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audits.router)
app.include_router(report.router)
app.include_router(ws.router)


@app.get("/", include_in_schema=False)
def index():
    """Serve the single-page HTML dashboard."""
    if _INDEX_HTML.exists():
        return FileResponse(_INDEX_HTML)
    return {"status": "ok", "message": "UI not found; API is running. See /docs."}


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "product": cfg.product_name,
        "ai_enabled": cfg.ai_enabled,
        "ai_provider": cfg.ai_provider,
        "ai_model": cfg.ai_model if cfg.ai_enabled else None,
        "ollama_model": cfg.ollama_model,
        "pdf_enabled": weasyprint_available(),
        "docx_enabled": docx_available(),
        "agency": cfg.agency_name,
    }
