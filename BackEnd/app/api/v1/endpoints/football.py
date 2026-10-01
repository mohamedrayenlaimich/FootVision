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
# One shared service instance — avoids redundant client creation
match_service = FootballMatchService()


def _handle_football_data_errors(err: Exception) -> None:
    """Centralized error handler — raises the appropriate HTTP exception."""
    if isinstance(err, FootballDataAuthError):
        logger.error("Authentication error (football-data.org): %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication failed with football-data.org. "
                "Please check FOOTBALL_DATA_API_KEY in BackEnd/.env."
            ),
        )
    if isinstance(err, FootballDataRateLimitError):
        logger.warning("Rate limit exceeded (football-data.org): %s", err)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Football-data.org rate limit exceeded. Please try again later.",
        )
    if isinstance(err, FootballDataNotFoundError):
        logger.error("Resource not found (football-data.org): %s", err)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested football data resource was not found.",
        )
    if isinstance(err, FootballDataTimeoutError):
        logger.error("Timeout (football-data.org): %s", err)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Football-data.org service is temporarily unavailable (timeout).",
        )
    if isinstance(err, FootballDataAPIError):
        logger.error("API error (football-data.org): %s", err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from football-data.org.",
        )
    logger.exception("Unexpected error in football endpoint")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An internal server error occurred while retrieving match data.",
    )


@router.get(
    "/matches",
    response_model=MatchListResponseSchema,
    summary="Get Football Matches (football-data.org)",
    description=(
        "Retrieve normalized football match data from football-data.org. "
        "Supports filtering by date range, competition, and status. "
        "Data provided by football-data.org"
    ),
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
    limit: Optional[int] = Query(None, ge=1, le=500, description="Maximum number of matches to return"),
    offset: Optional[int] = Query(None, ge=0, description="Pagination offset index"),
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

        # If API key is not configured, raw_data contains available=False
        if raw_data.get("available") is False:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=raw_data.get("message", "Football data service is not configured."),
            )

        matches_list = raw_data.get("matches", [])
        count = raw_data.get("count", len(matches_list))
        if "resultSet" in raw_data and isinstance(raw_data["resultSet"], dict):
            count = raw_data["resultSet"].get("count", count)

        return MatchListResponseSchema(count=count, matches=matches_list)

    except HTTPException:
        raise
    except Exception as err:
        _handle_football_data_errors(err)


@router.get(
    "/football-matches/{match_id}",
    summary="Get Single Match (football-data.org)",
    description=(
        "Retrieve a single match by its unique football-data.org match ID. "
        "Uses GET /v4/matches/{match_id} — each call is scoped to the exact match_id. "
        "Data provided by football-data.org"
    ),
)
async def get_football_match(match_id: int):
    """
    Returns data for exactly one match identified by match_id.
    Different match_ids always produce different responses — no shared state.
    Cache key (if caching is added) must include match_id.
    """
    try:
        raw_data = await match_service.get_match(match_id)

        if raw_data.get("available") is False:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=raw_data.get("message", "Football data service is not configured."),
            )

        return raw_data

    except HTTPException:
        raise
    except Exception as err:
        _handle_football_data_errors(err)


@router.get(
    "/competitions/{competition_code}/matches",
    response_model=MatchListResponseSchema,
    summary="Get Competition Matches (football-data.org)",
    description=(
        "Retrieve all matches for a specific competition by its code (e.g., PL, CL, BL1). "
        "Uses GET /v4/competitions/{competition_code}/matches. "
        "Data provided by football-data.org"
    ),
)
async def get_competition_matches(
    competition_code: str,
    dateFrom: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    dateTo: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    status_filter: Optional[str] = Query(None, alias="status", description="Match status (e.g., SCHEDULED, FINISHED)"),
    matchday: Optional[int] = Query(None, description="Filter by matchday number"),
):
    try:
        raw_data = await match_service.get_competition_matches(
            competition_code=competition_code.upper(),
            date_from=dateFrom,
            date_to=dateTo,
            status=status_filter,
            matchday=matchday,
        )

        if raw_data.get("available") is False:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=raw_data.get("message", "Football data service is not configured."),
            )

        matches_list = raw_data.get("matches", [])
        count = raw_data.get("count", len(matches_list))
        if "resultSet" in raw_data and isinstance(raw_data["resultSet"], dict):
            count = raw_data["resultSet"].get("count", count)

        return MatchListResponseSchema(count=count, matches=matches_list)

    except HTTPException:
        raise
    except Exception as err:
        _handle_football_data_errors(err)
