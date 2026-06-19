// API client + shared types for the Website Doctor AI dashboard.

export interface AuditOptions {
  max_pages: number;
  check_links: boolean;
  use_ai: boolean;
  check_performance: boolean;
  client_name?: string | null;
  primary_keyword?: string | null;
}

export interface Issue {
  title: string;
  category: string;
  severity: string;
  priority: string;
  impact: string;
  difficulty: string;
  description: string;
  recommendation: string;
  affected?: string | null;
}

export interface CategoryScore {
  category: string;
  score: number;
  issue_count: number;
}

export interface Analysis {
  executive_summary: string;
  score: number;
  category_scores: CategoryScore[];
  issues: Issue[];
  quick_wins: string[];
  expected_results: string[];
}

export interface Vitals {
  source: string;
  performance_score?: number | null;
  lcp_ms?: number | null;
  cls?: number | null;
  inp_ms?: number | null;
  tbt_ms?: number | null;
}

export interface Audit {
  id: string;
  url: string;
  client_name?: string | null;
  status: string;
  score?: number | null;
  crawl?: { domain: string; https: boolean; links_checked: number; pages: unknown[]; vitals?: Vitals | null; broken_links: { url: string; status?: number | null; error?: string | null; internal: boolean }[] } | null;
  analysis?: Analysis | null;
  error?: string | null;
}

export async function health() {
  return (await fetch("/api/health")).json();
}

export async function startAudit(url: string, options: AuditOptions) {
  const r = await fetch("/api/audits", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, options }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Failed to start audit");
  return r.json() as Promise<{ id: string; status: string }>;
}

export async function getAudit(id: string): Promise<Audit> {
  const r = await fetch(`/api/audits/${id}`);
  if (!r.ok) throw new Error("Audit not found");
  return r.json();
}

export const reportHtmlUrl = (id: string) => `/api/audits/${id}/report.html`;
export const reportPdfUrl = (id: string) => `/api/audits/${id}/report.pdf`;

export function subscribeProgress(
  id: string,
  onEvent: (e: { status: string; message: string; pct: number }) => void,
  onDone?: (last?: { status: string; message: string; pct: number }) => void
) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/audits/${id}`);
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    onEvent(data);
    if (data.status === "done" || data.status === "error") onDone?.(data);
  };
  ws.onclose = () => onDone?.();
  ws.onerror = () => onDone?.();
  return () => ws.close();
}
