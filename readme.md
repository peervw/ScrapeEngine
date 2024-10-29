# caseAlpha ScrapeEngine API

## Overview

**ScrapeEngine API** is a robust and scalable web scraping service built with FastAPI. It leverages multiple scraper runners and proxies to perform efficient and authenticated scraping tasks. The API provides endpoints to initiate scraping, retrieve scraper and proxy data, and ensures secure access through token-based authentication. Additionally, it includes a proxy manager that continuously updates proxy lists from the Webshare API.

## Features

- **FastAPI Framework**: High-performance API built with FastAPI.
- **Concurrent Scraping**: Utilizes `ThreadPoolExecutor` for running multiple scrapers concurrently.
- **Token-Based Authentication**: Secure endpoints using API tokens.
- **Proxy Management**: Automatically fetches and updates proxies from the Webshare API.
- **Caching**: Implements caching for scraper and proxy data using `cachetools`.
- **Error Handling**: Comprehensive error handling and logging for reliable operations.
- **Configurable**: Easily configurable through environment variables.

## API Endpoints

### 1. Scrape Endpoint

- **URL:** `/api/scrape`
- **Method:** `GET`
- **Authentication:** Required (Token in `Authorization` header)
- **Description:** Initiates a scraping task for the provided URL.

**Request Headers:**

```http
Authorization: your_secure_api_token
Content-Type: application/json

**Request Body**
```json
{
"url": "https://example.com/article",
"link_or_article": "article",  // Optional: "link" or "article" (default: "article")
"other_params": {
// Additional parameters if needed
}
}

```