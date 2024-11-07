import pytest
from fastapi import status

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

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