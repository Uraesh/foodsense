import { ArrowLeft, ArrowRight } from "lucide-react";

export default function Pagination() {
  const pages = ["1", "2", "3", "…", "15"];
  return (
    <nav className="flex items-center justify-center gap-2 py-8 text-sm">
      <button
        aria-label="Previous page"
        className="grid h-8 w-8 place-items-center rounded-full text-slate-400 transition-colors hover:bg-slate-100"
      >
        <ArrowLeft className="h-4 w-4" />
      </button>
      {pages.map((p, i) => (
        <button
          key={`${p}-${i}`}
          className={
            p === "1"
              ? "grid h-8 w-8 place-items-center rounded-full border border-brand text-sm font-semibold text-brand"
              : "grid h-8 w-8 place-items-center rounded-full text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100"
          }
        >
          {p}
        </button>
      ))}
      <button
        aria-label="Next page"
        className="grid h-8 w-8 place-items-center rounded-full text-slate-400 transition-colors hover:bg-slate-100"
      >
        <ArrowRight className="h-4 w-4" />
      </button>
    </nav>
  );
}
