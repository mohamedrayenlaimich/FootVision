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
            logger.info("API_FOOTBALL_KEY is not configured. Cannot fetch lineups for fixture %s.", fixture_id)
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Lineups are currently unavailable from the data provider.",
                "lineups": [],
            }

        try:
            raw_data = await self.client.get("fixtures/lineups", params={"fixture": fixture_id})
            res = self._normalize_lineups(raw_data, fixture_id)
            if not res.get("lineups"):
                return {
                    "fixture_id": fixture_id,
                    "available": False,
                    "message": "Lineups are not yet available for this fixture.",
                    "lineups": [],
                }
            return res
        except Exception as err:
            logger.warning("Live API-Football lineups unavailable for fixture %s: %s.", fixture_id, err)
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Lineups are currently unavailable from the data provider.",
                "lineups": [],
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
