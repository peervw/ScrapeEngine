import pytest
from fastapi import status

@pytest.mark.integration
async def test_full_scrape_flow(async_client, auth_headers):
    url = "https://example.com"
    response = await async_client.post(
        "/api/scrape",
        json={"url": url, "link_or_article": "article"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)

@pytest.mark.integration
async def test_proxy_rotation(async_client, auth_headers):
    responses = []
    for _ in range(2):
        response = await async_client.post(
            "/api/scrape",
            json={"url": "https://example.com"},
            headers=auth_headers
        )
        responses.append(response)
    
    assert all(r.status_code == status.HTTP_200_OK for r in responses)