"use client";
import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Ev { status: string; message: string; pct: number }

export function ProgressLog({ events, pct, status }: { events: Ev[]; pct: number; status: string }) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [events]);
  if (!events.length) return null;

  const statusColor = status === "done" ? "text-emerald-600" : status === "error" ? "text-red-600" : "text-primary";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Live progress</CardTitle>
        <span className={`text-sm font-bold capitalize ${statusColor}`}>{status.replace(/_/g, " ")}</span>
      </CardHeader>
      <CardContent>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all duration-300" style={{ width: `${pct}%` }} />
        </div>
        <div className="mt-3 max-h-56 space-y-1.5 overflow-y-auto text-sm">
          {events.map((e, i) => (
            <div key={i} className={`flex items-center gap-2 ${e.status === "error" ? "text-red-600" : "text-muted-foreground"}`}>
              <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${e.status === "done" ? "bg-emerald-600" : e.status === "error" ? "bg-red-600" : "bg-primary"}`} />
              {e.message}
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </CardContent>
    </Card>
  );
}
