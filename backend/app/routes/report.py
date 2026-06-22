"""Stateless report rendering for external no-code tools (e.g. a Google Opal app).

Opal can't emit binary files, so a workflow step POSTs the audit JSON here and gets back a
download URL. The .docx is built with the same `render_docx` used by the live app and held
briefly in memory, then served from a GET link Opal can present to the user.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from ..report import docx_available, render_docx, render_html
from ..schemas import AuditResult, AuditStatus, CrawlResult, ReportRequest

router = APIRouter(prefix="/api/report", tags=["report"])

# token -> (filename, bytes). Small LRU-ish cap so memory can't grow unbounded.
_FILES: dict[str, tuple[str, bytes]] = {}
_MAX_FILES = 100


def _to_audit(req: ReportRequest) -> AuditResult:
    domain = req.url.split("//")[-1].split("/")[0] or "site"
    crawl = CrawlResult(
        start_url=req.url or f"https://{domain}",
        domain=domain,
        https=req.https,
        pages=[],  # stateless: no crawl pages — the builder only needs counts/vitals
        links_checked=req.links_checked,
        vitals=req.vitals,
        crawled_at=datetime.now(timezone.utc),
    )
    return AuditResult(
        id=uuid.uuid4().hex[:12],
        url=req.url,
        client_name=req.client_name,
        status=AuditStatus.done,
        created_at=datetime.now(timezone.utc),
        crawl=crawl,
        analysis=req.analysis,
        score=req.analysis.score,
    )


@router.post("/docx")
def report_docx(req: ReportRequest, request: Request) -> dict:
    """Build a .docx from posted analysis JSON; return a short-lived download URL."""
    if not docx_available():
        raise HTTPException(501, "Word export unavailable (python-docx not installed).")
    audit = _to_audit(req)
    data = render_docx(audit)
    if len(_FILES) >= _MAX_FILES:
        _FILES.pop(next(iter(_FILES)))
    token = uuid.uuid4().hex
    filename = f"website-audit-{audit.crawl.domain}.docx"
    _FILES[token] = (filename, data)
    base = str(request.base_url).rstrip("/")
    return {"download_url": f"{base}/api/report/file/{token}", "filename": filename}


@router.post("/html", response_class=HTMLResponse)
def report_html(req: ReportRequest) -> HTMLResponse:
    """Same, but returns the branded HTML report inline (handy for Opal preview)."""
    return HTMLResponse(render_html(_to_audit(req)))


@router.get("/file/{token}")
def report_file(token: str) -> Response:
    item = _FILES.get(token)
    if not item:
        raise HTTPException(404, "File expired or not found. Re-generate the report.")
    filename, data = item
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
