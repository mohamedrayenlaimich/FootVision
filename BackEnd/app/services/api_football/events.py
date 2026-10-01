import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballEventsService:
    """
    Service for retrieving real match events timeline from API-Football (/fixtures/events).
    Goals, cards, substitutions, VAR decisions — from real API data only.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_events(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.warning("API_FOOTBALL_KEY is not configured. Cannot fetch events for fixture %s.", fixture_id)
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "events": [],
            }

        try:
            raw_data = await self.client.get("fixtures/events", params={"fixture": fixture_id})
            return self._normalize_events(raw_data, fixture_id)
        except Exception as err:
            logger.warning("Live API-Football events unavailable for fixture %s: %s", fixture_id, err)
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
                "events": [],
            }

    def _normalize_events(self, raw_data: Dict[str, Any], fixture_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        normalized_events = []

        for item in response:
            time_info = item.get("time", {})
            team_info = item.get("team", {})
            player_info = item.get("player", {})
            assist_info = item.get("assist", {})

            elapsed = time_info.get("elapsed")
            extra = time_info.get("extra")
            time_display = f"{elapsed}+{extra}'" if extra else f"{elapsed}'"

            normalized_events.append({
                "time": time_display,
                "elapsed": elapsed,
                "extra": extra,
                "team": {
                    "id": team_info.get("id"),
                    "name": team_info.get("name"),
                    "logo": team_info.get("logo"),
                },
                "type": item.get("type"),
                "detail": item.get("detail"),
                "comments": item.get("comments"),
                "player": {
                    "id": player_info.get("id"),
                    "name": player_info.get("name"),
                },
                "assist": {
                    "id": assist_info.get("id"),
                    "name": assist_info.get("name"),
                } if assist_info.get("name") else None,
            })

        return {
            "fixture_id": fixture_id,
            "available": True,
            "events_count": len(normalized_events),
            "events": normalized_events,
        }
