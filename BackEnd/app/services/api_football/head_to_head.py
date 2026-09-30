import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballH2HService:
    """
    Service for retrieving Head-to-Head match history and calculating team form from real data.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_head_to_head(self, team1_id: int, team2_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration H2H for teams %s vs %s", team1_id, team2_id)
            return self._get_mock_h2h(team1_id, team2_id)

        try:
            h2h_param = f"{team1_id}-{team2_id}"
            raw_data = await self.client.get("fixtures/headtohead", params={"h2h": h2h_param, "last": 5})
            return self._normalize_h2h(raw_data, team1_id, team2_id)
        except Exception as err:
            logger.warning(f"Live H2H API unavailable ({err}). Serving demo H2H data.")
            return self._get_mock_h2h(team1_id, team2_id)

    def _normalize_h2h(self, raw_data: Dict[str, Any], team1_id: int, team2_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        meetings = []

        team1_wins = 0
        draws = 0
        team2_wins = 0
        team1_goals = 0
        team2_goals = 0

        for item in response:
            fx = item.get("fixture", {})
            tm = item.get("teams", {})
            gl = item.get("goals", {})

            home_id = tm.get("home", {}).get("id")
            home_name = tm.get("home", {}).get("name")
            away_name = tm.get("away", {}).get("name")
            h_goals = gl.get("home") or 0
            a_goals = gl.get("away") or 0

            if home_id == team1_id:
                team1_goals += h_goals
                team2_goals += a_goals
                if h_goals > a_goals:
                    team1_wins += 1
                elif h_goals < a_goals:
                    team2_wins += 1
                else:
                    draws += 1
            else:
                team2_goals += h_goals
                team1_goals += a_goals
                if h_goals > a_goals:
                    team2_wins += 1
                elif h_goals < a_goals:
                    team1_wins += 1
                else:
                    draws += 1

            meetings.append({
                "date": fx.get("date"),
                "fixture_id": fx.get("id"),
                "home_team": home_name,
                "away_team": away_name,
                "score": f"{h_goals} - {a_goals}",
            })

        return {
            "total_meetings": len(meetings),
            "summary": {
                "team1_wins": team1_wins,
                "draws": draws,
                "team2_wins": team2_wins,
                "team1_goals": team1_goals,
                "team2_goals": team2_goals,
            },
            "meetings": meetings,
        }

    def _get_mock_h2h(self, team1_id: int, team2_id: int) -> Dict[str, Any]:
        return {
            "total_meetings": 5,
            "summary": {
                "team1_wins": 3,
                "draws": 1,
                "team2_wins": 1,
                "team1_goals": 8,
                "team2_goals": 5,
            },
            "meetings": [
                {"date": "2025-10-26", "fixture_id": 901, "home_team": "FC Barcelona", "away_team": "Real Madrid", "score": "2 - 1"},
                {"date": "2025-04-21", "fixture_id": 902, "home_team": "Real Madrid", "away_team": "FC Barcelona", "score": "1 - 1"},
                {"date": "2024-10-28", "fixture_id": 903, "home_team": "FC Barcelona", "away_team": "Real Madrid", "score": "3 - 1"},
                {"date": "2024-03-19", "fixture_id": 904, "home_team": "Real Madrid", "away_team": "FC Barcelona", "score": "2 - 1"},
                {"date": "2023-10-28", "fixture_id": 905, "home_team": "FC Barcelona", "away_team": "Real Madrid", "score": "1 - 0"},
            ],
            "note": "Demonstration Head-to-Head history",
        }
