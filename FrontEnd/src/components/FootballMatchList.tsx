import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Calendar, RefreshCw, Trophy, ShieldAlert, Filter, Clock, ExternalLink } from "lucide-react";
import { fetchMatches, Match, FetchMatchesParams } from "@/lib/api/football";


export default function FootballMatchList() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [competition, setCompetition] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const loadMatches = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: FetchMatchesParams = {};
      if (competition) params.competition = competition;
      if (statusFilter) params.status = statusFilter;
      if (dateFrom) params.dateFrom = dateFrom;
      if (dateTo) params.dateTo = dateTo;

      const data = await fetchMatches(params);
      setMatches(data.matches || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to connect to FootVision Football API.");
      }
    } finally {
      setLoading(false);
    }
  }, [competition, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

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

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "FINISHED":
        return <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[10px] font-bold tracking-wider">FINISHED</span>;
      case "IN_PLAY":
      case "LIVE":
      case "PAUSED":
        return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold tracking-wider animate-pulse">LIVE</span>;
      case "TIMED":
      case "SCHEDULED":
        return <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold tracking-wider">UPCOMING</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-bold tracking-wider">{status}</span>;
    }
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
            <h2 className="text-lg font-bold text-slate-100">Official Football Matches</h2>
            <p className="text-xs text-slate-400">External Match Metadata integrated via football-data.org API</p>
          </div>
        </div>

        <button
          onClick={loadMatches}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 text-xs font-semibold border border-slate-700/60 transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Matches
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Trophy className="w-3 h-3 text-emerald-400" /> Competition
          </label>
          <select
            value={competition}
            onChange={(e) => setCompetition(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Competitions</option>
            <option value="PL">Premier League (PL)</option>
            <option value="CL">UEFA Champions League (CL)</option>
            <option value="PD">La Liga (PD)</option>
            <option value="SA">Serie A (SA)</option>

            <option value="BL1">Bundesliga (BL1)</option>
            <option value="FL1">Ligue 1 (FL1)</option>
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
            <option value="FINISHED">Finished</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="IN_PLAY">Live / In Play</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" /> Date From
          </label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-slate-600"
          />
        </div>

        <div>
          <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" /> Date To
          </label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-slate-600"
          />
        </div>
      </div>

      {/* Main Content States */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
          <p className="text-xs font-medium">Fetching real football match data from FootVision API...</p>
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-semibold">Match Data Service Alert</p>
            <p className="opacity-90">{error}</p>
          </div>
        </div>
      ) : matches.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 gap-2 text-slate-400">
          <Clock className="w-8 h-8 text-slate-600" />
          <p className="text-xs font-medium">No matches found for the selected filters.</p>
          <p className="text-[11px] text-slate-500">Try adjusting the competition, date range, or status filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {matches.map((match) => (
            <Link
              key={match.id}
              href={`/matches/${match.id}`}
              className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-emerald-500/50 hover:bg-slate-900/80 transition-all flex flex-col gap-3 group cursor-pointer"
            >
              {/* Top Meta info */}
              <div className="flex items-center justify-between text-xs border-b border-slate-800/60 pb-2">
                <span className="text-slate-400 font-medium flex items-center gap-1.5">
                  <Trophy className="w-3.5 h-3.5 text-amber-400" />
                  {match.competition?.name || "Football Match"}
                </span>
                <div className="flex items-center gap-2">
                  {getStatusBadge(match.status)}
                  <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                </div>
              </div>

              {/* Teams & Score Card */}
              <div className="flex items-center justify-between px-2 py-1">
                {/* Home Team */}
                <div className="flex items-center gap-2 flex-1">
                  {match.homeTeam.crest ? (
                    <img src={match.homeTeam.crest} alt={match.homeTeam.name} className="w-6 h-6 object-contain" />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                      {match.homeTeam.tla || match.homeTeam.name.substring(0, 3)}
                    </div>
                  )}
                  <span className="text-xs font-bold text-slate-200 truncate group-hover:text-emerald-400 transition-colors">{match.homeTeam.name}</span>
                </div>

                {/* Score / VS */}
                <div className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-center min-w-[64px]">
                  {match.status === "FINISHED" || match.status === "IN_PLAY" ? (
                    <span className="text-sm font-black text-emerald-400">
                      {match.score?.fullTime?.home ?? 0} - {match.score?.fullTime?.away ?? 0}
                    </span>
                  ) : (
                    <span className="text-xs font-semibold text-slate-400">VS</span>
                  )}
                </div>

                {/* Away Team */}
                <div className="flex items-center justify-end gap-2 flex-1 text-right">
                  <span className="text-xs font-bold text-slate-200 truncate group-hover:text-emerald-400 transition-colors">{match.awayTeam.name}</span>
                  {match.awayTeam.crest ? (
                    <img src={match.awayTeam.crest} alt={match.awayTeam.name} className="w-6 h-6 object-contain" />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300">
                      {match.awayTeam.tla || match.awayTeam.name.substring(0, 3)}
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Date / Matchday & CTA */}
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-500" />
                  {formatDate(match.utcDate)}
                </span>
                <span className="text-emerald-400 font-semibold group-hover:underline flex items-center gap-1">
                  Match Intelligence →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

    </div>
  );
}
