// API client + shared types for the Website Audit & Recommendation System dashboard.

// Backend base URL. Empty = same-origin (dev uses Next rewrites to :8000).
// On GitHub Pages set NEXT_PUBLIC_API_BASE to your hosted FastAPI URL to enable real audits.
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, "");

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
  const r = await fetch(`${API_BASE}/api/health`);
  if (!r.ok) throw new Error("backend unavailable");
  return r.json();
}

export async function startAudit(url: string, options: AuditOptions) {
  const r = await fetch(`${API_BASE}/api/audits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, options }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || "Failed to start audit");
  return r.json() as Promise<{ id: string; status: string }>;
}

export async function getAudit(id: string): Promise<Audit> {
  const r = await fetch(`${API_BASE}/api/audits/${id}`);
  if (!r.ok) throw new Error("Audit not found");
  return r.json();
}

export const reportHtmlUrl = (id: string) => `${API_BASE}/api/audits/${id}/report.html`;
export const reportPdfUrl = (id: string) => `${API_BASE}/api/audits/${id}/report.pdf`;
export const reportDocxUrl = (id: string) => `${API_BASE}/api/audits/${id}/report.docx`;

export function subscribeProgress(
  id: string,
  onEvent: (e: { status: string; message: string; pct: number }) => void,
  onDone?: (last?: { status: string; message: string; pct: number }) => void
) {
  const wsBase = API_BASE
    ? API_BASE.replace(/^http/, "ws")
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  const ws = new WebSocket(`${wsBase}/ws/audits/${id}`);
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    onEvent(data);
    if (data.status === "done" || data.status === "error") onDone?.(data);
  };
  ws.onclose = () => onDone?.();
  ws.onerror = () => onDone?.();
  return () => ws.close();
}
