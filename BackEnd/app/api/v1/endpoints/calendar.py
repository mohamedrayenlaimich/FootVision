import logging
from typing import Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Query, HTTPException
from app.services.sportmonks.calendar import sportmonks_calendar_service

logger = logging.getLogger("api.calendar")
router = APIRouter()


@router.get("/leagues", summary="Get supported leagues on Sportmonks token")
async def get_leagues():
    """
    Retrieve all leagues available on the configured Sportmonks token.
    """
    try:
        leagues = await sportmonks_calendar_service.get_my_leagues()
        return {"total": len(leagues), "leagues": leagues}
    except Exception as e:
        logger.error("Failed to fetch leagues: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches", summary="Get match calendar for date range")
async def get_calendar_matches(
    start_date: Optional[str] = Query(
        None,
        description="Start date in YYYY-MM-DD format. Defaults to 7 days before today."
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date in YYYY-MM-DD format. Defaults to 21 days after today."
    ),
    league_id: Optional[int] = Query(
        None,
        description="Filter by Sportmonks League ID"
    ),
    status: Optional[str] = Query(
        None,
        description="Filter status: 'all', 'live', 'upcoming', 'finished'"
    ),
):
    """
    Get fixtures between start_date and end_date from Sportmonks API.
    Provides match calendar data with team badges, kickoff times, venues, and live scores.
    """
    try:
        today = date.today()
        if not start_date:
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")

        matches = await sportmonks_calendar_service.get_calendar(
            start_date=start_date,
            end_date=end_date,
            league_id=league_id,
        )

        # Apply status filter if provided
        if status and status.lower() != "all":
            st = status.lower()
            if st == "live":
                matches = [m for m in matches if m["status"]["is_live"]]
            elif st == "upcoming":
                matches = [m for m in matches if not m["status"]["is_finished"] and not m["status"]["is_live"]]
            elif st == "finished":
                matches = [m for m in matches if m["status"]["is_finished"]]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total": len(matches),
            "matches": matches,
        }
    except Exception as e:
        logger.error("Failed to fetch match calendar: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date/{date_str}", summary="Get matches for a specific date")
async def get_matches_for_date(
    date_str: str,
    league_id: Optional[int] = Query(None, description="Optional League ID filter"),
):
    """
    Retrieve all match calendar fixtures scheduled for a specific date (YYYY-MM-DD).
    """
    try:
        matches = await sportmonks_calendar_service.get_fixtures_by_date(
            date_str=date_str,
            league_id=league_id,
        )
        return {
            "date": date_str,
            "total": len(matches),
            "matches": matches,
        }
    except Exception as e:
        logger.error("Failed to fetch matches for date %s: %s", date_str, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/livescores", summary="Get live football matches")
async def get_livescores():
    """
    Fetch in-play matches right now from Sportmonks.
    """
    try:
        matches = await sportmonks_calendar_service.get_livescores()
        return {
            "total": len(matches),
            "matches": matches,
        }
    except Exception as e:
        logger.error("Failed to fetch livescores: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixture/{fixture_id}", summary="Get detailed fixture data")
async def get_fixture(fixture_id: int):
    """
    Retrieve detailed fixture information including lineups, statistics, and events.
    """
    try:
        fixture = await sportmonks_calendar_service.get_fixture_details(fixture_id)
        return {"fixture": fixture}
    except Exception as e:
        logger.error("Failed to fetch fixture %s: %s", fixture_id, e)
        raise HTTPException(status_code=500, detail=str(e))
