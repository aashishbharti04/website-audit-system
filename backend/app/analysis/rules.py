"""Deterministic, rule-based audit across all 7 categories. Produces issues
(with priority/impact/difficulty), per-category scores, and an overall score.

Runs always — gives real value without an AI key, and gives the AI layer verified
findings to expand on rather than invent.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from ..schemas import (
    AIAnalysis,
    Category,
    CategoryScore,
    CrawlResult,
    Difficulty,
    Impact,
    Issue,
    Priority,
    Severity,
)

_SEV_PENALTY = {Severity.critical: 25, Severity.high: 12, Severity.medium: 6, Severity.low: 2, Severity.info: 0}
_PRIORITY = {
    Severity.critical: Priority.p1, Severity.high: Priority.p1,
    Severity.medium: Priority.p2, Severity.low: Priority.p3, Severity.info: Priority.p3,
}
# overall-score weighting per category
_WEIGHTS = {
    Category.technical: 0.20, Category.on_page: 0.20, Category.performance: 0.18,
    Category.content: 0.14, Category.local: 0.10, Category.ux: 0.10, Category.accessibility: 0.08,
}


def rule_based_analysis(crawl: CrawlResult, primary_keyword: str | None = None) -> AIAnalysis:
    issues: list[Issue] = []
    pages = [p for p in crawl.pages if not p.error]
    errored = [p for p in crawl.pages if p.error]

    def add(title, cat, sev, desc, rec, impact=Impact.medium, diff=Difficulty.medium, affected=None):
        issues.append(Issue(
            title=title, category=cat, severity=sev, priority=_PRIORITY[sev],
            impact=impact, difficulty=diff, description=desc, recommendation=rec, affected=affected,
        ))

    # ===================== TECHNICAL SEO =====================
    if not crawl.https:
        add("Site not served over HTTPS", Category.technical, Severity.critical,
            "The site is not using HTTPS, which harms trust, security and rankings.",
            "Install an SSL certificate and force HTTPS site-wide with 301 redirects.",
            Impact.high, Difficulty.medium)
    mixed = [p.url for p in pages if p.mixed_content]
    if mixed:
        add("Mixed content (HTTP assets on HTTPS pages)", Category.technical, Severity.high,
            f"{len(mixed)} page(s) load insecure http:// assets, triggering browser warnings.",
            "Update all asset URLs to https:// (or protocol-relative).", Impact.medium, Difficulty.easy, _s(mixed))
    if not crawl.robots_txt_found:
        add("Missing robots.txt", Category.technical, Severity.medium,
            "No robots.txt was found at the site root.",
            "Add a robots.txt that allows crawling and references your XML sitemap.",
            Impact.medium, Difficulty.easy)
    if not crawl.sitemap_found:
        add("Missing XML sitemap", Category.technical, Severity.medium,
            "No XML sitemap was found (checked robots.txt and /sitemap.xml).",
            "Generate an XML sitemap and submit it in Google Search Console.",
            Impact.medium, Difficulty.easy)
    if crawl.redirect_chains:
        add("Redirect chains", Category.technical, Severity.medium,
            f"{len(crawl.redirect_chains)} URL(s) go through 2+ redirect hops, wasting crawl budget and speed.",
            "Point links and redirects directly to the final destination (single hop).",
            Impact.medium, Difficulty.easy, _s([c.url for c in crawl.redirect_chains]))
    # broken links
    if crawl.broken_links:
        internal_broken = [b.url for b in crawl.broken_links if b.internal]
        sev = Severity.high if internal_broken else Severity.medium
        add("Broken links (404s)", Category.technical, sev,
            f"{len(crawl.broken_links)} broken link(s) found ({len(internal_broken)} internal).",
            "Fix or remove broken links; add 301 redirects where pages moved.",
            Impact.high, Difficulty.easy, _s([b.url for b in crawl.broken_links]))
    # canonical
    no_canon = [p.url for p in pages if not p.canonical]
    if no_canon:
        add("Missing canonical tags", Category.technical, Severity.medium,
            f"{len(no_canon)} page(s) have no canonical link, risking duplicate-content dilution.",
            'Add a self-referencing <link rel="canonical"> to each page.',
            Impact.medium, Difficulty.easy, _s(no_canon))
    # duplicate pages (by content hash)
    by_hash = defaultdict(list)
    for p in pages:
        if p.content_hash:
            by_hash[p.content_hash].append(p.url)
    dupe_groups = [urls for urls in by_hash.values() if len(urls) > 1]
    if dupe_groups:
        add("Duplicate pages", Category.technical, Severity.high,
            f"{len(dupe_groups)} group(s) of pages share identical content.",
            "Consolidate duplicates with canonical tags or 301 redirects to a single URL.",
            Impact.high, Difficulty.medium, _s([u for g in dupe_groups for u in g]))
    # indexability
    noindex = [p.url for p in pages if p.noindex]
    if noindex:
        home_noindex = any(u.rstrip("/") == crawl.start_url.rstrip("/") for u in noindex)
        add("Pages set to noindex", Category.technical,
            Severity.critical if home_noindex else Severity.high,
            f"{len(noindex)} page(s) have a noindex robots directive and won't appear in search.",
            "Remove noindex from pages that should rank.", Impact.high, Difficulty.easy, _s(noindex))
    # crawl depth
    deep = [p.url for p in pages if p.depth >= 4]
    if deep:
        add("Pages buried deep in the site", Category.technical, Severity.low,
            f"{len(deep)} page(s) are 4+ clicks from the homepage, reducing crawlability and authority flow.",
            "Flatten the architecture so key pages are within 3 clicks of the homepage.",
            Impact.low, Difficulty.medium, _s(deep))
    if errored:
        add("Pages failed to load", Category.technical, Severity.high,
            f"{len(errored)} URL(s) could not be fetched during the crawl.",
            "Ensure all linked pages return 200 and are reachable by crawlers.",
            Impact.high, Difficulty.medium, _s([p.url for p in errored]))

    # ===================== ON-PAGE SEO =====================
    no_title = [p.url for p in pages if not p.title]
    if no_title:
        add("Missing page titles", Category.on_page, Severity.critical,
            f"{len(no_title)} page(s) have no <title> tag.",
            "Add a unique, 50–60 character title with the primary keyword near the front.",
            Impact.high, Difficulty.easy, _s(no_title))
    dup_titles = _dupes([p.title for p in pages if p.title])
    if dup_titles:
        add("Duplicate title tags", Category.on_page, Severity.high,
            f"{len(dup_titles)} title(s) are used on more than one page.",
            "Make every title unique and descriptive of that page's content.",
            Impact.high, Difficulty.easy, _s(dup_titles))
    long_title = [p.url for p in pages if p.title and p.title_length > 60]
    if long_title:
        add("Title tags too long", Category.on_page, Severity.low,
            f"{len(long_title)} title(s) exceed 60 characters and may be truncated.",
            "Trim titles to ~60 characters.", Impact.low, Difficulty.easy, _s(long_title))
    no_meta = [p.url for p in pages if not p.meta_description]
    if no_meta:
        add("Missing meta descriptions", Category.on_page, Severity.high,
            f"{len(no_meta)} page(s) lack a meta description.",
            "Write a compelling 140–160 character meta description per page.",
            Impact.high, Difficulty.easy, _s(no_meta))
    dup_meta = _dupes([p.meta_description for p in pages if p.meta_description])
    if dup_meta:
        add("Duplicate meta descriptions", Category.on_page, Severity.medium,
            f"{len(dup_meta)} meta description(s) are reused across pages.",
            "Write a unique meta description for each page.", Impact.medium, Difficulty.easy)
    no_h1 = [p.url for p in pages if not p.h1]
    if no_h1:
        add("Missing H1 heading", Category.on_page, Severity.high,
            f"{len(no_h1)} page(s) have no H1 heading.",
            "Add exactly one descriptive H1 per page.", Impact.high, Difficulty.easy, _s(no_h1))
    multi_h1 = [p.url for p in pages if len(p.h1) > 1]
    if multi_h1:
        add("Multiple H1 headings", Category.on_page, Severity.low,
            f"{len(multi_h1)} page(s) have more than one H1.",
            "Use a single H1 and demote the rest to H2/H3.", Impact.low, Difficulty.easy, _s(multi_h1))
    alt = sum(p.images_missing_alt for p in pages)
    if alt:
        add("Images missing ALT text", Category.on_page, Severity.medium,
            f"{alt} image(s) are missing alt attributes.",
            "Add descriptive alt text to every meaningful image.", Impact.high, Difficulty.easy)
    orphans = [p.url for p in pages if p.internal_links < 2 and p.depth > 0]
    if orphans:
        add("Weak internal linking", Category.on_page, Severity.medium,
            f"{len(orphans)} page(s) have fewer than 2 internal links pointing onward.",
            "Add contextual internal links to distribute authority and aid discovery.",
            Impact.medium, Difficulty.easy, _s(orphans))
    if primary_keyword:
        kw = primary_keyword.lower()
        miss_kw = [p.url for p in pages if p.title and kw not in p.title.lower()]
        if miss_kw:
            add(f'Title missing target keyword "{primary_keyword}"', Category.on_page, Severity.low,
                f"{len(miss_kw)} page(s) don't include the target keyword in the title.",
                "Work the primary keyword naturally into titles where relevant.",
                Impact.medium, Difficulty.easy, _s(miss_kw))

    # ===================== PERFORMANCE =====================
    v = crawl.vitals
    performance_evaluated = bool(v and v.source == "psi")
    if performance_evaluated:
        if v.performance_score is not None and v.performance_score < 90:
            sev = Severity.critical if v.performance_score < 50 else Severity.medium
            add("Low performance score", Category.performance, sev,
                f"Lighthouse performance score is {v.performance_score}/100 (mobile).",
                "Optimise images, reduce JS/CSS, enable caching and a CDN.",
                Impact.high, Difficulty.hard, v.url)
        if v.lcp_ms and v.lcp_ms > 2500:
            sev = Severity.critical if v.lcp_ms > 4000 else Severity.high
            add("Slow Largest Contentful Paint (LCP)", Category.performance, sev,
                f"LCP is {v.lcp_ms/1000:.1f}s (target < 2.5s).",
                "Optimise the hero image/text, preload key resources, improve server response.",
                Impact.high, Difficulty.medium, v.url)
        if v.cls is not None and v.cls > 0.1:
            sev = Severity.high if v.cls > 0.25 else Severity.medium
            add("Layout shift (CLS) too high", Category.performance, sev,
                f"CLS is {v.cls:.3f} (target < 0.1).",
                "Set explicit width/height on images and reserve space for dynamic content.",
                Impact.medium, Difficulty.medium, v.url)
        if v.inp_ms and v.inp_ms > 200:
            add("Slow interactivity (INP)", Category.performance, Severity.medium,
                f"Interaction to Next Paint is {v.inp_ms:.0f}ms (target < 200ms).",
                "Reduce main-thread work and break up long JavaScript tasks.",
                Impact.medium, Difficulty.hard, v.url)
        heavy = (v.unused_css_kb or 0) + (v.unused_js_kb or 0)
        if heavy > 50:
            add("Unused CSS / JavaScript", Category.performance, Severity.low,
                f"~{heavy:.0f} KB of unused CSS/JS could be removed.",
                "Code-split, tree-shake, and defer non-critical CSS/JS.",
                Impact.medium, Difficulty.hard, v.url)
        if v.heavy_images_kb and v.heavy_images_kb > 100:
            add("Heavy / unoptimised images", Category.performance, Severity.medium,
                f"~{v.heavy_images_kb:.0f} KB could be saved with modern formats/compression.",
                "Serve WebP/AVIF, compress, and size images responsively.",
                Impact.high, Difficulty.medium, v.url)

    # ===================== CONTENT =====================
    content_pages = [p for p in pages if p.word_count > 0]
    thin = [p.url for p in content_pages if p.word_count < 300]
    if thin:
        add("Thin content", Category.content, Severity.medium,
            f"{len(thin)} page(s) have under 300 words and may be seen as low value.",
            "Expand thin pages with useful, original content (aim for 600+ words where relevant).",
            Impact.medium, Difficulty.medium, _s(thin))
    hard_read = [p.url for p in content_pages if p.readability is not None and p.readability < 40]
    if hard_read:
        add("Hard-to-read content", Category.content, Severity.low,
            f"{len(hard_read)} page(s) score below 40 on Flesch reading ease (difficult).",
            "Use shorter sentences and simpler words; break up long paragraphs.",
            Impact.low, Difficulty.medium, _s(hard_read))
    if not any(p.has_faq for p in pages):
        add("No FAQ content / schema", Category.content, Severity.low,
            "No FAQ section or FAQPage schema was detected.",
            "Add an FAQ section with FAQPage structured data to win rich results and answer intent.",
            Impact.medium, Difficulty.easy)
    add("Verify content originality", Category.content, Severity.info,
        "Automated AI-content and duplicate-content detection is an estimate, not a verdict.",
        "Spot-check key pages with a plagiarism/AI-detection tool and ensure content is original and helpful.",
        Impact.low, Difficulty.easy)

    # ===================== LOCAL SEO =====================
    all_types = {t for p in pages for t in p.jsonld_types}
    if not any("LocalBusiness" in t or t in ("Organization",) for t in all_types):
        add("No LocalBusiness schema", Category.local, Severity.high,
            "No LocalBusiness/Organization structured data was detected.",
            "Add LocalBusiness schema with name, address, phone, hours and geo-coordinates.",
            Impact.high, Difficulty.easy)
    if not any("AggregateRating" in t or "Review" in t for t in all_types):
        add("No review / rating schema", Category.local, Severity.medium,
            "No Review or AggregateRating schema was detected.",
            "Add Review/AggregateRating schema to show star ratings in search results.",
            Impact.medium, Difficulty.easy)
    phones = {p.phone for p in pages if p.phone}
    if not phones:
        add("No phone number (NAP) found", Category.local, Severity.medium,
            "No phone number was detected on the crawled pages.",
            "Display a consistent NAP (Name, Address, Phone) in the header/footer of every page.",
            Impact.medium, Difficulty.easy)
    elif len(phones) > 1:
        add("Inconsistent phone numbers (NAP)", Category.local, Severity.low,
            f"{len(phones)} different phone numbers were found, which can confuse local ranking signals.",
            "Use one consistent phone number matching your Google Business Profile.",
            Impact.medium, Difficulty.easy)
    if not any(p.address_hint for p in pages):
        add("No address found", Category.local, Severity.medium,
            "No physical address was detected on the crawled pages.",
            "Add your business address (ideally with PostalAddress schema) for local SEO.",
            Impact.medium, Difficulty.easy)

    # ===================== UX & CONVERSION =====================
    home = pages[0] if pages else None
    if home and home.cta_count == 0:
        add("No clear call-to-action", Category.ux, Severity.medium,
            "The homepage has no obvious call-to-action button.",
            "Add prominent CTAs (Call, Book, Get a Quote) above the fold.",
            Impact.high, Difficulty.easy, home.url)
    if not any(p.has_contact_form for p in pages):
        add("No contact form detected", Category.ux, Severity.medium,
            "No contact form was found on the crawled pages.",
            "Add a simple contact/lead form to capture enquiries.",
            Impact.high, Difficulty.medium)
    no_vp = [p.url for p in pages if not p.has_viewport]
    if no_vp:
        add("Not mobile-responsive (missing viewport)", Category.ux, Severity.high,
            f"{len(no_vp)} page(s) lack a responsive viewport meta tag.",
            'Add <meta name="viewport" content="width=device-width, initial-scale=1"> to all pages.',
            Impact.high, Difficulty.easy, _s(no_vp))

    # ===================== ACCESSIBILITY =====================
    no_label = sum(p.inputs_without_label for p in pages)
    if no_label:
        add("Form fields without labels", Category.accessibility, Severity.medium,
            f"{no_label} form field(s) have no accessible label.",
            "Associate every input with a <label> (or aria-label) for screen-reader users.",
            Impact.medium, Difficulty.easy)
    no_lang = [p.url for p in pages if not p.lang]
    if no_lang:
        add("Missing lang attribute", Category.accessibility, Severity.low,
            f"{len(no_lang)} page(s) have no <html lang> attribute.",
            'Add lang="en" (or the correct locale) to the <html> tag.',
            Impact.low, Difficulty.easy, _s(no_lang))
    add("Verify colour contrast & keyboard navigation", Category.accessibility, Severity.info,
        "Colour-contrast and keyboard-navigation checks require rendering and manual review.",
        "Run an automated WCAG checker (axe, Lighthouse a11y) and test tab-only navigation.",
        Impact.low, Difficulty.medium)

    # ===================== SCORING =====================
    evaluated = set(_WEIGHTS) - ({Category.performance} if not performance_evaluated else set())
    cat_pen: dict[Category, int] = defaultdict(int)
    cat_cnt: dict[Category, int] = defaultdict(int)
    for i in issues:
        cat_pen[i.category] += _SEV_PENALTY[i.severity]
        cat_cnt[i.category] += 1
    category_scores = [
        CategoryScore(category=c, score=max(0, 100 - cat_pen[c]), issue_count=cat_cnt[c])
        for c in _WEIGHTS if c in evaluated
    ]
    total_w = sum(_WEIGHTS[c.category] for c in category_scores)
    overall = round(sum(c.score * _WEIGHTS[c.category] for c in category_scores) / total_w) if total_w else 100

    summary = (
        f"Audited {len(crawl.pages)} page(s) on {crawl.domain} across {len(category_scores)} categories. "
        f"Found {len(issues)} issue(s). Overall website health: {overall}/100."
    )
    quick = [i.recommendation for i in sorted(issues, key=lambda x: list(Severity).index(x.severity))
             if i.difficulty == Difficulty.easy][:5]
    expected = [
        "Improved organic visibility and click-through from search",
        "Better Core Web Vitals and a faster experience",
        "Stronger local/GBP ranking signals",
        "Higher conversion rate from clearer CTAs and trust signals",
    ]
    return AIAnalysis(
        executive_summary=summary, score=overall, category_scores=category_scores,
        issues=issues, quick_wins=quick, expected_results=expected,
    )


def _dupes(values: list[str]) -> list[str]:
    counts = Counter(v.strip() for v in values if v and v.strip())
    return [v for v, n in counts.items() if n > 1]


def _s(urls: list[str], k: int = 5) -> str:
    shown = urls[:k]
    extra = len(urls) - len(shown)
    return ", ".join(shown) + (f" (+{extra} more)" if extra > 0 else "")
