/** @type {import('next').NextConfig} */
const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
const isPages = process.env.PAGES === "1";
const repo = "website-audit-recommendation-system";

const nextConfig = isPages
  ? {
      // Static export for GitHub Pages (no Node server). The crawler backend
      // is not available there — the live site runs in demo mode and can point
      // at a hosted API via NEXT_PUBLIC_API_BASE.
      reactStrictMode: true,
      output: "export",
      images: { unoptimized: true },
      basePath: `/${repo}`,
      assetPrefix: `/${repo}/`,
      trailingSlash: true,
    }
  : {
      reactStrictMode: true,
      async rewrites() {
        // Proxy API + WebSocket to the FastAPI backend in dev.
        return [
          { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
          { source: "/ws/:path*", destination: `${BACKEND}/ws/:path*` },
        ];
      },
    };

export default nextConfig;
