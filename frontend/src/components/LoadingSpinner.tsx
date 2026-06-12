import styles from "./LoadingSpinner.module.css";

export function LoadingSpinner() {
  return (
    <div className={styles.loading} aria-live="polite" aria-busy="true">
      <span className={styles.dot} aria-hidden="true" />
      <p className={styles.label}>Interrogation du moteur semantic...</p>
    </div>
  );
}
