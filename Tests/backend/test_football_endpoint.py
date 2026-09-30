from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from app.services.football_data.client import FootballDataAuthError, FootballDataRateLimitError
from main import app

client = TestClient(app)


def test_endpoint_matches_success():
    mock_matches = {
        "count": 1,
        "matches": [
            {
                "id": 123,
                "utcDate": "2026-01-15T19:00:00Z",
                "status": "FINISHED",
                "competition": {"id": 2021, "name": "Premier League", "code": "PL"},
                "homeTeam": {"id": 1, "name": "Arsenal"},
                "awayTeam": {"id": 2, "name": "Chelsea"},
                "score": {
                    "winner": "HOME_TEAM",
                    "fullTime": {"home": 2, "away": 1},
                },
            }
        ],
    }

    with patch("app.api.v1.endpoints.football.match_service.get_matches", new_callable=AsyncMock, return_value=mock_matches):
        response = client.get("/api/v1/football/matches?dateFrom=2026-01-01&dateTo=2026-01-31")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["matches"][0]["homeTeam"]["name"] == "Arsenal"
        assert data["matches"][0]["score"]["fullTime"]["home"] == 2


def test_endpoint_auth_error_handling():
    with patch(
        "app.api.v1.endpoints.football.match_service.get_matches",
        new_callable=AsyncMock,
        side_effect=FootballDataAuthError("Invalid Token", status_code=401),
    ):
        response = client.get("/api/v1/football/matches")
        assert response.status_code == 401
        assert "Authentication failed" in response.json()["detail"]


def test_endpoint_rate_limit_handling():
    with patch(
        "app.api.v1.endpoints.football.match_service.get_matches",
        new_callable=AsyncMock,
        side_effect=FootballDataRateLimitError("Rate limit", status_code=429),
    ):
        response = client.get("/api/v1/football/matches")
        assert response.status_code == 429
        assert "rate limit exceeded" in response.json()["detail"].lower()
