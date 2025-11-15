import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: "standalone",

  // React Compiler 활성화 (자동 메모이제이션)
  reactCompiler: true,

  // Disable TypeScript and ESLint checks during build (optional)
  // typescript: {
  //   ignoreBuildErrors: false,
  // },
  // eslint: {
  //   ignoreDuringBuilds: false,
  // },
};

export default nextConfig;
