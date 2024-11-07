import pytest
from app.webshare_proxy import master_webshare_get_proxies
from unittest.mock import patch, mock_open

def test_webshare_proxy_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "proxy_address": "127.0.0.1",
                "port": "8080",
                "username": "user",
                "password": "pass"
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)
    
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        master_webshare_get_proxies()
    
    mock_file().write.assert_called_with("127.0.0.1:8080:user:pass\n")

def test_webshare_proxy_error(mocker):
    # Mock the requests.get to raise an exception
    mocker.patch("requests.get", side_effect=Exception("API Error"))
    
    # Call the function and verify it returns an empty list
    result = master_webshare_get_proxies()
    assert result == []