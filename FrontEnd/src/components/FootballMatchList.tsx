import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Calendar, RefreshCw, Trophy, ShieldAlert, Filter, Clock, ChevronRight, MapPin, Zap } from "lucide-react";
import { fetchFixtures, FixtureItem } from "@/lib/api/football";

// ── Skeleton loader ───────────────────────────────────────────────────────────
function FixtureSkeletonCard() {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-white/[0.05] flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="h-3 w-32 rounded animate-shimmer" />
        <div className="h-5 w-16 rounded-full animate-shimmer" />
      </div>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-10 h-10 rounded-full animate-shimmer flex-shrink-0" />
          <div className="h-4 w-28 rounded animate-shimmer" />
        </div>
        <div className="w-20 h-9 rounded-xl animate-shimmer" />
        <div className="flex items-center justify-end gap-3 flex-1">
          <div className="h-4 w-28 rounded animate-shimmer" />
          <div className="w-10 h-10 rounded-full animate-shimmer flex-shrink-0" />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="h-3 w-40 rounded animate-shimmer" />
        <div className="h-3 w-24 rounded animate-shimmer" />
      </div>
    </div>
  );
}

export default function FootballMatchList() {
  const [fixtures, setFixtures] = useState<FixtureItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
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
      if (!leagueFilter && !statusFilter && !dateFilter) {
        params.next = 30;
      }
      const data = await fetchFixtures(params);
      setFixtures(data.fixtures || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to FootVision Football API.");
    } finally {
      setLoading(false);
    }
  }, [leagueFilter, statusFilter, dateFilter]);

  useEffect(() => { loadFixtures(); }, [loadFixtures]);

  const formatDate = (isoStr: string) => {
    try {
      return new Date(isoStr).toLocaleDateString("en-US", {
        weekday: "short", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return isoStr; }
  };

  const getStatusBadge = (statusShort?: string, statusLong?: string) => {
    const s = (statusShort || "").toUpperCase();
    if (["FT", "AET", "PEN"].includes(s)) {
      return <span className="badge-finished px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider">FT</span>;
    }
    if (["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"].includes(s)) {
      return (
        <span className="badge-live px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-live-blip" />
          LIVE
        </span>
      );
    }
    if (["NS", "TBD"].includes(s)) {
      return <span className="badge-upcoming px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider">UPCOMING</span>;
    }
    return <span className="badge-finished px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider">{statusLong || s || "—"}</span>;
  };

  const isFinished = (s?: string) => ["FT", "AET", "PEN"].includes((s || "").toUpperCase());
  const isLive = (s?: string) => ["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"].includes((s || "").toUpperCase());

  const LEAGUES = [
    { value: "", label: "🌍  All Upcoming" },
    { value: "39", label: "🏴󠁧󠁢󠁥󠁮󠁧󠁿  Premier League" },
    { value: "140", label: "🇪🇸  La Liga" },
    { value: "78", label: "🇩🇪  Bundesliga" },
    { value: "135", label: "🇮🇹  Serie A" },
    { value: "61", label: "🇫🇷  Ligue 1" },
    { value: "2", label: "🏆  Champions League" },
    { value: "3", label: "🥇  Europa League" },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* ── Section header ───────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-100 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-400" />
            Football Fixtures
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Live match data — click any fixture for full match intelligence
          </p>
        </div>
        <button
          id="fixtures-refresh"
          onClick={loadFixtures}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl glass-panel border border-white/[0.08] text-slate-300 hover:text-emerald-400 hover:border-emerald-500/30 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* ── Filter bar ───────────────────────────────────── */}
      <div className="glass-panel rounded-2xl p-4 border border-white/[0.06] grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Trophy className="w-3 h-3 text-amber-400" /> League
          </label>
          <select
            id="filter-league"
            value={leagueFilter}
            onChange={(e) => setLeagueFilter(e.target.value)}
            className="w-full bg-slate-950/80 text-slate-200 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-emerald-500 transition-colors"
          >
            {LEAGUES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Filter className="w-3 h-3 text-cyan-400" /> Status
          </label>
          <select
            id="filter-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-slate-950/80 text-slate-200 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-cyan-500 transition-colors"
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
          <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" /> Date
          </label>
          <input
            id="filter-date"
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="w-full bg-slate-950/80 text-slate-200 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-slate-600 transition-colors"
          />
        </div>
      </div>

      {/* ── Content ──────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <FixtureSkeletonCard key={i} />)}
        </div>
      ) : error ? (
        <div className="glass-panel rounded-2xl flex items-center gap-4 p-5 border border-red-500/20 bg-gradient-to-r from-red-950/20 to-slate-900/60">
          <ShieldAlert className="w-8 h-8 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-red-300">Match Data Unavailable</p>
            <p className="text-xs text-slate-400 mt-0.5">{error}</p>
          </div>
        </div>
      ) : fixtures.length === 0 ? (
        <div className="glass-panel rounded-2xl flex flex-col items-center justify-center py-16 gap-3 border border-white/[0.05]">
          <Clock className="w-10 h-10 text-slate-700" />
          <p className="text-sm font-semibold text-slate-400">No fixtures found</p>
          <p className="text-xs text-slate-600">Try adjusting the league, date, or status filters.</p>
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
                className="group glass-panel glass-panel-hover rounded-2xl p-5 border border-white/[0.06] flex flex-col gap-4 cursor-pointer animate-fade-in"
              >
                {/* Top meta row */}
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 font-medium flex items-center gap-1.5 min-w-0">
                    <Trophy className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                    <span className="truncate">{fixture.league?.name || "Football Match"}</span>
                    {fixture.league?.round && (
                      <span className="text-slate-600 truncate">· {fixture.league.round}</span>
                    )}
                  </span>
                  <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                    {getStatusBadge(statusShort, statusLong)}
                    {live && <Zap className="w-3.5 h-3.5 text-amber-400 animate-live-blip flex-shrink-0" />}
                  </div>
                </div>

                {/* Teams & Score */}
                <div className="flex items-center justify-between gap-3">
                  {/* Home team */}
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {fixture.home_team.logo ? (
                      <img
                        src={fixture.home_team.logo}
                        alt={fixture.home_team.name}
                        className="w-10 h-10 object-contain flex-shrink-0 drop-shadow-md"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-300 flex-shrink-0">
                        {fixture.home_team.name.substring(0, 3).toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0">
                      <span className="text-sm font-bold text-slate-100 group-hover:text-emerald-400 transition-colors truncate block">
                        {fixture.home_team.name}
                      </span>
                      <span className="text-[10px] text-slate-500">Home</span>
                    </div>
                  </div>

                  {/* Score / VS */}
                  <div className={`px-4 py-2.5 rounded-xl border text-center flex-shrink-0 min-w-[80px] ${
                    live
                      ? "bg-emerald-950/40 border-emerald-700/50 animate-border-glow"
                      : "bg-slate-950/80 border-slate-800"
                  }`}>
                    {finished || live ? (
                      <span className={`text-lg font-black ${live ? "text-emerald-400" : "text-slate-200"}`}>
                        {fixture.goals?.home ?? "—"} – {fixture.goals?.away ?? "—"}
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-slate-500">VS</span>
                    )}
                  </div>

                  {/* Away team */}
                  <div className="flex items-center justify-end gap-3 flex-1 min-w-0">
                    <div className="min-w-0 text-right">
                      <span className="text-sm font-bold text-slate-100 group-hover:text-emerald-400 transition-colors truncate block">
                        {fixture.away_team.name}
                      </span>
                      <span className="text-[10px] text-slate-500">Away</span>
                    </div>
                    {fixture.away_team.logo ? (
                      <img
                        src={fixture.away_team.logo}
                        alt={fixture.away_team.name}
                        className="w-10 h-10 object-contain flex-shrink-0 drop-shadow-md"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-300 flex-shrink-0">
                        {fixture.away_team.name.substring(0, 3).toUpperCase()}
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom meta */}
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-white/[0.04]">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(fixture.date)}
                    </span>
                    {fixture.venue?.name && (
                      <span className="hidden sm:flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {fixture.venue.name}
                      </span>
                    )}
                  </div>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1 group-hover:gap-2 transition-all">
                    Match Intelligence <ChevronRight className="w-3.5 h-3.5" />
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

