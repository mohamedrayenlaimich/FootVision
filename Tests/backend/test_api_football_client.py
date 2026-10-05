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

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(APIFootballTimeoutError):
            await client.get("fixtures")


@pytest.mark.asyncio
async def test_client_caches_identical_requests():
    client = APIFootballClient(api_key="test_key_xyz")
    mock_resp = httpx.Response(200, json={"errors": [], "results": 0, "response": []})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp) as mocked:
        await client.get("fixtures", {"live": "all"})
        await client.get("fixtures", {"live": "all"})
        assert mocked.await_count == 1


@pytest.mark.asyncio
async def test_client_retries_transient_errors_then_succeeds():
    client = APIFootballClient(api_key="test_key_xyz")
    ok = httpx.Response(200, json={"errors": [], "results": 0, "response": []})

    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=[httpx.TimeoutException("t"), ok],
    ) as mocked, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await client.get("fixtures")
        assert res["results"] == 0
        assert mocked.await_count == 2


@pytest.mark.asyncio
async def test_client_does_not_retry_auth_errors():
    client = APIFootballClient(api_key="bad")
    resp = httpx.Response(401, json={})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=resp) as mocked:
        with pytest.raises(APIFootballAuthError):
            await client.get("fixtures")
        assert mocked.await_count == 1
