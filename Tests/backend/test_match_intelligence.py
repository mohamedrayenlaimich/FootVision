from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_match_details():
    res = client.get("/api/v1/football/matches/123456")
    assert res.status_code == 200
    data = res.json()
    assert "fixture" in data
    assert data["fixture"]["fixture_id"] == 123456


def test_get_match_statistics():
    res = client.get("/api/v1/football/matches/123456/statistics")
    assert res.status_code == 200
    data = res.json()
    assert "teams" in data
    assert len(data["teams"]) == 2


def test_get_match_events():
    res = client.get("/api/v1/football/matches/123456/events")
    assert res.status_code == 200
    data = res.json()
    assert "events" in data


def test_get_match_lineups():
    res = client.get("/api/v1/football/matches/123456/lineups")
    assert res.status_code == 200
    data = res.json()
    assert "lineups" in data


def test_get_match_players():
    res = client.get("/api/v1/football/matches/123456/players")
    assert res.status_code == 200
    data = res.json()
    assert "teams" in data


def test_get_match_head_to_head():
    res = client.get("/api/v1/football/matches/123456/head-to-head")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data


def test_get_match_predictions():
    res = client.get("/api/v1/football/matches/123456/predictions")
    assert res.status_code == 200
    data = res.json()
    assert "external_api_prediction" in data
    assert "footvision_prediction" in data
    assert data["footvision_prediction"]["expected_goals"]["total"] > 0
