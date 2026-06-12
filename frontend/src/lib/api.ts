const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type SearchPayload = {
  results: Array<{
    product_id: string;
    title: string;
    score: number;
    avg_rating: number;
    nb_reviews: number;
    description: string;
    snippets: string[];
    category: string;
    semantic_similarity: number | null;
    vector_angle_degrees: number | null;
    relevance_percent: number | null;
  }>;
  search_time_ms: number;
  strategy: string;
  warning: string | null;
  total_indexed: number;
};

export type SummaryPayload = {
  product_id: string;
  product_label: string;
  summary: string;
  pros: string[];
  cons: string[];
  recommendation: string;
  cached: boolean;
  source_basis: string;
};

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to reach backend health endpoint.");
  }
  return response.json() as Promise<{ status: string }>;
}

export async function fetchSearch(input: {
  query: string;
  top_k?: number;
  min_score?: number;
  mode?: "semantic" | "keyword";
}) {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to fetch search results.");
  }

  return response.json() as Promise<SearchPayload>;
}

export async function fetchSummary(productId: string) {
  const response = await fetch(`${API_BASE_URL}/summarize/${productId}`, {
    method: "POST",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to fetch product summary.");
  }

  return response.json() as Promise<SummaryPayload>;
}
