import type { Audit } from "./api";

// A realistic sample audit used for the live demo (e.g. GitHub Pages, where there's
// no backend to run a real crawl). Mirrors the shape the backend returns.
export const SAMPLE_AUDIT: Audit = {
  id: "demo",
  url: "https://www.brightsmiledental.com",
  client_name: "BrightSmile Dental",
  status: "done",
  score: 68,
  crawl: {
    domain: "brightsmiledental.com",
    https: true,
    links_checked: 142,
    pages: new Array(18),
    vitals: {
      source: "psi",
      performance_score: 54,
      lcp_ms: 5300,
      cls: 0.21,
      inp_ms: 240,
      tbt_ms: 610,
    },
    broken_links: [
      { url: "https://www.brightsmiledental.com/services/whitening-old", status: 404, internal: true },
      { url: "https://facebook.com/brightsmile-old", status: 404, internal: false },
      { url: "https://www.brightsmiledental.com/blog/2019/summer", status: 404, internal: true },
    ],
  },
  analysis: {
    executive_summary:
      "BrightSmile Dental scores 68/100. The site is on HTTPS and well-structured, but performance is the biggest drag — the homepage takes 5.3s to render its main content and shifts layout noticeably. On-page SEO has gaps (23 pages missing meta descriptions, 11 missing an H1) and local SEO is weak: no LocalBusiness or review schema was found, which limits Google Business Profile visibility. Fixing the quick wins below should lift rankings, speed and conversions within a few weeks.",
    score: 68,
    category_scores: [
      { category: "Technical SEO", score: 74, issue_count: 4 },
      { category: "On-Page SEO", score: 61, issue_count: 5 },
      { category: "Performance", score: 48, issue_count: 4 },
      { category: "Content", score: 79, issue_count: 3 },
      { category: "Local SEO", score: 55, issue_count: 3 },
      { category: "UX & Conversion", score: 82, issue_count: 2 },
      { category: "Accessibility", score: 88, issue_count: 2 },
    ],
    quick_wins: [
      "Add unique meta descriptions to the 23 pages missing them.",
      "Add LocalBusiness + Review schema to power Google Business Profile rich results.",
      "Compress and lazy-load hero images to cut LCP from 5.3s toward 2.5s.",
      "Add an H1 to the 11 pages missing one.",
      "Fix the 3 broken links and add redirects for the retired pages.",
    ],
    expected_results: [
      "+10–20% organic traffic within 8–12 weeks",
      "Stronger Google Business Profile / local-pack rankings",
      "Faster pages and better Core Web Vitals (LCP < 2.5s target)",
      "Higher conversion rate from clearer trust signals and CTAs",
    ],
    issues: [
      { title: "Homepage LCP is 5.3 seconds", category: "Performance", severity: "critical", priority: "P1 — Critical", impact: "High", difficulty: "Medium", description: "Largest Contentful Paint is 5.3s on mobile (target < 2.5s), mostly from an uncompressed hero image.", recommendation: "Compress the hero to WebP/AVIF, set explicit dimensions, and preload it.", affected: "https://www.brightsmiledental.com/" },
      { title: "No LocalBusiness schema", category: "Local SEO", severity: "high", priority: "P1 — Critical", impact: "High", difficulty: "Easy", description: "No LocalBusiness/Organization structured data was detected, limiting local visibility.", recommendation: "Add LocalBusiness schema with name, address, phone, hours and geo-coordinates.", affected: null },
      { title: "23 pages missing meta descriptions", category: "On-Page SEO", severity: "high", priority: "P1 — Critical", impact: "High", difficulty: "Easy", description: "23 pages have no meta description, hurting click-through from search.", recommendation: "Write a 140–160 character meta description per page.", affected: "23 pages" },
      { title: "11 pages missing an H1 heading", category: "On-Page SEO", severity: "high", priority: "P1 — Critical", impact: "High", difficulty: "Easy", description: "11 pages have no H1, weakening topical relevance.", recommendation: "Add exactly one descriptive H1 per page.", affected: "11 pages" },
      { title: "Layout shift (CLS) too high", category: "Performance", severity: "high", priority: "P2 — Important", impact: "Medium", difficulty: "Medium", description: "CLS is 0.21 (target < 0.1) — content jumps as images and ads load.", recommendation: "Reserve space for media and dynamic content with explicit width/height.", affected: "https://www.brightsmiledental.com/" },
      { title: "Broken links (404s)", category: "Technical SEO", severity: "high", priority: "P2 — Important", impact: "High", difficulty: "Easy", description: "3 broken links found (2 internal).", recommendation: "Fix or remove broken links and add 301 redirects where pages moved.", affected: "3 links" },
      { title: "No review / rating schema", category: "Local SEO", severity: "medium", priority: "P2 — Important", impact: "Medium", difficulty: "Easy", description: "No Review/AggregateRating schema — no star ratings in search results.", recommendation: "Add AggregateRating/Review schema sourced from real reviews.", affected: null },
      { title: "17 images missing ALT text", category: "On-Page SEO", severity: "medium", priority: "P2 — Important", impact: "Medium", difficulty: "Easy", description: "17 images lack alt attributes, hurting accessibility and image SEO.", recommendation: "Add descriptive alt text to every meaningful image.", affected: "17 images" },
      { title: "Unused CSS / JavaScript", category: "Performance", severity: "low", priority: "P3 — Recommended", impact: "Medium", difficulty: "Hard", description: "~180 KB of unused CSS/JS could be removed.", recommendation: "Code-split, tree-shake and defer non-critical assets.", affected: "https://www.brightsmiledental.com/" },
      { title: "Thin content on 4 service pages", category: "Content", severity: "medium", priority: "P2 — Important", impact: "Medium", difficulty: "Medium", description: "4 pages have under 300 words and may be seen as low value.", recommendation: "Expand with useful, original content (600+ words where relevant).", affected: "4 pages" },
      { title: "Missing XML sitemap", category: "Technical SEO", severity: "medium", priority: "P2 — Important", impact: "Medium", difficulty: "Easy", description: "No XML sitemap was found.", recommendation: "Generate an XML sitemap and submit it in Google Search Console.", affected: null },
      { title: "Verify colour contrast & keyboard navigation", category: "Accessibility", severity: "info", priority: "P3 — Recommended", impact: "Low", difficulty: "Medium", description: "Colour-contrast and keyboard-nav checks need rendering and manual review (estimate).", recommendation: "Run an automated WCAG checker (axe, Lighthouse a11y) and test tab-only navigation.", affected: null },
    ],
  },
};
