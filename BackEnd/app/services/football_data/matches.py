import logging
from typing import Any, Dict, Optional

from app.services.football_data.client import (
    FootballDataAuthError,
    FootballDataClient,
    FootballDataNotFoundError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: This service returns ONLY real data from football-data.org.
# There is NO mock/demo/fallback data. If the API is unavailable or the key
# is missing, a structured error response is returned so the frontend can
# display "Data unavailable" — never fake data.
# ---------------------------------------------------------------------------


def _missing_key_response() -> Dict[str, Any]:
    """Return a structured error when FOOTBALL_DATA_API_KEY is not configured."""
    return {
        "available": False,
        "message": (
            "Football data service is not configured. "
            "Set FOOTBALL_DATA_API_KEY in BackEnd/.env to enable live match data."
        ),
    }


class FootballMatchService:
    """
    Service layer for fetching football match data using FootballDataClient.
    All data comes exclusively from the football-data.org API.
    No mock, demo, placeholder, or fallback data is returned in production.
    """

    def __init__(self, client: Optional[FootballDataClient] = None):
        self.client = client or FootballDataClient()

    def _is_key_configured(self) -> bool:
        key = self.client.api_key
        return bool(key) and key not in ("your_api_key_here", "")

    async def get_matches(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        competition: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve matches from football-data.org API.

        Supports:
          GET /v4/matches                          — all matches (with optional filters)
          GET /v4/competitions/{code}/matches      — competition-specific matches

        Returns real API data only. No mock data ever.
        """
        if not self._is_key_configured():
            logger.warning("FOOTBALL_DATA_API_KEY is not configured. Cannot fetch live match data.")
            return _missing_key_response()

        params: Dict[str, Any] = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status.upper()

        if competition:
            endpoint = f"competitions/{competition}/matches"
        else:
            endpoint = "matches"

        logger.info("Fetching football matches via endpoint '%s' with params: %s", endpoint, params)

        response = await self.client.get(endpoint, params=params if params else None)

        # Apply optional client-side pagination when the API does not paginate
        if (limit is not None or offset is not None) and isinstance(response.get("matches"), list):
            start = offset or 0
            end = (start + limit) if limit is not None else len(response["matches"])
            response["matches"] = response["matches"][start:end]
            if "resultSet" in response and isinstance(response["resultSet"], dict):
                response["resultSet"]["count"] = len(response["matches"])
            elif "count" in response:
                response["count"] = len(response["matches"])

        return response

    async def get_match(self, match_id: int) -> Dict[str, Any]:
        """
        Retrieve a single match by its unique match ID from football-data.org.

        Uses: GET /v4/matches/{match_id}

        This is the correct per-match endpoint — every call uses the exact
        match_id provided, preventing the same-match bug.
        """
        if not self._is_key_configured():
            logger.warning("FOOTBALL_DATA_API_KEY is not configured. Cannot fetch match %s.", match_id)
            return _missing_key_response()

        logger.info("Fetching match details for match_id=%s from football-data.org", match_id)
        response = await self.client.get(f"matches/{match_id}")
        return response

    async def get_competition_matches(
        self,
        competition_code: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,
        matchday: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve matches for a specific competition.

        Uses: GET /v4/competitions/{competition_code}/matches
        """
        if not self._is_key_configured():
            logger.warning(
                "FOOTBALL_DATA_API_KEY is not configured. Cannot fetch competition '%s' matches.",
                competition_code,
            )
            return _missing_key_response()

        params: Dict[str, Any] = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status.upper()
        if matchday is not None:
            params["matchday"] = matchday

        endpoint = f"competitions/{competition_code}/matches"
        logger.info(
            "Fetching competition matches via endpoint '%s' with params: %s", endpoint, params
        )
        return await self.client.get(endpoint, params=params if params else None)
