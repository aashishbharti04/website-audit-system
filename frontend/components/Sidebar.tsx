"use client";
import { Accessibility, BookOpen, Gauge, Github, Info, Search, X } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

export type View = "audit" | "guide" | "about";

const NAV: { key: View; label: string; icon: any }[] = [
  { key: "audit", label: "Run Audit", icon: Search },
  { key: "guide", label: "User Guide", icon: BookOpen },
  { key: "about", label: "About", icon: Info },
];

export function Sidebar({
  view, setView, open, setOpen, info,
}: {
  view: View; setView: (v: View) => void; open: boolean; setOpen: (b: boolean) => void; info: any;
}) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={() => setOpen(false)} />}
      <aside
        className={`fixed z-40 flex h-full w-64 flex-col bg-sidebar text-sidebar-foreground transition-transform md:sticky md:top-0 md:h-screen md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-5">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-lg">🩺</span>
            <div className="leading-tight">
              <div className="text-sm font-extrabold">Website Audit</div>
              <div className="text-[11px] text-sidebar-foreground/60">& Recommendation System</div>
            </div>
          </div>
          <button className="md:hidden" onClick={() => setOpen(false)} aria-label="Close menu"><X className="h-5 w-5" /></button>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {NAV.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => { setView(key); setOpen(false); }}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                view === key ? "bg-primary text-primary-foreground" : "text-sidebar-foreground/75 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </nav>

        <div className="mx-3 my-4 rounded-lg bg-white/5 p-3 text-xs text-sidebar-foreground/70">
          <div className="mb-2 font-semibold text-sidebar-foreground/90">What it checks</div>
          <div className="flex flex-wrap gap-1.5">
            {["Technical", "On-Page", "Performance", "Content", "Local SEO", "UX", "A11y"].map((t) => (
              <span key={t} className="rounded-full bg-white/10 px-2 py-0.5">{t}</span>
            ))}
          </div>
        </div>

        <div className="mt-auto space-y-3 p-4">
          <div className="flex items-center gap-2 text-xs text-sidebar-foreground/60">
            <Gauge className="h-3.5 w-3.5" /> AI {info?.ai_enabled ? `· ${info.ai_model}` : "off"}
            <Accessibility className="ml-1 h-3.5 w-3.5" /> 7 categories
          </div>
          <ThemeToggle />
          <a
            href="https://github.com/aashishbharti04/website-audit-recommendation-system"
            target="_blank" rel="noopener"
            className="flex items-center gap-2 text-xs text-sidebar-foreground/60 hover:text-white"
          >
            <Github className="h-3.5 w-3.5" /> View source
          </a>
        </div>
      </aside>
    </>
  );
}
