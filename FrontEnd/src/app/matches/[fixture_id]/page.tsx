"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  Trophy,
  Activity,
  ShieldAlert,
  Sparkles,
  BarChart2,
  Users,
  Award,
  TrendingUp,
  Info,
} from "lucide-react";
import Header from "@/components/Header";
import {
  fetchMatchDetails,
  fetchMatchStatistics,
  fetchMatchEvents,
  fetchMatchLineups,
  fetchMatchPlayers,
  fetchMatchHeadToHead,
  fetchMatchPredictions,
} from "@/lib/api/football";

// ---------------------------------------------------------------------------
// Helper: render an "unavailable" notice consistently
// ---------------------------------------------------------------------------
function UnavailableNotice({ message }: { message?: string }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 text-slate-400 text-xs">
      <Info className="w-4 h-4 flex-shrink-0 text-slate-500" />
      <span>{message || "Data unavailable from provider."}</span>
    </div>
  );
}

export default function MatchIntelligencePage({
  params,
}: {
  params: Promise<{ fixture_id: string }>;
}) {
  const resolvedParams = use(params);
  // Parse the fixture_id from the URL — this is the ONLY source of truth
  const fixtureId = parseInt(resolvedParams.fixture_id, 10);

  const [activeTab, setActiveTab] = useState<string>("matches");
  const [apiConnected, setApiConnected] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Match Intelligence Data states — all start as null (not fake defaults)
  const [matchDetail, setMatchDetail] = useState<any>(null);
  const [statistics, setStatistics] = useState<any>(null);
  const [events, setEvents] = useState<any>(null);
  const [lineups, setLineups] = useState<any>(null);
  const [players, setPlayers] = useState<any>(null);
  const [h2h, setH2H] = useState<any>(null);
  const [predictions, setPredictions] = useState<any>(null);

  useEffect(() => {
    async function loadAllMatchData() {
      if (!fixtureId || isNaN(fixtureId)) {
        setError("Invalid match fixture ID.");
        setLoading(false);
        return;
      }

      // Reset all state for this fixture_id — prevents stale data from a
      // previous match appearing while the new match is loading
      setMatchDetail(null);
      setStatistics(null);
      setEvents(null);
      setLineups(null);
      setPlayers(null);
      setH2H(null);
      setPredictions(null);
      setLoading(true);
      setError(null);

      try {
        const [
          detailRes,
          statsRes,
          eventsRes,
          lineupsRes,
          playersRes,
          h2hRes,
          predRes,
        ] = await Promise.allSettled([
          fetchMatchDetails(fixtureId),
          fetchMatchStatistics(fixtureId),
          fetchMatchEvents(fixtureId),
          fetchMatchLineups(fixtureId),
          fetchMatchPlayers(fixtureId),
          fetchMatchHeadToHead(fixtureId),
          fetchMatchPredictions(fixtureId),
        ]);

        // Each result is scoped to fixtureId — Promise.allSettled handles
        // partial failures gracefully without leaking data across matches
        if (detailRes.status === "fulfilled") setMatchDetail(detailRes.value.fixture);
        if (statsRes.status === "fulfilled") setStatistics(statsRes.value);
        if (eventsRes.status === "fulfilled") setEvents(eventsRes.value);
        if (lineupsRes.status === "fulfilled") setLineups(lineupsRes.value);
        if (playersRes.status === "fulfilled") setPlayers(playersRes.value);
        if (h2hRes.status === "fulfilled") setH2H(h2hRes.value);
        if (predRes.status === "fulfilled") setPredictions(predRes.value);

        // If match details themselves failed, show an error
        if (detailRes.status === "rejected") {
          setError("Match data is currently unavailable.");
        }
      } catch (err: any) {
        setError(err.message || "Failed to load match intelligence data.");
      } finally {
        setLoading(false);
      }
    }

    loadAllMatchData();
  }, [fixtureId]); // Re-runs whenever fixture_id changes — no stale data

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col items-center justify-center gap-4">
        <Activity className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">
          Loading match data...
        </p>
        <p className="text-xs text-slate-500">Fixture #{fixtureId}</p>
      </div>
    );
  }

  if (error && !matchDetail) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col items-center justify-center gap-4 px-6">
        <ShieldAlert className="w-10 h-10 text-red-400" />
        <p className="text-sm font-semibold text-red-300">Match data is currently unavailable.</p>
        <p className="text-xs text-slate-500">{error}</p>
        <Link
          href="/"
          className="mt-2 inline-flex items-center gap-2 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Resolve match data — never use hardcoded fallbacks for team names or scores
  // ---------------------------------------------------------------------------
  const fx = matchDetail || {};
  const homeTeam = fx.home_team || fx.homeTeam || {};
  const awayTeam = fx.away_team || fx.awayTeam || {};
  const league = fx.league || fx.competition || {};
  const venue = fx.venue || {};
  const score = fx.goals || fx.score?.fullTime || null;
  const statusStr = fx.status?.long || fx.status || null;

  const homeStats = statistics?.teams?.[0]?.statistics || null;
  const awayStats = statistics?.teams?.[1]?.statistics || null;
  const hasStatistics =
    statistics?.available !== false &&
    statistics?.teams &&
    statistics.teams.length > 0;

  const footvisionPred = predictions?.footvision_prediction || null;
  const extPred = predictions?.external_api_prediction || null;

  // Helper: stat bar widths from real numeric values only
  const calcBarWidths = (
    homeVal: any,
    awayVal: any
  ): { homeW: number; awayW: number } => {
    const parseNum = (v: any): number => {
      if (v === null || v === undefined) return 0;
      const str = String(v).replace("%", "").trim();
      return parseFloat(str) || 0;
    };
    const h = parseNum(homeVal);
    const a = parseNum(awayVal);
    const total = h + a;
    if (total === 0) return { homeW: 50, awayW: 50 };
    return {
      homeW: Math.round((h / total) * 100),
      awayW: Math.round((a / total) * 100),
    };
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiConnected={apiConnected}
        onRefreshApi={() => {}}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col gap-6">
        {/* Navigation Back Link */}
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>

        {/* Top Header Match Card Banner */}
        <div className="glass-panel rounded-3xl p-6 border border-slate-800 flex flex-col gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <Trophy className="w-64 h-64 text-emerald-400" />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold">
              <Trophy className="w-4 h-4 text-amber-400" />
              <span>{league.name || "—"}</span>
              {league.country && <span className="text-slate-500">• {league.country}</span>}
              {league.round && <span className="text-slate-500">• {league.round}</span>}
            </div>
            <div className="flex items-center gap-3 text-xs">
              {statusStr && (
                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
                  {statusStr}
                </span>
              )}
              {fx.date && (
                <span className="text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {new Date(fx.date).toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              )}
            </div>
          </div>

          {/* Teams vs Score Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center py-4">
            {/* Home Team */}
            <div className="flex items-center gap-4 justify-start md:justify-end text-right">
              <div>
                <h2 className="text-xl md:text-2xl font-black text-slate-100">
                  {homeTeam.name || "—"}
                </h2>
                <p className="text-xs text-slate-400 font-medium">Home Team</p>
              </div>
              {homeTeam.logo || homeTeam.crest ? (
                <img
                  src={homeTeam.logo || homeTeam.crest}
                  alt={homeTeam.name}
                  className="w-16 h-16 object-contain"
                />
              ) : (
                homeTeam.name && (
                  <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-lg">
                    {homeTeam.name.substring(0, 3).toUpperCase()}
                  </div>
                )
              )}
            </div>

            {/* Score Center */}
            <div className="flex flex-col items-center justify-center gap-2 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-inner">
              {score !== null ? (
                <div className="text-3xl md:text-4xl font-black text-emerald-400 tracking-wider">
                  {score.home ?? "—"} - {score.away ?? "—"}
                </div>
              ) : (
                <div className="text-2xl font-black text-slate-500">VS</div>
              )}
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-500" />
                {venue.name || "—"} {venue.city ? `(${venue.city})` : ""}
              </span>
            </div>

            {/* Away Team */}
            <div className="flex items-center gap-4 justify-start">
              {awayTeam.logo || awayTeam.crest ? (
                <img
                  src={awayTeam.logo || awayTeam.crest}
                  alt={awayTeam.name}
                  className="w-16 h-16 object-contain"
                />
              ) : (
                awayTeam.name && (
                  <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-lg">
                    {awayTeam.name.substring(0, 3).toUpperCase()}
                  </div>
                )
              )}
              <div>
                <h2 className="text-xl md:text-2xl font-black text-slate-100">
                  {awayTeam.name || "—"}
                </h2>
                <p className="text-xs text-slate-400 font-medium">Away Team</p>
              </div>
            </div>
          </div>

          {/* Data attribution */}
          <p className="text-[10px] text-slate-600 text-right">
            Match data provided by{" "}
            <a
              href="https://www.football-data.org"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-slate-400 transition-colors"
            >
              football-data.org
            </a>
          </p>
        </div>

        {/* SECTION: PREDICTIONS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* FootVision AI Prediction */}
          <div className="glass-panel rounded-2xl p-5 border border-emerald-500/40 bg-gradient-to-b from-emerald-950/20 to-slate-900/60 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-emerald-500/20 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">FootVision AI Prediction Engine</h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                Poisson xG Model
              </span>
            </div>

            {!footvisionPred ? (
              <UnavailableNotice message="Prediction unavailable — match data not loaded." />
            ) : footvisionPred.available === false ? (
              <UnavailableNotice message={footvisionPred.message} />
            ) : (
              <>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">
                      {homeTeam.name || "Home"} Win
                    </span>
                    <span className="text-xl font-black text-emerald-400">
                      {footvisionPred.probabilities?.home_win ?? "—"}%
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">Draw</span>
                    <span className="text-xl font-black text-amber-400">
                      {footvisionPred.probabilities?.draw ?? "—"}%
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">
                      {awayTeam.name || "Away"} Win
                    </span>
                    <span className="text-xl font-black text-cyan-400">
                      {footvisionPred.probabilities?.away_win ?? "—"}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
                  <span className="text-slate-400">Expected Goals (xG):</span>
                  <span className="font-bold text-slate-200">
                    {homeTeam.name || "Home"}:{" "}
                    <span className="text-emerald-400">
                      {footvisionPred.expected_goals?.home ?? "—"}
                    </span>{" "}
                    | {awayTeam.name || "Away"}:{" "}
                    <span className="text-cyan-400">
                      {footvisionPred.expected_goals?.away ?? "—"}
                    </span>
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
                  <span className="text-slate-400">Most Probable Score:</span>
                  <span className="font-extrabold text-emerald-400 text-sm">
                    {footvisionPred.most_probable_score ?? "—"}
                  </span>
                </div>

                <p className="text-[10px] text-slate-600">
                  Inputs source: {footvisionPred.inputs_source === "real_h2h_data"
                    ? "Real head-to-head data"
                    : "League average defaults (H2H unavailable)"}
                </p>
              </>
            )}
          </div>

          {/* External API-Football Prediction */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-slate-100">API-Football Prediction</h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                External API Engine
              </span>
            </div>

            {!extPred ? (
              <UnavailableNotice message="External prediction unavailable." />
            ) : extPred.available === false ? (
              <UnavailableNotice message={extPred.message || "Prediction not available for this fixture."} />
            ) : (
              <>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">Home</span>
                    <span className="text-lg font-bold text-slate-200">
                      {extPred.probabilities?.home ?? "—"}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">Draw</span>
                    <span className="text-lg font-bold text-slate-200">
                      {extPred.probabilities?.draw ?? "—"}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="block text-[11px] text-slate-400 mb-1">Away</span>
                    <span className="text-lg font-bold text-slate-200">
                      {extPred.probabilities?.away ?? "—"}
                    </span>
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs flex flex-col gap-1">
                  <span className="text-slate-400 font-medium">API Advice:</span>
                  <span className="text-slate-200 font-semibold">
                    {extPred.advice ?? "—"}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* SECTION: REAL MATCH STATISTICS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-5">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <BarChart2 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">Real Match Statistics</h3>
          </div>

          {!hasStatistics ? (
            <UnavailableNotice
              message={
                statistics?.message ||
                "Match statistics are not yet available for this fixture."
              }
            />
          ) : (
            <div className="flex flex-col gap-4">
              {[
                { label: "Possession", home: homeStats?.possession, away: awayStats?.possession },
                { label: "Total Shots", home: homeStats?.total_shots, away: awayStats?.total_shots },
                { label: "Shots on Target", home: homeStats?.shots_on_target, away: awayStats?.shots_on_target },
                { label: "Shots Off Target", home: homeStats?.shots_off_target, away: awayStats?.shots_off_target },
                { label: "Passes", home: homeStats?.passes, away: awayStats?.passes },
                { label: "Pass Accuracy", home: homeStats?.pass_accuracy, away: awayStats?.pass_accuracy },
                { label: "Corner Kicks", home: homeStats?.corners, away: awayStats?.corners },
                { label: "Fouls", home: homeStats?.fouls, away: awayStats?.fouls },
                { label: "Yellow Cards", home: homeStats?.yellow_cards, away: awayStats?.yellow_cards },
              ]
                .filter(
                  (st) =>
                    st.home !== null &&
                    st.home !== undefined &&
                    st.away !== null &&
                    st.away !== undefined
                )
                .map((st, idx) => {
                  const { homeW, awayW } = calcBarWidths(st.home, st.away);
                  return (
                    <div key={idx} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-center justify-between font-semibold">
                        <span className="text-emerald-400">{st.home}</span>
                        <span className="text-slate-400">{st.label}</span>
                        <span className="text-cyan-400">{st.away}</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${homeW}%` }} />
                        <div className="h-full bg-cyan-500 transition-all" style={{ width: `${awayW}%` }} />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>

        {/* SECTION: MATCH TIMELINE EVENTS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Clock className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-slate-100">Match Timeline Events</h3>
          </div>

          {events?.available === false ? (
            <UnavailableNotice message={events.message} />
          ) : (events?.events || []).length === 0 ? (
            <UnavailableNotice message="No match events available for this fixture." />
          ) : (
            <div className="flex flex-col gap-3">
              {(events.events || []).map((ev: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
                >
                  <span className="w-12 font-bold text-emerald-400">{ev.time}</span>
                  <span className="font-semibold text-slate-200">{ev.team?.name}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                    {ev.type}
                    {ev.detail && ev.detail !== ev.type ? ` — ${ev.detail}` : ""}
                  </span>
                  <span className="text-slate-400 max-w-[120px] truncate">
                    {ev.player?.name || ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SECTION: STARTING XI LINEUPS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Users className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-slate-100">Team Lineups & Formations</h3>
          </div>

          {lineups?.available === false ? (
            <UnavailableNotice
              message={lineups.message || "Lineups not yet available for this fixture."}
            />
          ) : (lineups?.lineups || []).length === 0 ? (
            <UnavailableNotice message="Lineups not yet available for this fixture." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {(lineups.lineups || []).map((lu: any, idx: number) => (
                <div key={idx} className="flex flex-col gap-3">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <div className="flex items-center gap-2">
                      {lu.team?.logo && (
                        <img
                          src={lu.team.logo}
                          alt={lu.team.name}
                          className="w-6 h-6 object-contain"
                        />
                      )}
                      <span className="font-bold text-slate-200">{lu.team?.name}</span>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-emerald-400">
                      {lu.formation || ""}
                    </span>
                  </div>
                  {lu.coach?.name && (
                    <div className="text-[11px] text-slate-400 flex items-center gap-1">
                      <span className="text-slate-500">Coach:</span>
                      <span className="font-semibold text-slate-300">{lu.coach.name}</span>
                    </div>
                  )}
                  <div className="flex flex-col gap-1.5 text-xs">
                    <span className="text-slate-400 font-medium mb-1">Starting XI:</span>
                    {(lu.start_xi || []).map((player: any, pi: number) => (
                      <div
                        key={pi}
                        className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50"
                      >
                        <span className="font-bold text-emerald-400 w-6">#{player.number}</span>
                        <span className="text-slate-200 flex-1">{player.name}</span>
                        <span className="text-slate-400">{player.pos}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SECTION: HEAD-TO-HEAD HISTORY */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Award className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">Head-to-Head History</h3>
          </div>

          {h2h?.available === false ? (
            <UnavailableNotice
              message={h2h.message || "Head-to-head history unavailable."}
            />
          ) : (
            <>
              {h2h?.summary && (
                <div className="grid grid-cols-3 gap-3 text-center mb-2">
                  <div className="p-2 rounded-xl bg-emerald-950/30 border border-emerald-800/30">
                    <div className="text-lg font-black text-emerald-400">
                      {h2h.summary.team1_wins ?? 0}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {homeTeam.name || "Home"} Wins
                    </div>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                    <div className="text-lg font-black text-amber-400">
                      {h2h.summary.draws ?? 0}
                    </div>
                    <div className="text-[10px] text-slate-400">Draws</div>
                  </div>
                  <div className="p-2 rounded-xl bg-cyan-950/30 border border-cyan-800/30">
                    <div className="text-lg font-black text-cyan-400">
                      {h2h.summary.team2_wins ?? 0}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {awayTeam.name || "Away"} Wins
                    </div>
                  </div>
                </div>
              )}
              <div className="flex flex-col gap-2 text-xs">
                {(h2h?.meetings || []).length === 0 ? (
                  <UnavailableNotice message="No H2H meetings data available." />
                ) : (
                  (h2h.meetings || []).map((m: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800"
                    >
                      <span className="text-slate-400">
                        {m.date
                          ? new Date(m.date).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })
                          : "—"}
                      </span>
                      <span className="font-bold text-slate-200">{m.home_team}</span>
                      <span className="px-3 py-0.5 rounded bg-slate-800 text-emerald-400 font-black">
                        {m.score}
                      </span>
                      <span className="font-bold text-slate-200">{m.away_team}</span>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>

        {/* Data Attribution Footer */}
        <div className="flex items-center justify-center gap-2 py-2 text-[11px] text-slate-600">
          <Info className="w-3 h-3" />
          <span>
            Match statistics and predictions data provided by{" "}
            <a
              href="https://www.football-data.org"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-slate-400 transition-colors"
            >
              football-data.org
            </a>{" "}
            and API-Football. FootVision AI is not the source of this data.
          </span>
        </div>
      </main>
    </div>
  );
}
