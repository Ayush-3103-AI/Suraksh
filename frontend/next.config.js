/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  // Fixed: Transpile ESM packages that Next.js can't handle by default
  transpilePackages: ['react-force-graph-3d'],
  // Fixed: Ensure proper chunk filename handling in dev mode
  experimental: {
    // Optimize package imports to reduce bundle size
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  // Fixed: Configure webpack to ensure chunks are properly named and accessible
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Fixed: Use named chunks in dev mode for better debugging and to prevent 404s
      config.optimization = {
        ...config.optimization,
        moduleIds: 'named',
        chunkIds: 'named',
      };
    }
    // Fixed: Ensure react-force-graph-3d ESM module is properly resolved
    config.resolve = {
      ...config.resolve,
      extensionAlias: {
        '.js': ['.js', '.ts', '.tsx'],
        '.mjs': ['.mjs', '.js'],
      },
    };
    return config;
  },
};

module.exports = nextConfig;

