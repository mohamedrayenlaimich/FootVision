"use client";

import React, { useState } from "react";
import { Eye, Flame, Layers, Maximize2, RotateCcw } from "lucide-react";

interface Player {
  id: number;
  team: "red" | "blue";
  number: number;
  name: string;
  x: number; // percentage 0 - 100
  y: number; // percentage 0 - 100
  speed: number;
  distance: number;
}

export default function TacticalPitch() {
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [showTrajectories, setShowTrajectories] = useState<boolean>(true);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  // Simulated live 2D pitch position data for 22 players + ball
  const players: Player[] = [
    // Team Red (Home) - 4-3-3 formation
    { id: 1, team: "red", number: 1, name: "G. Donnarumma", x: 6, y: 50, speed: 4.2, distance: 3.1 },
    { id: 2, team: "red", number: 2, name: "A. Hakimi", x: 28, y: 15, speed: 28.5, distance: 9.8 },
    { id: 3, team: "red", number: 4, name: "M. Marquinhos", x: 22, y: 38, speed: 22.1, distance: 8.5 },
    { id: 4, team: "red", number: 5, name: "W. Pacho", x: 22, y: 62, speed: 21.0, distance: 8.2 },
    { id: 5, team: "red", number: 25, name: "N. Mendes", x: 28, y: 85, speed: 29.4, distance: 9.9 },
    { id: 6, team: "red", number: 17, name: "Vitinna", x: 42, y: 50, speed: 25.6, distance: 10.4 },
    { id: 7, team: "red", number: 8, name: "F. Ruiz", x: 45, y: 30, speed: 24.0, distance: 10.1 },
    { id: 8, team: "red", number: 33, name: "W. Zaïre-Emery", x: 45, y: 70, speed: 26.8, distance: 10.7 },
    { id: 9, team: "red", number: 10, name: "O. Dembélé", x: 68, y: 20, speed: 32.8, distance: 9.2 },
    { id: 10, team: "red", number: 9, name: "G. Ramos", x: 72, y: 50, speed: 29.1, distance: 9.0 },
    { id: 11, team: "red", number: 29, name: "B. Barcola", x: 68, y: 80, speed: 33.5, distance: 9.6 },

    // Team Blue (Away) - 4-2-3-1 formation
    { id: 12, team: "blue", number: 1, name: "T. Courtois", x: 94, y: 50, speed: 3.8, distance: 2.9 },
    { id: 13, team: "blue", number: 2, name: "D. Carvajal", x: 72, y: 85, speed: 27.2, distance: 9.5 },
    { id: 14, team: "blue", number: 3, name: "E. Militão", x: 78, y: 62, speed: 23.4, distance: 8.4 },
    { id: 15, team: "blue", number: 22, name: "A. Rüdiger", x: 78, y: 38, speed: 24.1, distance: 8.7 },
    { id: 16, team: "blue", number: 23, name: "F. Mendy", x: 72, y: 15, speed: 28.0, distance: 9.1 },
    { id: 17, team: "blue", number: 14, name: "A. Tchouaméni", x: 58, y: 40, speed: 25.1, distance: 10.2 },
    { id: 18, team: "blue", number: 8, name: "F. Valverde", x: 58, y: 60, speed: 31.0, distance: 11.2 },
    { id: 19, team: "blue", number: 11, name: "Rodrygo", x: 42, y: 82, speed: 31.8, distance: 9.7 },
    { id: 20, team: "blue", number: 5, name: "J. Bellingham", x: 50, y: 50, speed: 28.9, distance: 10.8 },
    { id: 21, team: "blue", number: 7, name: "Vinícius Jr.", x: 42, y: 18, speed: 34.8, distance: 10.4 },
    { id: 22, team: "blue", number: 9, name: "K. Mbappé", x: 32, y: 48, speed: 35.2, distance: 9.3 },
  ];

  const ballPosition = { x: 52, y: 46 };

  return (
    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col gap-4">
      {/* Pitch Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            Tactical 2D Pitch Radar
          </h2>
          <p className="text-xs text-slate-400">Homography matrix mapped real-world positioning</p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              showHeatmap
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            Heatmap Mode
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
        </div>
      </div>

      {/* Pitch Area */}
      <div className="relative w-full aspect-[105/68] pitch-container rounded-xl overflow-hidden shadow-2xl">
        {/* Heatmap Overlay Simulation */}
        {showHeatmap && (
          <div className="absolute inset-0 pointer-events-none opacity-40 mix-blend-screen bg-[radial-gradient(ellipse_at_45%_50%,#ef4444_0%,transparent_50%),radial-gradient(ellipse_at_65%_30%,#3b82f6_0%,transparent_45%)]" />
        )}

        {/* SVG Pitch Markings */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 68" preserveAspectRatio="none">
          {/* Pitch Outer Line */}
          <rect x="2" y="2" width="96" height="64" className="pitch-line" rx="1" />
          {/* Halfway Line */}
          <line x1="50" y1="2" x2="50" y2="66" className="pitch-line" />
          {/* Center Circle */}
          <circle cx="50" cy="34" r="9.15" className="pitch-line" />
          <circle cx="50" cy="34" r="0.8" fill="#ffffff" />

          {/* Left Penalty Area */}
          <rect x="2" y="13.8" width="16.5" height="40.4" className="pitch-line" />
          <rect x="2" y="24.8" width="5.5" height="18.4" className="pitch-line" />
          <circle cx="13" cy="34" r="0.6" fill="#ffffff" />

          {/* Right Penalty Area */}
          <rect x="81.5" y="13.8" width="16.5" height="40.4" className="pitch-line" />
          <rect x="92.5" y="24.8" width="5.5" height="18.4" className="pitch-line" />
          <circle cx="87" cy="34" r="0.6" fill="#ffffff" />
        </svg>

        {/* Trajectory Lines */}
        {showTrajectories && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-60">
            {players.map((p) => (
              <line
                key={`traj-${p.id}`}
                x1={`${p.x - (p.team === "red" ? 4 : -4)}%`}
                y1={`${p.y - 2}%`}
                x2={`${p.x}%`}
                y2={`${p.y}%`}
                stroke={p.team === "red" ? "#ef4444" : "#3b82f6"}
                strokeWidth="1.5"
                strokeDasharray="2,2"
              />
            ))}
          </svg>
        )}

        {/* Ball */}
        <div
          className="absolute transform -translate-x-1/2 -translate-y-1/2 z-30 transition-all duration-500"
          style={{ left: `${ballPosition.x}%`, top: `${ballPosition.y}%` }}
        >
          <div className="w-3.5 h-3.5 bg-yellow-300 rounded-full shadow-[0_0_12px_#fde047] ring-2 ring-yellow-400 animate-pulse" />
        </div>

        {/* Players */}
        {players.map((player) => (
          <button
            key={player.id}
            onClick={() => setSelectedPlayer(player)}
            className={`absolute transform -translate-x-1/2 -translate-y-1/2 z-20 group transition-all duration-300 ${
              selectedPlayer?.id === player.id ? "scale-125 z-40" : "hover:scale-110"
            }`}
            style={{ left: `${player.x}%`, top: `${player.y}%` }}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] text-white border-2 shadow-md ${
                player.team === "red"
                  ? "bg-gradient-to-br from-red-500 to-rose-700 border-red-300 shadow-red-900/50"
                  : "bg-gradient-to-br from-blue-500 to-indigo-700 border-blue-300 shadow-blue-900/50"
              }`}
            >
              {player.number}
            </div>

            {/* Hover tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block bg-slate-900/95 border border-slate-700 text-slate-100 text-[10px] py-1 px-2.5 rounded shadow-xl whitespace-nowrap z-50">
              <span className="font-bold text-emerald-400">{player.name}</span> (#{player.number})
              <div className="text-slate-300">Speed: {player.speed} km/h | Dist: {player.distance}km</div>
            </div>
          </button>
        ))}
      </div>

      {/* Selected Player Detail Bar */}
      {selectedPlayer ? (
        <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 p-3 rounded-xl">
          <div className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white ${
                selectedPlayer.team === "red" ? "bg-red-600" : "bg-blue-600"
              }`}
            >
              #{selectedPlayer.number}
            </div>
            <div>
              <div className="text-sm font-bold text-slate-100">{selectedPlayer.name}</div>
              <div className="text-xs text-slate-400">
                Team {selectedPlayer.team === "red" ? "Home (Red)" : "Away (Blue)"} | Track ID: #{selectedPlayer.id}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6 text-xs">
            <div>
              <span className="text-slate-400">Max Speed: </span>
              <span className="font-bold text-emerald-400">{selectedPlayer.speed} km/h</span>
            </div>
            <div>
              <span className="text-slate-400">Distance: </span>
              <span className="font-bold text-cyan-400">{selectedPlayer.distance} km</span>
            </div>
            <button
              onClick={() => setSelectedPlayer(null)}
              className="text-slate-400 hover:text-white text-xs underline ml-2"
            >
              Close
            </button>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-400 text-center py-1">
          Click any player marker on the pitch to inspect detailed live telemetry.
        </div>
      )}
    </div>
  );
}
