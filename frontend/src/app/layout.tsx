import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "FoodSense",
  description: "Semantic search for food products and review summaries.",
};

const bodyStyle = {
  margin: 0,
  minHeight: "100vh",
  fontFamily: '"Segoe UI", sans-serif',
  background:
    "radial-gradient(circle at top, rgba(245, 209, 163, 0.32), transparent 32%), linear-gradient(180deg, #fffaf2 0%, #f6efe2 100%)",
  color: "#1f1a14",
} as const;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={bodyStyle}>{children}</body>
    </html>
  );
}
