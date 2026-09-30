from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.services.api_football.client import (
    APIFootballAuthError,
    APIFootballClient,
    APIFootballError,
    APIFootballRateLimitError,
    APIFootballTimeoutError,
)


@pytest.mark.asyncio
async def test_client_headers_initialization():
    client = APIFootballClient(api_key="test_key_xyz", base_url="https://v3.football.api-sports.io")
    headers = client._get_headers()
    assert headers["x-apisports-key"] == "test_key_xyz"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_client_get_success():
    client = APIFootballClient(api_key="test_key_xyz")
    mock_payload = {
        "get": "fixtures",
        "errors": [],
        "results": 1,
        "response": [{"fixture": {"id": 123456}}],
    }
    mock_resp = httpx.Response(200, json=mock_payload)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        res = await client.get("fixtures")
        assert res["results"] == 1
        assert res["response"][0]["fixture"]["id"] == 123456


@pytest.mark.asyncio
async def test_client_api_error_response():
    client = APIFootballClient(api_key="test_key_xyz")
    mock_payload = {
        "errors": {"token": "Error/Unauthorized API Key"}
    }
    mock_resp = httpx.Response(200, json=mock_payload)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        with pytest.raises(APIFootballAuthError):
            await client.get("fixtures")


@pytest.mark.asyncio
async def test_client_timeout():
    client = APIFootballClient(api_key="test_key_xyz")

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(APIFootballTimeoutError):
            await client.get("fixtures")
