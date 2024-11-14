# Web Scraping Distributed System

A scalable, distributed web scraping system built with FastAPI and Docker, featuring proxy rotation and multiple scraping methods.

## Features

- **Distributed Architecture**: Separate distributor and runner services
- **Multiple Scraping Methods**: 
  - Simple (aiohttp) for basic scraping
  - Advanced (Playwright) for JavaScript-heavy sites
- **Proxy Management**:
  - Automatic proxy rotation
  - Health monitoring
  - Success rate tracking
- **Stealth Features**:
  - Browser fingerprint randomization
  - Header rotation
  - User agent spoofing
- **Health Monitoring**:
  - Service health checks
  - Runner registration system
  - Proxy performance tracking

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│   Client    │────▶│  Distributor │────▶│ Runner 1 │
└─────────────┘     │   Service    │     └──────────┘
                    │              │     ┌──────────┐
                    │              │────▶│ Runner 2 │
                    └──────────────┘     └──────────┘
                          │             ┌──────────┐
                          └────────────▶│ Runner N │
                                       └──────────┘
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Webshare.io API token for proxies

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd web-scraping-system
```

2. Create `.env` file:
```bash
WEBSHARE_TOKEN=your_webshare_token
AUTH_TOKEN=your_auth_token
DEBUG=false
```

3. Start the services:
```bash
docker-compose up -d
```

## API Endpoints

### Distributor Service

**Base URL**: `http://localhost:8080`

#### Authentication
All protected endpoints require Bearer token authentication:
```bash
Authorization: Bearer <AUTH_TOKEN>
```

#### Endpoints

- **POST** `/api/scrape`
  - Initiates a scraping task
  - Request body:
```json
{
    "url": "https://example.com",
    "full_content": "yes",
    "stealth": true,
    "cache": true
}
```

- **GET** `/health/public`
  - Public health check endpoint

- **GET** `/api/debug/proxies`
  - View proxy status (protected)

- **GET** `/api/debug/runners`
  - View runner status (protected)

### Runner Service

**Base URL**: `http://localhost:8000`

- **POST** `/scrape`
  - Internal endpoint for scraping tasks
- **GET** `/health`
  - Health check endpoint

## Configuration

### Environment Variables

- `WEBSHARE_TOKEN`: Webshare.io API token
- `AUTH_TOKEN`: Authentication token for API access
- `DEBUG`: Enable debug logging (true/false)
- `DISTRIBUTOR_URL`: URL for distributor service
- `RUNNER_ID`: Unique ID for runner instances

### Docker Compose Configuration

The system uses Docker Compose for orchestration. Key configurations:

```yaml
services:
  distributor:
    ports:
      - "8080:8080"
    environment:
      - PYTHONUNBUFFERED=1
    
  runner:
    environment:
      - PYTHONUNBUFFERED=1
      - RUNNER_ID=runner-${HOSTNAME:-runner}
      - DISTRIBUTOR_URL=http://distributor:8080
```

## Development

### Project Structure

```
├── Distributor/
│   ├── app/
│   │   ├── services/
│   │   ├── config/
│   │   └── models.py
│   └── Dockerfile
├── Runner/
│   ├── app/
│   │   ├── services/
│   │   ├── config/
│   │   └── models.py
│   └── Dockerfile
└── docker-compose.yml
```

### Adding New Runners

The system automatically scales with additional runner instances. To add more runners:

```bash
docker-compose up -d --scale runner=3
```

## Monitoring

- Monitor service health via `/health` endpoints
- Check proxy status via `/api/debug/proxies`
- View runner status via `/api/debug/runners`

## Error Handling

The system includes:
- Automatic retry mechanisms for failed requests
- Proxy rotation on failures
- Runner health monitoring
- Detailed logging
