"""Async breadth-first crawler built on httpx. Fetches pages, tracks depth, and
records redirect chains, then extracts SEO/content/UX/a11y signals per page.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from ..config import get_settings
from ..schemas import CrawlResult, PageSEO, RedirectChain
from .seo_parser import parse_page
from .site_checks import site_level_checks


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _normalize_start(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


async def _fetch(client: httpx.AsyncClient, url: str):
    """Return (html, status, load_ms, error, redirect_chain_or_None)."""
    start = time.perf_counter()
    try:
        resp = await client.get(url, follow_redirects=True)
        load_ms = int((time.perf_counter() - start) * 1000)
        chain = None
        if len(resp.history) >= 2:  # more than one hop = redirect chain worth flagging
            chain = RedirectChain(
                url=url,
                hops=len(resp.history),
                final_url=str(resp.url),
                chain=[r.status_code for r in resp.history] + [resp.status_code],
            )
        ctype = resp.headers.get("content-type", "")
        if "text/html" not in ctype:
            return None, resp.status_code, load_ms, f"Not HTML ({ctype or 'unknown'})", chain
        return resp.text, resp.status_code, load_ms, None, chain
    except httpx.HTTPError as e:
        return None, None, int((time.perf_counter() - start) * 1000), str(e), None


async def crawl(start_url: str, max_pages: int = 25, on_page=None) -> tuple[CrawlResult, set[str]]:
    """Crawl up to `max_pages` internal pages from `start_url` (breadth-first, depth-tracked)."""
    cfg = get_settings()
    start_url = _normalize_start(start_url)
    base_domain = _domain(start_url)

    seen: set[str] = {start_url}
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    pages: list[PageSEO] = []
    redirect_chains: list[RedirectChain] = []
    all_links: set[str] = set()

    headers = {"User-Agent": cfg.user_agent}
    limits = httpx.Limits(max_connections=cfg.crawl_concurrency)
    async with httpx.AsyncClient(headers=headers, timeout=cfg.request_timeout, limits=limits) as client:
        while queue and len(pages) < max_pages:
            batch = [queue.popleft() for _ in range(min(cfg.crawl_concurrency, len(queue), max_pages - len(pages)))]
            results = await asyncio.gather(*[_fetch(client, u) for (u, _d) in batch])

            for (url, depth), (html, status, load_ms, error, chain) in zip(batch, results):
                if chain:
                    redirect_chains.append(chain)
                if error or not html:
                    pages.append(PageSEO(url=url, status=status, depth=depth, error=error))
                    continue
                page, links = parse_page(url, html, status, load_ms, base_domain, depth=depth)
                pages.append(page)
                all_links |= links

                for link in links:
                    if link not in seen and _domain(link) == base_domain and len(seen) < max_pages * 5:
                        seen.add(link)
                        queue.append((link, depth + 1))

                if on_page:
                    await on_page(len(pages), max_pages, url)

        # site-level checks (robots.txt, sitemap.xml, https)
        site = await site_level_checks(client, start_url, base_domain)

    result = CrawlResult(
        start_url=start_url,
        domain=base_domain,
        https=start_url.startswith("https://"),
        robots_txt_found=site["robots"],
        sitemap_found=site["sitemap"],
        pages=pages,
        redirect_chains=redirect_chains,
        crawled_at=datetime.now(timezone.utc),
    )
    return result, all_links
