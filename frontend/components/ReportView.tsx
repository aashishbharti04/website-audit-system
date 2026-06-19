"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScoreRing } from "./ScoreRing";
import { type Audit, reportHtmlUrl, reportPdfUrl } from "@/lib/api";
import { IMPACT_COLOR, SEV_COLOR, SEV_HEX, scoreBg, scoreColor } from "@/lib/utils";

const PRIORITIES = ["P1 — Critical", "P2 — Important", "P3 — Recommended"];

export function ReportView({ audit }: { audit: Audit }) {
  const a = audit.analysis;
  const [cat, setCat] = useState<string>("all");
  if (!a) return null;
  const score = audit.score ?? a.score ?? 0;
  const v = audit.crawl?.vitals;

  const cats = ["all", ...a.category_scores.map((c) => c.category)];
  const issues = cat === "all" ? a.issues : a.issues.filter((i) => i.category === cat);

  return (
    <div className="space-y-4">
      {/* header */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-6 pt-6">
          <ScoreRing score={score} />
          <div className="min-w-[240px] flex-1">
            <h2 className="text-xl font-bold">Audit results</h2>
            <p className="mt-1 text-sm text-muted-foreground">{a.executive_summary}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button asChild variant="outline"><a href={reportHtmlUrl(audit.id)} target="_blank" rel="noopener">Open HTML report</a></Button>
              <Button asChild><a href={reportPdfUrl(audit.id)} target="_blank" rel="noopener">Download PDF</a></Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* category scores */}
      <Card>
        <CardHeader><CardTitle>Category scores</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {a.category_scores.map((c) => (
            <div key={c.category} className="rounded-lg border p-3">
              <div className={`text-2xl font-extrabold ${scoreColor(c.score)}`}>{c.score}</div>
              <div className="mt-0.5 text-xs text-muted-foreground">{c.category} · {c.issue_count}</div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                <div className={`h-full rounded-full ${scoreBg(c.score)}`} style={{ width: `${c.score}%` }} />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* core web vitals */}
      {v && v.source === "psi" && (
        <Card>
          <CardHeader><CardTitle>Core Web Vitals (mobile)</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            {[
              ["Performance", v.performance_score != null ? String(v.performance_score) : "—"],
              ["LCP", v.lcp_ms ? `${(v.lcp_ms / 1000).toFixed(1)}s` : "—"],
              ["CLS", v.cls != null ? v.cls.toFixed(3) : "—"],
              ["INP", v.inp_ms ? `${v.inp_ms.toFixed(0)}ms` : "—"],
              ["TBT", v.tbt_ms ? `${v.tbt_ms.toFixed(0)}ms` : "—"],
            ].map(([k, val]) => (
              <div key={k} className="min-w-[100px] rounded-lg border p-3">
                <div className="text-xs uppercase text-muted-foreground">{k}</div>
                <div className="text-lg font-bold">{val}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* quick wins */}
      {a.quick_wins?.length > 0 && (
        <Card className="border-blue-200 bg-blue-50/60">
          <CardHeader><CardTitle>⚡ Quick wins</CardTitle></CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1 pl-5 text-sm">{a.quick_wins.map((w, i) => <li key={i}>{w}</li>)}</ul>
          </CardContent>
        </Card>
      )}

      {/* action plan */}
      <Card>
        <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
          <CardTitle>Action plan ({issues.length})</CardTitle>
          <div className="flex flex-wrap gap-1.5">
            {cats.map((c) => (
              <button key={c} onClick={() => setCat(c)}
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${cat === c ? "bg-primary text-primary-foreground border-primary" : "text-muted-foreground"}`}>
                {c === "all" ? `All (${a.issues.length})` : c}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          {PRIORITIES.map((prio) => {
            const items = issues.filter((i) => i.priority === prio);
            if (!items.length) return null;
            return (
              <div key={prio}>
                <h4 className="mb-2 text-sm font-bold">{prio} ({items.length})</h4>
                <div className="space-y-2">
                  {items.map((i, idx) => (
                    <div key={idx} className="rounded-lg border border-l-4 p-3"
                      style={{ borderLeftColor: SEV_HEX[i.severity] || "#64748b" }}>
                      <div className="flex items-start justify-between gap-3">
                        <h5 className="font-semibold">{i.title} <span className="text-xs font-normal text-muted-foreground">· {i.category}</span></h5>
                        <div className="flex shrink-0 gap-1.5">
                          <Badge className={IMPACT_COLOR[i.impact] || "bg-slate-500"}>{i.impact}</Badge>
                          <Badge className={SEV_COLOR[i.severity] || "bg-slate-500"}>{i.severity}</Badge>
                        </div>
                      </div>
                      <p className="mt-1.5 text-sm">{i.description}</p>
                      <div className="mt-2 rounded-md bg-muted px-3 py-2 text-sm">
                        <span className="font-semibold text-primary">Fix:</span> {i.recommendation}
                        <span className="text-muted-foreground"> · {i.difficulty}</span>
                      </div>
                      {i.affected && <p className="mt-1.5 break-all text-xs text-muted-foreground">Affected: {i.affected}</p>}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
