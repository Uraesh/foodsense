import { TrendingUp } from "lucide-react";

function MiniChart() {
  // simple upward trending sparkline (SVG, no images)
  const points = "0,46 18,40 36,42 54,30 72,33 90,22 108,26 126,14 144,18 162,6";
  return (
    <svg
      viewBox="0 0 162 52"
      className="h-20 w-full"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="insightFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,52 ${points} 162,52`} fill="url(#insightFill)" />
      <polyline
        points={points}
        fill="none"
        stroke="#2563eb"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function SearchInsights() {
  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card">
      <div className="mb-3 flex items-center gap-1.5">
        <TrendingUp className="h-4 w-4 text-brand" />
        <h3 className="text-sm font-bold text-ink">Search insights</h3>
      </div>
      <MiniChart />
      <p className="mt-3 text-xs leading-relaxed text-slate-500">
        We analyzed <span className="font-bold text-ink">3,000+ products</span>{" "}
        to find the most relevant results for your search.
      </p>
    </div>
  );
}
