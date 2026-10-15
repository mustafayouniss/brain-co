import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";
const isDev = process.env.NODE_ENV === "development";

/**
 * Security headers for every route.
 * CSP allows same-origin scripts/styles plus Google Analytics (only used when
 * NEXT_PUBLIC_GA_ID is configured). 'unsafe-inline' for scripts is required by
 * the inline theme bootstrap that prevents a light/dark flash on first paint.
 *
 * `'unsafe-eval'` is added to script-src ONLY in development: React 19 / Next 16
 * dev builds call `eval()` for debugging features (e.g. reconstructing
 * server-side call stacks) and throw "eval() is not supported in this
 * environment" when CSP omits it. React never uses eval() in production, so the
 * production header stays strict and unchanged.
 * Ref: https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy
 */
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-DNS-Prefetch-Control", value: "on" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  ...(isProd
    ? [
        {
          key: "Strict-Transport-Security",
          value: "max-age=63072000; includeSubDomains; preload",
        },
      ]
    : []),
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""} https://www.googletagmanager.com`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https:",
      "font-src 'self' data:",
      "connect-src 'self' https://www.googletagmanager.com https://*.google-analytics.com",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  images: {
    // SVG assets shipped with the original app are served un-optimized so the
    // particle-morph engine can parse them with DOMParser.
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
      {
        source: "/sw.js",
        headers: [
          { key: "Content-Type", value: "application/javascript; charset=utf-8" },
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
      {
        source: "/morphs/:path*",
        headers: [{ key: "Cache-Control", value: "public, max-age=31536000, immutable" }],
      },
    ];
  },
};

export default nextConfig;
