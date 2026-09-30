# FootVision AI - Football-Data.org API Integration

## 1. Overview
FootVision AI integrates [football-data.org](https://www.football-data.org/) (v4 API) to complement computer-vision player/ball tracking analytics with official match metadata, historical scores, upcoming fixtures, and competition standings.

---

## 2. Architecture & Security

```
football-data.org (v4 API)
           │ (HTTP Header: X-Auth-Token)
           ▼
    FootballDataClient (app.services.football_data.client)
           │
           ▼
   FootballMatchService (app.services.football_data.matches)
           │ (Normalization & Validation)
           ▼
   Match API Router (app.api.v1.endpoints.football)
           │ (JSON Response)
           ▼
 Next.js Frontend Client (lib.api.football) / Future ML & PostgreSQL
```

### Security Principles:
- **Zero API Key Exposure**: The `FOOTBALL_DATA_API_KEY` is loaded on the backend via `.env` / `app.core.config`.
- **Git Protection**: `.env` is strictly ignored by Git in `.gitignore`.
- **Environment Template**: `.env.example` provides a template without revealing real tokens.
- **Frontend Isolation**: Next.js communicates solely with the FootVision FastAPI backend (`/api/v1/football/matches`).

---

## 3. Configuration & Environment Variables

Required environment variables in `BackEnd/.env`:
```env
FOOTBALL_DATA_API_KEY=your_actual_api_key_here
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
```

Template in `BackEnd/.env.example`:
```env
FOOTBALL_DATA_API_KEY=your_api_key_here
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
```

---

## 4. Backend API Endpoint

### `GET /api/v1/football/matches`

#### Query Parameters:
| Parameter | Type | Format | Description | Example |
|---|---|---|---|---|
| `dateFrom` | string | `YYYY-MM-DD` | Start date filter | `2026-01-01` |
| `dateTo` | string | `YYYY-MM-DD` | End date filter | `2026-01-31` |
| `competition` | string | `Code/ID` | Competition code or ID | `PL`, `CL`, `PD` |
| `status` | string | `ENUM` | Match status (`FINISHED`, `SCHEDULED`, `IN_PLAY`) | `FINISHED` |
| `limit` | integer | `1-500` | Maximum matches to return | `10` |
| `offset` | integer | `>=0` | Pagination index | `0` |

#### Sample JSON Response:
```json
{
  "count": 1,
  "matches": [
    {
      "id": 12345,
      "utcDate": "2026-01-15T19:00:00Z",
      "status": "FINISHED",
      "matchday": 21,
      "stage": "REGULAR_SEASON",
      "competition": {
        "id": 2021,
        "name": "Premier League",
        "code": "PL"
      },
      "homeTeam": {
        "id": 57,
        "name": "Arsenal FC",
        "shortName": "Arsenal",
        "tla": "ARS",
        "crest": "https://crests.football-data.org/57.png"
      },
      "awayTeam": {
        "id": 61,
        "name": "Chelsea FC",
        "shortName": "Chelsea",
        "tla": "CHE",
        "crest": "https://crests.football-data.org/61.png"
      },
      "score": {
        "winner": "HOME_TEAM",
        "duration": "REGULAR",
        "fullTime": {
          "home": 2,
          "away": 1
        }
      }
    }
  ]
}
```

---

## 5. Error Handling & HTTP Status Codes

| Exception | HTTP Status | Detail |
|---|---|---|
| `FootballDataAuthError` | `401 Unauthorized` | Invalid or missing API key |
| `FootballDataNotFoundError` | `404 Not Found` | Requested competition or match not found |
| `FootballDataRateLimitError` | `429 Too Many Requests` | API rate limit exceeded |
| `FootballDataTimeoutError` | `504 Gateway Timeout` | External API request timeout |
| `FootballDataAPIError` | `502 Bad Gateway` | Network error / API service unavailable |

---

## 6. Testing

Unit tests for client, service layer, and FastAPI endpoints are located in `Tests/backend/`:
- `test_football_client.py`: Mocks `httpx` to verify header handling, 200 responses, 401 auth errors, 429 rate limits, and timeouts.
- `test_football_matches.py`: Tests `FootballMatchService` filter mapping and client-side pagination.
- `test_football_endpoint.py`: Uses `FastAPI TestClient` to test route response validation and status code translations.

Run unit tests locally:
```powershell
$env:PYTHONPATH="BackEnd"; python -m pytest Tests/backend -v
```

---

## 7. Next.js Frontend Layer

- **API Module**: `FrontEnd/src/lib/api/football.ts` exports `fetchMatches(params)` function.
- **UI Component**: `FrontEnd/src/components/FootballMatchList.tsx` provides an interactive match viewer with competition filters, date pickers, live/upcoming badges, and error states.

---

## 8. Future PostgreSQL & ML Feature Pipeline Integration

### Local Caching & Storage
To avoid repeated external API consumption and respect rate limits:
1. Matches and team results are stored in PostgreSQL (`matches`, `teams`, `competitions`, `scores` tables).
2. Cached match data feeds FootVision's feature engineering pipeline:
   - Rolling home/away team form (last 5 matches)
   - Goals scored / conceded averages
   - Head-to-head match history
   - Rest days between matches
3. Combined with CV tracking analytics (distance covered, speed, team compactness) to train machine learning prediction models (XGBoost, Poisson regression, Poisson Expected Goals).
