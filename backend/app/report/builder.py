"""Branded report builder. Renders an HTML report (Jinja2) and converts to PDF (WeasyPrint).

The same HTML template is used for the in-browser report view and the PDF export.
PDF generation degrades gracefully: if WeasyPrint's native deps aren't installed,
`render_pdf` raises a clear error and the API falls back to HTML.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import get_settings
from ..schemas import AuditResult, Priority, Severity

_TEMPLATES = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES)),
    autoescape=select_autoescape(["html", "xml"]),
)

_SEV_COLOR = {
    Severity.critical: "#dc2626",
    Severity.high: "#ea580c",
    Severity.medium: "#d97706",
    Severity.low: "#2563eb",
    Severity.info: "#6b7280",
}
_IMPACT_COLOR = {"High": "#dc2626", "Medium": "#d97706", "Low": "#16a34a"}


def _context(audit: AuditResult) -> dict:
    cfg = get_settings()
    analysis = audit.analysis
    issues = analysis.issues if analysis else []
    by_sev: dict[str, int] = {}
    for i in issues:
        by_sev[i.severity.value] = by_sev.get(i.severity.value, 0) + 1

    # group into the P1/P2/P3 action plan
    action_plan = {p.value: [i for i in issues if i.priority == p] for p in Priority}
    # recommended-fixes table: highest-impact items first
    impact_rank = {"High": 0, "Medium": 1, "Low": 2}
    fixes = sorted(issues, key=lambda i: (impact_rank.get(i.impact.value, 3),
                                          list(Severity).index(i.severity)))[:12]

    def score_color(s):
        return "#16a34a" if s >= 80 else "#d97706" if s >= 50 else "#dc2626"

    return {
        "audit": audit,
        "analysis": analysis,
        "issues": issues,
        "by_sev": by_sev,
        "sev_color": {s.value: c for s, c in _SEV_COLOR.items()},
        "impact_color": _IMPACT_COLOR,
        "action_plan": action_plan,
        "fixes": fixes,
        "category_scores": analysis.category_scores if analysis else [],
        "score_color": score_color,
        "score": audit.score if audit.score is not None else (analysis.score if analysis else None),
        "crawl": audit.crawl,
        "vitals": audit.crawl.vitals if audit.crawl else None,
        "product_name": cfg.product_name,
        "agency": {
            "name": cfg.agency_name,
            "logo_url": cfg.agency_logo_url,
            "primary": cfg.agency_primary_color,
            "website": cfg.agency_website,
            "email": cfg.agency_email,
        },
        "client_name": audit.client_name or (audit.crawl.domain if audit.crawl else audit.url),
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
    }


def render_html(audit: AuditResult) -> str:
    return _env.get_template("report.html").render(**_context(audit))


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except Exception:
        return False


def render_pdf(audit: AuditResult) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as e:  # native libs (pango/cairo) missing
        raise RuntimeError(
            "WeasyPrint is not available. Install its native dependencies "
            "(see https://doc.courtbouillon.org/weasyprint/stable/first_steps.html), "
            "or use the HTML export instead."
        ) from e
    html = render_html(audit)
    return HTML(string=html).write_pdf()
