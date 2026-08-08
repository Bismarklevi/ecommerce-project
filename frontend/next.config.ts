import type { NextConfig } from "next";

// Allows next/image to load product photos served by the Django backend
// (local disk in dev, Cloudflare R2 in production once that's configured --
// see backend/M4_CHANGELOG.md). NEXT_PUBLIC_MEDIA_HOST covers the R2 case;
// the two localhost patterns cover local dev against manage.py runserver.
const mediaHost = process.env.NEXT_PUBLIC_MEDIA_HOST;

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
      ...(mediaHost ? [{ protocol: "https" as const, hostname: mediaHost, pathname: "/**" }] : []),
    ],
    // Next.js 16 added an SSRF guard that refuses to optimize images from
    // hosts resolving to a private/loopback IP -- which 127.0.0.1 always is
    // -- regardless of remotePatterns matching. Without this, product
    // photos 400 in local dev the moment the backend runs on localhost.
    // Only matters for local dev: a real production host (R2's custom
    // domain, or a real backend domain) is never a private IP, so this
    // flag has no effect in production either way.
    dangerouslyAllowLocalIP: true,
  },
};

export default nextConfig;
