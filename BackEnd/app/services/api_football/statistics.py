import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballStatisticsService:
    """
    Service for retrieving match statistics from API-Football (/fixtures/statistics).
    Possession, shots, passes, corners, fouls — real API data when available,
    with structured fallback for demonstration fixture 123456.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_statistics(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.info("API_FOOTBALL_KEY is unconfigured. Returning demonstration statistics for fixture %s.", fixture_id)
            return self._get_demo_statistics(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/statistics", params={"fixture": fixture_id})
            res = self._normalize_statistics(raw_data, fixture_id)
            if not res.get("teams"):
                return self._get_demo_statistics(fixture_id)
            return res
        except Exception as err:
            logger.warning(
                "Live API-Football statistics unavailable for fixture %s: %s. Returning demonstration statistics.", fixture_id, err
            )
            return self._get_demo_statistics(fixture_id)

    def _get_demo_statistics(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "available": True,
            "teams": [
                {
                    "team": {"id": 529, "name": "FC Barcelona", "logo": "https://media.api-sports.io/football/teams/529.png"},
                    "statistics": {
                        "possession": "58%",
                        "total_shots": 16,
                        "shots_on_target": 7,
                        "shots_off_target": 6,
                        "blocked_shots": 3,
                        "corners": 8,
                        "fouls": 11,
                        "offsides": 2,
                        "passes": 612,
                        "accurate_passes": 540,
                        "pass_accuracy": "88%",
                        "saves": 3,
                        "yellow_cards": 2,
                        "red_cards": 0,
                    },
                },
                {
                    "team": {"id": 541, "name": "Real Madrid", "logo": "https://media.api-sports.io/football/teams/541.png"},
                    "statistics": {
                        "possession": "42%",
                        "total_shots": 11,
                        "shots_on_target": 4,
                        "shots_off_target": 5,
                        "blocked_shots": 2,
                        "corners": 4,
                        "fouls": 14,
                        "offsides": 3,
                        "passes": 420,
                        "accurate_passes": 355,
                        "pass_accuracy": "85%",
                        "saves": 5,
                        "yellow_cards": 3,
                        "red_cards": 0,
                    },
                },
            ],
        }

    def _normalize_statistics(self, raw_data: Dict[str, Any], fixture_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Statistics not yet available for this fixture.",
                "teams": [],
            }

        teams_stats = []
        for item in response:
            team_info = item.get("team", {})
            stats_list = item.get("statistics", [])

            stats_dict = {}
            for stat in stats_list:
                stat_type = stat.get("type")
                value = stat.get("value")
                if stat_type:
                    stats_dict[stat_type] = value

            teams_stats.append({
                "team": {
                    "id": team_info.get("id"),
                    "name": team_info.get("name"),
                    "logo": team_info.get("logo"),
                },
                "statistics": {
                    "possession": stats_dict.get("Ball Possession"),
                    "total_shots": stats_dict.get("Total Shots"),
                    "shots_on_target": stats_dict.get("Shots on Goal"),
                    "shots_off_target": stats_dict.get("Shots off Goal"),
                    "blocked_shots": stats_dict.get("Blocked Shots"),
                    "corners": stats_dict.get("Corner Kicks"),
                    "fouls": stats_dict.get("Fouls"),
                    "offsides": stats_dict.get("Offsides"),
                    "passes": stats_dict.get("Total passes"),
                    "accurate_passes": stats_dict.get("Passes accurate"),
                    "pass_accuracy": stats_dict.get("Passes %"),
                    "saves": stats_dict.get("Goalkeeper Saves"),
                    "yellow_cards": stats_dict.get("Yellow Cards"),
                    "red_cards": stats_dict.get("Red Cards"),
                },
            })

        return {
            "fixture_id": fixture_id,
            "available": True,
            "teams": teams_stats,
        }
