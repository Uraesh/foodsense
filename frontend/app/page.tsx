import { Sparkles } from "lucide-react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import ResultCard from "@/components/ResultCard";
import SearchInsights from "@/components/SearchInsights";
import RefineSidebar from "@/components/RefineSidebar";
import AboutResults from "@/components/AboutResults";
import Pagination from "@/components/Pagination";
import { results } from "@/lib/data";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />

      <section className="mx-auto max-w-7xl px-6 pb-16">
        <div className="rounded-3xl border border-slate-100 bg-white/70 p-4 shadow-card backdrop-blur sm:p-6">
          {/* results header */}
          <div className="flex items-center justify-between px-1 pb-4">
            <div>
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-brand" />
                <h2 className="text-base font-bold text-ink">
                  {results.length} results for your search
                </h2>
              </div>
              <p className="mt-0.5 text-xs text-slate-400">
                Search completed in{" "}
                <span className="font-medium text-brand">1.07s</span>
              </p>
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-500">
              Sort by:
              <select className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-brand">
                <option>Relevance</option>
                <option>Rating</option>
                <option>Most reviewed</option>
              </select>
            </label>
          </div>

          {/* grid: results + sidebar */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_300px]">
            <div className="space-y-4">
              {results.map((result) => (
                <ResultCard key={result.id} result={result} />
              ))}
              <Pagination />
            </div>

            <aside className="space-y-5">
              <SearchInsights />
              <RefineSidebar />
              <AboutResults />
            </aside>
          </div>
        </div>
      </section>
    </main>
  );
}
