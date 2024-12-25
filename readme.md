# ScrapeEngine

An easily scalable, distributed web scraping platform with a modern Next.js frontend and a powerful FastAPI backend. The system features proxy rotation (from Webshare.io), multiple scraping methods, and an intuitive user interface for managing and monitoring scraping tasks.

## 🚀 Features

### Frontend
- **Modern UI/UX**: Built with Next.js and Tailwind CSS
- **Real-time Monitoring**: Live status updates for scraping tasks
- **Interactive Dashboard**: Manage scraping tasks and view results
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### Backend
- **Distributed Architecture**: Separate distributor and runner services
- **Multiple Scraping Methods**: 
  - Simple (aiohttp) for basic scraping
  - Advanced (Playwright) for JavaScript-heavy sites
- **Proxy Management** (using Webshare.io):
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
│   Frontend  │────▶│  Distributor │────▶│ Runner 1 │
└─────────────┘     │   Service    │     └──────────┘
                    │              │     ┌──────────┐
                    │              │────▶│ Runner 2 │
                    └──────────────┘     └──────────┘
                          │              ┌──────────┐
                          └─────────────▶│ Runner N │
                                         └──────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- Webshare.io API token for proxies

## 🛠️ Quick Start

1. Clone the repository:
```bash
git clone https://github.com/PeerZ0/ScrapeEngine.git
cd ScrapeEngine
```

2. Create `.env` file in the root directory:
```bash
WEBSHARE_TOKEN=your_webshare_token
```

3. Start the backend services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080

## 🔍 API Endpoints

### Distributor Service

**Base URL**: `http://localhost:8080` (you can also make requests to the frontend at `http://localhost:3000`, which will be proxied to the distributor. This way you only need to expose the frontend to the outside world)

#### Authentication
All protected endpoints require Bearer token authentication set in the frontend under settings:
```bash
Authorization: Bearer <AUTH_TOKEN>
```

#### Endpoints
| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/api/scrape` | POST | Submit a URL for scraping | Yes |
| `/api/runners/register` | POST | Register a new runner | Yes |
| `/health` | GET | Check service health | Yes |
| `/health/public` | GET | Public health check | No |
| `/api/debug/proxies` | GET | View proxy status | Yes |
| `/api/debug/runners` | GET | View runner status | Yes |
| `/api/debug/test-scrape` | GET | Test scraping functionality | Yes |
| `/api/runners/health` | GET | Get health status of all runners | Yes |
| `/api/metrics` | GET | Get system-wide metrics | Yes |
| `/api/events` | GET | Get recent system events | Yes |
| `/api/logs` | GET | Get scraping logs with pagination | Yes |
| `/api/settings` | GET | Get system settings | Yes |
| `/api/settings` | POST | Update system settings | Yes |
| `/api/settings/api-key` | GET | Get current API key | No |
| `/api/settings/api-key/regenerate` | POST | Generate new API key | No |

#### Scrape Endpoint
`POST /api/scrape`

Submit a URL for scraping with customizable options.

**Request Body:**
```json
{
    "url": "https://example.com",
    "stealth": true,
    "render": true,
    "parse": true
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "stealth": false,
  "render": false,
  "parse": true,
  "proxy_used": ip:port,
  "runner_used": "runner-439346e9575e",
  "method_used": "aiohttp",
  "response_time": 1.263829,
  "content": {
    "raw_content": "<!doctype html>\n<html>\n<head>\n    <title>Example Domain</title>\n\n    <meta charset=\"utf-8\" />\n    <meta http-equiv=\"Content-type\" content=\"text/html; charset=utf-8\" />\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n    <style type=\"text/css\">\n    body {\n        background-color: #f0f0f2;\n        margin: 0;\n        padding: 0;\n        font-family: -apple-system, system-ui, BlinkMacSystemFont, \"Segoe UI\", \"Open Sans\", \"Helvetica Neue\", Helvetica, Arial, sans-serif;\n        \n    }\n    div {\n        width: 600px;\n        margin: 5em auto;\n        padding: 2em;\n        background-color: #fdfdff;\n        border-radius: 0.5em;\n        box-shadow: 2px 3px 7px 2px rgba(0,0,0,0.02);\n    }\n    a:link, a:visited {\n        color: #38488f;\n        text-decoration: none;\n    }\n    @media (max-width: 700px) {\n        div {\n            margin: 0 auto;\n            width: auto;\n        }\n    }\n    </style>    \n</head>\n\n<body>\n<div>\n    <h1>Example Domain</h1>\n    <p>This domain is for use in illustrative examples in documents. You may use this\n    domain in literature without prior coordination or asking for permission.</p>\n    <p><a href=\"https://www.iana.org/domains/example\">More information...</a></p>\n</div>\n</body>\n</html>\n",
    "text_content": "Example Domain Example Domain This domain is for use in illustrative examples in documents. You may use this\n    domain in literature without prior coordination or asking for permission. More information...",
    "title": "Example Domain",
    "links": [
      {
        "href": "https://www.iana.org/domains/example",
        "text": "More information..."
      }
    ],
    "parse_error": null
  }
}
```

### Key Environment Variables

- `WEBSHARE_TOKEN`: Webshare.io API token

## Development

### Project Structure

```
├── Frontend/
│   ├── app/
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   ├── public/
│   └── package.json
├── Distributor/
│   ├── app/
│   │   ├── migrations/     # Database migrations
│   │   ├── services/
│   │   ├── config/
│   │   ├── models.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── Runner/
│   ├── app/
│   │   ├── services/
│   │   ├── config/
│   │   ├── models.py
│   │   └── main.py
│   └── Dockerfile
├── docker-compose.yml
├── init-db.sh             # Database initialization script
├── pg_hba.conf           # PostgreSQL host-based authentication config
└── .env.example          # Environment variables template
```

### Database Setup

The system uses PostgreSQL for data persistence. Initial setup is handled by:
1. Database initialization script (`init-db.sh`)
2. PostgreSQL authentication configuration (`pg_hba.conf`)
3. Automatic migrations in the Distributor service

## Monitoring

The system provides multiple ways to monitor your scraping operations:

### Frontend Dashboard
- Real-time task status monitoring
- Proxy performance metrics
- Runner status overview
- Task history and results

### API Endpoints
- Monitor service health via `/health` endpoints
- Check proxy status and available proxies via `/api/debug/proxies`
- View runner status and registered runners via `/api/debug/runners`

## Error Handling

The system includes:
- Frontend error boundaries and fallbacks
- Automatic retry mechanisms for failed requests
- Proxy rotation on failures
- Runner health monitoring
- Detailed logging and error reporting
