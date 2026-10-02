import logging
from typing import Any, Dict, List, Optional

from app.services.api_football.client import APIFootballClient, APIFootballAuthError

logger = logging.getLogger(__name__)

# IMPORTANT: No mock, demo, or static fallback data in production.
# This service retrieves live match fixtures directly from configured APIs.


class APIFootballFixtureService:
    """
    Service layer for retrieving fixtures from API-Football (/fixtures endpoint)
    or converting live matches from football-data.org API.
    """

    def __init__(self, client: Optional[APIFootballClient] = None):
        self.client = client or APIFootballClient()

    async def get_fixtures(
        self,
        league: Optional[int] = None,
        season: Optional[int] = None,
        date: Optional[str] = None,
        next_matches: Optional[int] = None,
        status: Optional[str] = None,
        team: Optional[int] = None,
        fixture_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        is_placeholder_key = not self.client.api_key or self.client.api_key == "your_api_football_key_here"

        if not is_placeholder_key:
            params: Dict[str, Any] = {}
            if fixture_id:
                params["id"] = fixture_id
            if league:
                params["league"] = league
            if season:
                params["season"] = season
            if date:
                params["date"] = date
            if next_matches:
                params["next"] = next_matches
            if status:
                params["status"] = status
            if team:
                params["team"] = team

            try:
                raw_response = await self.client.get("fixtures", params=params)
                res = self._normalize_fixtures(raw_response)
                if res.get("fixtures"):
                    return res
            except Exception as err:
                logger.info("Live API-Football unavailable (%s), trying live football-data.org provider...", err)

        # Fallback / Primary provider using live football-data.org API
        try:
            from app.services.football_data.matches import FootballMatchService
            fd_service = FootballMatchService()
            if fd_service._is_key_configured():
                league_code_map = {39: "PL", 140: "PD", 78: "BL1", 135: "SA", 61: "FL1", 2: "CL", 3: "EL"}
                comp_code = league_code_map.get(league) if league else None
                fd_status = None
                if status:
                    st_map = {"FT": "FINISHED", "NS": "SCHEDULED", "1H": "IN_PLAY", "HT": "PAUSED", "2H": "IN_PLAY", "LIVE": "IN_PLAY"}
                    fd_status = st_map.get(status.upper(), status.upper())

                if fixture_id:
                    fd_data = await fd_service.get_match(fixture_id)
                    if fd_data and "id" in fd_data:
                        return {
                            "results": 1,
                            "fixtures": [self._convert_football_data_to_fixture(fd_data)],
                        }
                else:
                    fd_data = await fd_service.get_matches(
                        date_from=date,
                        date_to=date,
                        competition=comp_code,
                        status=fd_status,
                        limit=next_matches or 30,
                    )
                    raw_matches = fd_data.get("matches", [])
                    if raw_matches:
                        converted = [self._convert_football_data_to_fixture(m) for m in raw_matches]
                        return {"results": len(converted), "fixtures": converted}
        except Exception as fd_err:
            logger.warning("Football-data.org service failed: %s", fd_err)

        # Return real response structure with 0 results if live APIs yield no fixtures.
        # Never fall back to static or mock data.
        return {
            "results": 0,
            "fixtures": [],
        }

    def _convert_football_data_to_fixture(self, item: Dict[str, Any]) -> Dict[str, Any]:
        match_id = item.get("id")
        date_str = item.get("utcDate", "")
        status_raw = item.get("status", "SCHEDULED")
        
        status_map = {
            "FINISHED": {"long": "Match Finished", "short": "FT", "elapsed": 90},
            "IN_PLAY": {"long": "In Play", "short": "1H", "elapsed": 45},
            "PAUSED": {"long": "Half Time", "short": "HT", "elapsed": 45},
            "SCHEDULED": {"long": "Not Started", "short": "NS", "elapsed": None},
            "TIMED": {"long": "Not Started", "short": "NS", "elapsed": None},
            "POSTPONED": {"long": "Postponed", "short": "PST", "elapsed": None},
            "CANCELLED": {"long": "Cancelled", "short": "CANC", "elapsed": None},
        }
        st_info = status_map.get(status_raw, {"long": status_raw, "short": status_raw[:3].upper(), "elapsed": None})

        home = item.get("homeTeam", {})
        away = item.get("awayTeam", {})
        comp = item.get("competition", {})
        score = item.get("score", {})
        full_time = score.get("fullTime", {}) if score else {}
        half_time = score.get("halfTime", {}) if score else {}
        winner_str = score.get("winner") if score else None

        home_win = True if winner_str == "HOME_TEAM" else (False if winner_str == "AWAY_TEAM" else None)
        away_win = True if winner_str == "AWAY_TEAM" else (False if winner_str == "HOME_TEAM" else None)

        league_code = comp.get("code", "")
        league_id_map = {"PL": 39, "PD": 140, "BL1": 78, "SA": 135, "FL1": 61, "CL": 2, "EC": 3}
        league_id = league_id_map.get(league_code, comp.get("id", 0))

        return {
            "fixture_id": match_id,
            "date": date_str,
            "status": st_info,
            "venue": {"id": None, "name": item.get("venue", "Stadium"), "city": ""},
            "league": {
                "id": league_id,
                "name": comp.get("name", "Football Match"),
                "country": "Europe",
                "logo": comp.get("emblem", f"https://media.api-sports.io/football/leagues/{league_id}.png"),
                "flag": None,
                "season": 2025,
                "round": f"Matchday {item.get('matchday', '')}" if item.get("matchday") else item.get("stage", ""),
            },
            "home_team": {
                "id": home.get("id"),
                "name": home.get("shortName") or home.get("name", "Home Team"),
                "logo": home.get("crest"),
                "winner": home_win,
            },
            "away_team": {
                "id": away.get("id"),
                "name": away.get("shortName") or away.get("name", "Away Team"),
                "logo": away.get("crest"),
                "winner": away_win,
            },
            "goals": {
                "home": full_time.get("home"),
                "away": full_time.get("away"),
            },
            "score": {
                "halftime": {"home": half_time.get("home"), "away": half_time.get("away")},
                "fulltime": {"home": full_time.get("home"), "away": full_time.get("away")},
                "extratime": {"home": None, "away": None},
                "penalty": {"home": None, "away": None},
            },
        }

    def _normalize_fixtures(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        response_list = raw_data.get("response", [])
        normalized_fixtures = []

        for item in response_list:
            fx = item.get("fixture", {})
            lg = item.get("league", {})
            tm = item.get("teams", {})
            gl = item.get("goals", {})
            sc = item.get("score", {})

            normalized_fixtures.append({
                "fixture_id": fx.get("id"),
                "date": fx.get("date"),
                "status": {
                    "long": fx.get("status", {}).get("long"),
                    "short": fx.get("status", {}).get("short"),
                    "elapsed": fx.get("status", {}).get("elapsed"),
                },
                "venue": {
                    "id": fx.get("venue", {}).get("id"),
                    "name": fx.get("venue", {}).get("name"),
                    "city": fx.get("venue", {}).get("city"),
                },
                "league": {
                    "id": lg.get("id"),
                    "name": lg.get("name"),
                    "country": lg.get("country"),
                    "logo": lg.get("logo"),
                    "flag": lg.get("flag"),
                    "season": lg.get("season"),
                    "round": lg.get("round"),
                },
                "home_team": {
                    "id": tm.get("home", {}).get("id"),
                    "name": tm.get("home", {}).get("name"),
                    "logo": tm.get("home", {}).get("logo"),
                    "winner": tm.get("home", {}).get("winner"),
                },
                "away_team": {
                    "id": tm.get("away", {}).get("id"),
                    "name": tm.get("away", {}).get("name"),
                    "logo": tm.get("away", {}).get("logo"),
                    "winner": tm.get("away", {}).get("winner"),
                },
                "goals": {
                    "home": gl.get("home"),
                    "away": gl.get("away"),
                },
                "score": {
                    "halftime": sc.get("halftime", {}),
                    "fulltime": sc.get("fulltime", {}),
                    "extratime": sc.get("extratime", {}),
                    "penalty": sc.get("penalty", {}),
                },
            })

        return {
            "results": len(normalized_fixtures),
            "fixtures": normalized_fixtures,
        }

