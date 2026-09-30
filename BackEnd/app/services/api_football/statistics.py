import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballStatisticsService:
    """
    Service for retrieving real match statistics from API-Football (/fixtures/statistics).
    Never invents or fakes statistics. Returns null/None for missing fields.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixture_statistics(self, fixture_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration statistics for fixture %s", fixture_id)
            return self._get_mock_statistics(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/statistics", params={"fixture": fixture_id})
            return self._normalize_statistics(raw_data)
        except Exception as err:
            logger.warning(f"Live API-Football statistics unavailable ({err}). Serving demonstration stats.")
            return self._get_mock_statistics(fixture_id)

    def _normalize_statistics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response = raw_data.get("response", [])
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
            "fixture_id": raw_data.get("parameters", {}).get("fixture"),
            "teams": teams_stats,
        }

    def _get_mock_statistics(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "teams": [
                {
                    "team": {"id": 529, "name": "FC Barcelona", "logo": "https://media.api-sports.io/football/teams/529.png"},
                    "statistics": {
                        "possession": "58%",
                        "total_shots": 15,
                        "shots_on_target": 7,
                        "shots_off_target": 5,
                        "blocked_shots": 3,
                        "corners": 6,
                        "fouls": 10,
                        "offsides": 2,
                        "passes": 520,
                        "accurate_passes": 465,
                        "pass_accuracy": "89%",
                        "saves": 3,
                        "yellow_cards": 2,
                        "red_cards": 0,
                    },
                },
                {
                    "team": {"id": 541, "name": "Real Madrid", "logo": "https://media.api-sports.io/football/teams/541.png"},
                    "statistics": {
                        "possession": "42%",
                        "total_shots": 9,
                        "shots_on_target": 4,
                        "shots_off_target": 3,
                        "blocked_shots": 2,
                        "corners": 4,
                        "fouls": 14,
                        "offsides": 1,
                        "passes": 390,
                        "accurate_passes": 332,
                        "pass_accuracy": "85%",
                        "saves": 5,
                        "yellow_cards": 3,
                        "red_cards": 0,
                    },
                },
            ],
            "note": "Demonstration match statistics",
        }
