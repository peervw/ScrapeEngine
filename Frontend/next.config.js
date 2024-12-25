/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    const internalUrl = process.env.INTERNAL_API_URL || 'http://distributor:8080';
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