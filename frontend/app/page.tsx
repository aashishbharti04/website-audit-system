"use client";
import { useEffect, useState } from "react";
import { UrlForm } from "@/components/UrlForm";
import { ProgressLog } from "@/components/ProgressLog";
import { ReportView } from "@/components/ReportView";
import { type Audit, type AuditOptions, getAudit, health, startAudit, subscribeProgress } from "@/lib/api";

interface Ev { status: string; message: string; pct: number }
const RUNNING = ["queued", "crawling", "checking_links", "measuring_performance", "analyzing", "building_report"];

export default function Home() {
  const [info, setInfo] = useState<any>(null);
  const [events, setEvents] = useState<Ev[]>([]);
  const [pct, setPct] = useState(0);
  const [status, setStatus] = useState("idle");
  const [audit, setAudit] = useState<Audit | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { health().then(setInfo).catch(() => {}); }, []);
  const busy = RUNNING.includes(status);

  const onStart = async (url: string, options: AuditOptions) => {
    setError(null); setAudit(null); setEvents([]); setPct(0); setStatus("queued");
    try {
      const { id } = await startAudit(url, options);
      const close = subscribeProgress(
        id,
        (ev) => { setEvents((p) => [...p, ev]); setPct(ev.pct); setStatus(ev.status); },
        async (last) => {
          close();
          if (!last || last.status === "done") {
            try { setAudit(await getAudit(id)); setStatus("done"); }
            catch (e) { setError(String(e)); }
          } else if (last.status === "error") { setStatus("error"); setError(last.message); }
        }
      );
    } catch (e: any) { setStatus("error"); setError(String(e.message || e)); }
  };

  return (
    <div className="container py-6">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🩺</span>
          <div>
            <div className="text-lg font-extrabold tracking-tight">{info?.product || "Website Doctor AI"}</div>
            <div className="text-xs text-muted-foreground">Website Audit & Recommendation System {info?.agency ? `· ${info.agency}` : ""}</div>
          </div>
        </div>
        {info && (
          <div className="flex gap-2 text-xs font-bold">
            <span className={`rounded-full border px-3 py-1 ${info.ai_enabled ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "text-muted-foreground"}`}>
              AI {info.ai_enabled ? `· ${info.ai_model}` : "off"}
            </span>
            <span className={`rounded-full border px-3 py-1 ${info.pdf_enabled ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "text-muted-foreground"}`}>
              PDF {info.pdf_enabled ? "on" : "off"}
            </span>
          </div>
        )}
      </header>

      <main className="space-y-4">
        <UrlForm onStart={onStart} busy={busy} />
        {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">⚠️ {error}</div>}
        <ProgressLog events={events} pct={pct} status={status} />
        {audit && audit.status === "done" && <ReportView audit={audit} />}
      </main>

      <footer className="mt-10 text-center text-xs text-muted-foreground">
        Internal lead-gen & audit tool · crawls, analyses & reports — client data stays on your server.
      </footer>
    </div>
  );
}
