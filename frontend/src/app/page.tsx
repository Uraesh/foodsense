const shellStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  padding: "48px 24px",
} as const;

const cardStyle = {
  width: "min(760px, 100%)",
  padding: "40px",
  borderRadius: "28px",
  background: "rgba(255, 255, 255, 0.82)",
  boxShadow: "0 24px 80px rgba(84, 54, 22, 0.12)",
  backdropFilter: "blur(12px)",
} as const;

const badgeStyle = {
  display: "inline-block",
  padding: "8px 14px",
  borderRadius: "999px",
  background: "#efe1cc",
  color: "#7b4a16",
  fontSize: "0.85rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
} as const;

const titleStyle = {
  margin: "18px 0 12px",
  fontSize: "clamp(2.4rem, 5vw, 4.5rem)",
  lineHeight: 1,
} as const;

const textStyle = {
  margin: 0,
  maxWidth: "54ch",
  fontSize: "1.05rem",
  lineHeight: 1.7,
  color: "#4d4032",
} as const;

const listStyle = {
  margin: "28px 0 0",
  paddingLeft: "20px",
  color: "#4d4032",
  lineHeight: 1.8,
} as const;

export default function HomePage() {
  return (
    <main style={shellStyle}>
      <section style={cardStyle}>
        <span style={badgeStyle}>FoodSense bootstrap</span>
        <h1 style={titleStyle}>Semantic search for food products.</h1>
        <p style={textStyle}>
          The frontend is now wired with a viable Next.js foundation so the team can
          start building search, ranking, and review summarization flows without
          waiting for more scaffolding.
        </p>
        <ul style={listStyle}>
          <li>App Router structure is in place.</li>
          <li>TypeScript configuration is ready.</li>
          <li>The next step is to connect a search form to the FastAPI backend.</li>
        </ul>
      </section>
    </main>
  );
}
