import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os
from app.main import app
from app.config import Settings, get_settings
from app.functions import ProxyManager

@pytest.fixture
def test_settings():
    return Settings(
        AUTH_TOKEN="test_token",
        WEBSHARE_TOKEN="test_webshare_token",
        MAX_WORKERS=2,
        ENV="test"
    )

@pytest.fixture
def app_with_test_settings(test_settings):
    app.dependency_overrides[get_settings] = lambda: test_settings
    return app

@pytest.fixture
def client(app_with_test_settings):
    return TestClient(app_with_test_settings)

@pytest.fixture
async def async_client(app_with_test_settings):
    async with AsyncClient(app=app_with_test_settings, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_proxy_manager(mocker):
    mock_proxy = ProxyManager()
    mock_proxy.get_next_proxy = mocker.Mock(
        return_value=("127.0.0.1", "8080", "user", "pass")
    )
    return mock_proxy

@pytest.fixture
def auth_headers(test_settings):
    return {"Authorization": test_settings.AUTH_TOKEN}

@pytest.fixture
def sample_html():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>Test content</p>
            </article>
            <a href="https://example.com/1">Link 1</a>
            <a href="https://example.com/2">Link 2</a>
        </body>
    </html>
    """ 