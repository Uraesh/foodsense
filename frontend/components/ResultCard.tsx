import { Star, Bookmark } from "lucide-react";
import type { Result } from "@/lib/data";
import ProductPlaceholder from "./ProductPlaceholder";

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-3.5 w-3.5 ${
            i < Math.round(rating)
              ? "fill-amber-400 text-amber-400"
              : "fill-slate-200 text-slate-200"
          }`}
        />
      ))}
    </div>
  );
}

export default function ResultCard({ result }: { result: Result }) {
  return (
    <article className="relative flex gap-5 rounded-2xl border border-slate-100 bg-white p-5 shadow-card transition-shadow hover:shadow-md">
      {/* rank badge */}
      <div className="absolute -left-2.5 top-5 grid h-7 w-7 place-items-center rounded-full bg-brand text-xs font-bold text-white shadow-sm">
        {result.id}
      </div>

      {/* product placeholder (no generated images) */}
      <ProductPlaceholder label={result.category} />

      {/* content */}
      <div className="min-w-0 flex-1">
        {result.topMatch && (
          <span className="mb-2 inline-block rounded bg-brand/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-brand">
            Top Match
          </span>
        )}

        <h3 className="pr-20 text-[15px] font-bold leading-snug text-ink">
          {result.title}
        </h3>

        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">{result.rating}</span>
          <Stars rating={result.rating} />
          <span>{result.reviews} reviews</span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-500">
            {result.brand}
          </span>
        </div>

        <p className="mt-2 text-xs leading-relaxed text-slate-500">
          {result.description}
        </p>

        <div className="mt-3 rounded-lg bg-brand/[0.04] p-3">
          <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-brand">
            Key points
          </p>
          <ul className="space-y-1">
            {result.keyPoints.map((point) => (
              <li
                key={point}
                className="flex items-start gap-1.5 text-xs text-slate-600"
              >
                <span className="mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-leaf" />
                {point}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* relevance + bookmark */}
      <div className="flex w-20 shrink-0 flex-col items-end justify-between">
        <div className="text-right">
          <p className="text-[9px] font-semibold uppercase tracking-wide text-slate-400">
            Relevance
          </p>
          <p className="text-lg font-extrabold text-relevance">
            {result.relevance}%
          </p>
          <div className="mt-1 h-1 w-16 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-relevance"
              style={{ width: `${result.relevance}%` }}
            />
          </div>
        </div>
        <button
          aria-label="Save result"
          className="rounded-lg border border-slate-200 p-1.5 text-slate-400 transition-colors hover:border-brand/40 hover:text-brand"
        >
          <Bookmark className="h-4 w-4" />
        </button>
      </div>
    </article>
  );
}
