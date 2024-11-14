# ScrapeEngine

A distributed web scraping service with proxy rotation and load balancing capabilities.

## Components

### Distributor
The central coordinator that:
- Manages a pool of runner nodes
- Handles proxy rotation and health checks
- Distributes scraping tasks across runners
- Provides API endpoints for scraping requests

### Runner
Worker nodes that:
- Register with the distributor
- Execute scraping tasks
- Support multiple scraping methods
- Handle proxy configuration

## Setup

1. Copy `.env.example` to `.env` and configure:
