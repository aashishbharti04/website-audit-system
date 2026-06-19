/** @type {import('next').NextConfig} */
const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    // Proxy API + WebSocket to the FastAPI backend in dev.
    return [
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      { source: "/ws/:path*", destination: `${BACKEND}/ws/:path*` },
    ];
  },
};

export default nextConfig;
