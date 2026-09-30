import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballLineupsService:
    """
    Service for retrieving team lineups from API-Football (/fixtures/lineups).
    Returns Starting XI, Substitutes, Coach, and Formation.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixture_lineups(self, fixture_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration lineups for fixture %s", fixture_id)
            return self._get_mock_lineups(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/lineups", params={"fixture": fixture_id})
            return self._normalize_lineups(raw_data)
        except Exception as err:
            logger.warning(f"Live API-Football lineups unavailable ({err}). Serving demonstration lineups.")
            return self._get_mock_lineups(fixture_id)

    def _normalize_lineups(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": raw_data.get("parameters", {}).get("fixture"),
                "available": False,
                "message": "Lineups not available yet.",
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
                    "colors": team_lineup.get("team", {}).get("colors"),
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
            "fixture_id": raw_data.get("parameters", {}).get("fixture"),
            "available": True,
            "lineups": lineups,
        }

    def _get_mock_lineups(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "available": True,
            "lineups": [
                {
                    "team": {"id": 529, "name": "FC Barcelona", "logo": "https://media.api-sports.io/football/teams/529.png"},
                    "formation": "4-3-3",
                    "coach": {"id": 10, "name": "Hansi Flick"},
                    "start_xi": [
                        {"id": 101, "name": "Marc-André ter Stegen", "number": 1, "pos": "G", "grid": "1:1"},
                        {"id": 102, "name": "Jules Koundé", "number": 23, "pos": "D", "grid": "2:4"},
                        {"id": 103, "name": "Pau Cubarsí", "number": 2, "pos": "D", "grid": "2:3"},
                        {"id": 104, "name": "Iñigo Martínez", "number": 5, "pos": "D", "grid": "2:2"},
                        {"id": 105, "name": "Alejandro Balde", "number": 3, "pos": "D", "grid": "2:1"},
                        {"id": 106, "name": "Pedri", "number": 8, "pos": "M", "grid": "3:3"},
                        {"id": 107, "name": "Marc Casadó", "number": 17, "pos": "M", "grid": "3:2"},
                        {"id": 108, "name": "Dani Olmo", "number": 20, "pos": "M", "grid": "3:1"},
                        {"id": 109, "name": "Lamine Yamal", "number": 19, "pos": "F", "grid": "4:3"},
                        {"id": 110, "name": "Robert Lewandowski", "number": 9, "pos": "F", "grid": "4:2"},
                        {"id": 111, "name": "Raphinha", "number": 11, "pos": "F", "grid": "4:1"},
                    ],
                    "substitutes": [
                        {"id": 112, "name": "Iñaki Peña", "number": 13, "pos": "G"},
                        {"id": 113, "name": "Fermin López", "number": 16, "pos": "M"},
                        {"id": 114, "name": "Ferran Torres", "number": 7, "pos": "F"},
                    ],
                },
                {
                    "team": {"id": 541, "name": "Real Madrid", "logo": "https://media.api-sports.io/football/teams/541.png"},
                    "formation": "4-3-3",
                    "coach": {"id": 20, "name": "Carlo Ancelotti"},
                    "start_xi": [
                        {"id": 201, "name": "Thibaut Courtois", "number": 1, "pos": "G", "grid": "1:1"},
                        {"id": 202, "name": "Dani Carvajal", "number": 2, "pos": "D", "grid": "2:4"},
                        {"id": 203, "name": "Éder Militão", "number": 3, "pos": "D", "grid": "2:3"},
                        {"id": 204, "name": "Antonio Rüdiger", "number": 22, "pos": "D", "grid": "2:2"},
                        {"id": 205, "name": "Ferland Mendy", "number": 23, "pos": "D", "grid": "2:1"},
                        {"id": 206, "name": "Federico Valverde", "number": 8, "pos": "M", "grid": "3:3"},
                        {"id": 207, "name": "Aurelien Tchouaméni", "number": 14, "pos": "M", "grid": "3:2"},
                        {"id": 208, "name": "Jude Bellingham", "number": 5, "pos": "M", "grid": "3:1"},
                        {"id": 209, "name": "Rodrygo", "number": 11, "pos": "F", "grid": "4:3"},
                        {"id": 210, "name": "Kylian Mbappé", "number": 9, "pos": "F", "grid": "4:2"},
                        {"id": 211, "name": "Vinícius Júnior", "number": 7, "pos": "F", "grid": "4:1"},
                    ],
                    "substitutes": [
                        {"id": 212, "name": "Andriy Lunin", "number": 13, "pos": "G"},
                        {"id": 213, "name": "Luka Modrić", "number": 10, "pos": "M"},
                        {"id": 214, "name": "Brahim Díaz", "number": 21, "pos": "F"},
                    ],
                },
            ],
            "note": "Demonstration starting XI lineups",
        }
