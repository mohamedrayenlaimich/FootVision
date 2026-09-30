from unittest.mock import AsyncMock
import pytest

from app.services.football_data.matches import FootballMatchService


@pytest.mark.asyncio
async def test_match_service_get_matches_filters():
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "count": 2,
        "matches": [
            {"id": 1, "utcDate": "2026-01-01T15:00:00Z", "status": "FINISHED"},
            {"id": 2, "utcDate": "2026-01-02T15:00:00Z", "status": "FINISHED"},
        ],
    }

    service = FootballMatchService(client=mock_client)
    result = await service.get_matches(
        date_from="2026-01-01",
        date_to="2026-01-31",
        competition="PL",
        status="FINISHED",
    )

    mock_client.get.assert_called_once_with(
        "competitions/PL/matches",
        params={"dateFrom": "2026-01-01", "dateTo": "2026-01-31", "status": "FINISHED"},
    )
    assert result["count"] == 2
    assert len(result["matches"]) == 2


@pytest.mark.asyncio
async def test_match_service_pagination_limit_offset():
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "count": 5,
        "matches": [{"id": i} for i in range(1, 6)],
    }

    service = FootballMatchService(client=mock_client)
    result = await service.get_matches(limit=2, offset=1)

    assert len(result["matches"]) == 2
    assert result["matches"][0]["id"] == 2
    assert result["matches"][1]["id"] == 3
