export interface MatchCalendarItem {
  id: number;
  name: string;
  starting_at: string;
  match_date: string;
  kickoff_time: string;
  starting_at_timestamp?: number;
  status: {
    name: string;
    short: string;
    is_live: boolean;
    is_finished: boolean;
  };
  result_info?: string | null;
  length: number;
  has_odds: boolean;
  league: {
    id: number;
    name: string;
    logo?: string;
    round?: string;
  };
  home_team: {
    id: number;
    name: string;
    short_code?: string;
    logo?: string;
    score?: number | null;
  };
  away_team: {
    id: number;
    name: string;
    short_code?: string;
    logo?: string;
    score?: number | null;
  };
  score: {
    home?: number | null;
    away?: number | null;
    half_time?: {
      home?: number | null;
      away?: number | null;
    } | null;
  };
  venue?: {
    id?: number;
    name?: string;
    city?: string;
  } | null;
}

export interface CalendarMatchesResponse {
  start_date: string;
  end_date: string;
  total: number;
  matches: MatchCalendarItem[];
}

export interface SportmonksLeague {
  id: number;
  name: string;
  active?: boolean;
  image_path?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchCalendarMatches(params?: {
  startDate?: string;
  endDate?: string;
  leagueId?: number;
  status?: string;
}): Promise<CalendarMatchesResponse> {
  const query = new URLSearchParams();
  if (params?.startDate) query.append("start_date", params.startDate);
  if (params?.endDate) query.append("end_date", params.endDate);
  if (params?.leagueId) query.append("league_id", params.leagueId.toString());
  if (params?.status && params.status !== "all") query.append("status", params.status);

  const queryString = query.toString();
  const url = `${API_BASE_URL}/calendar/matches${queryString ? `?${queryString}` : ""}`;

  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch calendar matches" }));
    throw new Error(errorData.detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function fetchCalendarByDate(dateStr: string, leagueId?: number): Promise<{
  date: string;
  total: number;
  matches: MatchCalendarItem[];
}> {
  const query = leagueId ? `?league_id=${leagueId}` : "";
  const url = `${API_BASE_URL}/calendar/date/${dateStr}${query}`;

  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    throw new Error(`Failed to fetch matches for date: ${dateStr}`);
  }
  return res.json();
}

export async function fetchCalendarLivescores(): Promise<{
  total: number;
  matches: MatchCalendarItem[];
}> {
  const url = `${API_BASE_URL}/calendar/livescores`;
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    throw new Error("Failed to fetch live scores");
  }
  return res.json();
}

export async function fetchCalendarLeagues(): Promise<{
  total: number;
  leagues: SportmonksLeague[];
}> {
  const url = `${API_BASE_URL}/calendar/leagues`;
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    throw new Error("Failed to fetch leagues");
  }
  return res.json();
}

export async function fetchCalendarFixture(fixtureId: number): Promise<{
  fixture: MatchCalendarItem & {
    events?: any[];
    lineups?: any[];
    statistics?: any[];
  };
}> {
  const url = `${API_BASE_URL}/calendar/fixture/${fixtureId}`;
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    throw new Error("Failed to fetch fixture details");
  }
  return res.json();
}
