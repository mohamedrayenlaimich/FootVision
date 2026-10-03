import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from app.services.sportmonks.client import SportmonksClient, sportmonks_client

logger = logging.getLogger("sportmonks.calendar")

DEFAULT_INCLUDES = [
    "participants",
    "scores",
    "league",
    "state",
    "venue",
    "round",
    "stage",
]


class SportmonksCalendarService:
    """
    High-level service for querying football match calendar, schedules,
    livescores, and fixture details from Sportmonks API v3.
    """

    def __init__(self, client: Optional[SportmonksClient] = None):
        self.client = client or sportmonks_client

    def normalize_fixture(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a Sportmonks fixture JSON into a standardized, rich FootVision match object.
        """
        participants = raw.get("participants", []) or []
        home_participant: Dict[str, Any] = {}
        away_participant: Dict[str, Any] = {}

        for p in participants:
            meta = p.get("meta", {}) or {}
            loc = meta.get("location")
            if loc == "home":
                home_participant = p
            elif loc == "away":
                away_participant = p

        # If location is not explicitly tagged, fall back to order [home, away]
        if not home_participant and len(participants) > 0:
            home_participant = participants[0]
        if not away_participant and len(participants) > 1:
            away_participant = participants[1]

        # Extract scores
        scores = raw.get("scores", []) or []
        home_score = None
        away_score = None
        ht_home = None
        ht_away = None

        for sc in scores:
            desc = (sc.get("description") or "").upper()
            score_data = sc.get("score") or {}
            goals = score_data.get("goals")
            participant_side = score_data.get("participant")

            if desc in ("CURRENT", "SCORE"):
                if participant_side == "home":
                    home_score = goals
                elif participant_side == "away":
                    away_score = goals
            elif desc in ("1ST_HALF", "HALF_TIME", "HT"):
                if participant_side == "home":
                    ht_home = goals
                elif participant_side == "away":
                    ht_away = goals

        # If full-time or normal time scores exist but CURRENT was missing
        if home_score is None:
            for sc in scores:
                desc = (sc.get("description") or "").upper()
                score_data = sc.get("score") or {}
                goals = score_data.get("goals")
                participant_side = score_data.get("participant")
                if desc in ("FULL_TIME", "FT", "ORDINARY_TIME", "2ND_HALF"):
                    if participant_side == "home":
                        home_score = goals
                    elif participant_side == "away":
                        away_score = goals

        state_data = raw.get("state") or {}
        state_name = state_data.get("name", "Scheduled")
        state_short = state_data.get("short_name", "")

        # Determine status flags
        is_live = state_name.lower() in [
            "inplay", "1st half", "2nd half", "half time", "extra time", "penalties"
        ]
        is_finished = state_name.lower() in [
            "finished", "full-time", "ended", "ft", "aet", "pen."
        ]

        league_data = raw.get("league") or {}
        venue_data = raw.get("venue") or {}
        round_data = raw.get("round") or {}

        # Starting time parsing
        starting_at = raw.get("starting_at", "")
        formatted_date = ""
        formatted_time = ""
        if starting_at:
            try:
                dt = datetime.strptime(starting_at[:19], "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime("%Y-%m-%d")
                formatted_time = dt.strftime("%H:%M")
            except Exception:
                formatted_date = starting_at[:10]
                formatted_time = starting_at[11:16]

        return {
            "id": raw.get("id"),
            "name": raw.get("name", ""),
            "starting_at": starting_at,
            "match_date": formatted_date,
            "kickoff_time": formatted_time,
            "starting_at_timestamp": raw.get("starting_at_timestamp"),
            "status": {
                "name": state_name,
                "short": state_short,
                "is_live": is_live,
                "is_finished": is_finished,
            },
            "result_info": raw.get("result_info"),
            "length": raw.get("length", 90),
            "has_odds": raw.get("has_odds", False),
            "league": {
                "id": league_data.get("id"),
                "name": league_data.get("name", "Unknown League"),
                "logo": league_data.get("image_path"),
                "round": round_data.get("name"),
            },
            "home_team": {
                "id": home_participant.get("id"),
                "name": home_participant.get("name", "Home Team"),
                "short_code": home_participant.get("short_code"),
                "logo": home_participant.get("image_path"),
                "score": home_score,
            },
            "away_team": {
                "id": away_participant.get("id"),
                "name": away_participant.get("name", "Away Team"),
                "short_code": away_participant.get("short_code"),
                "logo": away_participant.get("image_path"),
                "score": away_score,
            },
            "score": {
                "home": home_score,
                "away": away_score,
                "half_time": {
                    "home": ht_home,
                    "away": ht_away,
                } if (ht_home is not None or ht_away is not None) else None,
            },
            "venue": {
                "id": venue_data.get("id"),
                "name": venue_data.get("name"),
                "city": venue_data.get("city_name") or venue_data.get("city"),
            } if venue_data else None,
        }

    async def get_my_leagues(self) -> List[Dict[str, Any]]:
        """
        Fetch available football leagues permitted on the token.
        """
        try:
            res = await self.client.get(
                endpoint="/my/leagues",
                use_root_v3=True,
                ttl_seconds=300,  # 5 min cache
            )
            raw_leagues = res.get("data", []) or []
            # Filter football leagues (sport_id == 1 or has name)
            leagues = []
            for lg in raw_leagues:
                # Sport ID 1 is soccer/football
                if lg.get("sport_id") == 1:
                    leagues.append({
                        "id": lg.get("id"),
                        "name": lg.get("name"),
                        "active": lg.get("active", True),
                        "image_path": lg.get("image_path"),
                    })
            return leagues
        except Exception as e:
            logger.warning("Error fetching Sportmonks leagues: %s", e)
            return [
                {"id": 271, "name": "Superliga", "active": True},
                {"id": 501, "name": "Premiership", "active": True},
                {"id": 513, "name": "Premiership Play-Offs", "active": True},
                {"id": 1659, "name": "Superliga Play-offs", "active": True},
            ]

    async def get_calendar(
        self,
        start_date: str,
        end_date: str,
        league_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch match fixtures between two dates: start_date to end_date (YYYY-MM-DD).
        """
        endpoint = f"/fixtures/between/{start_date}/{end_date}"
        params: Dict[str, Any] = {}
        if league_id:
            params["filters"] = f"fixtureLeagues:{league_id}"

        res = await self.client.get(
            endpoint=endpoint,
            params=params,
            includes=DEFAULT_INCLUDES,
            ttl_seconds=60,
        )

        raw_fixtures = res.get("data", []) or []
        fixtures = [self.normalize_fixture(f) for f in raw_fixtures]

        # In-memory filter fallback for league_id if API filter didn't apply
        if league_id:
            fixtures = [f for f in fixtures if f.get("league", {}).get("id") == league_id]

        # Sort chronologically by starting_at
        fixtures.sort(key=lambda x: x.get("starting_at") or "")
        return fixtures

    async def get_fixtures_by_date(
        self,
        date_str: str,
        league_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all matches for a specific date (YYYY-MM-DD).
        """
        endpoint = f"/fixtures/date/{date_str}"
        params: Dict[str, Any] = {}
        if league_id:
            params["filters"] = f"fixtureLeagues:{league_id}"

        res = await self.client.get(
            endpoint=endpoint,
            params=params,
            includes=DEFAULT_INCLUDES,
            ttl_seconds=30,
        )

        raw_fixtures = res.get("data", []) or []
        fixtures = [self.normalize_fixture(f) for f in raw_fixtures]

        if league_id:
            fixtures = [f for f in fixtures if f.get("league", {}).get("id") == league_id]

        fixtures.sort(key=lambda x: x.get("starting_at") or "")
        return fixtures

    async def get_livescores(self) -> List[Dict[str, Any]]:
        """
        Fetch in-play or today's live matches.
        """
        res = await self.client.get(
            endpoint="/livescores",
            includes=DEFAULT_INCLUDES,
            ttl_seconds=15,  # Short TTL for live data
        )

        raw_fixtures = res.get("data", []) or []
        return [self.normalize_fixture(f) for f in raw_fixtures]

    async def get_fixture_details(self, fixture_id: int) -> Dict[str, Any]:
        """
        Fetch comprehensive fixture details including events, lineups, statistics.
        """
        extended_includes = DEFAULT_INCLUDES + [
            "events",
            "lineups",
            "statistics",
            "coaches",
            "referees",
        ]
        res = await self.client.get(
            endpoint=f"/fixtures/{fixture_id}",
            includes=extended_includes,
            ttl_seconds=45,
        )

        raw = res.get("data", {}) or {}
        normalized = self.normalize_fixture(raw)
        normalized["events"] = raw.get("events", [])
        normalized["lineups"] = raw.get("lineups", [])
        normalized["statistics"] = raw.get("statistics", [])
        return normalized


# Singleton instance
sportmonks_calendar_service = SportmonksCalendarService()
