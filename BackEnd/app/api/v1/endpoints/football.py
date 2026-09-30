import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.football import MatchListResponseSchema
from app.services.football_data import (
    FootballMatchService,
    FootballDataAuthError,
    FootballDataNotFoundError,
    FootballDataRateLimitError,
    FootballDataTimeoutError,
    FootballDataAPIError,
)

logger = logging.getLogger(__name__)

router = APIRouter()
match_service = FootballMatchService()


@router.get(
    "/matches",
    response_model=MatchListResponseSchema,
    summary="Get Football Matches",
    description="Retrieve normalized football match data from football-data.org with optional filtering.",
)
async def get_matches(
    dateFrom: Optional[str] = Query(
        None,
        description="Filter start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    dateTo: Optional[str] = Query(
        None,
        description="Filter end date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    competition: Optional[str] = Query(
        None,
        description="Competition code or ID (e.g., PL, CL, 2021)",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Match status (e.g., SCHEDULED, LIVE, FINISHED)",
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=500,
        description="Maximum number of matches to return",
    ),
    offset: Optional[int] = Query(
        None,
        ge=0,
        description="Pagination offset index",
    ),
):
    try:
        raw_data = await match_service.get_matches(
            date_from=dateFrom,
            date_to=dateTo,
            competition=competition,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        matches_list = raw_data.get("matches", [])
        count = raw_data.get("count", len(matches_list))
        if "resultSet" in raw_data and isinstance(raw_data["resultSet"], dict):
            count = raw_data["resultSet"].get("count", count)

        return MatchListResponseSchema(count=count, matches=matches_list)

    except FootballDataAuthError as err:
        logger.error(f"Authentication error in football endpoint: {err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with external football data service. Please check API key configuration.",
        )
    except FootballDataRateLimitError as err:
        logger.warning(f"Rate limit exceeded in football endpoint: {err}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Football Data API rate limit exceeded. Please try again later.",
        )
    except FootballDataNotFoundError as err:
        logger.error(f"Resource not found in football endpoint: {err}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested football data resource was not found.",
        )
    except FootballDataTimeoutError as err:
        logger.error(f"Timeout in football endpoint: {err}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Football data service is temporarily unavailable (timeout).",
        )
    except FootballDataAPIError as err:
        logger.error(f"API error in football endpoint: {err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from external football service.",
        )
    except Exception as err:
        logger.exception("Unexpected error processing football matches endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while retrieving match data.",
        )
