import { SearchBar } from "@/components/SearchBar";
import { ResultCard, type SearchResult } from "@/components/ResultCard";
import { SummaryPanel } from "@/components/SummaryPanel";

const shellStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  padding: "48px 24px",
} as const;

const cardStyle = {
  width: "min(760px, 100%)",
  padding: "40px",
  borderRadius: "28px",
  background: "rgba(255, 255, 255, 0.82)",
  boxShadow: "0 24px 80px rgba(84, 54, 22, 0.12)",
  backdropFilter: "blur(12px)",
} as const;

const badgeStyle = {
  display: "inline-block",
  padding: "8px 14px",
  borderRadius: "999px",
  background: "#efe1cc",
  color: "#7b4a16",
  fontSize: "0.85rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
} as const;

const titleStyle = {
  margin: "18px 0 12px",
  fontSize: "clamp(2.4rem, 5vw, 4.5rem)",
  lineHeight: 1,
} as const;

const textStyle = {
  margin: 0,
  maxWidth: "54ch",
  fontSize: "1.05rem",
  lineHeight: 1.7,
  color: "#4d4032",
} as const;

const gridStyle = {
  marginTop: "28px",
  display: "grid",
  gap: "16px",
} as const;

export default function HomePage() {
  const sampleResults: SearchResult[] = [
    {
      product_id: "B001E4KFG0",
      title: "Good Quality Dog Food",
      score: 0.921,
      avg_rating: 4.6,
      nb_reviews: 312,
    },
    {
      product_id: "B00813GRG4",
      title: "Not as Advertised",
      score: 0.774,
      avg_rating: 2.1,
      nb_reviews: 58,
    },
  ];

  return (
    <main style={shellStyle}>
      <section style={cardStyle}>
        <span style={badgeStyle}>FoodSense bootstrap</span>
        <h1 style={titleStyle}>Semantic search for food products.</h1>
        <p style={textStyle}>
          The frontend is now wired with a viable Next.js foundation so the team can
          start building search, ranking, and review summarization flows without
          waiting for more scaffolding.
        </p>
        <div style={gridStyle}>
          <SearchBar query="dark chocolate low sugar" onQueryChange={() => undefined} />
          {sampleResults.map((result) => (
            <ResultCard key={result.product_id} result={result} />
          ))}
        </div>
        <SummaryPanel
          title="Planned V1 behavior"
          items={[
            "The page will query the FastAPI /search endpoint.",
            "Result cards will expose a dedicated summarize action.",
            "LLM summaries remain a backend concern behind /summarize/{product_id}.",
          ]}
        />
      </section>
    </main>
  );
}
