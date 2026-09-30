import logging
from typing import Any, Dict, Optional

from app.services.football_data.client import FootballDataClient

logger = logging.getLogger(__name__)


class FootballMatchService:
    """
    Service layer for fetching football match data using FootballDataClient.
    Separates external API data retrieval from FastAPI router logic.
    """

    def __init__(self, client: Optional[FootballDataClient] = None):
        self.client = client or FootballDataClient()

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
        Retrieves matches from football-data.org API with optional filtering.

        :param date_from: Start date in YYYY-MM-DD format.
        :param date_to: End date in YYYY-MM-DD format.
        :param competition: Competition code or ID (e.g., 'PL', 'CL', '2021').
        :param status: Match status (e.g., 'FINISHED', 'SCHEDULED', 'IN_PLAY').
        :param limit: Maximum number of matches to return.
        :param offset: Pagination offset index.
        :return: Raw API response dictionary containing matches metadata.
        """
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

        logger.info(f"Fetching football matches via endpoint '{endpoint}' with parameters: {params}")

        response = await self.client.get(endpoint, params=params if params else None)

        # Handle optional limit and offset pagination on results list
        if (limit is not None or offset is not None) and "matches" in response and isinstance(response["matches"], list):
            start = offset or 0
            end = (start + limit) if limit is not None else len(response["matches"])
            response["matches"] = response["matches"][start:end]
            if "resultSet" in response and isinstance(response["resultSet"], dict):
                response["resultSet"]["count"] = len(response["matches"])
            elif "count" in response:
                response["count"] = len(response["matches"])

        return response
