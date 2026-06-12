import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FoodSense — Discover. Understand. Eat Better.",
  description:
    "AI-powered search that helps you find the best food for your body and mind.",
  openGraph: {
    title: "FoodSense — Discover. Understand. Eat Better.",
    description:
      "AI-powered search that helps you find the best food for your body and mind.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
