import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Calendar, RefreshCw, Trophy, ShieldAlert, Filter, Clock, ExternalLink, MapPin } from "lucide-react";
import { fetchFixtures, FixtureItem } from "@/lib/api/football";

export default function FootballMatchList() {
  const [fixtures, setFixtures] = useState<FixtureItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [leagueFilter, setLeagueFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("");

  const loadFixtures = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: { league?: number; season?: number; date?: string; status?: string; next?: number } = {};
      if (leagueFilter) params.league = parseInt(leagueFilter);
      if (statusFilter) params.status = statusFilter;
      if (dateFilter) params.date = dateFilter;
      // Default: load next 20 upcoming matches if no filters
      if (!leagueFilter && !statusFilter && !dateFilter) {
        params.next = 20;
      }

      const data = await fetchFixtures(params);
      setFixtures(data.fixtures || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to connect to FootVision Football API.");
      }
    } finally {
      setLoading(false);
    }
  }, [leagueFilter, statusFilter, dateFilter]);

  useEffect(() => {
    loadFixtures();
  }, [loadFixtures]);

  const formatDate = (isoStr: string) => {
    try {
      const date = new Date(isoStr);
      return date.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  const getStatusBadge = (statusShort?: string, statusLong?: string) => {
    const s = (statusShort || "").toUpperCase();
    switch (s) {
      case "FT":
      case "AET":
      case "PEN":
        return (
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-bold tracking-wider">
            FINISHED
          </span>
        );
      case "1H":
      case "HT":
      case "2H":
      case "ET":
      case "BT":
      case "P":
      case "INT":
      case "LIVE":
        return (
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold tracking-wider animate-pulse">
            LIVE
          </span>
        );
      case "NS":
      case "TBD":
        return (
          <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold tracking-wider">
            UPCOMING
          </span>
        );
      case "CANC":
      case "ABD":
      case "AWD":
      case "WO":
        return (
          <span className="px-2.5 py-0.5 rounded-full bg-red-900/40 text-red-400 border border-red-800/40 text-[10px] font-bold tracking-wider">
            {statusLong || s}
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-bold tracking-wider">
            {statusLong || s || "—"}
          </span>
        );
    }
  };

  const isFinished = (s?: string) => {
    const fs = (s || "").toUpperCase();
    return ["FT", "AET", "PEN"].includes(fs);
  };

  const isLive = (s?: string) => {
    const fs = (s || "").toUpperCase();
    return ["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"].includes(fs);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-5">
      {/* Title Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-500 flex items-center justify-center shadow-md shadow-emerald-500/20">
            <Trophy className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Football Fixtures</h2>
            <p className="text-xs text-slate-400">
              Real match data via API-Football — click any match for full intelligence
            </p>
          </div>
        </div>

        <button
          onClick={loadFixtures}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700/60 transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Trophy className="w-3 h-3 text-emerald-400" /> League
          </label>
          <select
            value={leagueFilter}
            onChange={(e) => setLeagueFilter(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
          >
            <option value="">Upcoming (All)</option>
            <option value="39">Premier League (39)</option>
            <option value="140">La Liga (140)</option>
            <option value="78">Bundesliga (78)</option>
            <option value="135">Serie A (135)</option>
            <option value="61">Ligue 1 (61)</option>
            <option value="2">UEFA Champions League (2)</option>
            <option value="3">UEFA Europa League (3)</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Filter className="w-3 h-3 text-cyan-400" /> Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Statuses</option>
            <option value="FT">Finished (FT)</option>
            <option value="NS">Not Started (NS)</option>
            <option value="1H">First Half (1H)</option>
            <option value="HT">Half Time (HT)</option>
            <option value="2H">Second Half (2H)</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" /> Date
          </label>
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-slate-600"
          />
        </div>
      </div>

      {/* Main Content States */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
          <p className="text-xs font-medium">Fetching real football fixture data...</p>
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-semibold">Match Data Service Alert</p>
            <p className="opacity-90">{error}</p>
          </div>
        </div>
      ) : fixtures.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 gap-2 text-slate-400">
          <Clock className="w-8 h-8 text-slate-600" />
          <p className="text-xs font-medium">No fixtures found for the selected filters.</p>
          <p className="text-[11px] text-slate-500">Try adjusting the league, date, or status filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fixtures.map((fixture) => {
            const statusShort = fixture.status?.short;
            const statusLong = fixture.status?.long;
            const finished = isFinished(statusShort);
            const live = isLive(statusShort);

            return (
              <Link
                key={fixture.fixture_id}
                href={`/matches/${fixture.fixture_id}`}
                className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-emerald-500/50 hover:bg-slate-900/80 transition-all flex flex-col gap-3 group cursor-pointer"
              >
                {/* Top Meta */}
                <div className="flex items-center justify-between text-xs border-b border-slate-800/60 pb-2">
                  <span className="text-slate-400 font-medium flex items-center gap-1.5">
                    <Trophy className="w-3.5 h-3.5 text-amber-400" />
                    {fixture.league?.name || "Football Match"}
                    {fixture.league?.round && (
                      <span className="text-slate-500 ml-1">· {fixture.league.round}</span>
                    )}
                  </span>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(statusShort, statusLong)}
                    <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                  </div>
                </div>

                {/* Teams & Score */}
                <div className="flex items-center justify-between px-2 py-1">
                  {/* Home Team */}
                  <div className="flex items-center gap-2 flex-1">
                    {fixture.home_team.logo ? (
                      <img
                        src={fixture.home_team.logo}
                        alt={fixture.home_team.name}
                        className="w-7 h-7 object-contain"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                        {fixture.home_team.name.substring(0, 3).toUpperCase()}
                      </div>
                    )}
                    <span className="text-xs font-bold text-slate-200 truncate group-hover:text-emerald-400 transition-colors">
                      {fixture.home_team.name}
                    </span>
                  </div>

                  {/* Score / VS */}
                  <div className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-center min-w-[72px]">
                    {finished || live ? (
                      <span className={`text-sm font-black ${live ? "text-emerald-400 animate-pulse" : "text-slate-200"}`}>
                        {fixture.goals?.home ?? "—"} - {fixture.goals?.away ?? "—"}
                      </span>
                    ) : (
                      <span className="text-xs font-semibold text-slate-400">VS</span>
                    )}
                  </div>

                  {/* Away Team */}
                  <div className="flex items-center justify-end gap-2 flex-1 text-right">
                    <span className="text-xs font-bold text-slate-200 truncate group-hover:text-emerald-400 transition-colors">
                      {fixture.away_team.name}
                    </span>
                    {fixture.away_team.logo ? (
                      <img
                        src={fixture.away_team.logo}
                        alt={fixture.away_team.name}
                        className="w-7 h-7 object-contain"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                        {fixture.away_team.name.substring(0, 3).toUpperCase()}
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom Meta */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {formatDate(fixture.date)}
                    </span>
                    {fixture.venue?.name && (
                      <span className="flex items-center gap-1 hidden sm:flex">
                        <MapPin className="w-3 h-3 text-slate-600" />
                        {fixture.venue.name}
                      </span>
                    )}
                  </div>
                  <span className="text-emerald-400 font-semibold group-hover:underline flex items-center gap-1">
                    Match Intelligence →
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
