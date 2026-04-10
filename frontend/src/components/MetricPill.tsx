import styles from "./MetricPill.module.css";

type MetricPillProps = {
  label: string;
  value: string;
  tone?: "default" | "accent";
};

export function MetricPill({
  label,
  value,
  tone = "default",
}: MetricPillProps) {
  return (
    <div
      className={`${styles.pill} ${tone === "accent" ? styles.accent : ""}`}
    >
      <span className={styles.label}>{label}</span>
      <strong className={styles.value}>{value}</strong>
    </div>
  );
}
