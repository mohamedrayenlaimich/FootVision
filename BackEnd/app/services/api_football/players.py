import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballPlayersService:
    """
    Service for retrieving player match statistics from API-Football (/fixtures/players).
    Player ratings, minutes, shots, goals, assists, passes, tackles, dribbles — real data only.
    Never returns fake player names, fake ratings, or fake statistics.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_players(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.warning(
                "API_FOOTBALL_KEY is not configured. Cannot fetch player stats for fixture %s.", fixture_id
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "teams": [],
            }

        try:
            raw_data = await self.client.get("fixtures/players", params={"fixture": fixture_id})
            return self._normalize_players(raw_data, fixture_id)
        except Exception as err:
            logger.warning(
                "Live API-Football player statistics unavailable for fixture %s: %s", fixture_id, err
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "teams": [],
            }

    def _normalize_players(self, raw_data: Dict[str, Any], fixture_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Player statistics not yet available for this fixture.",
                "teams": [],
            }

        teams_players = []
        for item in response:
            tm = item.get("team", {})
            players_list = item.get("players", [])

            player_stats = []
            for p_entry in players_list:
                p_info = p_entry.get("player", {})
                st = p_entry.get("statistics", [{}])[0] if p_entry.get("statistics") else {}

                player_stats.append({
                    "id": p_info.get("id"),
                    "name": p_info.get("name"),
                    "photo": p_info.get("photo"),
                    "minutes": st.get("games", {}).get("minutes"),
                    "number": st.get("games", {}).get("number"),
                    "position": st.get("games", {}).get("position"),
                    "rating": st.get("games", {}).get("rating"),
                    "captain": st.get("games", {}).get("captain", False),
                    "substitute": st.get("games", {}).get("substitute", False),
                    "shots": {
                        "total": st.get("shots", {}).get("total"),
                        "on_target": st.get("shots", {}).get("on"),
                    },
                    "goals": {
                        "total": st.get("goals", {}).get("total"),
                        "conceded": st.get("goals", {}).get("conceded"),
                        "assists": st.get("goals", {}).get("assists"),
                        "saves": st.get("goals", {}).get("saves"),
                    },
                    "passes": {
                        "total": st.get("passes", {}).get("total"),
                        "key": st.get("passes", {}).get("key"),
                        "accuracy": st.get("passes", {}).get("accuracy"),
                    },
                    "tackles": {
                        "total": st.get("tackles", {}).get("total"),
                        "blocks": st.get("tackles", {}).get("blocks"),
                        "interceptions": st.get("tackles", {}).get("interceptions"),
                    },
                    "duels": {
                        "total": st.get("duels", {}).get("total"),
                        "won": st.get("duels", {}).get("won"),
                    },
                    "cards": {
                        "yellow": st.get("cards", {}).get("yellow"),
                        "red": st.get("cards", {}).get("red"),
                    },
                })

            teams_players.append({
                "team": {
                    "id": tm.get("id"),
                    "name": tm.get("name"),
                    "logo": tm.get("logo"),
                },
                "players": player_stats,
            })

        return {
            "fixture_id": fixture_id,
            "available": True,
            "teams": teams_players,
        }
