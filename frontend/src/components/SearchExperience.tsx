"use client";

import { startTransition, useState } from "react";

import { fetchSearch, type SearchPayload } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { ResultCard } from "@/components/ResultCard";
import { SearchBar } from "@/components/SearchBar";
import styles from "./SearchExperience.module.css";

function SearchMark() {
  return (
    <span className={styles.brandMark} aria-hidden="true">
      <svg viewBox="0 0 64 64" className={styles.brandSvg}>
        <defs>
          <linearGradient id="foodsenseGradient" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#4285F4" />
            <stop offset="100%" stopColor="#34A853" />
          </linearGradient>
        </defs>
        <circle cx="30" cy="30" r="16" fill="none" stroke="url(#foodsenseGradient)" strokeWidth="5" />
        <path d="M42 42 L56 56" stroke="#4285F4" strokeWidth="5" strokeLinecap="round" />
        <circle cx="24" cy="28" r="2.8" fill="#34A853" />
        <circle cx="34" cy="24" r="2.8" fill="#FBBC05" />
        <circle cx="37" cy="34" r="2.8" fill="#EA4335" />
        <path
          d="M24 28 L34 24 L37 34 L24 28"
          fill="none"
          stroke="#5F6368"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export function SearchExperience() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchPayload["results"]>([]);
  const [totalIndexed, setTotalIndexed] = useState(0);
  const [strategy, setStrategy] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [searchTimeMs, setSearchTimeMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sortKey, setSortKey] = useState<"relevance" | "rating" | "reviews">("relevance");

  async function runSearch(nextQuery = query) {
    const normalizedQuery = nextQuery.trim();
    if (!normalizedQuery) {
      setError("Merci de saisir une requete avant de lancer la recherche.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = await fetchSearch({ query: normalizedQuery, top_k: 5, mode: "semantic" });
      startTransition(() => {
        setResults(payload.results);
        setTotalIndexed(payload.total_indexed);
        setStrategy(payload.strategy);
        setWarning(payload.warning);
        setSearchTimeMs(payload.search_time_ms);
      });
    } catch {
      setError(
        "Le backend est actuellement indisponible. Verifie Docker, Ollama et l'API FastAPI.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  const sortedResults = [...results].sort((left, right) => {
    if (sortKey === "rating") {
      return right.avg_rating - left.avg_rating || right.nb_reviews - left.nb_reviews;
    }
    if (sortKey === "reviews") {
      return right.nb_reviews - left.nb_reviews || right.avg_rating - left.avg_rating;
    }
    return right.score - left.score || right.nb_reviews - left.nb_reviews;
  });

  const hasSearchState =
    isLoading ||
    sortedResults.length > 0 ||
    warning !== null ||
    error !== null ||
    searchTimeMs !== null;

  const resultMeta =
    sortedResults.length > 0
      ? `${sortedResults.length} resultats sur ${totalIndexed.toLocaleString("fr-FR")} produits indexes`
      : null;

  return (
    <section className={`${styles.shell} ${hasSearchState ? styles.shellActive : styles.shellIdle}`}>
      <div className={`${styles.searchPanel} ${hasSearchState ? styles.searchPanelActive : styles.searchPanelIdle}`}>
        <div className={styles.brandBlock}>
          <SearchMark />
          <h1 className={styles.brandTitle}>FoodSense</h1>
        </div>

        <SearchBar
          query={query}
          onQueryChange={setQuery}
          onSubmit={() => void runSearch()}
          disabled={isLoading}
          centered={!hasSearchState}
        />

        {warning ? <p className={styles.warning}>{warning}</p> : null}
        {error ? <p className={styles.error}>{error}</p> : null}
      </div>

      {hasSearchState ? (
        <div className={styles.resultsPanel}>
          <div className={styles.resultsHeader}>
            <div className={styles.resultsMeta}>
              {resultMeta ? <p className={styles.resultsHint}>{resultMeta}</p> : null}
              {strategy ? <p className={styles.strategyHint}>{strategy.replaceAll("_", " ")}</p> : null}
              {searchTimeMs !== null ? <p className={styles.timeHint}>{`${searchTimeMs} ms`}</p> : null}
            </div>

            <label className={styles.sortLabel}>
              <span>Trier par</span>
              <select
                className={styles.sortSelect}
                value={sortKey}
                onChange={(event) =>
                  setSortKey(event.target.value as "relevance" | "rating" | "reviews")
                }
              >
                <option value="relevance">Pertinence</option>
                <option value="rating">Note</option>
                <option value="reviews">Avis</option>
              </select>
            </label>
          </div>

          {isLoading ? <LoadingSpinner /> : null}

          {!isLoading && sortedResults.length > 0 ? (
            <div className={styles.resultsGrid}>
              {sortedResults.map((result, index) => (
                <ResultCard key={result.product_id} result={result} rank={index + 1} />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
