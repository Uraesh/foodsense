type SummaryPanelProps = {
  title: string;
  items: string[];
};

export function SummaryPanel({ title, items }: SummaryPanelProps) {
  return (
    <section style={{ marginTop: 24 }}>
      <h4 style={{ marginBottom: 8 }}>{title}</h4>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
