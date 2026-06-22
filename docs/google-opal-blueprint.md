# Website Audit & Recommendation System — Google Opal blueprint

How to rebuild this project as a no-code **Google Opal** mini-app (opal.withgoogle.com).
Opal = inputs → chained AI/tool steps ("generations") → output. It fetches one URL at a
time (no full crawl, no native Lighthouse), so this audits the homepage + any extra URLs
you paste, and pulls real Core Web Vitals via the PageSpeed API URL.

> UI labels in Opal change often (it's experimental). Variable mentions are shown as `@name`.

---

## 0. Fastest path — paste this into Opal's "Describe your app" box

> Build a "Website Audit & Recommendation System". Inputs: Website URL (required), Client
> name, Target keyword, Business type/location, Extra page URLs (comma-separated), and a
> Focus dropdown (Both / On-Page only / On-Site only). Step 1: browse the Website URL and
> each extra URL and capture the raw HTML and visible content. Step 2: extract on-page SEO
> signals (title, meta description, H1s, headings, word count, image alt text, internal
> links, keyword usage). Step 3: extract on-site/technical signals (HTTPS, canonical,
> viewport, lang, JSON-LD schema types, robots/sitemap hints, mixed content, contact form,
> CTAs). Step 4: call the Google PageSpeed Insights API for the URL and extract LCP, CLS,
> INP, TBT and the performance score. Step 5: score 7 categories (Technical SEO, On-Page
> SEO, Performance, Content, Local SEO, UX & Conversion, Accessibility) 0-100, write an
> executive summary, list prioritised issues (P1/P2/P3 with severity, impact, difficulty
> and a specific fix), and quick wins. Step 6: render a client-ready report with an On-Page
> section and an On-Site section. Be honest: never invent data; label estimates as
> estimates. Then refine each step with the exact prompts below.

---

## 1. INPUT SECTION (define these app inputs)

| # | Field name | Type | Required | Default | Notes |
|---|-----------|------|----------|---------|-------|
| 1 | `website_url` | Text | ✅ | — | e.g. `https://clientsite.com` |
| 2 | `client_name` | Text | ❌ | — | Shown on the report |
| 3 | `target_keyword` | Text | ❌ | — | e.g. `plumber in Austin` |
| 4 | `business_type` | Text | ❌ | — | e.g. `dental clinic, Austin TX` (powers Local SEO) |
| 5 | `extra_pages` | Text (long) | ❌ | — | Comma-separated extra URLs to also analyse |
| 6 | `focus` | Dropdown | ✅ | `Both On-Page & On-Site` | Options: `Both On-Page & On-Site`, `On-Page only`, `On-Site / Technical only` |
| 7 | `use_pagespeed` | Toggle/Dropdown | ❌ | `Yes` | Whether to call PageSpeed for real vitals |

---

## 2. PERSONA (paste into the app's System / Instructions box)

```
You are the senior auditor behind a professional Website Audit & Recommendation System
used by a digital-marketing agency. You analyse ONLY real data fetched from the site in
earlier steps — never invent pages, metrics, or facts not present in the data. Produce a
client-ready audit across 7 categories: Technical SEO, On-Page SEO, Performance, Content,
Local SEO, UX & Conversion, Accessibility. Write for a non-technical business owner. Be
honest about estimates (AI-content detection, full WCAG, competitor gaps are approximations
— frame them as such, never as fact). Be specific and grounded; no generic filler.
```

---

## 3. GENERATION SECTION (the workflow steps)

### Step 1 — Fetch pages  ·  Tool: **Browse / Fetch URL**
**Inputs:** `@website_url`, `@extra_pages`
**Prompt:**
```
Browse @website_url and return its full content. Capture verbatim: the <title>, meta
description, all H1 and H2 headings, the main body text, every link with its href, every
<img> (note whether alt text is present or missing), every <script type="application/ld+json">
block, the <html lang> value, the viewport meta tag, the canonical link, whether the page is
served over https, and whether any contact form / call-to-action buttons exist.
If @extra_pages is not empty, repeat for each comma-separated URL.
Output the raw captured data per URL — do not analyse yet.
```
**Output var:** `fetched_pages`

---

### Step 2 — Extract On-Page signals  ·  LLM (structured)
**Inputs:** `@fetched_pages`, `@target_keyword`
**Prompt:**
```
From @fetched_pages, extract on-page SEO signals per URL as JSON:
{ "url", "title", "title_length", "meta_description", "meta_description_length",
  "h1_count", "h1_text", "h2_count", "word_count", "images_total", "images_missing_alt",
  "internal_links", "external_links",
  "keyword_in_title": <does @target_keyword appear in the title? true/false/na>,
  "keyword_in_h1": <true/false/na> }
Use only data present. If a field is unknown, use null.
```
**Output var:** `onpage_signals`

---

### Step 3 — Extract On-Site / Technical signals  ·  LLM (structured)
**Inputs:** `@fetched_pages`
**Prompt:**
```
From @fetched_pages, extract on-site / technical signals as JSON:
{ "https": true/false,
  "canonical_present", "viewport_present", "lang_present",
  "jsonld_types": [list of schema.org @types found, e.g. "LocalBusiness","Organization","Review","AggregateRating","FAQPage"],
  "has_contact_form", "cta_count",
  "mixed_content": <any http:// assets on an https page?>,
  "phone_found", "address_found",
  "robots_or_sitemap_hint": <mentioned/linked anywhere?> }
Only use data present in the fetched content.
```
**Output var:** `onsite_signals`

---

### Step 4 — Core Web Vitals (real)  ·  Tool: **Call API / Fetch URL**  *(skip if `use_pagespeed` = No)*
**Inputs:** `@website_url`
**Tool URL to fetch:**
```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=@website_url&strategy=mobile&category=performance
```
**Prompt (to parse the JSON the tool returns):**
```
From the PageSpeed Insights JSON, extract: performance_score (categories.performance.score × 100),
LCP ms (audits."largest-contentful-paint".numericValue), CLS (audits."cumulative-layout-shift".numericValue),
INP/FID ms (loadingExperience.metrics.INTERACTION_TO_NEXT_PAINT.percentile, else FIRST_INPUT_DELAY_MS),
TBT ms (audits."total-blocking-time".numericValue). If the call failed, output source:"unavailable"
and DO NOT score Performance later.
```
**Output var:** `vitals`

---

### Step 5 — Analyse, score & prioritise  ·  LLM (structured to schema)
**Inputs:** `@onpage_signals`, `@onsite_signals`, `@vitals`, `@target_keyword`, `@business_type`, `@focus`
**Prompt:**
```
Using @onpage_signals, @onsite_signals and @vitals, produce the full audit. Respect @focus
(if "On-Page only", only score/raise On-Page SEO + Content; if "On-Site / Technical only",
only Technical SEO, Performance, Local SEO, UX & Conversion, Accessibility).

Rules:
- Score each evaluated category 0-100. If @vitals.source is "unavailable", EXCLUDE Performance
  from scoring (do not fake it).
- Overall score = weighted blend (Technical .20, On-Page .20, Performance .18, Content .14,
  Local .10, UX .10, Accessibility .08), renormalised over evaluated categories.
- Each issue: title, category, severity (critical|high|medium|low|info),
  priority (P1 — Critical | P2 — Important | P3 — Recommended),
  impact (High|Medium|Low), difficulty (Easy|Medium|Hard),
  a plain-English business-impact description, and a specific fix.
- Use @target_keyword for keyword-fit checks and @business_type for Local SEO opportunities.
- Honesty: label AI-content / full-WCAG / competitor items as estimates.

Output JSON matching this schema:
{ "executive_summary": "3-5 sentences",
  "score": 0-100,
  "category_scores": [ { "category", "score", "issue_count" } ],
  "issues": [ { "title","category","severity","priority","impact","difficulty","description","recommendation","affected" } ],
  "quick_wins": ["3-5 high-impact, easy actions"],
  "expected_results": ["realistic outcomes if fixed"] }
```
**Output var:** `audit`

---

### Step 6 — Render the report (On-Page + On-Site)  ·  LLM (Markdown/HTML output)
**Inputs:** `@audit`, `@client_name`, `@website_url`, `@vitals`
**Prompt:**
```
Render @audit as a clean, client-ready report in Markdown. Layout:

# Website Audit Report — @client_name
**Site:** @website_url   **Overall health:** {{score}}/100
> {{executive_summary}}

## On-Page report
Roll-up score = average of "On-Page SEO" + "Content" category scores. Then list those two
category scores and every issue whose category is On-Page SEO or Content.

## On-Site / Technical report
Roll-up score = average of Technical SEO, Performance, Local SEO, UX & Conversion,
Accessibility. List those category scores and their issues.

## Core Web Vitals (mobile)
Table of Performance, LCP, CLS, INP, TBT from @vitals (omit if unavailable).

## ⚡ Quick wins
Bulleted quick_wins.

## Action plan
Group issues under P1 — Critical, P2 — Important, P3 — Recommended. For each: **title** ·
category — description — **Fix:** recommendation (difficulty). Show impact & severity tags.

## Expected results
Bulleted expected_results.
```
**Output var:** `report`  → set as the **app Output**.

---

## 4. OUTPUT SECTION
Display `@report` (Markdown). Optionally add a second output showing raw `@audit` JSON for
power users, and an "Export" note (Opal outputs copy/share via link; PDF/Word export stays in
the FastAPI version).

---

## 5. Field → category cheat-sheet (parity with the real engine)

| Category | Driven by |
|---|---|
| Technical SEO | https, canonical, mixed_content, robots/sitemap hint, redirects |
| On-Page SEO | title/meta length, H1 count, image alt, internal links, keyword-in-title |
| Performance | `@vitals` (LCP/CLS/INP/TBT/score) — excluded if unavailable |
| Content | word_count (thin <300), FAQ schema, readability |
| Local SEO | LocalBusiness/Review/AggregateRating schema, phone/address, business_type |
| UX & Conversion | cta_count, has_contact_form, viewport |
| Accessibility | lang, form labels, (contrast/keyboard = manual estimate) |

---

## 6. Limits vs the real backend (set client expectations)
- **No full crawl** — Opal audits the URLs you give it (homepage + `extra_pages`), not the whole site.
- **No broken-link checker / duplicate-content hashing** — those need the Python crawler.
- **Real vitals** only if the PageSpeed step succeeds (keyless works at low volume).
- **No PDF/Word export** — Opal shares via link; keep the FastAPI app for branded file exports.
- For full fidelity (multi-page crawl, link checks, exports, local Ollama), run the FastAPI
  backend — the Opal app is the lightweight, shareable, no-code version.
```
