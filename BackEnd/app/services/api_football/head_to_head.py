import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballH2HService:
    """
    Service for retrieving Head-to-Head match history from API-Football.
    All historical meeting data is sourced from the real API.
    No fake meetings, no hardcoded team names, no invented results.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_head_to_head(self, team1_id: int, team2_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.warning(
                "API_FOOTBALL_KEY is not configured. Cannot fetch H2H for teams %s vs %s.",
                team1_id,
                team2_id,
            )
            return {
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "total_meetings": 0,
                "summary": {},
                "meetings": [],
            }

        try:
            h2h_param = f"{team1_id}-{team2_id}"
            raw_data = await self.client.get(
                "fixtures/headtohead", params={"h2h": h2h_param, "last": 5}
            )
            return self._normalize_h2h(raw_data, team1_id, team2_id)
        except Exception as err:
            logger.warning(
                "Live H2H API unavailable for teams %s vs %s: %s", team1_id, team2_id, err
            )
            return {
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "total_meetings": 0,
                "summary": {},
                "meetings": [],
            }

    def _normalize_h2h(
        self, raw_data: Dict[str, Any], team1_id: int, team2_id: int
    ) -> Dict[str, Any]:
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
            "available": True,
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
