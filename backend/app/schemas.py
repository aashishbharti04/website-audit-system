"""Pydantic models shared across the backend (crawl data, AI analysis, audit results).

Website Doctor AI — full 7-category audit model.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------- request ----------
class AuditOptions(BaseModel):
    max_pages: int = Field(25, ge=1, le=300, description="How many pages to crawl.")
    check_links: bool = True
    use_ai: bool = True
    check_performance: bool = True  # Google PageSpeed Insights (Core Web Vitals)
    client_name: Optional[str] = None
    primary_keyword: Optional[str] = None  # for basic keyword-optimisation checks


class AuditRequest(BaseModel):
    url: str
    options: AuditOptions = AuditOptions()


# ---------- crawl ----------
class LinkStatus(BaseModel):
    url: str
    status: Optional[int] = None
    ok: bool = False
    internal: bool = True
    error: Optional[str] = None


class RedirectChain(BaseModel):
    url: str
    hops: int
    final_url: str
    chain: list[int] = []  # status codes along the way


class PageSEO(BaseModel):
    url: str
    status: Optional[int] = None
    depth: int = 0
    # on-page
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    h1: list[str] = []
    h2_count: int = 0
    canonical: Optional[str] = None
    robots_meta: Optional[str] = None
    noindex: bool = False
    # content
    word_count: int = 0
    content_hash: Optional[str] = None
    readability: Optional[float] = None  # Flesch reading ease (0-100, higher = easier)
    has_faq: bool = False
    # media
    images_total: int = 0
    images_missing_alt: int = 0
    # technical / mobile
    has_viewport: bool = False
    mixed_content: bool = False  # http assets on an https page
    lang: Optional[str] = None
    # structured data / local
    has_open_graph: bool = False
    jsonld_types: list[str] = []
    phone: Optional[str] = None
    address_hint: Optional[str] = None
    # ux / conversion
    cta_count: int = 0
    has_contact_form: bool = False
    # accessibility
    inputs_without_label: int = 0
    # links
    internal_links: int = 0
    external_links: int = 0
    load_ms: Optional[int] = None
    error: Optional[str] = None


class CoreWebVitals(BaseModel):
    url: str
    performance_score: Optional[int] = None  # 0-100
    lcp_ms: Optional[float] = None
    cls: Optional[float] = None
    inp_ms: Optional[float] = None  # INP replaced FID as the responsiveness metric
    fcp_ms: Optional[float] = None
    tbt_ms: Optional[float] = None
    speed_index_ms: Optional[float] = None
    unused_css_kb: Optional[float] = None
    unused_js_kb: Optional[float] = None
    heavy_images_kb: Optional[float] = None
    source: str = "psi"  # or "unavailable"
    error: Optional[str] = None


class CrawlResult(BaseModel):
    start_url: str
    domain: str
    https: bool = False
    robots_txt_found: bool = False
    sitemap_found: bool = False
    pages: list[PageSEO] = []
    broken_links: list[LinkStatus] = []
    redirect_chains: list[RedirectChain] = []
    links_checked: int = 0
    vitals: Optional[CoreWebVitals] = None
    crawled_at: datetime


# ---------- analysis ----------
class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Category(str, Enum):
    technical = "Technical SEO"
    on_page = "On-Page SEO"
    performance = "Performance"
    content = "Content"
    local = "Local SEO"
    ux = "UX & Conversion"
    accessibility = "Accessibility"


class Priority(str, Enum):
    p1 = "P1 — Critical"
    p2 = "P2 — Important"
    p3 = "P3 — Recommended"


class Impact(str, Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class Difficulty(str, Enum):
    easy = "Easy"
    medium = "Medium"
    hard = "Hard"


class Issue(BaseModel):
    title: str
    category: Category
    severity: Severity
    priority: Priority
    impact: Impact
    difficulty: Difficulty
    description: str
    recommendation: str
    affected: Optional[str] = Field(None, description="Pages or elements affected, if specific.")


class CategoryScore(BaseModel):
    category: Category
    score: int = Field(..., ge=0, le=100)
    issue_count: int = 0


class AIAnalysis(BaseModel):
    """The schema Claude is forced to fill (structured outputs)."""
    executive_summary: str = Field(..., description="3-5 sentence plain-English overview for the client.")
    score: int = Field(..., ge=0, le=100, description="Overall website health score 0-100.")
    category_scores: list[CategoryScore] = Field(..., description="Score per audit category.")
    issues: list[Issue] = Field(..., description="Prioritised issues, most severe first.")
    quick_wins: list[str] = Field(default_factory=list, description="3-5 highest-impact, easiest actions to do first.")
    expected_results: list[str] = Field(default_factory=list, description="Realistic outcomes if the fixes are applied.")


# ---------- audit job ----------
class AuditStatus(str, Enum):
    queued = "queued"
    crawling = "crawling"
    checking_links = "checking_links"
    measuring_performance = "measuring_performance"
    analyzing = "analyzing"
    building_report = "building_report"
    done = "done"
    error = "error"


class ProgressEvent(BaseModel):
    status: AuditStatus
    message: str
    pct: int = 0


class AuditResult(BaseModel):
    id: str
    url: str
    client_name: Optional[str] = None
    status: AuditStatus
    created_at: datetime
    crawl: Optional[CrawlResult] = None
    analysis: Optional[AIAnalysis] = None
    score: Optional[int] = None
    error: Optional[str] = None
