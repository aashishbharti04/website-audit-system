"use client";
import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Sidebar, type View } from "@/components/Sidebar";
import { Footer } from "@/components/Footer";
import { UserGuide } from "@/components/UserGuide";
import { UrlForm } from "@/components/UrlForm";
import { ProgressLog } from "@/components/ProgressLog";
import { ReportView } from "@/components/ReportView";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type Audit, type AuditOptions, getAudit, health, startAudit, subscribeProgress } from "@/lib/api";
import { SAMPLE_AUDIT } from "@/lib/sample";

interface Ev { status: string; message: string; pct: number }
const RUNNING = ["queued", "crawling", "checking_links", "measuring_performance", "analyzing", "building_report"];

export default function Home() {
  const [view, setView] = useState<View>("audit");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [info, setInfo] = useState<any>(null);
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [events, setEvents] = useState<Ev[]>([]);
  const [pct, setPct] = useState(0);
  const [status, setStatus] = useState("idle");
  const [audit, setAudit] = useState<Audit | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    health().then((i) => { setInfo(i); setBackendUp(true); }).catch(() => setBackendUp(false));
  }, []);

  const busy = RUNNING.includes(status);

  const showSample = () => {
    setError(null); setEvents([]); setStatus("done"); setIsDemo(true); setAudit(SAMPLE_AUDIT); setView("audit");
  };

  const onStart = async (url: string, options: AuditOptions) => {
    if (backendUp === false) { showSample(); return; }
    setError(null); setAudit(null); setEvents([]); setPct(0); setStatus("queued"); setIsDemo(false);
    try {
      const { id } = await startAudit(url, options);
      const close = subscribeProgress(
        id,
        (ev) => { setEvents((p) => [...p, ev]); setPct(ev.pct); setStatus(ev.status); },
        async (last) => {
          close();
          if (!last || last.status === "done") {
            try { setAudit(await getAudit(id)); setStatus("done"); } catch (e) { setError(String(e)); }
          } else if (last.status === "error") { setStatus("error"); setError(last.message); }
        }
      );
    } catch (e: any) { setStatus("error"); setError(String(e.message || e)); }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar view={view} setView={setView} open={sidebarOpen} setOpen={setSidebarOpen} info={info} />

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b p-4 md:hidden">
          <button onClick={() => setSidebarOpen(true)} aria-label="Menu"><Menu className="h-6 w-6" /></button>
          <span className="font-bold">Website Audit System</span>
        </div>

        <main className="mx-auto w-full max-w-4xl flex-1 p-5 md:p-8">
          {backendUp === false && (
            <div className="mb-4 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
              <b>Live demo.</b> No audit backend is connected to this static site, so real crawling is disabled.
              Click <b>View sample report</b> to see the full output. To run real audits, host the FastAPI backend
              and set <code>NEXT_PUBLIC_API_BASE</code>, or run it locally.
            </div>
          )}

          {view === "guide" && <UserGuide />}

          {view === "about" && (
            <Card>
              <CardHeader><CardTitle>About</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>The <b className="text-foreground">Website Audit &amp; Recommendation System</b> scans a client&apos;s
                  website and produces a branded, prioritised report across 7 categories: Technical SEO, On-Page SEO,
                  Performance, Content, Local SEO, UX &amp; Conversion, and Accessibility.</p>
                <p>Backend: Python · FastAPI · httpx · BeautifulSoup · aiohttp. Performance from Google PageSpeed
                  Insights. AI analysis via Claude (structured outputs). Reports as PDF, Word and HTML. Frontend:
                  Next.js · Tailwind · Shadcn-style UI with light/dark mode.</p>
                <p>Designed as an internal agency tool and a lead-generation funnel: clients get a free score,
                  then unlock the full report.</p>
              </CardContent>
            </Card>
          )}

          {view === "audit" && (
            <div className="space-y-4">
              <UrlForm onStart={onStart} busy={busy} onSample={showSample} demoMode={backendUp === false} />
              {error && <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm font-semibold text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">⚠️ {error}</div>}
              {isDemo && audit && (
                <div className="rounded-xl border border-blue-300 bg-blue-50 p-3 text-sm text-blue-800 dark:border-blue-500/40 dark:bg-blue-500/10 dark:text-blue-200">
                  📋 Showing a <b>sample report</b> for demonstration. Connect a backend to audit a real site.
                </div>
              )}
              <ProgressLog events={events} pct={pct} status={status} />
              {audit && audit.status === "done" && <ReportView audit={audit} />}
            </div>
          )}

          <Footer />
        </main>
      </div>
    </div>
  );
}
