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

export interface FixtureItem {
  fixture_id: number;
  date: string;
  status?: {
    long?: string;
    short?: string;
    elapsed?: number;
  };
  venue?: {
    id?: number;
    name?: string;
    city?: string;
  };
  league?: {
    id: number;
    name: string;
    country?: string;
    logo?: string;
    flag?: string;
    season?: number;
    round?: string;
  };
  home_team: {
    id: number;
    name: string;
    logo?: string;
    winner?: boolean;
  };
  away_team: {
    id: number;
    name: string;
    logo?: string;
    winner?: boolean;
  };
  goals?: {
    home?: number;
    away?: number;
  };
  score?: {
    halftime?: { home?: number; away?: number };
    fulltime?: { home?: number; away?: number };
  };
}

export interface FixtureListResponse {
  results: number;
  fixtures: FixtureItem[];
  note?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

  const response = await fetch(url, { method: "GET", headers: { "Content-Type": "application/json" } });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to fetch matches" }));
    throw new Error(errorData.detail || `Error ${response.status}`);
  }
  return response.json();
}

export async function fetchFixtures(params?: {
  league?: number;
  season?: number;
  date?: string;
  next?: number;
  status?: string;
  team?: number;
  fixture_id?: number;
}): Promise<FixtureListResponse> {
  const query = new URLSearchParams();
  if (params?.league) query.append("league", params.league.toString());
  if (params?.season) query.append("season", params.season.toString());
  if (params?.date) query.append("date", params.date);
  if (params?.next) query.append("next", params.next.toString());
  if (params?.status) query.append("status", params.status);
  if (params?.team) query.append("team", params.team.toString());
  if (params?.fixture_id) query.append("fixture_id", params.fixture_id.toString());

  const queryString = query.toString();
  const url = `${API_BASE_URL}/football/fixtures${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, { method: "GET", headers: { "Content-Type": "application/json" } });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to fetch fixtures" }));
    throw new Error(errorData.detail || `Error ${response.status}`);
  }
  return response.json();
}

export async function fetchMatchDetails(fixtureId: number): Promise<{ fixture: FixtureItem; note?: string }> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}`);
  if (!response.ok) throw new Error("Failed to fetch match details");
  return response.json();
}

export async function fetchMatchStatistics(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/statistics`);
  if (!response.ok) throw new Error("Failed to fetch match statistics");
  return response.json();
}

export async function fetchMatchEvents(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/events`);
  if (!response.ok) throw new Error("Failed to fetch match events");
  return response.json();
}

export async function fetchMatchLineups(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/lineups`);
  if (!response.ok) throw new Error("Failed to fetch match lineups");
  return response.json();
}

export async function fetchMatchPlayers(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/players`);
  if (!response.ok) throw new Error("Failed to fetch match player stats");
  return response.json();
}

export async function fetchMatchHeadToHead(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/head-to-head`);
  if (!response.ok) throw new Error("Failed to fetch head-to-head history");
  return response.json();
}

export async function fetchMatchPredictions(fixtureId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/football/matches/${fixtureId}/predictions`);
  if (!response.ok) throw new Error("Failed to fetch match predictions");
  return response.json();
}
