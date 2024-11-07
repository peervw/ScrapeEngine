import pytest
from fastapi import status

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check that all required fields are present
    assert "status" in data
    assert "version" in data
    assert "uptime" in data
    assert "proxy_count" in data
    assert "scraper_count" in data
    
    # Check specific values we can predict
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert isinstance(data["uptime"], (int, float))
    assert isinstance(data["proxy_count"], int)
    assert isinstance(data["scraper_count"], int)

def test_unauthorized_access(client):
    response = client.post("/api/scrape", json={"url": "https://example.com"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_scrape_endpoint_success(client, auth_headers, mocker):
    # Mock the scrape function to return a valid response
    mock_response = {
        "status": "success",
        "data": "<html></html>",
        "url": "https://example.com",
        "timestamp": 1234567890,
        "used_scraper": {"url": "test.example.com"},
        "used_proxy": ("127.0.0.1", "8080", "user", "pass")
    }
    mocker.patch('app.functions.scrape', return_value=mock_response)

    response = client.post(
        "/api/scrape",
        json={
            "url": "https://example.com",
            "link_or_article": "article"
        },
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

def test_invalid_url_format(client, auth_headers):
    response = client.post(
        "/api/scrape",
        json={"url": "not-a-valid-url"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY