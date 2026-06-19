"""Core Web Vitals via the Google PageSpeed Insights (Lighthouse) API.

PSI works without an API key at low volume; set GOOGLE_PSI_API_KEY for higher quota.
Runs on the homepage only by default (it's slow and quota-limited). Degrades gracefully:
on any error it returns a CoreWebVitals with source="unavailable" so the audit still completes.
"""
from __future__ import annotations

import httpx

from ..config import get_settings
from ..schemas import CoreWebVitals

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _num(audits: dict, key: str) -> float | None:
    a = audits.get(key) or {}
    v = a.get("numericValue")
    return round(float(v), 1) if isinstance(v, (int, float)) else None


def _savings_kb(audits: dict, key: str) -> float | None:
    a = audits.get(key) or {}
    bytes_ = (a.get("details") or {}).get("overallSavingsBytes")
    if isinstance(bytes_, (int, float)):
        return round(bytes_ / 1024, 1)
    return None


async def core_web_vitals(
    url: str, strategy: str = "mobile", api_key: str | None = None
) -> CoreWebVitals:
    cfg = get_settings()
    key = api_key or cfg.google_psi_api_key  # per-request key (UI Settings) wins over env
    params = {"url": url, "strategy": strategy, "category": "performance"}
    if key:
        params["key"] = key
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(PSI_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        return CoreWebVitals(url=url, source="unavailable", error=str(e))

    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    perf = (lh.get("categories", {}).get("performance", {}) or {}).get("score")
    perf_score = int(perf * 100) if isinstance(perf, (int, float)) else None

    # field data (real users) — INP / FID if available
    field = (data.get("loadingExperience", {}) or {}).get("metrics", {}) or {}
    inp = field.get("INTERACTION_TO_NEXT_PAINT", {}).get("percentile")
    if inp is None:
        inp = field.get("FIRST_INPUT_DELAY_MS", {}).get("percentile")

    return CoreWebVitals(
        url=url,
        performance_score=perf_score,
        lcp_ms=_num(audits, "largest-contentful-paint"),
        cls=(lambda v: round(v, 3) if v is not None else None)(_num(audits, "cumulative-layout-shift")),
        inp_ms=float(inp) if isinstance(inp, (int, float)) else None,
        fcp_ms=_num(audits, "first-contentful-paint"),
        tbt_ms=_num(audits, "total-blocking-time"),
        speed_index_ms=_num(audits, "speed-index"),
        unused_css_kb=_savings_kb(audits, "unused-css-rules"),
        unused_js_kb=_savings_kb(audits, "unused-javascript"),
        heavy_images_kb=_savings_kb(audits, "uses-optimized-images") or _savings_kb(audits, "modern-image-formats"),
        source="psi",
    )
