"use client";

import React, { useState } from "react";
import { Layers, Flame, Eye, Compass, Zap, Shield, Sparkles, RefreshCw } from "lucide-react";

export interface PlayerMetricItem {
  track_id: number;
  team?: string;
  jersey_number?: number | null;
  player_name?: string | null;
  distance_covered_meters: number;
  max_speed_kmh: number;
  sprint_count: number;
  average_pitch_x: number; // percentage 0 - 100
  average_pitch_y: number; // percentage 0 - 100
}

interface TacticalPitchProps {
  players?: PlayerMetricItem[];
  selectedPlayer?: PlayerMetricItem | null;
  onSelectPlayer?: (player: PlayerMetricItem | null) => void;
  onLoadSample?: () => void;
  loading?: boolean;
}

export default function TacticalPitch({
  players = [],
  selectedPlayer: controlledSelectedPlayer,
  onSelectPlayer,
  onLoadSample,
  loading = false,
}: TacticalPitchProps) {
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [showTrajectories, setShowTrajectories] = useState<boolean>(true);
  const [showVectors, setShowVectors] = useState<boolean>(false);
  const [internalSelectedPlayer, setInternalSelectedPlayer] = useState<PlayerMetricItem | null>(null);

  const activePlayer = controlledSelectedPlayer !== undefined ? controlledSelectedPlayer : internalSelectedPlayer;
  const setActivePlayer = (p: PlayerMetricItem | null) => {
    if (onSelectPlayer) {
      onSelectPlayer(p);
    } else {
      setInternalSelectedPlayer(p);
    }
  };

  const hasPlayers = players && players.length > 0;

  return (
    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col gap-4 border border-white/[0.08] shadow-2xl">
      {/* Pitch Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            Tactical 2D Pitch Radar
            {hasPlayers && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-semibold">
                {players.length} Tracked Entities
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400">
            Homography matrix 2D projection extracted from computer vision pipeline
          </p>
        </div>

        {/* Radar Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {onLoadSample && !hasPlayers && (
            <button
              onClick={onLoadSample}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-all active:scale-95 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              Load CV Telemetry Demo
            </button>
          )}

          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              showHeatmap
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            Heatmap
          </button>

          <button
            onClick={() => setShowTrajectories(!showTrajectories)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              showTrajectories
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            Trajectories
          </button>

          <button
            onClick={() => setShowVectors(!showVectors)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              showVectors
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            Velocity Vectors
          </button>
        </div>
      </div>

      {/* Pitch Area */}
      <div className="relative w-full aspect-[105/68] pitch-container rounded-2xl overflow-hidden shadow-2xl border border-emerald-900/30">
        {/* Heatmap Overlay Simulation */}
        {showHeatmap && hasPlayers && (
          <div className="absolute inset-0 pointer-events-none opacity-45 mix-blend-screen bg-[radial-gradient(ellipse_at_35%_50%,#ef4444_0%,transparent_50%),radial-gradient(ellipse_at_65%_50%,#3b82f6_0%,transparent_50%)]" />
        )}

        {/* SVG Pitch Markings */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 68" preserveAspectRatio="none">
          {/* Pitch Outer Line */}
          <rect x="2" y="2" width="96" height="64" className="pitch-line" rx="1.5" />
          {/* Halfway Line */}
          <line x1="50" y1="2" x2="50" y2="66" className="pitch-line" />
          {/* Center Circle */}
          <circle cx="50" cy="34" r="9.15" className="pitch-line" />
          <circle cx="50" cy="34" r="0.8" fill="#ffffff" />

          {/* Left Penalty Area */}
          <rect x="2" y="13.8" width="16.5" height="40.4" className="pitch-line" />
          <rect x="2" y="24.8" width="5.5" height="18.4" className="pitch-line" />
          <circle cx="13" cy="34" r="0.6" fill="#ffffff" />
          {/* Left Arc */}
          <path d="M 18.5 28.5 A 9.15 9.15 0 0 1 18.5 39.5" fill="none" className="pitch-line" />

          {/* Right Penalty Area */}
          <rect x="81.5" y="13.8" width="16.5" height="40.4" className="pitch-line" />
          <rect x="92.5" y="24.8" width="5.5" height="18.4" className="pitch-line" />
          <circle cx="87" cy="34" r="0.6" fill="#ffffff" />
          {/* Right Arc */}
          <path d="M 81.5 28.5 A 9.15 9.15 0 0 0 81.5 39.5" fill="none" className="pitch-line" />
        </svg>

        {/* Empty state overlay when no players are loaded */}
        {!hasPlayers && !loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 bg-slate-950/70 backdrop-blur-sm z-30 text-center">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-3 shadow-lg shadow-emerald-500/10">
              <Layers className="w-7 h-7" />
            </div>
            <h3 className="text-sm font-bold text-slate-100 mb-1">No Active Radar Telemetry Loaded</h3>
            <p className="text-xs text-slate-400 max-w-md mb-4 leading-relaxed">
              Upload a match video in the Video Pipeline to extract real-time tracking, or click below to preview sample computer-vision telemetry on the pitch.
            </p>
            {onLoadSample && (
              <button
                onClick={onLoadSample}
                className="btn-primary inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Load Sample Telemetry Demo
              </button>
            )}
          </div>
        )}

        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/70 backdrop-blur-sm z-30">
            <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mb-2" />
            <p className="text-xs text-slate-300 font-medium">Computing tactical homography projection...</p>
          </div>
        )}

        {/* Trajectory Lines */}
        {showTrajectories && hasPlayers && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-50">
            {players.map((p) => {
              const isHome = (p.team || "").toLowerCase().includes("red") || (p.team || "").toLowerCase().includes("home") || p.track_id % 2 !== 0;
              const dx = isHome ? -3 : 3;
              const dy = (p.track_id % 3 === 0) ? -2 : 2;
              return (
                <line
                  key={`traj-${p.track_id}`}
                  x1={`${p.average_pitch_x + dx}%`}
                  y1={`${p.average_pitch_y + dy}%`}
                  x2={`${p.average_pitch_x}%`}
                  y2={`${p.average_pitch_y}%`}
                  stroke={isHome ? "#ef4444" : "#3b82f6"}
                  strokeWidth="1.5"
                  strokeDasharray="2,2"
                />
              );
            })}
          </svg>
        )}

        {/* Velocity Vectors */}
        {showVectors && hasPlayers && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-80">
            {players.map((p) => {
              const angle = (p.track_id * 37) % 360;
              const length = Math.min(6, (p.max_speed_kmh / 35.0) * 4);
              const rad = (angle * Math.PI) / 180;
              const vx = Math.cos(rad) * length;
              const vy = Math.sin(rad) * length;
              return (
                <line
                  key={`vec-${p.track_id}`}
                  x1={`${p.average_pitch_x}%`}
                  y1={`${p.average_pitch_y}%`}
                  x2={`${p.average_pitch_x + vx}%`}
                  y2={`${p.average_pitch_y + vy}%`}
                  stroke="#10b981"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              );
            })}
          </svg>
        )}

        {/* Render Tracked Players */}
        {hasPlayers &&
          players.map((player) => {
            const isHome =
              (player.team || "").toLowerCase().includes("red") ||
              (player.team || "").toLowerCase().includes("home") ||
              player.track_id % 2 !== 0;
            const isSelected = activePlayer?.track_id === player.track_id;

            return (
              <button
                key={player.track_id}
                onClick={() => setActivePlayer(isSelected ? null : player)}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 z-20 group transition-all duration-300 ${
                  isSelected ? "scale-125 z-40" : "hover:scale-115"
                }`}
                style={{ left: `${player.average_pitch_x}%`, top: `${player.average_pitch_y}%` }}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] text-white border-2 shadow-md transition-all ${
                    isHome
                      ? "bg-gradient-to-br from-red-500 to-rose-700 border-red-300 shadow-red-900/50"
                      : "bg-gradient-to-br from-blue-500 to-indigo-700 border-blue-300 shadow-blue-900/50"
                  } ${isSelected ? "ring-4 ring-emerald-400 ring-offset-2 ring-offset-slate-950 scale-110" : ""}`}
                >
                  {player.jersey_number ?? player.track_id}
                </div>

                {/* Hover Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block bg-slate-900/95 border border-slate-700 text-slate-100 text-[10px] py-1 px-2.5 rounded shadow-xl whitespace-nowrap z-50 pointer-events-none">
                  <span className="font-bold text-emerald-400">
                    {player.player_name || `Track #${player.track_id}`}
                  </span>{" "}
                  ({player.team || (isHome ? "Home" : "Away")})
                  <div className="text-slate-300">
                    Speed: {player.max_speed_kmh} km/h | Dist: {(player.distance_covered_meters / 1000).toFixed(2)} km
                  </div>
                </div>
              </button>
            );
          })}
      </div>

      {/* Selected Player Detail Bar */}
      {activePlayer ? (
        <div className="flex items-center justify-between bg-slate-900/90 border border-emerald-500/30 p-3.5 rounded-xl animate-fade-in">
          <div className="flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs text-white shadow-md ${
                (activePlayer.team || "").toLowerCase().includes("red") ||
                (activePlayer.team || "").toLowerCase().includes("home") ||
                activePlayer.track_id % 2 !== 0
                  ? "bg-red-600"
                  : "bg-blue-600"
              }`}
            >
              #{activePlayer.jersey_number ?? activePlayer.track_id}
            </div>
            <div>
              <div className="text-sm font-bold text-slate-100">
                {activePlayer.player_name || `Tracked Player #${activePlayer.track_id}`}
              </div>
              <div className="text-xs text-slate-400">
                Team: {activePlayer.team || "Tracked Entity"} · ID: #{activePlayer.track_id} · Pitch Coord: (
                {activePlayer.average_pitch_x}%, {activePlayer.average_pitch_y}%)
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6 text-xs">
            <div>
              <span className="text-slate-400">Max Speed: </span>
              <span className="font-bold text-emerald-400 font-mono">{activePlayer.max_speed_kmh} km/h</span>
            </div>
            <div>
              <span className="text-slate-400">Distance: </span>
              <span className="font-bold text-cyan-400 font-mono">
                {activePlayer.distance_covered_meters.toLocaleString()} m
              </span>
            </div>
            <div>
              <span className="text-slate-400">Sprints: </span>
              <span className="font-bold text-amber-400 font-mono">{activePlayer.sprint_count}</span>
            </div>
            <button
              onClick={() => setActivePlayer(null)}
              className="text-slate-400 hover:text-white text-xs underline ml-2"
            >
              Close
            </button>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-500 text-center py-1">
          {hasPlayers
            ? "Click any player marker on the pitch radar to inspect detailed telemetry."
            : "Tactical telemetry will display real tracking positions once video processing completes."}
        </div>
      )}
    </div>
  );
}
