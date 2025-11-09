import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',

  // Disable TypeScript and ESLint checks during build (optional)
  // typescript: {
  //   ignoreBuildErrors: false,
  // },
  // eslint: {
  //   ignoreDuringBuilds: false,
  // },
};

export default nextConfig;
