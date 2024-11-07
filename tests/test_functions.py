import pytest
from app.functions import ProxyManager, import_proxies, scrape_url
from tenacity import RetryError

def test_proxy_manager_singleton():
    pm1 = ProxyManager()
    pm2 = ProxyManager()
    assert pm1 is pm2

def test_proxy_manager_initialization(tmp_path, mocker):
    proxy_file = tmp_path / "test_proxies.txt"
    proxy_file.write_text("127.0.0.1:8080:user:pass\n")
    mocker.patch("app.functions.PROXY_FILE", str(proxy_file))
    
    pm = ProxyManager()
    proxy = pm.get_next_proxy()
    assert proxy == ("127.0.0.1", "8080", "user", "pass")

@pytest.mark.asyncio
async def test_scrape_url_article(mock_proxy_manager, sample_html, mocker):
    mock_response = mocker.Mock()
    mock_response.text = sample_html
    mocker.patch("requests.get", return_value=mock_response)
    
    result = await scrape_url("https://example.com", "article")
    assert "title" in result
    assert "content" in result
    assert result["title"] == "Test Article"

@pytest.mark.asyncio
async def test_scrape_url_links(mock_proxy_manager, sample_html, mocker):
    mock_response = mocker.Mock()
    mock_response.text = sample_html
    mocker.patch("requests.get", return_value=mock_response)
    
    result = await scrape_url("https://example.com", "link")
    assert "links" in result
    assert len(result["links"]) == 2 