export type SearchResult = {
  product_id: string;
  title: string;
  score: number;
  avg_rating: number;
  nb_reviews: number;
};

type ResultCardProps = {
  result: SearchResult;
};

export function ResultCard({ result }: ResultCardProps) {
  return (
    <article
      style={{
        padding: 20,
        borderRadius: 20,
        background: "rgba(255, 255, 255, 0.8)",
        boxShadow: "0 18px 48px rgba(84, 54, 22, 0.1)",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>{result.title}</h3>
      <p style={{ margin: 0, color: "#6c5b4d" }}>Product ID: {result.product_id}</p>
      <p style={{ marginBottom: 0, color: "#6c5b4d" }}>
        Score: {result.score.toFixed(3)} | Rating: {result.avg_rating.toFixed(1)} | Reviews:{" "}
        {result.nb_reviews}
      </p>
    </article>
  );
}
