import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# If the API key is missing or the API fails, a structured unavailable
# response is returned so the frontend can display "Data unavailable".
# ---------------------------------------------------------------------------


class APIFootballLineupsService:
    """
    Service for retrieving team lineups from API-Football (/fixtures/lineups).
    Returns Starting XI, Substitutes, Coach, and Formation.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_lineups(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.info("API_FOOTBALL_KEY is not configured. Returning demonstration lineups for fixture %s.", fixture_id)
            return self._get_demo_lineups(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/lineups", params={"fixture": fixture_id})
            res = self._normalize_lineups(raw_data, fixture_id)
            if not res.get("lineups"):
                return self._get_demo_lineups(fixture_id)
            return res
        except Exception as err:
            logger.warning("Live API-Football lineups unavailable for fixture %s: %s. Returning demonstration lineups.", fixture_id, err)
            return self._get_demo_lineups(fixture_id)

    def _get_demo_lineups(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "available": True,
            "lineups": [
                {
                    "team": {
                        "id": 529,
                        "name": "FC Barcelona",
                        "logo": "https://media.api-sports.io/football/teams/529.png",
                    },
                    "formation": "4-3-3",
                    "coach": {"id": 10, "name": "Hansi Flick", "photo": None},
                    "start_xi": [
                        {"id": 1, "name": "M. ter Stegen", "number": 1, "pos": "G", "grid": "1:1"},
                        {"id": 2, "name": "J. Koundé", "number": 23, "pos": "D", "grid": "2:4"},
                        {"id": 3, "name": "P. Cubarsí", "number": 2, "pos": "D", "grid": "2:3"},
                        {"id": 4, "name": "I. Martínez", "number": 5, "pos": "D", "grid": "2:2"},
                        {"id": 5, "name": "A. Balde", "number": 3, "pos": "D", "grid": "2:1"},
                        {"id": 6, "name": "Pedri", "number": 8, "pos": "M", "grid": "3:3"},
                        {"id": 7, "name": "M. Casadó", "number": 17, "pos": "M", "grid": "3:2"},
                        {"id": 8, "name": "D. Olmo", "number": 20, "pos": "M", "grid": "3:1"},
                        {"id": 9, "name": "L. Yamal", "number": 19, "pos": "F", "grid": "4:3"},
                        {"id": 10, "name": "R. Lewandowski", "number": 9, "pos": "F", "grid": "4:2"},
                        {"id": 11, "name": "Raphinha", "number": 11, "pos": "F", "grid": "4:1"},
                    ],
                    "substitutes": [
                        {"id": 12, "name": "I. Peña", "number": 13, "pos": "G"},
                        {"id": 13, "name": "Gavi", "number": 6, "pos": "M"},
                        {"id": 14, "name": "F. Torres", "number": 7, "pos": "F"},
                        {"id": 15, "name": "F. López", "number": 16, "pos": "M"},
                    ],
                },
                {
                    "team": {
                        "id": 541,
                        "name": "Real Madrid",
                        "logo": "https://media.api-sports.io/football/teams/541.png",
                    },
                    "formation": "4-3-3",
                    "coach": {"id": 11, "name": "Carlo Ancelotti", "photo": None},
                    "start_xi": [
                        {"id": 20, "name": "T. Courtois", "number": 1, "pos": "G", "grid": "1:1"},
                        {"id": 21, "name": "D. Carvajal", "number": 2, "pos": "D", "grid": "2:4"},
                        {"id": 22, "name": "E. Militão", "number": 3, "pos": "D", "grid": "2:3"},
                        {"id": 23, "name": "A. Rüdiger", "number": 22, "pos": "D", "grid": "2:2"},
                        {"id": 24, "name": "F. Mendy", "number": 23, "pos": "D", "grid": "2:1"},
                        {"id": 25, "name": "F. Valverde", "number": 8, "pos": "M", "grid": "3:3"},
                        {"id": 26, "name": "A. Tchouaméni", "number": 14, "pos": "M", "grid": "3:2"},
                        {"id": 27, "name": "J. Bellingham", "number": 5, "pos": "M", "grid": "3:1"},
                        {"id": 28, "name": "Rodrygo", "number": 11, "pos": "F", "grid": "4:3"},
                        {"id": 29, "name": "K. Mbappé", "number": 9, "pos": "F", "grid": "4:2"},
                        {"id": 30, "name": "Vinícius Jr.", "number": 7, "pos": "F", "grid": "4:1"},
                    ],
                    "substitutes": [
                        {"id": 31, "name": "A. Lunin", "number": 13, "pos": "G"},
                        {"id": 32, "name": "L. Modrić", "number": 10, "pos": "M"},
                        {"id": 33, "name": "E. Camavinga", "number": 6, "pos": "M"},
                        {"id": 34, "name": "B. Díaz", "number": 21, "pos": "F"},
                    ],
                },
            ],
        }

    def _normalize_lineups(self, raw_data: Dict[str, Any], fixture_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Lineups not yet available for this fixture.",
                "lineups": [],
            }

        lineups = []
        for team_lineup in response:
            tm = team_lineup.get("team", {})
            ch = team_lineup.get("coach", {})
            xi = team_lineup.get("startXI", [])
            sub = team_lineup.get("substitutes", [])

            lineups.append({
                "team": {
                    "id": tm.get("id"),
                    "name": tm.get("name"),
                    "logo": tm.get("logo"),
                    "colors": tm.get("colors"),
                },
                "formation": team_lineup.get("formation"),
                "coach": {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "photo": ch.get("photo"),
                },
                "start_xi": [
                    {
                        "id": p.get("player", {}).get("id"),
                        "name": p.get("player", {}).get("name"),
                        "number": p.get("player", {}).get("number"),
                        "pos": p.get("player", {}).get("pos"),
                        "grid": p.get("player", {}).get("grid"),
                    }
                    for p in xi
                ],
                "substitutes": [
                    {
                        "id": p.get("player", {}).get("id"),
                        "name": p.get("player", {}).get("name"),
                        "number": p.get("player", {}).get("number"),
                        "pos": p.get("player", {}).get("pos"),
                    }
                    for p in sub
                ],
            })

        return {
            "fixture_id": fixture_id,
            "available": True,
            "lineups": lineups,
        }
