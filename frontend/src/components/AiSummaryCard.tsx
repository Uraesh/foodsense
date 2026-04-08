import type { SummaryPayload } from "@/lib/api";
import styles from "./AiSummaryCard.module.css";

type AiSummaryCardProps = {
  summary: SummaryPayload;
  onClose: () => void;
};

export function AiSummaryCard({ summary, onClose }: AiSummaryCardProps) {
  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>Synthese IA - Mistral Small 3.1</p>
          <span className={styles.cache}>
            <span className={styles.cacheDot} aria-hidden="true" />
            {summary.cached ? "en cache" : "genere a la demande"}
          </span>
        </div>

        <button className={styles.closeButton} type="button" onClick={onClose}>
          Fermer
        </button>
      </div>

      <dl className={styles.grid}>
        <div className={styles.row}>
          <dt className={styles.term}>Vue globale</dt>
          <dd className={styles.definition}>{summary.summary}</dd>
        </div>
        <div className={styles.row}>
          <dt className={styles.term}>Avantages</dt>
          <dd className={styles.definition}>
            {summary.pros.length > 0
              ? summary.pros.join(", ")
              : "Aucun avantage distinctif n'a ete extrait."}
          </dd>
        </div>
        <div className={styles.row}>
          <dt className={styles.term}>Inconvenients</dt>
          <dd className={styles.definition}>
            {summary.cons.length > 0
              ? summary.cons.join(", ")
              : "Aucun inconvenient notable n'a ete extrait."}
          </dd>
        </div>
        <div className={styles.row}>
          <dt className={styles.term}>Recommandation</dt>
          <dd className={styles.definition}>{summary.recommendation}</dd>
        </div>
      </dl>
    </section>
  );
}
