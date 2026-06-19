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


def analyze_with_ai(crawl: CrawlResult, rule_findings: AIAnalysis | None = None) -> AIAnalysis:
    """Run the Claude analysis. Raises if no API key is configured (caller should check first)."""
    import anthropic

    cfg = get_settings()
    if not cfg.ai_enabled:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; AI analysis unavailable.")

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    payload = summarize_crawl(crawl, rule_findings)

    response = client.messages.parse(
        model=cfg.ai_model,
        max_tokens=cfg.ai_max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                "Here is the audit data (crawl + Lighthouse + rule-based findings). "
                "Return the structured audit.\n\n" + json.dumps(payload, ensure_ascii=False, default=str)
            ),
        }],
        output_format=AIAnalysis,
    )
    return response.parsed_output
