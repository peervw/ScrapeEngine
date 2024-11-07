import pytest
from fastapi import status
from app.main import app

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

def test_unauthorized_access(client):
    response = client.post("/api/scrape", json={"url": "https://example.com"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_scrape_endpoint_success(async_client, auth_headers, mocker):
    test_data = {"title": "Test Article", "content": "Test content"}
    mocker.patch("app.main.scrape_url", return_value=test_data)
    
    response = await async_client.post(
        "/api/scrape",
        json={"url": "https://example.com", "link_or_article": "article"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == test_data

def test_invalid_url_format(client, auth_headers):
    response = client.post(
        "/api/scrape",
        json={"url": "not-a-valid-url"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 