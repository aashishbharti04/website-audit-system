import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Website Doctor AI — Website Audit & Recommendations",
  description: "Scan any website and get a branded, prioritised audit: SEO, performance, local SEO, UX, accessibility.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
