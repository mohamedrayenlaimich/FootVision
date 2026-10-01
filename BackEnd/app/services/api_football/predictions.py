import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: No mock, demo, or fallback data in production.
# ---------------------------------------------------------------------------


class APIFootballPredictionsService:
    """
    Service for retrieving external API-Football predictions (/predictions?fixture={fixture_id}).
    Distinctly labeled as 'API-Football Prediction'.
    Returns real API data or a structured unavailable response — never fake predictions.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_football_key_here", "")

    async def get_fixture_prediction(self, fixture_id: int) -> Dict[str, Any]:
        if not self._is_key_configured():
            logger.warning(
                "API_FOOTBALL_KEY is not configured. Cannot fetch prediction for fixture %s.", fixture_id
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
            }

        try:
            raw_data = await self.client.get("predictions", params={"fixture": fixture_id})
            return self._normalize_prediction(raw_data, fixture_id)
        except Exception as err:
            logger.warning(
                "Live API-Football prediction unavailable for fixture %s: %s", fixture_id, err
            )
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "Data is currently unavailable from the data provider.",
            }

    def _normalize_prediction(self, raw_data: Dict[str, Any], fixture_id: int) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": fixture_id,
                "available": False,
                "message": "External API prediction not available for this fixture.",
            }

        pred_data = response[0]
        predictions = pred_data.get("predictions", {})
        winner = predictions.get("winner", {})
        percent = predictions.get("percent", {})

        return {
            "fixture_id": fixture_id,
            "available": True,
            "provider": "API-Football External Engine",
            "winner": {
                "name": winner.get("name"),
                "comment": winner.get("comment"),
            },
            "advice": predictions.get("advice"),
            "probabilities": {
                "home": percent.get("home"),
                "draw": percent.get("draw"),
                "away": percent.get("away"),
            },
            "predicted_score": predictions.get("score"),
        }
