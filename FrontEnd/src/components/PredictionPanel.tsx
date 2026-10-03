"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Trophy, Target, RefreshCw, AlertCircle, Calendar, ArrowRight, Activity, Percent } from "lucide-react";
import { fetchFixtures, FixtureItem } from "@/lib/api/football";

interface LikelyScore {
  score: string;
  prob: string;
}

interface PredictionData {
  homeTeam: string;
  awayTeam: string;
  xGHome: number;
  xGAway: number;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  scorelines: LikelyScore[];
}

const POPULAR_MATCHUPS = [
  { home: "Arsenal", away: "Chelsea" },
  { home: "Real Madrid", away: "FC Barcelona" },
  { home: "Manchester City", away: "Liverpool" },
  { home: "Bayern Munich", away: "Borussia Dortmund" },
  { home: "Paris Saint Germain", away: "Marseille" },
  { home: "Inter", away: "AC Milan" },
];

export default function PredictionPanel() {
  const [homeTeam, setHomeTeam] = useState<string>("Arsenal");
  const [awayTeam, setAwayTeam] = useState<string>("Chelsea");
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);

  // Fixtures from real API for quick-selection
  const [upcomingMatches, setUpcomingMatches] = useState<FixtureItem[]>([]);
  const [loadingFixtures, setLoadingFixtures] = useState<boolean>(false);

  useEffect(() => {
    async function loadUpcoming() {
      setLoadingFixtures(true);
      try {
        const data = await fetchFixtures({ next: 8 });
        setUpcomingMatches(data.fixtures || []);
      } catch {
        // Fallback to popular presets
      } finally {
        setLoadingFixtures(false);
      }
    }
    loadUpcoming();
  }, []);

  const runPrediction = async (home: string, away: string) => {
    if (!home.trim() || !away.trim()) return;
    setIsPredicting(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/prediction/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home_team: home, away_team: away }),
      });

      if (!res.ok) {
        throw new Error("FootVision Prediction Service returned an error.");
      }

      const data = await res.json();
      const scorelinesParsed: LikelyScore[] = (data.most_likely_scorelines || []).map((item: any) => {
        const key = Object.keys(item)[0];
        const val = item[key];
        return { score: key.replace("-", " - "), prob: `${val}%` };
      });

      setPrediction({
        homeTeam: data.home_team || home,
        awayTeam: data.away_team || away,
        xGHome: data.expected_goals_home,
        xGAway: data.expected_goals_away,
        homeWinProb: data.win_probability_home,
        drawProb: data.draw_probability,
        awayWinProb: data.win_probability_away,
        scorelines: scorelinesParsed,
      });
    } catch (err: any) {
      setError(err.message || "Failed to generate prediction.");
    } finally {
      setIsPredicting(false);
    }
  };

  useEffect(() => {
    runPrediction(homeTeam, awayTeam);
  }, []);

  const selectMatch = (h: string, a: string) => {
    setHomeTeam(h);
    setAwayTeam(a);
    runPrediction(h, a);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 border border-white/[0.08] shadow-2xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            FootVision AI Match Forecast &amp; xG Engine
          </h2>
          <p className="text-xs text-slate-400">
            Poisson Probability Distribution &amp; Expected Goals (xG) Statistical Model
          </p>
        </div>

        <button
          onClick={() => runPrediction(homeTeam, awayTeam)}
          disabled={isPredicting}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs hover:from-emerald-400 hover:to-cyan-400 transition-all shadow-lg shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isPredicting ? "animate-spin" : ""}`} />
          Recalculate AI Forecast
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Quick Select Real Upcoming Matches */}
      {upcomingMatches.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3 h-3 text-emerald-400" />
            Quick-Select Upcoming Match from Real Fixtures
          </span>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {upcomingMatches.map((m) => (
              <button
                key={m.fixture_id}
                onClick={() => selectMatch(m.home_team.name, m.away_team.name)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border flex-shrink-0 ${
                  homeTeam === m.home_team.name && awayTeam === m.away_team.name
                    ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10"
                    : "bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900"
                }`}
              >
                {m.home_team.logo && <img src={m.home_team.logo} alt="" className="w-4 h-4 object-contain" />}
                <span>{m.home_team.name}</span>
                <span className="text-[10px] text-slate-500 font-bold">vs</span>
                {m.away_team.logo && <img src={m.away_team.logo} alt="" className="w-4 h-4 object-contain" />}
                <span>{m.away_team.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Popular Derbies Selector (if fixtures unavailable) */}
      {upcomingMatches.length === 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Popular High-Stakes Matchups
          </span>
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {POPULAR_MATCHUPS.map((m) => (
              <button
                key={`${m.home}-${m.away}`}
                onClick={() => selectMatch(m.home, m.away)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all border flex-shrink-0 ${
                  homeTeam === m.home && awayTeam === m.away
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
              >
                {m.home} vs {m.away}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Matchup Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center bg-slate-900/60 p-5 rounded-2xl border border-slate-800 text-center">
        <div>
          <div className="text-xs font-bold text-red-400 uppercase tracking-wider mb-1.5">Home Team</div>
          <input
            type="text"
            value={homeTeam}
            onChange={(e) => setHomeTeam(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-100 font-black text-center text-sm rounded-xl py-2 px-3 w-full outline-none focus:border-red-500 transition-colors"
          />
        </div>

        <div className="flex flex-col items-center">
          <span className="text-xs font-black text-slate-500 uppercase tracking-widest">VS</span>
          <span className="text-[10px] text-emerald-400 font-semibold mt-1">Poisson xG Simulation</span>
        </div>

        <div>
          <div className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-1.5">Away Team</div>
          <input
            type="text"
            value={awayTeam}
            onChange={(e) => setAwayTeam(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-100 font-black text-center text-sm rounded-xl py-2 px-3 w-full outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {prediction && (
        <div className="flex flex-col gap-6 animate-fade-in">
          {/* xG Comparison Gauge */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs font-bold">
              <span className="text-red-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                {prediction.homeTeam} xG: {prediction.xGHome}
              </span>
              <span className="text-slate-400 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-emerald-400" /> Expected Goals (xG) Split
              </span>
              <span className="text-blue-400 flex items-center gap-1.5">
                {prediction.awayTeam} xG: {prediction.xGAway}
                <span className="w-2 h-2 rounded-full bg-blue-400" />
              </span>
            </div>

            <div className="flex h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-gradient-to-r from-red-600 to-rose-400 h-full transition-all duration-700"
                style={{
                  width: `${(prediction.xGHome / (prediction.xGHome + prediction.xGAway || 1)) * 100}%`,
                }}
              />
              <div
                className="bg-gradient-to-r from-blue-400 to-indigo-600 h-full transition-all duration-700"
                style={{
                  width: `${(prediction.xGAway / (prediction.xGHome + prediction.xGAway || 1)) * 100}%`,
                }}
              />
            </div>
          </div>

          {/* Win Probabilities Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-red-950/40 to-slate-900 border border-red-900/40 p-4 rounded-xl text-center">
              <div className="text-xs text-red-300 font-medium">{prediction.homeTeam} Win</div>
              <div className="text-2xl font-black text-red-400 mt-1">{prediction.homeWinProb}%</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-xs text-slate-400 font-medium">Draw Probability</div>
              <div className="text-2xl font-black text-amber-400 mt-1">{prediction.drawProb}%</div>
            </div>

            <div className="bg-gradient-to-br from-blue-950/40 to-slate-900 border border-blue-900/40 p-4 rounded-xl text-center">
              <div className="text-xs text-blue-300 font-medium">{prediction.awayTeam} Win</div>
              <div className="text-2xl font-black text-blue-400 mt-1">{prediction.awayWinProb}%</div>
            </div>
          </div>

          {/* Most Likely Scorelines Matrix */}
          {prediction.scorelines && prediction.scorelines.length > 0 && (
            <div className="border-t border-slate-800/80 pt-4">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Trophy className="w-4 h-4 text-amber-400" />
                Most Probable Exact Scorelines (Poisson Distribution)
              </h4>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {prediction.scorelines.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-900/90 border border-slate-800 hover:border-emerald-500/50 p-3.5 rounded-xl text-center transition-all hover:scale-105"
                  >
                    <div className="text-lg font-black text-slate-100">{item.score}</div>
                    <div className="text-xs text-emerald-400 font-bold mt-0.5">{item.prob} probability</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
