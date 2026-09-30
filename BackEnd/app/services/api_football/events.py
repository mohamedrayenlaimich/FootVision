import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballEventsService:
    """
    Service for retrieving real match events timeline from API-Football (/fixtures/events).
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixture_events(self, fixture_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration events for fixture %s", fixture_id)
            return self._get_mock_events(fixture_id)

        try:
            raw_data = await self.client.get("fixtures/events", params={"fixture": fixture_id})
            return self._normalize_events(raw_data)
        except Exception as err:
            logger.warning(f"Live API-Football events unavailable ({err}). Serving demonstration events.")
            return self._get_mock_events(fixture_id)

    def _normalize_events(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
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
            "fixture_id": raw_data.get("parameters", {}).get("fixture"),
            "events_count": len(normalized_events),
            "events": normalized_events,
        }

    def _get_mock_events(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "events_count": 5,
            "events": [
                {
                    "time": "00'",
                    "elapsed": 0,
                    "team": {"id": 529, "name": "FC Barcelona"},
                    "type": "Kickoff",
                    "detail": "Match Start",
                    "player": {"id": None, "name": None},
                    "assist": None,
                },
                {
                    "time": "23'",
                    "elapsed": 23,
                    "team": {"id": 529, "name": "FC Barcelona"},
                    "type": "Goal",
                    "detail": "Normal Goal",
                    "player": {"id": 1, "name": "Robert Lewandowski"},
                    "assist": {"id": 2, "name": "Pedri"},
                },
                {
                    "time": "45+2'",
                    "elapsed": 45,
                    "extra": 2,
                    "team": {"id": 541, "name": "Real Madrid"},
                    "type": "Card",
                    "detail": "Yellow Card",
                    "player": {"id": 3, "name": "Jude Bellingham"},
                    "assist": None,
                },
                {
                    "time": "67'",
                    "elapsed": 67,
                    "team": {"id": 541, "name": "Real Madrid"},
                    "type": "subst",
                    "detail": "Substitution",
                    "player": {"id": 4, "name": "Luka Modrić"},
                    "assist": {"id": 5, "name": "Toni Kroos"},
                },
                {
                    "time": "82'",
                    "elapsed": 82,
                    "team": {"id": 529, "name": "FC Barcelona"},
                    "type": "Goal",
                    "detail": "Normal Goal",
                    "player": {"id": 6, "name": "Lamine Yamal"},
                    "assist": {"id": 7, "name": "Raphinha"},
                },
            ],
            "note": "Demonstration match timeline events",
        }
