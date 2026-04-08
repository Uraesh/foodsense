import { SearchExperience } from "@/components/SearchExperience";
import styles from "./page.module.css";

export default function HomePage() {
  return (
    <main className={styles.pageShell}>
      <div className={styles.ambientHalo} aria-hidden="true" />
      <SearchExperience />
    </main>
  );
}
