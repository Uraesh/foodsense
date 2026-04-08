import styles from "./ResultCard.module.css";

export type SearchResult = {
  product_id: string;
  title: string;
  score: number;
  avg_rating: number;
  nb_reviews: number;
  description: string;
  category: string;
  semantic_similarity: number | null;
  vector_angle_degrees: number | null;
  relevance_percent: number | null;
};

type ResultCardProps = {
  result: SearchResult;
  rank: number;
};

const STAR_COUNT = 5;

function buildStars(avgRating: number) {
  const rounded = Math.max(0, Math.min(STAR_COUNT, Math.round(avgRating)));
  return Array.from({ length: STAR_COUNT }, (_, index) => index < rounded);
}

export function ResultCard({ result, rank }: ResultCardProps) {
  const relevancePercent = result.relevance_percent;
  const stars = buildStars(result.avg_rating);

  return (
    <article className={styles.card}>
      <div className={styles.content}>
        <div className={styles.header}>
          <div className={styles.titleBlock}>
            <p className={styles.rank}>#{String(rank).padStart(2, "0")}</p>
            <h3 className={styles.title}>{result.title}</h3>
          </div>

          <div
            className={styles.relevance}
            aria-label={
              relevancePercent !== null
                ? `Pertinence vectorielle ${relevancePercent}%`
                : "Pertinence vectorielle indisponible"
            }
            title={
              result.vector_angle_degrees !== null
                ? `Angle vectoriel ${result.vector_angle_degrees.toFixed(2)} deg`
                : "Angle vectoriel indisponible"
            }
          >
            <div className={styles.relevanceBar}>
              <span
                className={styles.relevanceFill}
                style={{ width: `${relevancePercent ?? 0}%` }}
              />
            </div>
            <strong className={styles.relevanceValue}>
              {relevancePercent !== null ? `${relevancePercent}%` : "N/A"}
            </strong>
          </div>
        </div>

        <div className={styles.metaRow}>
          <div
            className={styles.stars}
            aria-label={`Note moyenne ${result.avg_rating.toFixed(1)} sur 5`}
          >
            {stars.map((filled, index) => (
              <span
                key={`${result.product_id}-star-${index}`}
                className={`${styles.star} ${filled ? styles.starFilled : ""}`}
                aria-hidden="true"
              >
                {"\u2605"}
              </span>
            ))}
          </div>
          <span className={styles.reviewCount}>{`${result.nb_reviews} avis`}</span>
          <span className={styles.category}>{result.category}</span>
        </div>

        <p className={styles.description}>{result.description}</p>
        <p className={styles.productId}>{result.product_id}</p>
      </div>
    </article>
  );
}
