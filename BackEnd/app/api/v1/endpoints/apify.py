"""
Apify / FotMob live data endpoints.

All data is sourced from the FotMob website via the Apify crawloop/fotmob-scraper actor.
No mock data — if the Apify actor fails, `available: false` is returned.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.apify.fotmob_service import ApifyFotMobService

logger = logging.getLogger(__name__)
router = APIRouter()

fotmob = ApifyFotMobService()


@router.get(
    "/live/today",
    summary="Today's Fixtures (FotMob via Apify)",
    description="Fetch all of today's football fixtures with live scores, status, and xG from FotMob via Apify.",
)
async def get_todays_matches():
    result = await fotmob.get_todays_matches()
    return result


@router.get(
    "/live/match/{match_id}",
    summary="Full Match Detail (FotMob via Apify)",
    description="Get complete match detail including stats, lineups, match events, xG, and player ratings from FotMob.",
)
async def get_match_detail(match_id: str):
    result = await fotmob.get_match_detail(match_id)
    if not result.get("available"):
        raise HTTPException(status_code=404, detail=result.get("message", "Match not found."))
    return result


@router.get(
    "/live/standings",
    summary="League Standings (FotMob via Apify)",
    description="Get the current league table for any league from FotMob.",
)
async def get_standings(
    league_id: int = Query(..., description="FotMob league ID (e.g. 47 for Premier League)"),
    season: int = Query(2024, description="Season year (e.g. 2024)"),
):
    result = await fotmob.get_standings(league_id, season)
    return result


@router.get(
    "/live/team/{team_id}/matches",
    summary="Team Recent Matches (FotMob via Apify)",
    description="Get recent and upcoming fixtures for a specific team from FotMob.",
)
async def get_team_matches(team_id: int):
    result = await fotmob.get_team_matches(team_id)
    return result
