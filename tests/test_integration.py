import pytest
from fastapi import status
from app.main import app

@pytest.mark.integration
def test_full_scrape_flow(client, auth_headers):
    # Test the entire flow from request to response
    url = "https://example.com"
    response = client.post(
        "/api/scrape",
        json={"url": url, "link_or_article": "article"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert any(key in data for key in ["title", "content", "links"])

@pytest.mark.integration
def test_proxy_rotation(client, auth_headers):
    # Test that proxies are properly rotated
    responses = []
    for _ in range(3):
        response = client.post(
            "/api/scrape",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        responses.append(response)
    
    assert all(r.status_code == status.HTTP_200_OK for r in responses) 