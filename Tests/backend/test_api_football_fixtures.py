from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from app.services.api_football.fixtures import APIFootballFixtureService
from main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_fixture_service_normalization():
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "response": [
            {
                "fixture": {"id": 999, "date": "2026-05-01T15:00:00Z", "status": {"short": "NS"}},
                "league": {"id": 39, "name": "Premier League"},
                "teams": {
                    "home": {"id": 1, "name": "Arsenal", "winner": None},
                    "away": {"id": 2, "name": "Chelsea", "winner": None},
                },
                "goals": {"home": None, "away": None},
                "score": {},
            }
        ]
    }

    service = APIFootballFixtureService(client=mock_client)
    res = await service.get_fixtures(league=39, season=2025)

    assert res["results"] == 1
    assert res["fixtures"][0]["fixture_id"] == 999
    assert res["fixtures"][0]["home_team"]["name"] == "Arsenal"


def test_endpoint_fixtures_get():
    response = client.get("/api/v1/football/fixtures")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "fixtures" in data
    assert len(data["fixtures"]) > 0
    assert data["fixtures"][0]["fixture_id"] is not None
