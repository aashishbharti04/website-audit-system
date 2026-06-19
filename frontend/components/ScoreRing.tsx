import { scoreColor } from "@/lib/utils";

export function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const r = (size - 14) / 2;
  const c = 2 * Math.PI * r;
  const stroke = score >= 80 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth={10} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={stroke} strokeWidth={10}
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c - (score / 100) * c}
          style={{ transition: "stroke-dashoffset .6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-extrabold ${scoreColor(score)}`}>{score}</span>
        <span className="text-xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}
