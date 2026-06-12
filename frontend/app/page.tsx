'use client';

import { useState } from "react";
import { Sparkles } from "lucide-react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import ResultCard from "@/components/ResultCard";
import SearchInsights from "@/components/SearchInsights";
import RefineSidebar from "@/components/RefineSidebar";
import AboutResults from "@/components/AboutResults";
import Pagination from "@/components/Pagination";
import type { Result } from "@/lib/types";
import { mapSearchProductToResult, searchProducts } from "@/lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [totalIndexed, setTotalIndexed] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(searchQuery: string) {
    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      setError("Veuillez saisir une requête de recherche.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setWarning(null);

    try {
      const response = await searchProducts(trimmedQuery, 10);
      setResults(
        response.results.map((product, index) =>
          mapSearchProductToResult(product, index),
        ),
      );
      setSearchTime(response.search_time_ms);
      setStrategy(response.strategy);
      setWarning(response.warning ?? null);
      setTotalIndexed(response.total_indexed);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Échec de la recherche. Veuillez réessayer.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      <Header />
      <Hero
        query={query}
        isLoading={isLoading}
        onQueryChange={setQuery}
        onSearch={() => handleSearch(query)}
      />

      <section className="mx-auto max-w-7xl px-6 pb-16">
        <div className="rounded-3xl border border-slate-100 bg-white/70 p-4 shadow-card backdrop-blur sm:p-6">
          {/* results header */}
          <div className="flex flex-col gap-4 px-1 pb-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-brand" />
                <h2 className="text-base font-bold text-ink">
                  {results.length} results for your search
                </h2>
              </div>
              <p className="mt-0.5 text-xs text-slate-400">
                Search completed in{" "}
                <span className="font-medium text-brand">
                  {searchTime !== null ? `${searchTime}ms` : "1.07s"}
                </span>
                {strategy ? ` · ${strategy}` : ""}
                {totalIndexed !== null ? ` · indexed: ${totalIndexed}` : ""}
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

          {(warning || error) && (
            <div className="mb-4 rounded-2xl border border-orange-100 bg-orange-50 px-4 py-3 text-sm text-orange-700">
              {error ?? warning}
            </div>
          )}

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
