import asyncio
import sys
import os

# Add BackEnd to sys.path
sys.path.insert(0, os.path.abspath("BackEnd"))

from app.services.sportmonks.calendar import sportmonks_calendar_service

async def main():
    print("Testing Sportmonks Calendar Service...")
    leagues = await sportmonks_calendar_service.get_my_leagues()
    print("Leagues:", len(leagues), [l["name"] for l in leagues])

    calendar = await sportmonks_calendar_service.get_calendar("2026-10-01", "2026-10-25")
    print(f"Total fixtures in Oct 2026: {len(calendar)}")
    for f in calendar[:3]:
        print(f"  [{f['match_date']} {f['kickoff_time']}] {f['league']['name']}: {f['home_team']['name']} vs {f['away_team']['name']} | Status: {f['status']['name']}")

if __name__ == "__main__":
    asyncio.run(main())
