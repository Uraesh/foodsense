import styles from "./SearchBar.module.css";

type SearchBarProps = {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  centered?: boolean;
};

export function SearchBar({
  query,
  onQueryChange,
  onSubmit,
  disabled = false,
  centered = false,
}: SearchBarProps) {
  return (
    <form
      className={`${styles.form} ${centered ? styles.centered : ""}`}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label htmlFor="query" className={styles.searchField}>
        <span className={styles.searchIcon} aria-hidden="true">
          <svg viewBox="0 0 24 24" className={styles.iconSvg}>
            <circle cx="11" cy="11" r="6.75" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="M16.2 16.2 L21 21" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </span>
        <input
          id="query"
          className={styles.input}
          type="text"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Rechercher un produit alimentaire"
          disabled={disabled}
        />
        <button
          className={styles.iconButton}
          type="submit"
          disabled={disabled}
          aria-label={disabled ? "Recherche en cours" : "Lancer la recherche"}
        >
          <svg viewBox="0 0 24 24" className={styles.submitSvg}>
            <path
              d="M5 12 H17"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M12.5 7 L18 12 L12.5 17"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </label>
    </form>
  );
}
