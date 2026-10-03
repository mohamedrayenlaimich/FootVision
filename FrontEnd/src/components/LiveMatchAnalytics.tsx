"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity, RefreshCw, Trophy, ShieldAlert, Users, Star, Target,
  ChevronRight, BarChart2, Zap, Shield, Swords, Flag, ArrowUpRight,
  Circle, Search, Hash
} from "lucide-react";
import { fetchFixtures, fetchMatchStatistics, fetchMatchPlayers, FixtureItem } from "@/lib/api/football";

// ─── Types ─────────────────────────────────────────────────────────────────
interface StatRow {
  label: string;
  home: string | number | null;
  away: string | number | null;
}

interface PlayerStat {
  id?: number;
  name?: string;
  photo?: string;
  number?: number;
  position?: string;
  rating?: string;
  minutes?: number;
  goals?: { total?: number; assists?: number; saves?: number };
  shots?: { total?: number; on_target?: number };
  passes?: { total?: number; key?: number; accuracy?: string };
  tackles?: { total?: number; interceptions?: number };
  cards?: { yellow?: number; red?: number };
}

interface TeamData {
  team: { id?: number; name?: string; logo?: string };
  statistics?: Record<string, string | number | null>;
  players?: PlayerStat[];
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function pct(val: string | number | null): number {
  if (!val) return 0;
  const s = String(val).replace("%", "");
  return parseFloat(s) || 0;
}

function StatBar({ label, home, away }: StatRow) {
  const hNum = pct(home);
  const aNum = pct(away);
  const isPercent = String(home || "").includes("%") || String(away || "").includes("%");

  let hW = 50, aW = 50;
  if (isPercent) {
    hW = hNum;
    aW = aNum;
  } else {
    const total = hNum + aNum;
    hW = total > 0 ? Math.round((hNum / total) * 100) : 50;
    aW = 100 - hW;
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-bold text-red-400 min-w-[40px]">{home ?? "—"}</span>
        <span className="text-slate-400 text-[11px] font-medium">{label}</span>
        <span className="font-bold text-blue-400 min-w-[40px] text-right">{away ?? "—"}</span>
      </div>
      <div className="flex h-1.5 w-full rounded-full overflow-hidden bg-slate-900 border border-slate-800/60">
        <div className="bg-gradient-to-r from-red-600 to-rose-400 h-full transition-all duration-700" style={{ width: `${hW}%` }} />
        <div className="bg-gradient-to-r from-blue-400 to-indigo-600 h-full transition-all duration-700" style={{ width: `${aW}%` }} />
      </div>
    </div>
  );
}

function RatingBadge({ rating }: { rating?: string | null }) {
  const r = parseFloat(rating || "0");
  const color = r >= 8 ? "text-emerald-400 border-emerald-500/40 bg-emerald-500/10"
    : r >= 7 ? "text-cyan-400 border-cyan-500/40 bg-cyan-500/10"
    : r >= 6 ? "text-amber-400 border-amber-500/40 bg-amber-500/10"
    : "text-slate-400 border-slate-700 bg-slate-800/40";
  return rating
    ? <span className={`px-1.5 py-0.5 rounded text-[10px] font-black border ${color}`}>{parseFloat(rating).toFixed(1)}</span>
    : <span className="text-slate-600 text-[10px]">—</span>;
}

function posColor(pos?: string) {
  switch ((pos || "").toUpperCase()) {
    case "G": return "bg-amber-600";
    case "D": return "bg-blue-700";
    case "M": return "bg-emerald-700";
    case "F": return "bg-red-700";
    default:  return "bg-slate-700";
  }
}

// ─── Skeleton ───────────────────────────────────────────────────────────────
function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-shimmer rounded ${className}`} />;
}

// ─── Main Component ─────────────────────────────────────────────────────────
export default function LiveMatchAnalytics() {
  const [recentMatches, setRecentMatches] = useState<FixtureItem[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [matchError, setMatchError] = useState<string | null>(null);

  const [selectedFixture, setSelectedFixture] = useState<FixtureItem | null>(null);
  const [statsData, setStatsData] = useState<{ home: TeamData | null; away: TeamData | null }>({ home: null, away: null });
  const [playersData, setPlayersData] = useState<{ home: PlayerStat[]; away: PlayerStat[] }>({ home: [], away: [] });
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [playerTab, setPlayerTab] = useState<"home" | "away">("home");
  const [searchQ, setSearchQ] = useState("");

  // Load recent finished fixtures
  const loadRecentMatches = useCallback(async () => {
    setLoadingMatches(true);
    setMatchError(null);
    try {
      const today = new Date().toISOString().split("T")[0];
      const result = await fetchFixtures({ status: "FT", date: today });
      let fixtures = result.fixtures || [];
      // If no matches today, load next recent finished from PL
      if (fixtures.length === 0) {
        const plResult = await fetchFixtures({ league: 39, season: 2024, status: "FT" });
        fixtures = (plResult.fixtures || []).slice(0, 20);
      }
      setRecentMatches(fixtures);
    } catch (err: any) {
      setMatchError(err.message || "Could not load recent matches.");
    } finally {
      setLoadingMatches(false);
    }
  }, []);

  useEffect(() => { loadRecentMatches(); }, [loadRecentMatches]);

  const loadMatchDetail = useCallback(async (fixture: FixtureItem) => {
    setSelectedFixture(fixture);
    setLoadingDetail(true);
    setDetailError(null);
    setStatsData({ home: null, away: null });
    setPlayersData({ home: [], away: [] });
    setSearchQ("");

    try {
      const [statsRes, playersRes] = await Promise.allSettled([
        fetchMatchStatistics(fixture.fixture_id),
        fetchMatchPlayers(fixture.fixture_id),
      ]);

      // Parse statistics
      if (statsRes.status === "fulfilled") {
        const teams: TeamData[] = statsRes.value?.teams || [];
        setStatsData({
          home: teams[0] || null,
          away: teams[1] || null,
        });
      }

      // Parse player stats
      if (playersRes.status === "fulfilled") {
        const teams = playersRes.value?.teams || [];
        setPlayersData({
          home: teams[0]?.players || [],
          away: teams[1]?.players || [],
        });
      }

      if (statsRes.status === "rejected" && playersRes.status === "rejected") {
        setDetailError("Analytics data unavailable from provider for this fixture.");
      }
    } catch (err: any) {
      setDetailError(err.message || "Failed to load match analytics.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const statRows: StatRow[] = statsData.home && statsData.away
    ? [
        { label: "Ball Possession", home: statsData.home.statistics?.possession ?? null, away: statsData.away.statistics?.possession ?? null },
        { label: "Total Shots", home: statsData.home.statistics?.total_shots ?? null, away: statsData.away.statistics?.total_shots ?? null },
        { label: "Shots on Target", home: statsData.home.statistics?.shots_on_target ?? null, away: statsData.away.statistics?.shots_on_target ?? null },
        { label: "Corner Kicks", home: statsData.home.statistics?.corners ?? null, away: statsData.away.statistics?.corners ?? null },
        { label: "Fouls", home: statsData.home.statistics?.fouls ?? null, away: statsData.away.statistics?.fouls ?? null },
        { label: "Offsides", home: statsData.home.statistics?.offsides ?? null, away: statsData.away.statistics?.offsides ?? null },
        { label: "Total Passes", home: statsData.home.statistics?.passes ?? null, away: statsData.away.statistics?.passes ?? null },
        { label: "Pass Accuracy", home: statsData.home.statistics?.pass_accuracy ?? null, away: statsData.away.statistics?.pass_accuracy ?? null },
        { label: "Yellow Cards", home: statsData.home.statistics?.yellow_cards ?? null, away: statsData.away.statistics?.yellow_cards ?? null },
        { label: "Saves", home: statsData.home.statistics?.saves ?? null, away: statsData.away.statistics?.saves ?? null },
      ].filter(r => r.home !== null || r.away !== null)
    : [];

  const activePlayers = (playerTab === "home" ? playersData.home : playersData.away)
    .filter(p => !searchQ || (p.name || "").toLowerCase().includes(searchQ.toLowerCase()))
    .sort((a, b) => parseFloat(b.rating || "0") - parseFloat(a.rating || "0"));

  return (
    <div className="flex flex-col gap-6">
      {/* ── Match Selector ──────────────────────────────────────── */}
      <div className="glass-panel rounded-2xl p-5 border border-white/[0.08] flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-4.5 h-4.5 text-emerald-400" />
              Live Match Analytics
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select a finished match below to load real team statistics &amp; player ratings from API-Football
            </p>
          </div>
          <button
            onClick={loadRecentMatches}
            disabled={loadingMatches}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 border border-slate-700/60 text-slate-200 hover:bg-slate-800 transition-all active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingMatches ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {matchError && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>{matchError}</span>
          </div>
        )}

        {loadingMatches ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : recentMatches.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            <Trophy className="w-8 h-8 mx-auto mb-2 text-slate-700" />
            No recent finished matches found. Try refreshing.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1 scrollbar-thin">
            {recentMatches.map((m) => {
              const isSelected = selectedFixture?.fixture_id === m.fixture_id;
              return (
                <button
                  key={m.fixture_id}
                  onClick={() => loadMatchDetail(m)}
                  className={`flex flex-col gap-2 p-3.5 rounded-xl border text-left transition-all ${
                    isSelected
                      ? "bg-emerald-500/10 border-emerald-500/50 shadow-md shadow-emerald-500/10"
                      : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/80"
                  }`}
                >
                  {/* League */}
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-medium flex items-center gap-1">
                      <Trophy className="w-3 h-3 text-amber-400" />
                      {m.league?.name || "Football"}
                      {m.league?.round && <span className="text-slate-500"> · {m.league.round}</span>}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-bold">FT</span>
                  </div>
                  {/* Teams */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {m.home_team.logo && <img src={m.home_team.logo} alt="" className="w-6 h-6 object-contain flex-shrink-0" />}
                      <span className="text-xs font-bold text-slate-200 truncate">{m.home_team.name}</span>
                    </div>
                    <div className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs font-black text-slate-100 whitespace-nowrap">
                      {m.goals?.home ?? "—"} – {m.goals?.away ?? "—"}
                    </div>
                    <div className="flex items-center justify-end gap-2 flex-1 min-w-0">
                      <span className="text-xs font-bold text-slate-200 truncate text-right">{m.away_team.name}</span>
                      {m.away_team.logo && <img src={m.away_team.logo} alt="" className="w-6 h-6 object-contain flex-shrink-0" />}
                    </div>
                  </div>
                  {isSelected && (
                    <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                      <ArrowUpRight className="w-3 h-3" /> Loading analytics below...
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Analytics Detail Panel ───────────────────────────────── */}
      {selectedFixture && (
        <div className="flex flex-col gap-5 animate-fade-in">
          {/* Match Header */}
          <div className="glass-panel rounded-2xl p-5 border border-white/[0.08]">
            <div className="flex flex-col md:flex-row md:items-center gap-4">
              {/* Home */}
              <div className="flex items-center gap-3 flex-1">
                {selectedFixture.home_team.logo && (
                  <img src={selectedFixture.home_team.logo} alt="" className="w-12 h-12 object-contain drop-shadow-xl" />
                )}
                <div>
                  <div className="text-xl font-black text-slate-100">{selectedFixture.home_team.name}</div>
                  <div className="text-xs text-red-400 font-semibold">HOME</div>
                </div>
              </div>
              {/* Score */}
              <div className="flex flex-col items-center gap-1">
                <div className="text-4xl font-black text-slate-100 tracking-tight">
                  {selectedFixture.goals?.home ?? "—"} <span className="text-slate-500">–</span> {selectedFixture.goals?.away ?? "—"}
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-bold">FULL TIME</span>
                <div className="text-[10px] text-slate-500">{selectedFixture.league?.name}</div>
              </div>
              {/* Away */}
              <div className="flex items-center justify-end gap-3 flex-1">
                <div className="text-right">
                  <div className="text-xl font-black text-slate-100">{selectedFixture.away_team.name}</div>
                  <div className="text-xs text-blue-400 font-semibold">AWAY</div>
                </div>
                {selectedFixture.away_team.logo && (
                  <img src={selectedFixture.away_team.logo} alt="" className="w-12 h-12 object-contain drop-shadow-xl" />
                )}
              </div>
            </div>
          </div>

          {loadingDetail ? (
            <div className="glass-panel rounded-2xl p-10 border border-white/[0.08] flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
              <p className="text-xs text-slate-400 font-medium">Fetching live match analytics from API-Football...</p>
            </div>
          ) : detailError ? (
            <div className="glass-panel rounded-2xl p-6 border border-amber-500/20 flex items-start gap-3 text-amber-300 text-xs">
              <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold mb-1">Analytics Unavailable</p>
                <p className="opacity-80">{detailError}</p>
                <p className="text-slate-500 mt-1.5">
                  Statistics are only available for matches processed by API-Football (usually 2026 season fixtures with an active API key).
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* ── Team Statistics Bars ───────────────────────── */}
              {statRows.length > 0 ? (
                <div className="glass-panel rounded-2xl p-5 border border-white/[0.08]">
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      <BarChart2 className="w-4 h-4 text-emerald-400" />
                      Team Statistics
                    </h3>
                    <div className="flex items-center gap-4 text-[11px] font-bold">
                      <span className="flex items-center gap-1.5 text-red-400">
                        {selectedFixture.home_team.logo && <img src={selectedFixture.home_team.logo} alt="" className="w-4 h-4 object-contain" />}
                        {selectedFixture.home_team.name}
                      </span>
                      <span className="text-slate-600">vs</span>
                      <span className="flex items-center gap-1.5 text-blue-400">
                        {selectedFixture.away_team.name}
                        {selectedFixture.away_team.logo && <img src={selectedFixture.away_team.logo} alt="" className="w-4 h-4 object-contain" />}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-4">
                    {statRows.map((row) => (
                      <StatBar key={row.label} {...row} />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="glass-panel rounded-2xl p-6 border border-white/[0.08] text-center text-slate-500 text-sm">
                  <BarChart2 className="w-8 h-8 mx-auto mb-2 text-slate-700" />
                  Team statistics not yet available for this fixture from the provider.
                </div>
              )}

              {/* ── Player Stats Table ──────────────────────────── */}
              {(playersData.home.length > 0 || playersData.away.length > 0) ? (
                <div className="glass-panel rounded-2xl p-5 border border-white/[0.08] flex flex-col gap-4">
                  {/* Table Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                      <Users className="w-4 h-4 text-emerald-400" />
                      Player Performance Ratings
                    </h3>
                    {/* Team Tabs */}
                    <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
                      <button
                        onClick={() => setPlayerTab("home")}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          playerTab === "home"
                            ? "bg-red-500/20 text-red-300 border border-red-500/30"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {selectedFixture.home_team.logo && <img src={selectedFixture.home_team.logo} alt="" className="w-3.5 h-3.5 object-contain" />}
                        {selectedFixture.home_team.name}
                      </button>
                      <button
                        onClick={() => setPlayerTab("away")}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          playerTab === "away"
                            ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                            : "text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {selectedFixture.away_team.logo && <img src={selectedFixture.away_team.logo} alt="" className="w-3.5 h-3.5 object-contain" />}
                        {selectedFixture.away_team.name}
                      </button>
                    </div>
                    {/* Search */}
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                      <input
                        type="text"
                        placeholder="Filter players..."
                        value={searchQ}
                        onChange={e => setSearchQ(e.target.value)}
                        className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg pl-7 pr-3 py-1.5 w-40 outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>
                  </div>

                  {/* Player Table */}
                  <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-900/90 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                          <th className="py-3 px-3">#</th>
                          <th className="py-3 px-3">Player</th>
                          <th className="py-3 px-3">Pos</th>
                          <th className="py-3 px-3 text-center">Rating</th>
                          <th className="py-3 px-3 text-center">Min</th>
                          <th className="py-3 px-3 text-center">Goals</th>
                          <th className="py-3 px-3 text-center">Assists</th>
                          <th className="py-3 px-3 text-center">Shots</th>
                          <th className="py-3 px-3 text-center">Passes</th>
                          <th className="py-3 px-3 text-center">Tackles</th>
                          <th className="py-3 px-3 text-center">Cards</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-xs text-slate-200">
                        {activePlayers.length === 0 ? (
                          <tr>
                            <td colSpan={11} className="py-8 text-center text-slate-500">No players found</td>
                          </tr>
                        ) : activePlayers.map((p, idx) => (
                          <tr key={p.id ?? idx} className="hover:bg-slate-800/40 transition-colors">
                            <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">{p.number ?? "—"}</td>
                            <td className="py-2.5 px-3">
                              <div className="flex items-center gap-2">
                                {p.photo
                                  ? <img src={p.photo} alt="" className="w-6 h-6 rounded-full object-cover bg-slate-800 flex-shrink-0" />
                                  : <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center flex-shrink-0"><Users className="w-3 h-3 text-slate-500" /></div>
                                }
                                <span className="font-semibold text-slate-100 whitespace-nowrap">{p.name || "—"}</span>
                              </div>
                            </td>
                            <td className="py-2.5 px-3">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold text-white ${posColor(p.position)}`}>
                                {p.position || "?"}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-center"><RatingBadge rating={p.rating} /></td>
                            <td className="py-2.5 px-3 text-center font-mono text-slate-400">{p.minutes ?? "—"}</td>
                            <td className="py-2.5 px-3 text-center font-bold text-emerald-400">{p.goals?.total ?? 0}</td>
                            <td className="py-2.5 px-3 text-center font-bold text-cyan-400">{p.goals?.assists ?? 0}</td>
                            <td className="py-2.5 px-3 text-center text-slate-300">
                              {p.shots?.on_target ?? 0}/{p.shots?.total ?? 0}
                            </td>
                            <td className="py-2.5 px-3 text-center text-slate-300">
                              {p.passes?.total ?? "—"}
                              {p.passes?.accuracy && <span className="text-slate-500 ml-1">({p.passes.accuracy})</span>}
                            </td>
                            <td className="py-2.5 px-3 text-center text-slate-300">{p.tackles?.total ?? "—"}</td>
                            <td className="py-2.5 px-3 text-center">
                              <div className="flex items-center justify-center gap-1">
                                {(p.cards?.yellow ?? 0) > 0 && (
                                  <span className="w-3 h-4 bg-yellow-400 rounded-[2px] inline-block" title="Yellow Card" />
                                )}
                                {(p.cards?.red ?? 0) > 0 && (
                                  <span className="w-3 h-4 bg-red-500 rounded-[2px] inline-block" title="Red Card" />
                                )}
                                {!(p.cards?.yellow) && !(p.cards?.red) && <span className="text-slate-600">—</span>}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                statRows.length === 0 && (
                  <div className="glass-panel rounded-2xl p-6 border border-slate-800/60 text-center text-slate-500 text-sm">
                    <Users className="w-8 h-8 mx-auto mb-2 text-slate-700" />
                    Player statistics are not yet available for this fixture from the provider.
                  </div>
                )
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
