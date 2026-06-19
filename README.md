# 🩺 Website Audit & Recommendation System

Enter a client URL → it crawls the whole site, runs a **7-category audit** (with real Core Web
Vitals from Google) plus an AI analysis, and produces a **branded, prioritised report** with
per-category scores and a P1/P2/P3 action plan — exportable as **PDF, Word (.docx) and HTML**.

[![Live demo](https://img.shields.io/badge/▶_Live_demo-2563eb?style=for-the-badge)](https://aashishbharti04.github.io/website-audit-recommendation-system/)

> **Live site = UI demo.** GitHub Pages is static-only, so the live link runs in
> **sample-report demo mode** (no real crawling). To run real audits, host the FastAPI backend
> (Railway/Render/VPS) and set `NEXT_PUBLIC_API_BASE`, or run it locally (below).

**Highlights:** Next.js + Tailwind + Shadcn UI · **light / dark / system** theme · sidebar + user
guide · 7-category engine · Google PageSpeed Core Web Vitals · Claude analysis · PDF / Word / HTML export.

---

## Architecture

```
Frontend (Next.js + Tailwind + Shadcn)      Backend (FastAPI / Python)               AI + data
┌──────────────────────────────┐   REST/WS  ┌──────────────────────────────┐  API  ┌────────────────────┐
│ URL + options                │ ─────────▶ │ Crawler (httpx, depth-aware) │ ────▶ │ Claude API          │
│ Live progress (WebSocket)    │            │ Link checker (aiohttp)       │       │  (claude-sonnet-4-6)│
│ Score rings + category cards │            │ robots/sitemap/HTTPS checks  │       │ Google PageSpeed    │
│ Action plan (P1/P2/P3)       │ ◀───────── │ Rules engine (7 categories)  │ ◀──── │  Insights (Vitals)  │
│ HTML / PDF export            │            │ AI analyst (structured out)  │       │ PostgreSQL (history)│
└──────────────────────────────┘            │ Report builder (WeasyPrint)  │       └────────────────────┘
                                            └──────────────────────────────┘
```

## What it checks (7 categories)

1. **Technical SEO** — HTTPS, mixed content, robots.txt, XML sitemap, redirect chains, broken links (404s), canonicals, duplicate pages, crawl depth, indexability (noindex), unreachable pages.
2. **On-Page SEO** — missing/duplicate titles, title length, missing/duplicate meta descriptions, missing/multiple H1, image ALT text, weak internal linking, target-keyword-in-title.
3. **Performance** — **real Core Web Vitals via Google PageSpeed Insights** (LCP, CLS, INP, TBT, performance score), unused CSS/JS, heavy images.
4. **Content** — thin content, readability (Flesch), FAQ presence/schema, originality reminder (AI-content detection is flagged as an estimate, not a verdict).
5. **Local SEO** — LocalBusiness/Organization schema, Review/AggregateRating schema, NAP (phone/address) presence & consistency.
6. **UX & Conversion** — call-to-action presence, contact form, mobile responsiveness (viewport).
7. **Accessibility** — form-field labels, `lang` attribute, plus a flagged manual pass for colour-contrast & keyboard nav (these need rendering).

Each category gets a **0–100 score**; issues carry **severity, priority (P1/P2/P3), impact and difficulty**.

### Honesty by design
A deterministic **rules engine** runs on every audit (works with no API key) and feeds the AI
verified findings to expand on. Things no tool can do reliably — AI-content detection, competitor
gaps, full WCAG, field FID — are **labelled as estimates**, never presented as fact. If PageSpeed
data isn't available, the Performance category is **excluded from scoring** rather than faked.

## Quick start

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY (AI) + GOOGLE_PSI_API_KEY (vitals) — both optional
uvicorn app.main:app --reload
```
API at `http://localhost:8000` · docs at `/docs` · health at `/api/health`.

> **PDF export** needs WeasyPrint's native libs (in the Dockerfile). Without them, HTML export works and the API returns a clear 501 for PDF.

### Frontend — single-file HTML (default, no build step)
The backend **serves the whole UI** at its root: just start the backend and open
**`http://localhost:8000/`**. The dashboard ([frontend/index.html](frontend/index.html)) is one
self-contained HTML file (vanilla JS + CSS) — same-origin, so live WebSocket progress and report
exports work with zero CORS setup. Open it directly as a file too; set the backend URL under **Settings**.

**API keys via the UI.** Open **Settings** in the sidebar to paste your **Anthropic** key (AI analysis)
and optional **Google PageSpeed** key. Keys are stored **only in your browser** (localStorage) and sent
with each audit request, overriding the server's env vars — so the server needs no keys of its own.

### Frontend — Next.js (optional, alternative)
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 (proxies /api + /ws to :8000 via next.config rewrites)
```

### Docker (API + Postgres)
```bash
ANTHROPIC_API_KEY=sk-... docker compose up --build
```

## Flow
1. `POST /api/audits` `{ url, options }` → audit `id`, background job starts.
2. Dashboard opens `ws://…/ws/audits/{id}` → **live progress** (crawl → links → vitals → analysis).
3. Job: crawl → check links → **PageSpeed Insights** → **rules engine (7 cats)** → **Claude** → result.
4. `GET /api/audits/{id}` → full result; `…/report.html` & `…/report.pdf` export the branded report.

## Tech stack
| Layer | Tool |
|---|---|
| Frontend | Next.js · Tailwind · Shadcn-style UI · TypeScript |
| Backend | Python · FastAPI · httpx · BeautifulSoup · aiohttp |
| Performance | Google PageSpeed Insights (Lighthouse) |
| AI | Anthropic SDK (`claude-sonnet-4-6`), structured outputs |
| Reports | Jinja2 + WeasyPrint |
| DB | PostgreSQL (SQLAlchemy) — optional, scaffolded |
| Deploy | Docker / Railway / Render |

## Configuration (env — see `backend/.env.example`)
| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Enables AI analysis (else rules engine only). |
| `GOOGLE_PSI_API_KEY` | Higher PageSpeed quota (works keyless at low volume). |
| `AI_MODEL` | `claude-sonnet-4-6` (default) or `claude-opus-4-8`. |
| `PRODUCT_NAME`, `AGENCY_*` | White-label branding on the UI and every report. |
| `DATABASE_URL` | Postgres for audit history (Phase 5). |

## Cost
~$0.10–0.30 per audit (Sonnet 4.6) · PageSpeed free · hosting ~$5–10/mo · **under ~$20/mo** at agency scale.

## Tests
```bash
cd backend && python -m pytest -q     # parser, 7-category rules, scoring, report — no network/key
```

## Roadmap (the "Website Doctor AI" product vision)
- [ ] **Lead-gen funnel** — free score → email-gate the full PDF → capture qualified SEO leads
- [ ] Wire `db.py` persistence + audit-history / score-trend per client domain
- [ ] Agency login / multi-user auth
- [ ] **Competitor gap analysis** + DataForSEO keyword rankings
- [ ] Headless render pass (JS-heavy SPA sites) and full WCAG via axe-core
- [ ] GBP landing-page & local-pack optimisation module

---

© Website Audit & Recommendation System.
