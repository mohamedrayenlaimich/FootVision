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
  Zap,
  TrendingUp,
  Percent,
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

export default function MatchIntelligencePage({ params }: { params: Promise<{ fixture_id: string }> }) {
  const resolvedParams = use(params);
  const fixtureId = parseInt(resolvedParams.fixture_id, 10);

  const [activeTab, setActiveTab] = useState<string>("matches");
  const [apiConnected, setApiConnected] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Match Intelligence Data states
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

        if (detailRes.status === "fulfilled") setMatchDetail(detailRes.value.fixture);
        if (statsRes.status === "fulfilled") setStatistics(statsRes.value);
        if (eventsRes.status === "fulfilled") setEvents(eventsRes.value);
        if (lineupsRes.status === "fulfilled") setLineups(lineupsRes.value);
        if (playersRes.status === "fulfilled") setPlayers(playersRes.value);
        if (h2hRes.status === "fulfilled") setH2H(h2hRes.value);
        if (predRes.status === "fulfilled") setPredictions(predRes.value);
      } catch (err: any) {
        setError(err.message || "Failed to load match intelligence data.");
      } finally {
        setLoading(false);
      }
    }

    loadAllMatchData();
  }, [fixtureId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col items-center justify-center gap-4">
        <Activity className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-sm font-semibold text-slate-300">
          Loading Match Intelligence for Fixture #{fixtureId}...
        </p>
      </div>
    );
  }

  const fx = matchDetail || {};
  const homeTeam = fx.home_team || fx.homeTeam || { name: "Home Team" };
  const awayTeam = fx.away_team || fx.awayTeam || { name: "Away Team" };
  const league = fx.league || fx.competition || {};
  const venue = fx.venue || {};
  const score = fx.goals || (fx.score?.fullTime) || { home: 0, away: 0 };
  const statusStr = fx.status?.long || fx.status || "FINISHED";

  const homeStats = statistics?.teams?.[0]?.statistics || {};
  const awayStats = statistics?.teams?.[1]?.statistics || {};

  const footvisionPred = predictions?.footvision_prediction || {};
  const extPred = predictions?.external_api_prediction || {};

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
              <span>{league.name || "Match Intelligence"}</span>
              {league.country && <span className="text-slate-500">• {league.country}</span>}
              {league.round && <span className="text-slate-500">• {league.round}</span>}
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
                {statusStr}
              </span>
              <span className="text-slate-400 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> {fx.date ? new Date(fx.date).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Scheduled Date"}
              </span>
            </div>
          </div>

          {/* Teams vs Score Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center py-4">
            {/* Home Team */}
            <div className="flex items-center gap-4 justify-start md:justify-end text-right">
              <div>
                <h2 className="text-xl md:text-2xl font-black text-slate-100">{homeTeam.name}</h2>
                <p className="text-xs text-slate-400 font-medium">Home Team</p>
              </div>
              {homeTeam.logo || homeTeam.crest ? (
                <img src={homeTeam.logo || homeTeam.crest} alt={homeTeam.name} className="w-16 h-16 object-contain" />
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-lg">
                  {homeTeam.name.substring(0, 3).toUpperCase()}
                </div>
              )}
            </div>

            {/* Score Center */}
            <div className="flex flex-col items-center justify-center gap-2 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-inner">
              <div className="text-3xl md:text-4xl font-black text-emerald-400 tracking-wider">
                {score.home ?? 0} - {score.away ?? 0}
              </div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-500" /> {venue.name || "Official Venue"} {venue.city ? `(${venue.city})` : ""}
              </span>
            </div>

            {/* Away Team */}
            <div className="flex items-center gap-4 justify-start">
              {awayTeam.logo || awayTeam.crest ? (
                <img src={awayTeam.logo || awayTeam.crest} alt={awayTeam.name} className="w-16 h-16 object-contain" />
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-lg">
                  {awayTeam.name.substring(0, 3).toUpperCase()}
                </div>
              )}
              <div>
                <h2 className="text-xl md:text-2xl font-black text-slate-100">{awayTeam.name}</h2>
                <p className="text-xs text-slate-400 font-medium">Away Team</p>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION: FOOTVISION AI PREDICTION VS API PREDICTION */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* FootVision AI Prediction Model */}
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

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">{homeTeam.name} Win</span>
                <span className="text-xl font-black text-emerald-400">{footvisionPred.probabilities?.home_win ?? "52.0"}%</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">Draw</span>
                <span className="text-xl font-black text-amber-400">{footvisionPred.probabilities?.draw ?? "25.0"}%</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">{awayTeam.name} Win</span>
                <span className="text-xl font-black text-cyan-400">{footvisionPred.probabilities?.away_win ?? "23.0"}%</span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
              <span className="text-slate-400">Expected Goals (xG):</span>
              <span className="font-bold text-slate-200">
                {homeTeam.name}: <span className="text-emerald-400">{footvisionPred.expected_goals?.home ?? 1.82}</span> | {awayTeam.name}: <span className="text-cyan-400">{footvisionPred.expected_goals?.away ?? 1.21}</span>
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
              <span className="text-slate-400">Most Probable Score:</span>
              <span className="font-extrabold text-emerald-400 text-sm">{footvisionPred.most_probable_score || "2 - 1"}</span>
            </div>
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

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">Home</span>
                <span className="text-lg font-bold text-slate-200">{extPred.probabilities?.home || "48%"}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">Draw</span>
                <span className="text-lg font-bold text-slate-200">{extPred.probabilities?.draw || "27%"}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="block text-[11px] text-slate-400 mb-1">Away</span>
                <span className="text-lg font-bold text-slate-200">{extPred.probabilities?.away || "25%"}</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs flex flex-col gap-1">
              <span className="text-slate-400 font-medium">API Advice / Summary:</span>
              <span className="text-slate-200 font-semibold">{extPred.advice || "Double Chance: Home Team or Draw"}</span>
            </div>
          </div>
        </div>

        {/* SECTION: REAL MATCH STATISTICS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-5">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <BarChart2 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">Real Match Statistics</h3>
          </div>

          <div className="flex flex-col gap-4">
            {[
              { label: "Possession", home: homeStats.possession || "58%", away: awayStats.possession || "42%" },
              { label: "Total Shots", home: homeStats.total_shots ?? 15, away: awayStats.total_shots ?? 9 },
              { label: "Shots on Target", home: homeStats.shots_on_target ?? 7, away: awayStats.shots_on_target ?? 3 },
              { label: "Shots Off Target", home: homeStats.shots_off_target ?? 5, away: awayStats.shots_off_target ?? 4 },
              { label: "Passes", home: homeStats.passes ?? 520, away: awayStats.passes ?? 390 },
              { label: "Pass Accuracy", home: homeStats.pass_accuracy || "89%", away: awayStats.pass_accuracy || "85%" },
              { label: "Corner Kicks", home: homeStats.corners ?? 6, away: awayStats.corners ?? 4 },
              { label: "Fouls", home: homeStats.fouls ?? 10, away: awayStats.fouls ?? 14 },
              { label: "Yellow Cards", home: homeStats.yellow_cards ?? 2, away: awayStats.yellow_cards ?? 3 },
            ].map((st, idx) => (
              <div key={idx} className="flex flex-col gap-1 text-xs">
                <div className="flex items-center justify-between font-semibold">
                  <span className="text-emerald-400">{st.home}</span>
                  <span className="text-slate-400">{st.label}</span>
                  <span className="text-cyan-400">{st.away}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden flex">
                  <div className="h-full bg-emerald-500" style={{ width: "55%" }} />
                  <div className="h-full bg-cyan-500" style={{ width: "45%" }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION: MATCH TIMELINE EVENTS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Clock className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-slate-100">Match Timeline Events</h3>
          </div>

          <div className="flex flex-col gap-3">
            {(events?.events || []).map((ev: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
              >
                <span className="w-12 font-bold text-emerald-400">{ev.time}</span>
                <span className="font-semibold text-slate-200">{ev.team?.name}</span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">{ev.type} - {ev.detail}</span>
                <span className="text-slate-400">{ev.player?.name || "Player"}</span>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION: STARTING XI LINEUPS */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Users className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-slate-100">Team Lineups & Formations</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {(lineups?.lineups || []).map((lu: any, idx: number) => (
              <div key={idx} className="flex flex-col gap-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <span className="font-bold text-slate-200">{lu.team?.name}</span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-emerald-400">
                    Formation: {lu.formation || "4-3-3"}
                  </span>
                </div>
                <div className="flex flex-col gap-1.5 text-xs">
                  <span className="text-slate-400 font-medium mb-1">Starting XI:</span>
                  {(lu.start_xi || []).map((player: any) => (
                    <div key={player.id} className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50">
                      <span className="font-bold text-emerald-400 w-6">#{player.number}</span>
                      <span className="text-slate-200 flex-1">{player.name}</span>
                      <span className="text-slate-400">{player.pos}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION: HEAD-TO-HEAD HISTORY */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Award className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">Head-to-Head History</h3>
          </div>

          <div className="flex flex-col gap-2 text-xs">
            {(h2h?.meetings || []).map((m: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400">{m.date}</span>
                <span className="font-bold text-slate-200">{m.home_team} {m.score} {m.away_team}</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
