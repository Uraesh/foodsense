type SearchBarProps = {
  query: string;
  onQueryChange: (value: string) => void;
};

export function SearchBar({ query, onQueryChange }: SearchBarProps) {
  return (
    <form style={{ display: "grid", gap: 12 }}>
      <label htmlFor="query" style={{ fontWeight: 700 }}>
        Search intent
      </label>
      <input
        id="query"
        type="text"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder="e.g. sugar free chocolate"
        style={{
          width: "100%",
          padding: "14px 16px",
          borderRadius: 16,
          border: "1px solid rgba(143, 79, 19, 0.24)",
          background: "rgba(255, 255, 255, 0.95)",
        }}
      />
    </form>
  );
}
