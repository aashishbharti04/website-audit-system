"""AI analysis layer — sends real crawl + Lighthouse data to Claude and gets back a
prioritised, validated audit via structured outputs (guaranteed to match `AIAnalysis`).

Uses the official Anthropic Python SDK with `messages.parse()`.
"""
from __future__ import annotations

import json

from ..config import get_settings
from ..schemas import AIAnalysis, CrawlResult

SYSTEM_PROMPT = """You are the senior auditor behind "Website Doctor AI", a professional
website audit tool used by a digital-marketing agency. You receive REAL data already
collected by a crawler and Google's PageSpeed Insights (Lighthouse) — do not invent pages,
metrics, or facts not present in the data.

Produce a client-ready audit across these 7 categories:
Technical SEO, On-Page SEO, Performance, Content, Local SEO, UX & Conversion, Accessibility.

Requirements:
- Write a clear executive summary a non-technical business owner understands.
- Give an overall website health score (0-100) and a score per category, grounded in the data.
- List concrete, prioritised issues. Each issue needs: title, category, severity, priority
  (P1 critical / P2 important / P3 recommended), impact (High/Medium/Low), difficulty
  (Easy/Medium/Hard), a plain-English description of the business impact, and a specific fix.
- Build on the supplied rule-based findings: refine and explain them, merge duplicates, and
  ADD insights the rules can't compute (keyword/intent fit, content gaps, internal-linking
  strategy, local-SEO/GBP opportunities, conversion improvements).
- Be honest about estimates: AI-content detection, competitor gaps, full WCAG and FID are
  approximations — frame them as such, never as certainties.
- End with 3-5 quick wins (high impact, easy) and realistic expected results.
Be specific and grounded. Do not pad with generic advice unsupported by the data."""


def summarize_crawl(crawl: CrawlResult, rule_findings: AIAnalysis | None = None) -> dict:
    """Compact the crawl + vitals into a JSON-friendly payload for the model."""
    pages = []
    for p in crawl.pages[:60]:
        pages.append({
            "url": p.url, "status": p.status, "depth": p.depth, "title": p.title,
            "title_length": p.title_length, "meta_description_length": p.meta_description_length,
            "h1": p.h1[:3], "h2_count": p.h2_count, "canonical": bool(p.canonical),
            "noindex": p.noindex, "word_count": p.word_count, "readability": p.readability,
            "images_total": p.images_total, "images_missing_alt": p.images_missing_alt,
            "has_viewport": p.has_viewport, "mixed_content": p.mixed_content,
            "jsonld_types": p.jsonld_types, "phone": bool(p.phone), "address": bool(p.address_hint),
            "cta_count": p.cta_count, "has_contact_form": p.has_contact_form,
            "inputs_without_label": p.inputs_without_label, "internal_links": p.internal_links,
            "has_faq": p.has_faq, "load_ms": p.load_ms, "error": p.error,
        })
    payload = {
        "domain": crawl.domain,
        "https": crawl.https,
        "robots_txt_found": crawl.robots_txt_found,
        "sitemap_found": crawl.sitemap_found,
        "pages_crawled": len(crawl.pages),
        "links_checked": crawl.links_checked,
        "broken_links": [{"url": b.url, "status": b.status, "internal": b.internal} for b in crawl.broken_links[:30]],
        "redirect_chains": [{"url": c.url, "hops": c.hops} for c in crawl.redirect_chains[:20]],
        "core_web_vitals": crawl.vitals.model_dump() if crawl.vitals else None,
        "pages": pages,
    }
    if rule_findings:
        payload["rule_based_findings"] = [
            {"title": i.title, "category": i.category.value, "severity": i.severity.value,
             "impact": i.impact.value, "difficulty": i.difficulty.value, "affected": i.affected}
            for i in rule_findings.issues
        ]
        payload["rule_based_scores"] = {c.category.value: c.score for c in rule_findings.category_scores}
    return payload


_USER_PREAMBLE = (
    "Here is the audit data (crawl + Lighthouse + rule-based findings). "
    "Return the structured audit.\n\n"
)


def analyze_with_ai(
    crawl: CrawlResult,
    rule_findings: AIAnalysis | None = None,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    ollama_base_url: str | None = None,
) -> AIAnalysis:
    """Run the AI analysis with the chosen provider. Raises on misconfiguration/transport
    errors so the caller can fall back to the rule-based report.

    All args (from the UI Settings panel) override the server's env config.
    """
    cfg = get_settings()
    prov = (provider or cfg.ai_provider or "anthropic").lower()
    if prov == "ollama":
        return _analyze_with_ollama(crawl, rule_findings, model=model, base_url=ollama_base_url)
    return _analyze_with_anthropic(crawl, rule_findings, api_key=api_key, model=model)


def _analyze_with_anthropic(
    crawl: CrawlResult,
    rule_findings: AIAnalysis | None,
    api_key: str | None,
    model: str | None,
) -> AIAnalysis:
    import anthropic

    cfg = get_settings()
    key = api_key or cfg.anthropic_api_key  # per-request key (UI Settings) wins over env
    if not key:
        raise RuntimeError("No Anthropic API key available; AI analysis unavailable.")

    client = anthropic.Anthropic(api_key=key)
    payload = summarize_crawl(crawl, rule_findings)

    response = client.messages.parse(
        model=model or cfg.ai_model,
        max_tokens=cfg.ai_max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": _USER_PREAMBLE + json.dumps(payload, ensure_ascii=False, default=str),
        }],
        output_format=AIAnalysis,
    )
    return response.parsed_output


def _analyze_with_ollama(
    crawl: CrawlResult,
    rule_findings: AIAnalysis | None,
    model: str | None,
    base_url: str | None,
) -> AIAnalysis:
    """Run the analysis against a local Ollama server using structured (JSON-schema) output.

    Needs a running Ollama (`ollama serve`) with the model pulled (e.g. `ollama pull llama3.1`).
    """
    import httpx

    cfg = get_settings()
    base = (base_url or cfg.ollama_base_url).rstrip("/")
    name = model or cfg.ollama_model
    payload = summarize_crawl(crawl, rule_findings)

    body = {
        "model": name,
        "stream": False,
        "format": AIAnalysis.model_json_schema(),  # constrain output to our schema
        "options": {"temperature": 0.2, "num_predict": cfg.ai_max_tokens},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _USER_PREAMBLE + json.dumps(payload, ensure_ascii=False, default=str)},
        ],
    }
    try:
        resp = httpx.post(f"{base}/api/chat", json=body, timeout=httpx.Timeout(600.0))
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Could not reach Ollama at {base} ({e}).") from e

    content = (resp.json().get("message") or {}).get("content") or ""
    return AIAnalysis.model_validate_json(content)
