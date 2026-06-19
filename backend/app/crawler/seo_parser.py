"""Extract on-page SEO, content, local, UX and accessibility signals with BeautifulSoup."""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from ..schemas import PageSEO

_PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4})")
_CTA_WORDS = ("contact", "call", "book", "buy", "get a quote", "get quote", "sign up", "signup",
              "subscribe", "request", "demo", "schedule", "order", "start", "get started",
              "free", "download", "shop now", "learn more", "enquire", "inquire")


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def normalize_link(base_url: str, href: str) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return None
    absolute = urljoin(base_url, href)
    absolute, _ = urldefrag(absolute)
    if not absolute.startswith(("http://", "https://")):
        return None
    return absolute


def _count_syllables(word: str) -> int:
    word = word.lower()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> float | None:
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[A-Za-z]+", text)
    if len(words) < 30:
        return None
    syllables = sum(_count_syllables(w) for w in words)
    wc = len(words)
    score = 206.835 - 1.015 * (wc / sentences) - 84.6 * (syllables / wc)
    return round(max(0.0, min(100.0, score)), 1)


def _jsonld_types(soup: BeautifulSoup) -> list[str]:
    types: set[str] = set()
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "{}")
        except Exception:
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict):
                t = obj.get("@type")
                if isinstance(t, str):
                    types.add(t)
                elif isinstance(t, list):
                    types.update(x for x in t if isinstance(x, str))
                # @graph
                for node in obj.get("@graph", []) if isinstance(obj.get("@graph"), list) else []:
                    if isinstance(node, dict) and isinstance(node.get("@type"), str):
                        types.add(node["@type"])
    for tag in soup.find_all(attrs={"itemtype": True}):
        it = tag.get("itemtype", "")
        if it:
            types.add(it.rstrip("/").split("/")[-1])
    return sorted(types)


def parse_page(url: str, html: str, status: int | None, load_ms: int | None,
               base_domain: str, depth: int = 0) -> tuple[PageSEO, set[str]]:
    soup = BeautifulSoup(html, "lxml")
    is_https = url.startswith("https://")

    title_tag = soup.title.string.strip() if soup.title and soup.title.string else None

    def meta(name: str, attr: str = "name") -> str | None:
        tag = soup.find("meta", attrs={attr: name})
        return tag.get("content", "").strip() if tag and tag.get("content") else None

    robots_meta = meta("robots")
    meta_desc = meta("description")
    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href") if canonical_tag else None

    images = soup.find_all("img")
    missing_alt = sum(1 for img in images if not img.get("alt", "").strip())

    body_text = soup.get_text(" ", strip=True)
    words = body_text.split()
    word_count = len(words)
    content_hash = hashlib.sha1(re.sub(r"\s+", " ", body_text.lower()).encode()).hexdigest() if word_count else None

    # links
    internal, external = 0, 0
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        absolute = normalize_link(url, a["href"])
        if not absolute:
            continue
        links.add(absolute)
        if _domain(absolute) == base_domain:
            internal += 1
        else:
            external += 1

    jsonld = _jsonld_types(soup)

    # local / NAP hints
    phone_match = _PHONE_RE.search(body_text)
    phone = phone_match.group(0).strip() if phone_match else None
    address_hint = None
    addr_tag = soup.find("address")
    if addr_tag:
        address_hint = addr_tag.get_text(" ", strip=True)[:200]
    elif any("PostalAddress" in t for t in jsonld):
        address_hint = "PostalAddress schema present"

    # FAQ
    has_faq = ("FAQPage" in jsonld) or bool(soup.find(string=re.compile(r"frequently asked", re.I)))

    # UX / conversion
    text_lower = body_text.lower()
    clickables = soup.find_all(["a", "button"])
    cta_count = 0
    for el in clickables:
        label = el.get_text(" ", strip=True).lower()
        cls = " ".join(el.get("class", [])).lower()
        if any(w in label for w in _CTA_WORDS) or "btn" in cls or "cta" in cls or "button" in cls:
            cta_count += 1
    forms = soup.find_all("form")
    has_contact_form = any(
        f.find("input", attrs={"type": re.compile("email|tel", re.I)})
        or "contact" in (f.get("action", "") + " ".join(f.get("class", []))).lower()
        for f in forms
    ) or ("contact" in text_lower and bool(forms))

    # accessibility: inputs without an accessible name
    labelled_ids = {lbl.get("for") for lbl in soup.find_all("label") if lbl.get("for")}
    inputs_without_label = 0
    for inp in soup.find_all(["input", "select", "textarea"]):
        if inp.get("type", "").lower() in ("hidden", "submit", "button", "image", "reset"):
            continue
        has_name = bool(inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("title")
                        or inp.get("placeholder") or (inp.get("id") and inp.get("id") in labelled_ids))
        if not has_name:
            inputs_without_label += 1

    # mixed content
    mixed_content = False
    if is_https:
        for tag, attr in (("img", "src"), ("script", "src"), ("link", "href"), ("iframe", "src")):
            for el in soup.find_all(tag):
                src = el.get(attr, "")
                if src.startswith("http://"):
                    mixed_content = True
                    break
            if mixed_content:
                break

    page = PageSEO(
        url=url,
        status=status,
        depth=depth,
        title=title_tag,
        title_length=len(title_tag) if title_tag else 0,
        meta_description=meta_desc,
        meta_description_length=len(meta_desc) if meta_desc else 0,
        h1=h1,
        h2_count=len(soup.find_all("h2")),
        canonical=canonical,
        robots_meta=robots_meta,
        noindex=bool(robots_meta and "noindex" in robots_meta.lower()),
        word_count=word_count,
        content_hash=content_hash,
        readability=flesch_reading_ease(body_text),
        has_faq=has_faq,
        images_total=len(images),
        images_missing_alt=missing_alt,
        has_viewport=bool(soup.find("meta", attrs={"name": "viewport"})),
        mixed_content=mixed_content,
        lang=(soup.html.get("lang") if soup.html else None),
        has_open_graph=bool(soup.find("meta", attrs={"property": "og:title"})),
        jsonld_types=jsonld,
        phone=phone,
        address_hint=address_hint,
        cta_count=cta_count,
        has_contact_form=has_contact_form,
        inputs_without_label=inputs_without_label,
        internal_links=internal,
        external_links=external,
        load_ms=load_ms,
    )
    return page, links
