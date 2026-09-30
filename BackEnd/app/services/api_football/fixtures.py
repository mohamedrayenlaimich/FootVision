import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient, APIFootballAuthError

logger = logging.getLogger(__name__)

MOCK_FIXTURES: List[Dict[str, Any]] = [
    {
        "fixture_id": 123456,
        "date": "2026-03-22T20:00:00Z",
        "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
        "venue": {"id": 556, "name": "Spotify Camp Nou", "city": "Barcelona"},
        "league": {
            "id": 140,
            "name": "La Liga",
            "country": "Spain",
            "logo": "https://media.api-sports.io/football/leagues/140.png",
            "flag": "https://media.api-sports.io/flags/es.svg",
            "season": 2025,
            "round": "Regular Season - 28",
        },
        "home_team": {
            "id": 529,
            "name": "FC Barcelona",
            "logo": "https://media.api-sports.io/football/teams/529.png",
            "winner": True,
        },
        "away_team": {
            "id": 541,
            "name": "Real Madrid",
            "logo": "https://media.api-sports.io/football/teams/541.png",
            "winner": False,
        },
        "goals": {"home": 2, "away": 1},
        "score": {
            "halftime": {"home": 1, "away": 0},
            "fulltime": {"home": 2, "away": 1},
            "extratime": {"home": None, "away": None},
            "penalty": {"home": None, "away": None},
        },
    },
    {
        "fixture_id": 123457,
        "date": "2026-03-29T16:30:00Z",
        "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
        "venue": {"id": 504, "name": "Emirates Stadium", "city": "London"},
        "league": {
            "id": 39,
            "name": "Premier League",
            "country": "England",
            "logo": "https://media.api-sports.io/football/leagues/39.png",
            "flag": "https://media.api-sports.io/flags/gb.svg",
            "season": 2025,
            "round": "Regular Season - 29",
        },
        "home_team": {
            "id": 42,
            "name": "Arsenal",
            "logo": "https://media.api-sports.io/football/teams/42.png",
            "winner": True,
        },
        "away_team": {
            "id": 49,
            "name": "Chelsea",
            "logo": "https://media.api-sports.io/football/teams/49.png",
            "winner": False,
        },
        "goals": {"home": 3, "away": 1},
        "score": {
            "halftime": {"home": 2, "away": 0},
            "fulltime": {"home": 3, "away": 1},
            "extratime": {"home": None, "away": None},
            "penalty": {"home": None, "away": None},
        },
    },
    {
        "fixture_id": 123458,
        "date": "2026-04-12T19:00:00Z",
        "status": {"long": "Not Started", "short": "NS", "elapsed": None},
        "venue": {"id": 550, "name": "Santiago Bernabéu", "city": "Madrid"},
        "league": {
            "id": 2,
            "name": "UEFA Champions League",
            "country": "World",
            "logo": "https://media.api-sports.io/football/leagues/2.png",
            "flag": None,
            "season": 2025,
            "round": "Quarter-Finals",
        },
        "home_team": {
            "id": 541,
            "name": "Real Madrid",
            "logo": "https://media.api-sports.io/football/teams/541.png",
            "winner": None,
        },
        "away_team": {
            "id": 157,
            "name": "Bayern Munich",
            "logo": "https://media.api-sports.io/football/teams/157.png",
            "winner": None,
        },
        "goals": {"home": None, "away": None},
        "score": {
            "halftime": {"home": None, "away": None},
            "fulltime": {"home": None, "away": None},
            "extratime": {"home": None, "away": None},
            "penalty": {"home": None, "away": None},
        },
    },
]


class APIFootballFixtureService:
    """
    Service layer for retrieving fixtures from API-Football (/fixtures endpoint).
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixtures(
        self,
        league: Optional[int] = None,
        season: Optional[int] = None,
        date: Optional[str] = None,
        next_matches: Optional[int] = None,
        status: Optional[str] = None,
        team: Optional[int] = None,
        fixture_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        is_placeholder_key = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder_key:
            logger.warning("API_FOOTBALL_KEY is placeholder. Returning demonstration fixtures dataset.")
            return self._get_mock_fixtures(
                league=league,
                status=status,
                team=team,
                fixture_id=fixture_id,
            )

        params: Dict[str, Any] = {}
        if fixture_id:
            params["id"] = fixture_id
        if league:
            params["league"] = league
        if season:
            params["season"] = season
        if date:
            params["date"] = date
        if next_matches:
            params["next"] = next_matches
        if status:
            params["status"] = status
        if team:
            params["team"] = team

        try:
            raw_response = await self.client.get("fixtures", params=params)
            return self._normalize_fixtures(raw_response)
        except APIFootballAuthError as err:
            logger.warning(f"Live API-Football auth failed ({err}). Serving demonstration fixtures.")
            return self._get_mock_fixtures(
                league=league,
                status=status,
                team=team,
                fixture_id=fixture_id,
            )

    def _normalize_fixtures(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response_list = raw_data.get("response", [])
        normalized_fixtures = []

        for item in response_list:
            fx = item.get("fixture", {})
            lg = item.get("league", {})
            tm = item.get("teams", {})
            gl = item.get("goals", {})
            sc = item.get("score", {})

            normalized_fixtures.append({
                "fixture_id": fx.get("id"),
                "date": fx.get("date"),
                "status": {
                    "long": fx.get("status", {}).get("long"),
                    "short": fx.get("status", {}).get("short"),
                    "elapsed": fx.get("status", {}).get("elapsed"),
                },
                "venue": {
                    "id": fx.get("venue", {}).get("id"),
                    "name": fx.get("venue", {}).get("name"),
                    "city": fx.get("venue", {}).get("city"),
                },
                "league": {
                    "id": lg.get("id"),
                    "name": lg.get("name"),
                    "country": lg.get("country"),
                    "logo": lg.get("logo"),
                    "flag": lg.get("flag"),
                    "season": lg.get("season"),
                    "round": lg.get("round"),
                },
                "home_team": {
                    "id": tm.get("home", {}).get("id"),
                    "name": tm.get("home", {}).get("name"),
                    "logo": tm.get("home", {}).get("logo"),
                    "winner": tm.get("home", {}).get("winner"),
                },
                "away_team": {
                    "id": tm.get("away", {}).get("id"),
                    "name": tm.get("away", {}).get("name"),
                    "logo": tm.get("away", {}).get("logo"),
                    "winner": tm.get("away", {}).get("winner"),
                },
                "goals": {
                    "home": gl.get("home"),
                    "away": gl.get("away"),
                },
                "score": {
                    "halftime": sc.get("halftime", {}),
                    "fulltime": sc.get("fulltime", {}),
                    "extratime": sc.get("extratime", {}),
                    "penalty": sc.get("penalty", {}),
                },
            })

        return {
            "results": len(normalized_fixtures),
            "fixtures": normalized_fixtures,
        }

    def _get_mock_fixtures(
        self,
        league: Optional[int] = None,
        status: Optional[str] = None,
        team: Optional[int] = None,
        fixture_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        filtered = list(MOCK_FIXTURES)

        if fixture_id:
            filtered = [f for f in filtered if f.get("fixture_id") == fixture_id]

        if league:
            filtered = [f for f in filtered if f.get("league", {}).get("id") == league]

        if status:
            st_upper = status.upper()
            filtered = [f for f in filtered if f.get("status", {}).get("short") == st_upper]

        if team:
            filtered = [
                f for f in filtered
                if f.get("home_team", {}).get("id") == team or f.get("away_team", {}).get("id") == team
            ]

        return {
            "results": len(filtered),
            "fixtures": filtered,
            "note": "Demonstration fixtures dataset (Configure API_FOOTBALL_KEY in BackEnd/.env for live data).",
        }
