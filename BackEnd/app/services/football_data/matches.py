import logging
from typing import Any, Dict, List, Optional

from app.services.football_data.client import FootballDataAuthError, FootballDataClient

logger = logging.getLogger(__name__)

MOCK_MATCHES: List[Dict[str, Any]] = [
    {
        "id": 1001,
        "utcDate": "2026-03-15T16:30:00Z",
        "status": "FINISHED",
        "matchday": 29,
        "stage": "REGULAR_SEASON",
        "competition": {
            "id": 2021,
            "name": "Premier League",
            "code": "PL",
            "type": "LEAGUE",
            "emblem": "https://crests.football-data.org/PL.png",
        },
        "homeTeam": {
            "id": 57,
            "name": "Arsenal FC",
            "shortName": "Arsenal",
            "tla": "ARS",
            "crest": "https://crests.football-data.org/57.png",
        },
        "awayTeam": {
            "id": 61,
            "name": "Chelsea FC",
            "shortName": "Chelsea",
            "tla": "CHE",
            "crest": "https://crests.football-data.org/61.png",
        },
        "score": {
            "winner": "HOME_TEAM",
            "duration": "REGULAR",
            "fullTime": {"home": 2, "away": 1},
            "halfTime": {"home": 1, "away": 0},
        },
    },
    {
        "id": 1002,
        "utcDate": "2026-03-22T20:00:00Z",
        "status": "FINISHED",
        "matchday": 30,
        "stage": "REGULAR_SEASON",
        "competition": {
            "id": 2021,
            "name": "Premier League",
            "code": "PL",
            "type": "LEAGUE",
            "emblem": "https://crests.football-data.org/PL.png",
        },
        "homeTeam": {
            "id": 65,
            "name": "Manchester City FC",
            "shortName": "Man City",
            "tla": "MCI",
            "crest": "https://crests.football-data.org/65.png",
        },
        "awayTeam": {
            "id": 64,
            "name": "Liverpool FC",
            "shortName": "Liverpool",
            "tla": "LIV",
            "crest": "https://crests.football-data.org/64.png",
        },
        "score": {
            "winner": "DRAW",
            "duration": "REGULAR",
            "fullTime": {"home": 2, "away": 2},
            "halfTime": {"home": 1, "away": 1},
        },
    },
    {
        "id": 1003,
        "utcDate": "2026-04-05T19:00:00Z",
        "status": "SCHEDULED",
        "matchday": 31,
        "stage": "REGULAR_SEASON",
        "competition": {
            "id": 2021,
            "name": "Premier League",
            "code": "PL",
            "type": "LEAGUE",
            "emblem": "https://crests.football-data.org/PL.png",
        },
        "homeTeam": {
            "id": 66,
            "name": "Manchester United FC",
            "shortName": "Man United",
            "tla": "MUN",
            "crest": "https://crests.football-data.org/66.png",
        },
        "awayTeam": {
            "id": 57,
            "name": "Arsenal FC",
            "shortName": "Arsenal",
            "tla": "ARS",
            "crest": "https://crests.football-data.org/57.png",
        },
        "score": {
            "winner": None,
            "duration": "REGULAR",
            "fullTime": {"home": None, "away": None},
            "halfTime": {"home": None, "away": None},
        },
    },
    {
        "id": 1004,
        "utcDate": "2026-04-14T20:00:00Z",
        "status": "IN_PLAY",
        "stage": "QUARTER_FINALS",
        "competition": {
            "id": 2001,
            "name": "UEFA Champions League",
            "code": "CL",
            "type": "CUP",
            "emblem": "https://crests.football-data.org/CL.png",
        },
        "homeTeam": {
            "id": 86,
            "name": "Real Madrid CF",
            "shortName": "Real Madrid",
            "tla": "RMA",
            "crest": "https://crests.football-data.org/86.png",
        },
        "awayTeam": {
            "id": 5,
            "name": "FC Bayern München",
            "shortName": "Bayern",
            "tla": "BAY",
            "crest": "https://crests.football-data.org/5.png",
        },
        "score": {
            "winner": None,
            "duration": "REGULAR",
            "fullTime": {"home": 1, "away": 0},
            "halfTime": {"home": 1, "away": 0},
        },
    },
]


class FootballMatchService:
    """
    Service layer for fetching football match data using FootballDataClient.
    Provides fallback demonstration data when using placeholder API key.
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
        Falls back gracefully to mock matches if using default placeholder API key.
        """
        is_placeholder_key = not self.client.api_key or self.client.api_key == "your_api_key_here"

        if is_placeholder_key:
            logger.warning("FOOTBALL_DATA_API_KEY is unconfigured or placeholder. Returning demonstration match data.")
            return self._get_mock_matches(
                competition=competition,
                status=status,
                limit=limit,
                offset=offset,
            )

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

        try:
            response = await self.client.get(endpoint, params=params if params else None)
        except FootballDataAuthError as err:
            logger.warning(f"Live API authentication failed ({err}). Falling back to demonstration dataset.")
            return self._get_mock_matches(
                competition=competition,
                status=status,
                limit=limit,
                offset=offset,
            )

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

    def _get_mock_matches(
        self,
        competition: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        filtered = list(MOCK_MATCHES)

        if competition:
            comp_upper = competition.upper()
            filtered = [
                m for m in filtered
                if m.get("competition", {}).get("code") == comp_upper
                or str(m.get("competition", {}).get("id")) == comp_upper
            ]

        if status:
            st_upper = status.upper()
            filtered = [m for m in filtered if m.get("status") == st_upper]

        start = offset or 0
        end = (start + limit) if limit is not None else len(filtered)
        sliced = filtered[start:end]

        return {
            "count": len(sliced),
            "matches": sliced,
            "note": "Demonstration match dataset (Configure FOOTBALL_DATA_API_KEY in BackEnd/.env for live data)."
        }
