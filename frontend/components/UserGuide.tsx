import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STEPS = [
  { n: 1, t: "Enter the website URL", d: "Paste your client's domain (e.g. clientsite.com). Optionally add the client name (for the report header) and a target keyword." },
  { n: 2, t: "Pick your options", d: "Choose how many pages to crawl, and toggle link checking, Core Web Vitals (Google PageSpeed), and AI analysis (Claude)." },
  { n: 3, t: "Run the audit", d: "Watch live progress as the crawler scans pages, checks links, measures performance, and analyses across 7 categories." },
  { n: 4, t: "Review the report", d: "Get an overall score, per-category scores, quick wins, and a prioritised P1/P2/P3 action plan with impact & difficulty." },
  { n: 5, t: "Export & share", d: "Download a branded report as PDF, Word (.docx) or HTML to hand straight to the client." },
];

const CATS = [
  ["Technical SEO", "HTTPS, mixed content, robots.txt, XML sitemap, redirect chains, 404s, canonicals, duplicate pages, crawl depth, indexability."],
  ["On-Page SEO", "Titles & metas (missing/duplicate), H1s, image ALT text, internal linking, target-keyword usage."],
  ["Performance", "Real Core Web Vitals via Google PageSpeed Insights — LCP, CLS, INP, TBT — plus unused CSS/JS and heavy images."],
  ["Content", "Thin content, readability (Flesch), FAQ presence; AI-content detection is flagged as an estimate, never asserted."],
  ["Local SEO", "LocalBusiness & Review schema, NAP (name/address/phone) presence and consistency for Google Business Profile."],
  ["UX & Conversion", "Calls-to-action, contact forms, mobile responsiveness."],
  ["Accessibility", "Form-field labels, lang attribute; colour-contrast & keyboard nav flagged for manual review."],
];

export function UserGuide() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>How it works</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {STEPS.map((s) => (
            <div key={s.n} className="flex gap-4">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary font-bold text-primary-foreground">{s.n}</span>
              <div>
                <div className="font-semibold">{s.t}</div>
                <p className="text-sm text-muted-foreground">{s.d}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>What gets checked (7 categories)</CardTitle></CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          {CATS.map(([t, d]) => (
            <div key={t} className="rounded-lg border p-3">
              <div className="font-semibold text-primary">{t}</div>
              <p className="mt-1 text-sm text-muted-foreground">{d}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Scoring & honesty</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>Each category gets a 0–100 score; the overall score is a weighted average. Issues carry a <b className="text-foreground">severity</b>, a <b className="text-foreground">priority</b> (P1 critical / P2 important / P3 recommended), an <b className="text-foreground">impact</b> and a <b className="text-foreground">difficulty</b>.</p>
          <p>A deterministic rules engine runs on every audit (so it works even without an AI key). Things no tool can do reliably — AI-content detection, competitor gaps, full WCAG — are labelled as estimates. If PageSpeed data isn't available, Performance is excluded from scoring rather than faked.</p>
        </CardContent>
      </Card>
    </div>
  );
}
