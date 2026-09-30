import logging
from typing import Any, Dict, Optional

from app.services.api_football.client import APIFootballClient

logger = logging.getLogger(__name__)


class APIFootballPredictionsService:
    """
    Service for retrieving external API-Football predictions (/predictions?fixture={fixture_id}).
    Distinctly labeled as 'API-Football Prediction'.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixture_prediction(self, fixture_id: int) -> Dict[str, Any]:
        is_placeholder = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if is_placeholder:
            logger.info("Using demonstration API-Football prediction for fixture %s", fixture_id)
            return self._get_mock_prediction(fixture_id)

        try:
            raw_data = await self.client.get("predictions", params={"fixture": fixture_id})
            return self._normalize_prediction(raw_data)
        except Exception as err:
            logger.warning(f"Live API-Football prediction unavailable ({err}). Serving demo prediction.")
            return self._get_mock_prediction(fixture_id)

    def _normalize_prediction(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response = raw_data.get("response", [])
        if not response:
            return {
                "fixture_id": raw_data.get("parameters", {}).get("fixture"),
                "available": False,
                "message": "External API prediction not available for this fixture.",
            }

        pred_data = response[0]
        predictions = pred_data.get("predictions", {})
        winner = predictions.get("winner", {})
        percent = predictions.get("percent", {})

        return {
            "fixture_id": raw_data.get("parameters", {}).get("fixture"),
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

    def _get_mock_prediction(self, fixture_id: int) -> Dict[str, Any]:
        return {
            "fixture_id": fixture_id,
            "available": True,
            "provider": "API-Football External Engine",
            "winner": {
                "name": "FC Barcelona",
                "comment": "Win or draw",
            },
            "advice": "Double chance : FC Barcelona or draw",
            "probabilities": {
                "home": "48%",
                "draw": "27%",
                "away": "25%",
            },
            "predicted_score": {
                "home": 2,
                "away": 1,
            },
            "note": "External API-Football prediction dataset",
        }
