export interface Team {
  id: number;
  name: string;
  shortName?: string;
  tla?: string;
  crest?: string;
}

export interface Competition {
  id: number;
  name: string;
  code?: string;
  type?: string;
  emblem?: string;
}

export interface ScoreTime {
  home?: number;
  away?: number;
}

export interface MatchScore {
  winner?: string;
  duration?: string;
  fullTime?: ScoreTime;
  halfTime?: ScoreTime;
}

export interface Match {
  id: number;
  utcDate: string;
  status: string;
  matchday?: number;
  stage?: string;
  group?: string;
  competition?: Competition;
  homeTeam: Team;
  awayTeam: Team;
  score?: MatchScore;
}

export interface MatchListResponse {
  count: number;
  matches: Match[];
}

export interface FetchMatchesParams {
  dateFrom?: string;
  dateTo?: string;
  competition?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Fetch matches via FootVision FastAPI backend (/api/v1/football/matches).
 * Keeps API keys safely on the backend.
 */
export async function fetchMatches(params?: FetchMatchesParams): Promise<MatchListResponse> {
  const query = new URLSearchParams();
  if (params?.dateFrom) query.append("dateFrom", params.dateFrom);
  if (params?.dateTo) query.append("dateTo", params.dateTo);
  if (params?.competition) query.append("competition", params.competition);
  if (params?.status) query.append("status", params.status);
  if (params?.limit) query.append("limit", params.limit.toString());
  if (params?.offset) query.append("offset", params.offset.toString());

  const queryString = query.toString();
  const url = `${API_BASE_URL}/football/matches${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to fetch matches" }));
    throw new Error(errorData.detail || `Error ${response.status}`);
  }

  return response.json();
}
