import styles from "./SummaryPanel.module.css";

type SummaryPanelProps = {
  title: string;
  items: string[];
  tone?: "default" | "accent";
};

export function SummaryPanel({
  title,
  items,
  tone = "default",
}: SummaryPanelProps) {
  return (
    <section
      className={`${styles.panel} ${tone === "accent" ? styles.accent : ""}`}
    >
      <h2 className={styles.title}>{title}</h2>
      <ul className={styles.list}>
        {items.map((item) => (
          <li className={styles.item} key={item}>
            <span className={styles.bullet} aria-hidden="true" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
