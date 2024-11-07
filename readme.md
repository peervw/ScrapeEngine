# CaseAlpha ScrapeEngine

A robust, scalable web scraping service built with FastAPI, featuring proxy rotation, rate limiting, and caching capabilities.

## 🚀 Features

- **High Performance Scraping**: Asynchronous scraping with automatic retries
- **Proxy Management**: Automatic proxy rotation and management
- **Rate Limiting**: Built-in rate limiting to prevent overloading
- **Caching**: Intelligent caching system to minimize redundant requests
- **API Authentication**: Secure endpoint access with token authentication
- **Error Handling**: Comprehensive error handling and logging
- **Input Validation**: Request validation using Pydantic models

## 📋 Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/casealpha-scrapeengine.git
cd casealpha-scrapeengine
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Update the `.env` file with your configuration:
```env
AUTH_TOKEN=your_auth_token
WEBSHARE_TOKEN=your_webshare_token
MAX_WORKERS=4
HOST=0.0.0.0
PORT=8080
```

## 🚀 Running the Application

### Development
```bash
uvicorn app.main:app --reload
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

## 🔍 API Documentation

Once the application is running, access the API documentation at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### Basic Usage

```python
import requests

headers = {
    "Authorization": "your_auth_token"
}

payload = {
    "url": "https://example.com",
    "link_or_article": "article"
}

response = requests.post(
    "http://localhost:8080/api/scrape",
    json=payload,
    headers=headers
)

print(response.json())
```

## 🧪 Testing

Run the test suite:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## 📁 Project Structure

```
casealpha-scrapeengine/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── functions.py
│   └── static/
│       └── proxies.txt
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main.py
│   └── test_functions.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

## 🔒 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| AUTH_TOKEN | Authentication token for API access | - |
| WEBSHARE_TOKEN | Token for proxy service | - |
| MAX_WORKERS | Number of worker processes | 4 |
| HOST | Host address | 0.0.0.0 |
| PORT | Port number | 8080 |

## 🛡️ Error Handling

The API uses standard HTTP status codes:

- 200: Successful request
- 401: Unauthorized
- 422: Validation error
- 429: Too many requests
- 500: Internal server error

## 🔧 Development

1. Copy the development environment file:
```bash
cp .env.example .env.development
```

2. Update the development environment variables in `.env.development`

3. Run in development mode:
```bash
python scripts/dev.py
```

## 🚀 Production

1. Set up production environment variables:
```bash
# Using actual environment variables
export AUTH_TOKEN=your_token
export WEBSHARE_TOKEN=your_webshare_token

# Or copy and edit production env file
cp .env.example .env.production
```

2. Run in production mode:
```bash
ENV=production uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## 🐳 Docker

Development:
```bash
docker-compose up
```

Production:
```bash
docker build -t scrapeengine .
docker run -p 8080:8080 \
  -e AUTH_TOKEN=your_token \
  -e WEBSHARE_TOKEN=your_webshare_token \
  scrapeengine
```