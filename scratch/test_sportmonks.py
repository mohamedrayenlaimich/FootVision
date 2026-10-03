import httpx
import json

token = 'fT3UKE2YFmSNJ4eruJUxBqwo5oTr7wBPs6cBbWEz1pwlFoqqkldn6XKMiXyh'

r = httpx.get(f'https://api.sportmonks.com/v3/my/leagues?api_token={token}')
data = r.json()
leagues = data.get('data', [])
print(f'Total leagues available on token: {len(leagues)}')
for lg in leagues:
    print(f"- ID {lg['id']}: {lg['name']} ({lg.get('country', {}).get('name', 'N/A') if isinstance(lg.get('country'), dict) else ''})")

# Let's inspect fixtures for one of these leagues or date ranges
if leagues:
    first_league_id = leagues[0]['id']
    print(f"\nChecking fixtures for League {first_league_id} ({leagues[0]['name']})...")
    # Let's fetch seasons or fixtures
    f_res = httpx.get(f"https://api.sportmonks.com/v3/football/fixtures/between/2026-08-01/2026-10-15?api_token={token}&include=participants;scores;league;state;venue")
    f_data = f_res.json()
    print("Fixtures between status:", f_res.status_code, "Count:", len(f_data.get('data', [])))
    if f_data.get('data'):
        print("Sample fixture:")
        sample = f_data['data'][0]
        print(json.dumps(sample, indent=2)[:800])
