"""
Apify FotMob Service — fetches LIVE football data via the FotMob scraper actor.

Actor: crawloop/fotmob-scraper
Docs: https://apify.com/crawloop/fotmob-scraper

Flow:
  1. POST /acts/crawloop~fotmob-scraper/run-sync-get-dataset-items   → runs actor + returns items immediately
  2. Parse the returned items into normalized dicts.

Supported queries (via `task_type` input param):
  - "todays_matches"     → all fixtures for today
  - "match_detail"       → full detail for a single matchId
  - "standings"          → league table for leagueId+season
  - "team_matches"       → recent fixtures for a teamId
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN", "")
ACTOR_ID = "crawloop~fotmob-scraper"
SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"

# Timeout for Apify sync run (actor usually finishes in <30s)
ACTOR_TIMEOUT = 90


class ApifyFotMobService:
    """Wrapper around the Apify FotMob scraper actor."""

    def __init__(self):
        self.token = APIFY_TOKEN

    def _is_configured(self) -> bool:
        return bool(self.token) and self.token not in ("", "your_apify_token_here")

    async def _run_actor(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run actor synchronously and return dataset items."""
        if not self._is_configured():
            logger.warning("APIFY_API_TOKEN is not configured.")
            return []

        url = f"{SYNC_URL}?token={self.token}&timeout={ACTOR_TIMEOUT}&memory=256"
        try:
            async with httpx.AsyncClient(timeout=ACTOR_TIMEOUT + 10) as client:
                resp = await client.post(url, json=input_data)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    return data
                return []
        except httpx.HTTPStatusError as e:
            logger.error("Apify actor HTTP error: %s — %s", e.response.status_code, e.response.text[:300])
            return []
        except Exception as e:
            logger.error("Apify actor request failed: %s", e)
            return []

    # ── Public methods ────────────────────────────────────────────────────

    async def get_todays_matches(self) -> Dict[str, Any]:
        """Return all of today's fixtures grouped by league."""
        items = await self._run_actor({"type": "todays_matches"})
        if not items:
            return {"available": False, "message": "No live data available. Apify actor returned no results.", "matches": []}

        return {
            "available": True,
            "source": "apify_fotmob",
            "matches": self._normalize_matches(items),
        }

    async def get_match_detail(self, match_id: str) -> Dict[str, Any]:
        """Return full match detail including stats, lineups, events, xG."""
        items = await self._run_actor({"type": "match_detail", "matchId": str(match_id)})
        if not items:
            return {"available": False, "message": f"No detail found for match {match_id}."}

        raw = items[0] if items else {}
        return {"available": True, "source": "apify_fotmob", "match": self._normalize_match_detail(raw)}

    async def get_standings(self, league_id: int, season: int) -> Dict[str, Any]:
        """Return league table standings."""
        items = await self._run_actor({"type": "standings", "leagueId": league_id, "season": season})
        if not items:
            return {"available": False, "message": "No standings data available."}
        return {"available": True, "source": "apify_fotmob", "standings": items}

    async def get_team_matches(self, team_id: int) -> Dict[str, Any]:
        """Return recent and upcoming matches for a team."""
        items = await self._run_actor({"type": "team_matches", "teamId": team_id})
        if not items:
            return {"available": False, "message": f"No matches found for team {team_id}."}
        return {
            "available": True,
            "source": "apify_fotmob",
            "matches": self._normalize_matches(items),
        }

    # ── Normalizers ───────────────────────────────────────────────────────

    def _normalize_matches(self, items: List[Dict]) -> List[Dict]:
        normalized = []
        for item in items:
            # FotMob actor may return items directly as match objects
            match_id = item.get("id") or item.get("matchId") or item.get("match_id")
            home = item.get("home") or item.get("homeTeam") or {}
            away = item.get("away") or item.get("awayTeam") or {}
            score = item.get("score") or item.get("result") or {}
            status = item.get("status") or item.get("matchStatus") or {}
            league = item.get("league") or item.get("leagueName") or item.get("tournament") or {}

            normalized.append({
                "match_id": str(match_id) if match_id else None,
                "date": item.get("date") or item.get("kickoff") or item.get("startTimestamp"),
                "status": {
                    "long": status.get("long") or status if isinstance(status, str) else "Unknown",
                    "short": status.get("short") or "",
                    "elapsed": status.get("elapsed") or item.get("minute"),
                },
                "league": {
                    "id": (league.get("id") if isinstance(league, dict) else None),
                    "name": (league.get("name") if isinstance(league, dict) else str(league)) or item.get("leagueName"),
                    "logo": league.get("logo") if isinstance(league, dict) else None,
                    "country": league.get("country") if isinstance(league, dict) else None,
                },
                "home_team": {
                    "id": home.get("id"),
                    "name": home.get("name") or home.get("shortName"),
                    "logo": home.get("logo") or home.get("imageUrl"),
                },
                "away_team": {
                    "id": away.get("id"),
                    "name": away.get("name") or away.get("shortName"),
                    "logo": away.get("logo") or away.get("imageUrl"),
                },
                "score": {
                    "home": (score.get("home") if isinstance(score, dict) else None),
                    "away": (score.get("away") if isinstance(score, dict) else None),
                },
                "xg": {
                    "home": item.get("expectedGoals", {}).get("home") or item.get("xgHome"),
                    "away": item.get("expectedGoals", {}).get("away") or item.get("xgAway"),
                },
                "raw": item,  # pass through full raw item for frontend flexibility
            })
        return normalized

    def _normalize_match_detail(self, raw: Dict) -> Dict:
        """Extract key fields from a full match detail item."""
        stats = raw.get("stats") or raw.get("matchStats") or {}
        lineups = raw.get("lineups") or raw.get("lineup") or {}
        events = raw.get("events") or raw.get("matchEvents") or []
        xg = raw.get("expectedGoals") or raw.get("xg") or {}

        return {
            "match_id": raw.get("id") or raw.get("matchId"),
            "date": raw.get("date") or raw.get("kickoff"),
            "home_team": raw.get("home") or raw.get("homeTeam") or {},
            "away_team": raw.get("away") or raw.get("awayTeam") or {},
            "score": raw.get("score") or raw.get("result") or {},
            "status": raw.get("status") or {},
            "league": raw.get("league") or raw.get("tournament") or {},
            "stats": stats,
            "lineups": lineups,
            "events": events[:50],  # cap at 50 events
            "xg": xg,
            "player_ratings": raw.get("playerRatings") or raw.get("ratings") or {},
        }
