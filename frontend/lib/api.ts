import type { Result } from "@/lib/types";

export type SearchProduct = {
  product_id: string;
  title: string;
  score: number;
  avg_rating: number;
  nb_reviews: number;
  description: string;
  snippets: string[];
  category: string;
  relevance_percent?: number;
};

export type SearchResponse = {
  results: SearchProduct[];
  search_time_ms: number;
  strategy: string;
  warning?: string | null;
  total_indexed: number;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

// Try backend semantic search, and if it fails (network error or non-2xx),
// fall back to a lightweight lexical search using a local JSON file placed
// in `public/lexical_fallback.json`.
export async function searchProducts(
  query: string,
  top_k = 10,
): Promise<SearchResponse> {
  const url = new URL("/search", apiBaseUrl).href;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k, mode: "semantic" }),
    });

    if (!response.ok) {
      // treat non-ok like a failure to trigger lexical fallback
      throw new Error(`non-ok ${response.status}`);
    }

    return (await response.json()) as SearchResponse;
  } catch (err) {
    // lexical fallback: load a minimal product list from public/lexical_fallback.json
    try {
      const fallbackResp = await fetch("/lexical_fallback.json");
      if (!fallbackResp.ok) {
        throw new Error("No lexical fallback available");
      }
      const all: SearchProduct[] = await fallbackResp.json();
      const q = query.trim().toLowerCase();
      const matches = all
        .map((p) => ({
          product: p,
          score:
            (p.title || "").toLowerCase().includes(q) ? 1.0 : (p.description || "").toLowerCase().includes(q) ? 0.6 : 0.0,
        }))
        .filter((m) => m.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, top_k)
        .map((m) => m.product);

      return {
        results: matches,
        search_time_ms: 0,
        strategy: "lexical-fallback",
        warning: "Backend unreachable — using local lexical fallback",
        total_indexed: all.length,
      };
    } catch (lexErr) {
      throw new Error(
        `Search failed (backend + lexical fallback): ${String(err)} / ${String(lexErr)}`,
      );
    }
  }
}

export function mapSearchProductToResult(
  product: SearchProduct,
  index: number,
): Result {
  return {
    id: index + 1,
    topMatch: index === 0,
    title: product.title,
    rating: Number(product.avg_rating) || 0,
    reviews: product.nb_reviews || 0,
    brand: "FoodSense",
    category: product.category || "Produits",
    description:
      product.description || "Produit trouvé via recherche sémantique.",
    keyPoints:
      product.snippets && product.snippets.length > 0
        ? product.snippets
        : [`score: ${product.score.toFixed(2)}`],
    relevance:
      product.relevance_percent ?? Math.round((product.score || 0) * 100),
  };
}
