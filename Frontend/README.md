# Scraper Dashboard

A modern web dashboard for monitoring and managing your distributed web scraping system built with Next.js and shadcn/ui.

## Features

- **Real-time Monitoring**: Live updates of jobs, runners, and system health
- **Job Management**: View, pause, resume, and stop scraping jobs
- **Runner Status**: Monitor the health and performance of your scraping runners
- **Performance Analytics**: Charts and metrics for system performance
- **System Health**: Comprehensive health monitoring with alerts
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Dashboard Sections

### Overview
- System statistics and quick metrics
- Recent activity feed
- Success rates and performance indicators

### Jobs
- List all scraping jobs with their current status
- Monitor progress and estimated completion times
- Control job execution (pause, resume, stop)
- Download completed results

### Runners
- View all connected runner instances
- Monitor CPU, memory, and network usage
- Restart or stop individual runners
- Check connection status and version info

### Performance
- Real-time charts showing job and page metrics
- Response time analytics
- Success rate trends
- Error distribution

### Health
- Overall system status
- Individual component health metrics
- Active alerts and warnings
- Uptime statistics

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Start the development server
npm run dev

# Open http://localhost:3000 in your browser
```

### Production (Docker)

The dashboard is designed to run in Docker alongside your scraper services:

```bash
# Build and run with docker-compose
docker-compose up -d frontend

# The dashboard will be available at http://localhost:3000
```

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL`: URL of the distributor service API (default: http://localhost:8080)
- `NODE_ENV`: Environment mode (development/production)

### API Integration

The dashboard automatically connects to your distributor service using the configured API URL. It will:

- Fetch real-time data from the `/api/jobs`, `/api/runners`, and `/api/stats` endpoints
- Fall back to mock data if the API is unavailable
- Automatically retry failed requests
- Refresh data at appropriate intervals

## Architecture

```
Frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   ├── components/
│   │   ├── dashboard/       # Dashboard-specific components
│   │   └── ui/             # shadcn/ui components
│   ├── hooks/              # Custom React hooks for API calls
│   └── lib/                # Utility functions and API client
├── public/                 # Static assets
└── Dockerfile             # Container configuration
```

## API Endpoints Expected

The dashboard expects the following endpoints from your distributor service:

- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get specific job details
- `POST /api/jobs/{id}/pause` - Pause a job
- `POST /api/jobs/{id}/resume` - Resume a job
- `POST /api/jobs/{id}/stop` - Stop a job
- `GET /api/runners` - List all runners
- `GET /api/runners/{id}` - Get specific runner details
- `POST /api/runners/{id}/restart` - Restart a runner
- `POST /api/runners/{id}/stop` - Stop a runner
- `GET /api/stats` - Get system statistics
- `GET /health/public` - Health check endpoint

## Contributing

This dashboard is part of the ScrapeEngine project. When adding new features:

1. Follow the existing component structure
2. Use shadcn/ui components for consistency
3. Add proper TypeScript types
4. Include error handling and loading states
5. Update this README if needed

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Recharts** - Charts and data visualization
- **Lucide React** - Icons
