/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for S3 + CloudFront deployment
  output: "export",

  // Trailing slashes ensure S3 resolves /login → /login/index.html
  trailingSlash: true,

  // Disable image optimisation (not supported in static export; use plain <img>)
  images: {
    unoptimized: true,
  },

  // Strip unused JS — important for Lambda@Edge budget
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
};

export default nextConfig;
