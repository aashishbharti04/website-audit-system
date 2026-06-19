import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function scoreColor(s: number): string {
  return s >= 80 ? "text-emerald-600" : s >= 50 ? "text-amber-600" : "text-red-600";
}
export function scoreBg(s: number): string {
  return s >= 80 ? "bg-emerald-600" : s >= 50 ? "bg-amber-600" : "bg-red-600";
}

export const SEV_COLOR: Record<string, string> = {
  critical: "bg-red-600", high: "bg-orange-600", medium: "bg-amber-600", low: "bg-blue-600", info: "bg-slate-500",
};
export const IMPACT_COLOR: Record<string, string> = {
  High: "bg-red-600", Medium: "bg-amber-600", Low: "bg-emerald-600",
};
export const SEV_HEX: Record<string, string> = {
  critical: "#dc2626", high: "#ea580c", medium: "#d97706", low: "#2563eb", info: "#64748b",
};
