import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballPlayersService:
    """
    Service for retrieving player match statistics from API-Football (/fixtures/players).
    Returns player ratings, minutes, shots, goals, assists, passes, tackles, dribbles, etc.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixture_players(self, fixture_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration player statistics for fixture %s", fixture_id)
            return self._get_mock_players(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/players", params={"fixture": fixture_id})
            return self._normalize_players(raw_data)
        except Exception as err:
            logger.warning(f"Live API-Football player statistics unavailable ({err}). Serving demo player stats.")
            return self._get_mock_players(fixture_id)

    def _normalize_players(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response = raw_data.get("response", [])
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
            "fixture_id": raw_data.get("parameters", {}).get("fixture"),
            "teams": teams_players,
        }

    def _get_mock_players(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "teams": [
                {
                    "team": {"id": 529, "name": "FC Barcelona"},
                    "players": [
                        {
                            "id": 110,
                            "name": "Robert Lewandowski",
                            "minutes": 90,
                            "number": 9,
                            "position": "F",
                            "rating": "8.4",
                            "shots": {"total": 4, "on_target": 3},
                            "goals": {"total": 1, "assists": 0},
                            "passes": {"total": 28, "key": 2, "accuracy": "82%"},
                            "tackles": {"total": 1, "interceptions": 0},
                            "cards": {"yellow": 0, "red": 0},
                        },
                        {
                            "id": 109,
                            "name": "Lamine Yamal",
                            "minutes": 88,
                            "number": 19,
                            "position": "F",
                            "rating": "8.8",
                            "shots": {"total": 3, "on_target": 2},
                            "goals": {"total": 1, "assists": 1},
                            "passes": {"total": 42, "key": 4, "accuracy": "86%"},
                            "tackles": {"total": 2, "interceptions": 1},
                            "cards": {"yellow": 0, "red": 0},
                        },
                    ],
                },
                {
                    "team": {"id": 541, "name": "Real Madrid"},
                    "players": [
                        {
                            "id": 210,
                            "name": "Kylian Mbappé",
                            "minutes": 90,
                            "number": 9,
                            "position": "F",
                            "rating": "7.5",
                            "shots": {"total": 4, "on_target": 2},
                            "goals": {"total": 1, "assists": 0},
                            "passes": {"total": 31, "key": 1, "accuracy": "80%"},
                            "tackles": {"total": 0, "interceptions": 0},
                            "cards": {"yellow": 0, "red": 0},
                        },
                        {
                            "id": 208,
                            "name": "Jude Bellingham",
                            "minutes": 90,
                            "number": 5,
                            "position": "M",
                            "rating": "7.2",
                            "shots": {"total": 1, "on_target": 0},
                            "goals": {"total": 0, "assists": 1},
                            "passes": {"total": 54, "key": 2, "accuracy": "88%"},
                            "tackles": {"total": 3, "interceptions": 2},
                            "cards": {"yellow": 1, "red": 0},
                        },
                    ],
                },
            ],
            "note": "Demonstration player match statistics",
        }
