"""Site-level technical checks: robots.txt, XML sitemap, HTTPS reachability."""
from __future__ import annotations

from urllib.parse import urljoin

import httpx


async def _exists(client: httpx.AsyncClient, url: str) -> bool:
    try:
        resp = await client.get(url, follow_redirects=True)
        return resp.status_code == 200 and len(resp.text) > 0
    except httpx.HTTPError:
        return False


async def site_level_checks(client: httpx.AsyncClient, start_url: str, base_domain: str) -> dict:
    root = f"{start_url.split('://')[0]}://{httpx.URL(start_url).host}"
    robots_url = urljoin(root + "/", "robots.txt")
    robots = await _exists(client, robots_url)

    # sitemap: try robots.txt declaration, then the conventional path
    sitemap = False
    if robots:
        try:
            txt = (await client.get(robots_url, follow_redirects=True)).text
            for line in txt.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap = await _exists(client, line.split(":", 1)[1].strip())
                    if sitemap:
                        break
        except httpx.HTTPError:
            pass
    if not sitemap:
        sitemap = await _exists(client, urljoin(root + "/", "sitemap.xml"))

    return {"robots": robots, "sitemap": sitemap}
