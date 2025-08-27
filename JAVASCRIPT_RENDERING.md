# JavaScript Rendering Example

This document shows how to use the new JavaScript rendering feature in ScrapeEngine.

## API Usage Examples

### Static Content Scraping (aiohttp method)
Use this for fast scraping of static HTML content:

```bash
curl -X POST "http://localhost:8080/api/scrape" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "method": "aiohttp",
    "full_content": true,
    "stealth": true,
    "cache": true
  }'
```

### JavaScript Rendered Content (playwright method)
Use this for sites with dynamic JavaScript content:

```bash
curl -X POST "http://localhost:8080/api/scrape" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://spa-example.com",
    "method": "playwright",
    "full_content": true,
    "stealth": true,
    "cache": true
  }'
```

## Key Differences

| Method | Speed | JavaScript Support | Use Case |
|--------|-------|-------------------|----------|
| aiohttp | Fast | ❌ No | Static websites, APIs, simple pages |
| playwright | Slower | ✅ Yes | SPAs, JavaScript-heavy sites, dynamic content |

## When to Use Playwright

✅ **Use playwright when:**
- Site content is loaded dynamically with JavaScript
- You need the final rendered HTML after JS execution
- Working with Single Page Applications (SPAs)
- Content appears after AJAX calls or user interactions

❌ **Don't use playwright when:**
- Site content is static HTML
- Speed is critical and no JS rendering needed
- Working with APIs or simple data endpoints

## Response Format

Both methods return the same response format:

```json
{
  "url": "https://example.com",
  "method": "playwright",
  "full_content": true,
  "stealth": true,
  "cache": true,
  "parse": true,
  "proxy_used": "proxy.example.com:8080",
  "runner_used": "runner-123",
  "content": {
    "status": "success",
    "method": "playwright",
    "html": "<html>...rendered content...</html>",
    "title": "Page Title After JS Execution",
    "text_content": "Extracted text content...",
    "links": [...],
    "scrape_time": 2.34,
    "proxy_used": "proxy.example.com:8080"
  }
}
```

The key difference is that playwright returns the **final rendered HTML** after JavaScript execution, while aiohttp returns the **original HTML source**.