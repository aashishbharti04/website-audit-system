"""Application configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- product ---
    product_name: str = "Website Audit & Recommendation System"

    # --- AI ---
    # Provider for the AI analysis layer: "anthropic" (cloud) or "ollama" (local).
    ai_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    # The architecture specifies Sonnet 4.6 (best speed/cost for this volume).
    # Swap to "claude-opus-4-8" for the deepest analysis.
    ai_model: str = "claude-sonnet-4-6"
    ai_max_tokens: int = 12000

    # --- local AI (Ollama) ---
    # A locally-running Ollama server — free, private, no API key. Use any pulled model.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # --- performance (Google PageSpeed Insights) ---
    # PSI works without a key at low volume; set one for higher quota.
    google_psi_api_key: Optional[str] = None

    # --- crawler ---
    user_agent: str = "WebsiteAuditBot/1.0 (+https://example.com)"
    request_timeout: float = 15.0
    crawl_concurrency: int = 8
    link_check_concurrency: int = 20

    # --- database (Phase 5, optional) ---
    database_url: Optional[str] = None  # e.g. postgresql+psycopg://user:pass@host/db

    # --- branding (white-label) ---
    agency_name: str = "Your Agency"
    agency_logo_url: str = ""
    agency_primary_color: str = "#2563eb"
    agency_website: str = "https://example.com"
    agency_email: str = "hello@example.com"

    # --- server ---
    # Origins allowed to call the API from a browser. The live GitHub Pages site is
    # cross-origin, so it must be listed here (override with the CORS_ORIGINS env on your host).
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000,http://localhost:3300,"
        "https://aashishbharti04.github.io"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
