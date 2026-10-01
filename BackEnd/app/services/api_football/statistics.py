import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballStatisticsService:
    """
    Service for retrieving real match statistics from API-Football (/fixtures/statistics).
    Possession, shots, passes, corners, fouls — from real API data only.
    Returns null for any field the API does not provide. Never invents values.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_statistics(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.warning(
                "API_FOOTBALL_KEY is not configured. Cannot fetch statistics for fixture %s.", fixture_id
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "teams": [],
            }

        try:
            raw_data = await self.client.get("fixtures/statistics", params={"fixture": fixture_id})
            return self._normalize_statistics(raw_data, fixture_id)
        except Exception as err:
            logger.warning(
                "Live API-Football statistics unavailable for fixture %s: %s", fixture_id, err
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "teams": [],
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
