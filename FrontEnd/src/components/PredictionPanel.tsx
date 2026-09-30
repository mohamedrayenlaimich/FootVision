"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Trophy, Target, RefreshCw, AlertCircle } from "lucide-react";

interface LikelyScore {
  score: string;
  prob: string;
}

interface PredictionData {
  xGHome: number;
  xGAway: number;
  homeWinProb: number;
  drawProb: number;
  awayWinProb: number;
  scorelines: LikelyScore[];
}

export default function PredictionPanel() {
  const [homeTeam, setHomeTeam] = useState("FC Barcelona");
  const [awayTeam, setAwayTeam] = useState("Real Madrid");
  const [isPredicting, setIsPredicting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [prediction, setPrediction] = useState<PredictionData>({
    xGHome: 1.82,
    xGAway: 1.21,
    homeWinProb: 52.0,
    drawProb: 25.0,
    awayWinProb: 23.0,
    scorelines: [
      { score: "2 - 1", prob: "14.2%" },
      { score: "1 - 1", prob: "12.8%" },
      { score: "2 - 0", prob: "11.5%" },
      { score: "1 - 0", prob: "10.1%" },
    ],
  });

  const fetchPrediction = async () => {
    setIsPredicting(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/prediction/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam }),
      });

      if (!res.ok) {
        throw new Error("Failed to fetch prediction from FootVision API");
      }

      const data = await res.json();
      const scorelinesParsed: LikelyScore[] = (data.most_likely_scorelines || []).map((item: any) => {
        const key = Object.keys(item)[0];
        const val = item[key];
        return { score: key.replace("-", " - "), prob: `${val}%` };
      });

      setPrediction({
        xGHome: data.expected_goals_home,
        xGAway: data.expected_goals_away,
        homeWinProb: data.win_probability_home,
        drawProb: data.draw_probability,
        awayWinProb: data.win_probability_away,
        scorelines: scorelinesParsed.length > 0 ? scorelinesParsed : [
          { score: "2 - 1", prob: "14.2%" },
          { score: "1 - 1", prob: "12.8%" },
        ],
      });
    } catch (err: any) {
      setError(err.message || "Error generating prediction");
    } finally {
      setIsPredicting(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, []);

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            FootVision AI Match Forecast & xG Model
          </h2>
          <p className="text-xs text-slate-400">Data-driven Poisson Distribution & Match Outcome Forecasting</p>
        </div>

        <button
          onClick={fetchPrediction}
          disabled={isPredicting}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs hover:from-emerald-400 hover:to-cyan-400 transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isPredicting ? "animate-spin" : ""}`} />
          Recalculate AI Probabilities
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Matchup Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center bg-slate-900/60 p-5 rounded-xl border border-slate-800 text-center">
        <div>
          <div className="text-xs font-bold text-red-400 uppercase tracking-wider">Home Team</div>
          <input
            type="text"
            value={homeTeam}
            onChange={(e) => setHomeTeam(e.target.value)}
            className="mt-1 bg-slate-950 border border-slate-700 text-slate-100 font-black text-center text-sm rounded-lg py-1.5 px-3 w-full outline-none focus:border-red-500"
          />
        </div>

        <div className="flex flex-col items-center">
          <span className="text-xs font-black text-slate-500 uppercase tracking-widest">VS</span>
          <span className="text-[10px] text-emerald-400 font-semibold mt-1">Calculated Dynamically</span>
        </div>

        <div>
          <div className="text-xs font-bold text-blue-400 uppercase tracking-wider">Away Team</div>
          <input
            type="text"
            value={awayTeam}
            onChange={(e) => setAwayTeam(e.target.value)}
            className="mt-1 bg-slate-950 border border-slate-700 text-slate-100 font-black text-center text-sm rounded-lg py-1.5 px-3 w-full outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* xG Comparison Gauge */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl flex flex-col gap-3">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="text-red-400">{homeTeam} xG: {prediction.xGHome}</span>
          <span className="text-slate-400 flex items-center gap-1">
            <Target className="w-3.5 h-3.5 text-emerald-400" /> Expected Goals Comparison
          </span>
          <span className="text-blue-400">{awayTeam} xG: {prediction.xGAway}</span>
        </div>

        <div className="flex h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-red-600 to-rose-400 h-full transition-all duration-500"
            style={{ width: `${(prediction.xGHome / (prediction.xGHome + prediction.xGAway || 1)) * 100}%` }}
          />
          <div
            className="bg-gradient-to-r from-blue-400 to-indigo-600 h-full transition-all duration-500"
            style={{ width: `${(prediction.xGAway / (prediction.xGHome + prediction.xGAway || 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Win Probabilities Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-red-950/40 to-slate-900 border border-red-900/40 p-4 rounded-xl text-center">
          <div className="text-xs text-red-300 font-medium">Home Win Probability</div>
          <div className="text-2xl font-black text-red-400 mt-1">{prediction.homeWinProb}%</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
          <div className="text-xs text-slate-400 font-medium">Draw Probability</div>
          <div className="text-2xl font-black text-amber-400 mt-1">{prediction.drawProb}%</div>
        </div>

        <div className="bg-gradient-to-br from-blue-950/40 to-slate-900 border border-blue-900/40 p-4 rounded-xl text-center">
          <div className="text-xs text-blue-300 font-medium">Away Win Probability</div>
          <div className="text-2xl font-black text-blue-400 mt-1">{prediction.awayWinProb}%</div>
        </div>
      </div>

      {/* Most Likely Scorelines Matrix */}
      <div className="border-t border-slate-800/80 pt-4">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Trophy className="w-4 h-4 text-amber-400" />
          Most Likely Scorelines (Poisson Distribution)
        </h4>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {prediction.scorelines.map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-900/90 border border-slate-800 hover:border-emerald-500/50 p-3 rounded-xl text-center transition-all hover:scale-105"
            >
              <div className="text-base font-black text-slate-100">{item.score}</div>
              <div className="text-xs text-emerald-400 font-bold mt-0.5">{item.prob}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
