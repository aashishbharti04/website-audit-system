"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AuditOptions } from "@/lib/api";

export function UrlForm({ onStart, busy }: { onStart: (url: string, o: AuditOptions) => void; busy: boolean }) {
  const [url, setUrl] = useState("");
  const [clientName, setClientName] = useState("");
  const [keyword, setKeyword] = useState("");
  const [maxPages, setMaxPages] = useState(25);
  const [checkLinks, setCheckLinks] = useState(true);
  const [checkPerf, setCheckPerf] = useState(true);
  const [useAi, setUseAi] = useState(true);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onStart(url.trim(), {
      max_pages: Number(maxPages),
      check_links: checkLinks,
      check_performance: checkPerf,
      use_ai: useAi,
      client_name: clientName.trim() || null,
      primary_keyword: keyword.trim() || null,
    });
  };

  return (
    <Card>
      <CardHeader><CardTitle>New website audit</CardTitle></CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5">
              <span className="text-sm font-semibold text-muted-foreground">Website URL *</span>
              <Input placeholder="clientsite.com" value={url} onChange={(e) => setUrl(e.target.value)} disabled={busy} required />
            </label>
            <label className="space-y-1.5">
              <span className="text-sm font-semibold text-muted-foreground">Client name</span>
              <Input placeholder="Acme Inc." value={clientName} onChange={(e) => setClientName(e.target.value)} disabled={busy} />
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5">
              <span className="text-sm font-semibold text-muted-foreground">Target keyword (optional)</span>
              <Input placeholder="plumber in Austin" value={keyword} onChange={(e) => setKeyword(e.target.value)} disabled={busy} />
            </label>
            <label className="space-y-1.5">
              <span className="text-sm font-semibold text-muted-foreground">Max pages</span>
              <Input type="number" min={1} max={300} value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))} disabled={busy} />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-5">
            {[
              ["Check links", checkLinks, setCheckLinks],
              ["Core Web Vitals", checkPerf, setCheckPerf],
              ["AI analysis", useAi, setUseAi],
            ].map(([label, val, set]) => (
              <label key={label as string} className="flex items-center gap-2 text-sm font-medium">
                <input type="checkbox" className="h-4 w-4 accent-primary" checked={val as boolean}
                  onChange={(e) => (set as (v: boolean) => void)(e.target.checked)} disabled={busy} />
                {label as string}
              </label>
            ))}
            <Button type="submit" disabled={busy} className="ml-auto">
              {busy ? "Auditing…" : "Run audit"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
