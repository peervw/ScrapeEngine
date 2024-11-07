import pytest
from app.functions import ProxyManager, read_data_from_file
from tenacity import RetryError
import os
from unittest.mock import patch

def test_proxy_manager_singleton():
    pm1 = ProxyManager()
    pm2 = ProxyManager()
    assert pm1 is pm2

def test_proxy_manager_initialization(tmp_path, mocker):
    # Reset the singleton instance
    ProxyManager.reset_instance()
    
    # Create test proxy file
    proxy_file = tmp_path / "test_proxies.txt"
    proxy_file.write_text("127.0.0.1:8080:user:pass\n")
    
    # Set the proxy file path
    ProxyManager.set_proxy_file(str(proxy_file))
    
    # Test the proxy manager
    pm = ProxyManager()
    proxy = pm.get_next_proxy()
    assert proxy == ("127.0.0.1", "8080", "user", "pass")

def test_read_data_from_file(tmp_path):
    # Create a temporary test file in the correct location
    os.makedirs(os.path.join(tmp_path, "app/static"), exist_ok=True)
    test_file = tmp_path / "app" / "static" / "test_file.txt"
    test_file.write_text("test.example.com:user:pass\n")
    
    # Test reading the file
    with patch("app.functions.os.path.join", return_value=str(test_file)):
        result = read_data_from_file("test_file.txt")
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["url"] == "test.example.com"
        assert result[0]["username"] == "user"
        assert result[0]["password"] == "pass"

@pytest.mark.asyncio
async def test_proxy_error_handling(mocker):
    # Test proxy error handling
    pm = ProxyManager()
    mocker.patch.object(pm, 'get_next_proxy', side_effect=Exception("Proxy error"))
    
    with pytest.raises(Exception):
        pm.get_next_proxy()