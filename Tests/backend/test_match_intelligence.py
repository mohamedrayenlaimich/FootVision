from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

MOCK_FIXTURE_RESPONSE = {
    "results": 1,
    "fixtures": [
        {
            "fixture_id": 123456,
            "date": "2026-03-22T20:00:00Z",
            "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
            "venue": {"id": 556, "name": "Camp Nou", "city": "Barcelona"},
            "league": {"id": 140, "name": "La Liga", "season": 2025},
            "home_team": {"id": 529, "name": "FC Barcelona", "winner": True},
            "away_team": {"id": 541, "name": "Real Madrid", "winner": False},
            "goals": {"home": 2, "away": 1},
            "score": {"fulltime": {"home": 2, "away": 1}},
        }
    ],
}


def test_get_match_details():
    with patch("app.api.v1.endpoints.fixtures.fixture_service.get_fixtures", new_callable=AsyncMock, return_value=MOCK_FIXTURE_RESPONSE):
        res = client.get("/api/v1/football/matches/123456")
        assert res.status_code == 200
        data = res.json()
        assert "fixture" in data
        assert data["fixture"]["fixture_id"] == 123456


def test_get_match_statistics():
    mock_stats = {"fixture_id": 123456, "teams": [{"team": {"id": 1}, "statistics": []}, {"team": {"id": 2}, "statistics": []}]}
    with patch("app.api.v1.endpoints.fixtures.stats_service.get_fixture_statistics", new_callable=AsyncMock, return_value=mock_stats):
        res = client.get("/api/v1/football/matches/123456/statistics")
        assert res.status_code == 200
        data = res.json()
        assert "teams" in data
        assert len(data["teams"]) == 2


def test_get_match_events():
    mock_events = {"fixture_id": 123456, "events": []}
    with patch("app.api.v1.endpoints.fixtures.events_service.get_fixture_events", new_callable=AsyncMock, return_value=mock_events):
        res = client.get("/api/v1/football/matches/123456/events")
        assert res.status_code == 200
        data = res.json()
        assert "events" in data


def test_get_match_lineups():
    mock_lineups = {"fixture_id": 123456, "lineups": []}
    with patch("app.api.v1.endpoints.fixtures.lineups_service.get_fixture_lineups", new_callable=AsyncMock, return_value=mock_lineups):
        res = client.get("/api/v1/football/matches/123456/lineups")
        assert res.status_code == 200
        data = res.json()
        assert "lineups" in data


def test_get_match_players():
    mock_players = {"fixture_id": 123456, "teams": []}
    with patch("app.api.v1.endpoints.fixtures.players_service.get_fixture_players", new_callable=AsyncMock, return_value=mock_players):
        res = client.get("/api/v1/football/matches/123456/players")
        assert res.status_code == 200
        data = res.json()
        assert "teams" in data


def test_get_match_head_to_head():
    mock_h2h = {"available": True, "total_meetings": 5, "summary": {"team1_wins": 3, "draws": 1, "team2_wins": 1}}
    with patch("app.api.v1.endpoints.fixtures.h2h_service.get_head_to_head", new_callable=AsyncMock, return_value=mock_h2h):
        res = client.get("/api/v1/football/matches/123456/head-to-head")
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data


def test_get_match_predictions():
    with patch("app.api.v1.endpoints.fixtures.fixture_service.get_fixtures", new_callable=AsyncMock, return_value=MOCK_FIXTURE_RESPONSE):
        mock_ext_pred = {"win_probability": {"home": 50, "draw": 30, "away": 20}}
        with patch("app.api.v1.endpoints.fixtures.ext_predictions_service.get_fixture_prediction", new_callable=AsyncMock, return_value=mock_ext_pred):
            res = client.get("/api/v1/football/matches/123456/predictions")
            assert res.status_code == 200
            data = res.json()
            assert "external_api_prediction" in data
            assert "footvision_prediction" in data
            assert "probabilities" in data["footvision_prediction"]




