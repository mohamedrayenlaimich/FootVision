"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  CalendarDays,
  Clock,
  MapPin,
  RefreshCw,
  Trophy,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ShieldAlert,
  Radio,
  CheckCircle2,
  Calendar,
  X,
  ExternalLink,
} from "lucide-react";
import {
  fetchCalendarMatches,
  fetchCalendarLeagues,
  MatchCalendarItem,
  SportmonksLeague,
} from "@/lib/api/calendar";

export default function MatchCalendar() {
  const [matches, setMatches] = useState<MatchCalendarItem[]>([]);
  const [leagues, setLeagues] = useState<SportmonksLeague[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & State
  const [selectedLeagueId, setSelectedLeagueId] = useState<number | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedDate, setSelectedDate] = useState<string>(""); // "" = all dates
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [activeModalMatch, setActiveModalMatch] = useState<MatchCalendarItem | null>(null);

  // Date range state (default: current month)
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>(() => {
    const now = new Date();
    // Default to from start of current month to end of next month
    const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
    const end = new Date(now.getFullYear(), now.getMonth() + 2, 0).toISOString().split("T")[0];
    return { start, end };
  });

  // Fetch leagues once
  useEffect(() => {
    async function loadLeagues() {
      try {
        const res = await fetchCalendarLeagues();
        if (res.leagues && res.leagues.length > 0) {
          setLeagues(res.leagues);
        }
      } catch (err) {
        console.warn("Could not fetch leagues from backend:", err);
      }
    }
    loadLeagues();
  }, []);

  // Fetch matches
  const loadMatches = useCallback(
    async (isBackground = false) => {
      if (!isBackground) setLoading(true);
      else setRefreshing(true);
      setError(null);

      try {
        const res = await fetchCalendarMatches({
          startDate: dateRange.start,
          endDate: dateRange.end,
          leagueId: selectedLeagueId,
          status: selectedStatus !== "all" ? selectedStatus : undefined,
        });
        setMatches(res.matches || []);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load match calendar.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [dateRange.start, dateRange.end, selectedLeagueId, selectedStatus]
  );

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  // Auto-refresh interval (every 30s if enabled)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadMatches(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadMatches]);

  // Generate date strip items from unique dates in the matches or range
  const availableDates = useMemo(() => {
    const datesMap = new Map<string, number>();
    matches.forEach((m) => {
      const d = m.match_date;
      if (d) {
        datesMap.set(d, (datesMap.get(d) || 0) + 1);
      }
    });

    const sortedDates = Array.from(datesMap.keys()).sort();
    return sortedDates.map((dateStr) => {
      const parsed = new Date(dateStr + "T00:00:00");
      const dayName = parsed.toLocaleDateString("en-US", { weekday: "short" }).toUpperCase();
      const dayNum = parsed.getDate();
      const monthName = parsed.toLocaleDateString("en-US", { month: "short" }).toUpperCase();
      return {
        dateStr,
        dayName,
        dayNum,
        monthName,
        count: datesMap.get(dateStr) || 0,
      };
    });
  }, [matches]);

  // Filter matches by date and search query
  const filteredMatches = useMemo(() => {
    return matches.filter((m) => {
      if (selectedDate && m.match_date !== selectedDate) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const homeName = m.home_team.name?.toLowerCase() || "";
        const awayName = m.away_team.name?.toLowerCase() || "";
        const leagueName = m.league.name?.toLowerCase() || "";
        const venueName = m.venue?.name?.toLowerCase() || "";
        if (
          !homeName.includes(q) &&
          !awayName.includes(q) &&
          !leagueName.includes(q) &&
          !venueName.includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [matches, selectedDate, searchQuery]);

  // Group filtered matches by date
  const groupedMatches = useMemo(() => {
    const groups: { [dateStr: string]: MatchCalendarItem[] } = {};
    filteredMatches.forEach((m) => {
      const d = m.match_date || "Upcoming";
      if (!groups[d]) groups[d] = [];
      groups[d].push(m);
    });
    return groups;
  }, [filteredMatches]);

  // Quick jump: shifts range by months
  const shiftMonth = (delta: number) => {
    const curStart = new Date(dateRange.start + "T00:00:00");
    const newStart = new Date(curStart.getFullYear(), curStart.getMonth() + delta, 1);
    const newEnd = new Date(newStart.getFullYear(), newStart.getMonth() + 2, 0);
    setDateRange({
      start: newStart.toISOString().split("T")[0],
      end: newEnd.toISOString().split("T")[0],
    });
    setSelectedDate("");
  };

  const jumpToToday = () => {
    const todayStr = new Date().toISOString().split("T")[0];
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
    const end = new Date(now.getFullYear(), now.getMonth() + 2, 0).toISOString().split("T")[0];
    setDateRange({ start, end });
    setSelectedDate(todayStr);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* ── TOP HEADER & CONTROLS ─────────────────────────────────────────── */}
      <div className="glass-panel rounded-3xl p-6 border border-white/[0.08] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-emerald-500/10 via-cyan-500/5 to-transparent blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 flex-shrink-0">
              <CalendarDays className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-black text-slate-100 tracking-tight">Match Calendar</h2>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Sportmonks v3 Feed
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Official fixtures schedule, matchdays, venues, and real-time live match updates.
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={jumpToToday}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-white/[0.08] transition-colors"
            >
              <Calendar className="w-3.5 h-3.5 text-emerald-400" />
              Today
            </button>

            {/* Auto refresh switch */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                autoRefresh
                  ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                  : "bg-slate-800/50 border-white/[0.06] text-slate-400"
              }`}
            >
              <Radio className={`w-3.5 h-3.5 ${autoRefresh ? "text-emerald-400 animate-pulse" : "text-slate-500"}`} />
              Auto-Live: {autoRefresh ? "ON" : "OFF"}
            </button>

            {/* Refresh button */}
            <button
              onClick={() => loadMatches(false)}
              disabled={loading || refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing || loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* ── MONTH NAVIGATION & STATS ──────────────────────────────────── */}
        <div className="mt-6 pt-5 border-t border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => shiftMonth(-1)}
              className="p-1.5 rounded-lg bg-slate-900 border border-white/[0.07] text-slate-300 hover:bg-slate-800 transition-colors"
              title="Previous Month"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="text-xs font-bold text-slate-200 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-white/[0.08]">
              {new Date(dateRange.start + "T00:00:00").toLocaleDateString("en-US", { month: "short", year: "numeric" })} —{" "}
              {new Date(dateRange.end + "T00:00:00").toLocaleDateString("en-US", { month: "short", year: "numeric" })}
            </div>
            <button
              onClick={() => shiftMonth(1)}
              className="p-1.5 rounded-lg bg-slate-900 border border-white/[0.07] text-slate-300 hover:bg-slate-800 transition-colors"
              title="Next Month"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">{matches.length} Total Fixtures</span>
            <span className="text-slate-600">·</span>
            <span className="text-emerald-400 font-semibold">
              {matches.filter((m) => m.status.is_live).length} Live
            </span>
            <span className="text-slate-600">·</span>
            <span className="text-cyan-400 font-semibold">
              {matches.filter((m) => !m.status.is_finished && !m.status.is_live).length} Scheduled
            </span>
          </div>
        </div>

        {/* ── HORIZONTAL CALENDAR STRIP ──────────────────────────────────── */}
        <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <button
            onClick={() => setSelectedDate("")}
            className={`flex-shrink-0 flex flex-col items-center justify-center px-4 py-2.5 rounded-2xl border transition-all ${
              selectedDate === ""
                ? "bg-gradient-to-b from-emerald-500/25 to-cyan-500/15 border-emerald-500/40 text-emerald-300 shadow-md shadow-emerald-500/10"
                : "bg-slate-900/60 border-white/[0.06] text-slate-400 hover:bg-slate-800/80 hover:text-slate-200"
            }`}
          >
            <span className="text-[10px] font-bold tracking-wider">ALL</span>
            <span className="text-sm font-black mt-0.5">DATES</span>
            <span className="text-[10px] text-slate-400 mt-0.5">{matches.length}</span>
          </button>

          {availableDates.map((item) => {
            const isSelected = selectedDate === item.dateStr;
            const isToday = item.dateStr === new Date().toISOString().split("T")[0];

            return (
              <button
                key={item.dateStr}
                onClick={() => setSelectedDate(isSelected ? "" : item.dateStr)}
                className={`flex-shrink-0 flex flex-col items-center justify-center w-16 py-2.5 rounded-2xl border transition-all relative ${
                  isSelected
                    ? "bg-gradient-to-b from-emerald-500/25 to-cyan-500/15 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10 scale-105"
                    : "bg-slate-900/60 border-white/[0.06] text-slate-400 hover:bg-slate-800/80 hover:text-slate-200"
                }`}
              >
                {isToday && (
                  <span className="absolute -top-1 px-1.5 py-0.2 rounded-full bg-emerald-500 text-[8px] font-black text-slate-950">
                    TODAY
                  </span>
                )}
                <span className="text-[10px] font-semibold tracking-wider text-slate-400">{item.dayName}</span>
                <span className={`text-base font-black leading-none mt-0.5 ${isSelected ? "text-emerald-300" : "text-slate-200"}`}>
                  {item.dayNum}
                </span>
                <span className="text-[9px] font-semibold text-slate-500 mt-0.5">{item.monthName}</span>
                <span className={`text-[10px] font-bold mt-1 px-1.5 rounded-full ${isSelected ? "bg-emerald-500/30 text-emerald-200" : "bg-slate-800 text-slate-400"}`}>
                  {item.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── FILTER & SEARCH BAR ───────────────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search teams, league, or venue..."
            className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-slate-900/80 border border-white/[0.08] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* League Selector Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setSelectedLeagueId(undefined)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-all ${
              selectedLeagueId === undefined
                ? "bg-slate-800 text-emerald-300 border-emerald-500/30 shadow-inner"
                : "bg-slate-900/60 border-white/[0.06] text-slate-400 hover:bg-slate-800"
            }`}
          >
            All Leagues
          </button>
          {leagues.map((lg) => (
            <button
              key={lg.id}
              onClick={() => setSelectedLeagueId(selectedLeagueId === lg.id ? undefined : lg.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-all ${
                selectedLeagueId === lg.id
                  ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/15 text-emerald-300 border-emerald-500/40 shadow-inner"
                  : "bg-slate-900/60 border-white/[0.06] text-slate-400 hover:bg-slate-800"
              }`}
            >
              {lg.name}
            </button>
          ))}
        </div>

        {/* Status Tabs */}
        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-2xl border border-white/[0.06] flex-shrink-0">
          {[
            { id: "all", label: "All" },
            { id: "live", label: "Live" },
            { id: "upcoming", label: "Upcoming" },
            { id: "finished", label: "Results" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedStatus(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                selectedStatus === tab.id
                  ? "bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-black shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── ERROR ALERT ──────────────────────────────────────────────────── */}
      {error && (
        <div className="glass-panel rounded-2xl p-4 border border-red-500/20 bg-red-950/20 flex items-center gap-3 text-red-300 text-xs">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 text-red-400" />
          <div className="flex-1">
            <span className="font-bold">Error loading fixtures: </span>
            {error}
          </div>
          <button
            onClick={() => loadMatches(false)}
            className="px-3 py-1 rounded-lg bg-red-900/40 hover:bg-red-800/60 border border-red-500/30 text-white font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── MATCH CARDS / GRID ────────────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="glass-panel rounded-3xl p-5 border border-white/[0.06] flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <div className="h-3 w-28 rounded-md animate-shimmer" />
                <div className="h-5 w-16 rounded-full animate-shimmer" />
              </div>
              <div className="flex justify-between items-center my-3">
                <div className="h-10 w-24 rounded-lg animate-shimmer" />
                <div className="h-8 w-16 rounded-xl animate-shimmer" />
                <div className="h-10 w-24 rounded-lg animate-shimmer" />
              </div>
              <div className="h-3 w-36 rounded-md animate-shimmer" />
            </div>
          ))}
        </div>
      ) : Object.keys(groupedMatches).length === 0 ? (
        <div className="glass-panel rounded-3xl p-12 border border-white/[0.06] text-center flex flex-col items-center justify-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center border border-white/[0.08]">
            <Trophy className="w-7 h-7 text-slate-500" />
          </div>
          <h3 className="text-base font-bold text-slate-200">No Matches Found</h3>
          <p className="text-xs text-slate-400 max-w-sm">
            {selectedDate
              ? `No fixtures scheduled for ${selectedDate}. Try selecting another date or clearing your filters.`
              : "No fixtures matched your current league or status filter. Try clearing filters to view all scheduled games."}
          </p>
          <button
            onClick={() => {
              setSelectedDate("");
              setSelectedLeagueId(undefined);
              setSelectedStatus("all");
              setSearchQuery("");
            }}
            className="mt-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-semibold border border-emerald-500/20 transition-colors"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {Object.entries(groupedMatches).map(([dateGroup, groupItems]) => {
            const parsedDate = new Date(dateGroup + "T00:00:00");
            const formattedHeader = isNaN(parsedDate.getTime())
              ? dateGroup
              : parsedDate.toLocaleDateString("en-US", {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                });

            return (
              <div key={dateGroup} className="flex flex-col gap-4">
                {/* Date Group Heading */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <h3 className="text-sm font-black text-slate-200 tracking-wide uppercase">
                      {formattedHeader}
                    </h3>
                  </div>
                  <span className="text-[11px] font-bold text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded-full border border-white/[0.06]">
                    {groupItems.length} {groupItems.length === 1 ? "match" : "matches"}
                  </span>
                  <div className="flex-1 h-px bg-gradient-to-r from-white/[0.08] to-transparent" />
                </div>

                {/* Matches Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {groupItems.map((m) => (
                    <MatchCard
                      key={m.id}
                      match={m}
                      onSelect={() => setActiveModalMatch(m)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── MATCH DETAILS MODAL ───────────────────────────────────────────── */}
      {activeModalMatch && (
        <MatchDetailModal
          match={activeModalMatch}
          onClose={() => setActiveModalMatch(null)}
        />
      )}
    </div>
  );
}

// ── MATCH CARD COMPONENT ─────────────────────────────────────────────────────
function MatchCard({
  match,
  onSelect,
}: {
  match: MatchCalendarItem;
  onSelect: () => void;
}) {
  const isLive = match.status.is_live;
  const isFinished = match.status.is_finished;

  return (
    <div
      onClick={onSelect}
      className="glass-panel rounded-3xl p-5 border border-white/[0.07] hover:border-emerald-500/40 hover:bg-slate-900/60 transition-all duration-200 cursor-pointer flex flex-col justify-between gap-4 group relative overflow-hidden"
    >
      {/* Decorative top hover accent */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Card Header: League & Status */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 truncate">
          {match.league.logo ? (
            <img
              src={match.league.logo}
              alt={match.league.name}
              className="w-5 h-5 rounded-full object-contain bg-slate-950 p-0.5 border border-white/[0.1]"
              onError={(e) => ((e.target as HTMLElement).style.display = "none")}
            />
          ) : (
            <Trophy className="w-4 h-4 text-emerald-400" />
          )}
          <span className="text-[11px] font-bold text-slate-300 truncate">
            {match.league.name}
            {match.league.round ? ` · Round ${match.league.round}` : ""}
          </span>
        </div>

        {/* Status Pill */}
        {isLive ? (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            LIVE
          </span>
        ) : isFinished ? (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-slate-800 text-slate-400 border border-white/[0.08]">
            FT
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-cyan-400">
            <Clock className="w-3 h-3" />
            {match.kickoff_time || "TBD"}
          </span>
        )}
      </div>

      {/* Center Match Arena */}
      <div className="flex items-center justify-between gap-3 my-1">
        {/* Home Team */}
        <div className="flex-1 flex flex-col items-center text-center gap-1.5">
          <div className="w-12 h-12 rounded-2xl bg-slate-950 p-2 border border-white/[0.08] flex items-center justify-center shadow-md">
            {match.home_team.logo ? (
              <img
                src={match.home_team.logo}
                alt={match.home_team.name}
                className="max-h-full max-w-full object-contain"
                onError={(e) => ((e.target as HTMLElement).style.display = "none")}
              />
            ) : (
              <span className="text-xs font-black text-slate-400">
                {match.home_team.short_code || match.home_team.name.slice(0, 3).toUpperCase()}
              </span>
            )}
          </div>
          <span className="text-xs font-black text-slate-100 line-clamp-1 leading-tight">
            {match.home_team.name}
          </span>
        </div>

        {/* Score or Kickoff Time */}
        <div className="flex flex-col items-center justify-center px-3 py-2 rounded-2xl bg-slate-950/70 border border-white/[0.07] min-w-[70px]">
          {isLive || isFinished ? (
            <div className="flex items-center gap-2">
              <span className={`text-xl font-black ${isLive ? "text-emerald-400" : "text-slate-100"}`}>
                {match.score.home ?? match.home_team.score ?? 0}
              </span>
              <span className="text-slate-500 font-bold">:</span>
              <span className={`text-xl font-black ${isLive ? "text-emerald-400" : "text-slate-100"}`}>
                {match.score.away ?? match.away_team.score ?? 0}
              </span>
            </div>
          ) : (
            <span className="text-sm font-black text-cyan-300">
              {match.kickoff_time || "VS"}
            </span>
          )}
          <span className="text-[9px] font-semibold text-slate-500 mt-0.5">
            {match.status.name}
          </span>
        </div>

        {/* Away Team */}
        <div className="flex-1 flex flex-col items-center text-center gap-1.5">
          <div className="w-12 h-12 rounded-2xl bg-slate-950 p-2 border border-white/[0.08] flex items-center justify-center shadow-md">
            {match.away_team.logo ? (
              <img
                src={match.away_team.logo}
                alt={match.away_team.name}
                className="max-h-full max-w-full object-contain"
                onError={(e) => ((e.target as HTMLElement).style.display = "none")}
              />
            ) : (
              <span className="text-xs font-black text-slate-400">
                {match.away_team.short_code || match.away_team.name.slice(0, 3).toUpperCase()}
              </span>
            )}
          </div>
          <span className="text-xs font-black text-slate-100 line-clamp-1 leading-tight">
            {match.away_team.name}
          </span>
        </div>
      </div>

      {/* Card Footer */}
      <div className="pt-3 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5 truncate max-w-[190px]">
          <MapPin className="w-3 h-3 text-slate-400 flex-shrink-0" />
          <span className="truncate">
            {match.venue?.name || match.venue?.city || "Stadium"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {match.has_odds && (
            <span className="px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px] font-bold">
              ODDS
            </span>
          )}
          <span className="text-emerald-400 font-bold group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
            Details →
          </span>
        </div>
      </div>
    </div>
  );
}

// ── MATCH DETAIL MODAL ───────────────────────────────────────────────────────
function MatchDetailModal({
  match,
  onClose,
}: {
  match: MatchCalendarItem;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-lg rounded-3xl p-6 border border-white/[0.1] shadow-2xl relative flex flex-col gap-6">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2">
          {match.league.logo && (
            <img
              src={match.league.logo}
              alt=""
              className="w-6 h-6 object-contain"
            />
          )}
          <div>
            <h3 className="text-sm font-black text-slate-100">{match.league.name}</h3>
            <p className="text-[11px] text-slate-400">
              {match.match_date} · Kickoff {match.kickoff_time} UTC
            </p>
          </div>
        </div>

        {/* Teams & Scoreboard */}
        <div className="bg-slate-950/80 rounded-2xl p-5 border border-white/[0.08] flex items-center justify-between gap-4">
          <div className="flex-1 flex flex-col items-center text-center gap-2">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 p-2.5 border border-white/[0.08] flex items-center justify-center shadow-lg">
              {match.home_team.logo ? (
                <img
                  src={match.home_team.logo}
                  alt={match.home_team.name}
                  className="max-h-full max-w-full object-contain"
                />
              ) : (
                <span className="font-bold text-slate-400">{match.home_team.name.slice(0, 3)}</span>
              )}
            </div>
            <div className="text-xs font-bold text-slate-200">{match.home_team.name}</div>
          </div>

          <div className="flex flex-col items-center">
            {match.status.is_live || match.status.is_finished ? (
              <div className="text-3xl font-black text-slate-100 tracking-wider">
                {match.score.home ?? 0} : {match.score.away ?? 0}
              </div>
            ) : (
              <div className="text-base font-black text-cyan-400">
                {match.kickoff_time || "VS"}
              </div>
            )}
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 mt-1">
              {match.status.name}
            </span>
            {match.score.half_time && (
              <span className="text-[10px] text-slate-500 mt-1">
                HT: {match.score.half_time.home} - {match.score.half_time.away}
              </span>
            )}
          </div>

          <div className="flex-1 flex flex-col items-center text-center gap-2">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 p-2.5 border border-white/[0.08] flex items-center justify-center shadow-lg">
              {match.away_team.logo ? (
                <img
                  src={match.away_team.logo}
                  alt={match.away_team.name}
                  className="max-h-full max-w-full object-contain"
                />
              ) : (
                <span className="font-bold text-slate-400">{match.away_team.name.slice(0, 3)}</span>
              )}
            </div>
            <div className="text-xs font-bold text-slate-200">{match.away_team.name}</div>
          </div>
        </div>

        {/* Fixture Details List */}
        <div className="flex flex-col gap-2.5 text-xs">
          {match.result_info && (
            <div className="p-3 rounded-xl bg-slate-900/60 border border-white/[0.06] flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{match.result_info}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div className="p-3 rounded-xl bg-slate-900/40 border border-white/[0.06]">
              <span className="text-[10px] text-slate-500 block">Venue / Stadium</span>
              <span className="font-semibold text-slate-300 mt-0.5 block truncate">
                {match.venue?.name || "TBD"}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/40 border border-white/[0.06]">
              <span className="text-[10px] text-slate-500 block">City / Location</span>
              <span className="font-semibold text-slate-300 mt-0.5 block truncate">
                {match.venue?.city || "Europe"}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-white/[0.08] transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
