/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  output: 'standalone',
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: true,
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  // Optimize build speed
  swcMinify: true, // Use SWC for minification (faster than Terser)
  compiler: {
    // Disable React runtime checks in production
    removeConsole: process.env.NODE_ENV === 'production',
  },
  experimental: {
    // Enable parallel routes building
    parallelRoutes: true,
    // Optimize packages
    optimizePackageImports: ['@/components'],
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    };

    // Optimize build performance
    config.optimization = {
      ...config.optimization,
      moduleIds: 'deterministic',
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // Vendor chunk
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // Common chunk
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
        },
      },
    };

    return config;
  },
  async rewrites() {
    const internalUrl = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8080'  // Use local URL in development
      : (process.env.INTERNAL_API_URL || 'http://distributor:8080');
    
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: `${internalUrl}/api/:path*`,
          has: [
            {
              type: 'query',
              key: 'limit',
              value: undefined,
            },
          ],
        },
        {
          source: '/api/:path*',
          destination: `${internalUrl}/api/:path*`,
        },
      ],
    };
  },
}

module.exports = nextConfig 