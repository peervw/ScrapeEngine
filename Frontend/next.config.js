/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
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