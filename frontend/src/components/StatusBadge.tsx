import styles from "./StatusBadge.module.css";

type StatusBadgeProps = {
  tone?: "success" | "warning" | "neutral";
  children: string;
};

export function StatusBadge({
  tone = "neutral",
  children,
}: StatusBadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>
  );
}
