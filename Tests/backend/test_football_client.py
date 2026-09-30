from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.services.football_data.client import (
    FootballDataAPIError,
    FootballDataAuthError,
    FootballDataClient,
    FootballDataNotFoundError,
    FootballDataRateLimitError,
    FootballDataTimeoutError,
)


@pytest.mark.asyncio
async def test_client_headers_and_initialization():
    client = FootballDataClient(api_key="test_key_123", base_url="https://api.football-data.org/v4")
    headers = client._get_headers()
    assert headers["X-Auth-Token"] == "test_key_123"
    assert headers["Content-Type"] == "application/json"
    assert client.base_url == "https://api.football-data.org/v4"


@pytest.mark.asyncio
async def test_client_get_success():
    client = FootballDataClient(api_key="test_key_123")
    mock_response = httpx.Response(200, json={"matches": [{"id": 101, "status": "FINISHED"}]})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        data = await client.get("matches")
        assert "matches" in data
        assert data["matches"][0]["id"] == 101


@pytest.mark.asyncio
async def test_client_auth_error():
    client = FootballDataClient(api_key="invalid_key")
    mock_response = httpx.Response(401, json={"message": "Your API token is invalid."})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(FootballDataAuthError) as exc_info:
            await client.get("matches")
        assert "Authentication failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_rate_limit():
    client = FootballDataClient(api_key="test_key")
    mock_response = httpx.Response(429, json={"message": "Rate limit exceeded"})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(FootballDataRateLimitError):
            await client.get("matches")


@pytest.mark.asyncio
async def test_client_timeout():
    client = FootballDataClient(api_key="test_key")

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(FootballDataTimeoutError):
            await client.get("matches")
