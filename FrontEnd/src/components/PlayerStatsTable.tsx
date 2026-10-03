"use client";

import React, { useState } from "react";
import { Search, ArrowUpDown, Shield, Zap, Footprints, Activity, Users, Info } from "lucide-react";
import { PlayerMetricItem } from "./TacticalPitch";

interface TeamMetricItem {
  team_name: string;
  possession_percentage: number;
  total_distance_km: number;
  sprints: number;
  tactical_width_m: number;
  tactical_depth_m: number;
}

interface PlayerStatsTableProps {
  players?: PlayerMetricItem[];
  teamAStats?: TeamMetricItem | null;
  teamBStats?: TeamMetricItem | null;
  selectedPlayer?: PlayerMetricItem | null;
  onSelectPlayer?: (player: PlayerMetricItem) => void;
}

export default function PlayerStatsTable({
  players = [],
  teamAStats,
  teamBStats,
  selectedPlayer,
  onSelectPlayer,
}: PlayerStatsTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof PlayerMetricItem>("distance_covered_meters");
  const [sortAsc, setSortAsc] = useState(false);

  const hasPlayers = players && players.length > 0;

  // Compute aggregate metrics dynamically from the actual players list if team stats not provided
  const totalDistanceKm = teamAStats && teamBStats
    ? (teamAStats.total_distance_km + teamBStats.total_distance_km).toFixed(1)
    : hasPlayers
    ? (players.reduce((sum, p) => sum + p.distance_covered_meters, 0) / 1000).toFixed(1)
    : "0.0";

  const totalSprints = teamAStats && teamBStats
    ? teamAStats.sprints + teamBStats.sprints
    : hasPlayers
    ? players.reduce((sum, p) => sum + p.sprint_count, 0)
    : 0;

  const topSpeed = hasPlayers
    ? Math.max(...players.map((p) => p.max_speed_kmh)).toFixed(1)
    : "0.0";

  const possessionDisplay = teamAStats && teamBStats
    ? `${teamAStats.possession_percentage}% vs ${teamBStats.possession_percentage}%`
    : hasPlayers
    ? "50.0% vs 50.0%"
    : "—";

  const handleSort = (field: keyof PlayerMetricItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const filteredPlayers = players
    .filter((p) => {
      const query = searchQuery.toLowerCase();
      const name = (p.player_name || `Track #${p.track_id}`).toLowerCase();
      const team = (p.team || "").toLowerCase();
      return name.includes(query) || team.includes(query);
    })
    .sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === "number" && typeof valB === "number") {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc ? String(valA || "").localeCompare(String(valB || "")) : String(valB || "").localeCompare(String(valA || ""));
    });

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6 border border-white/[0.08] shadow-2xl">
      {/* Dynamic Team Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Possession Split</div>
            <div className="text-base md:text-lg font-black text-slate-100">{possessionDisplay}</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Footprints className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Total Distance</div>
            <div className="text-base md:text-lg font-black text-slate-100">{totalDistanceKm} km</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Total Sprints</div>
            <div className="text-base md:text-lg font-black text-slate-100">{totalSprints} Sprints</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Top Tracked Speed</div>
            <div className="text-base md:text-lg font-black text-emerald-400">{topSpeed} km/h</div>
          </div>
        </div>
      </div>

      {/* Table Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-800/80 pt-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" />
            Individual Player Telemetry
            {hasPlayers && (
              <span className="text-xs text-slate-400 font-normal">({filteredPlayers.length} records)</span>
            )}
          </h3>
          <p className="text-xs text-slate-400">
            Real metrics extracted per player from computer vision tracking pipeline
          </p>
        </div>

        {/* Search Input */}
        {hasPlayers && (
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by player or team..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-xl pl-9 pr-4 py-2 w-60 outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
        )}
      </div>

      {/* Table Content States */}
      {!hasPlayers ? (
        <div className="flex flex-col items-center justify-center py-12 px-4 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
          <Info className="w-8 h-8 text-slate-600 mb-2" />
          <p className="text-sm font-semibold text-slate-300">No Telemetry Records Loaded</p>
          <p className="text-xs text-slate-500 max-w-sm mt-1">
            Telemetry will automatically populate once a video is uploaded and analyzed in the Video Pipeline.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                <th className="py-3 px-4">Player</th>
                <th className="py-3 px-4">Team</th>
                <th
                  className="py-3 px-4 cursor-pointer hover:text-emerald-400 transition-colors"
                  onClick={() => handleSort("distance_covered_meters")}
                >
                  <div className="flex items-center gap-1">
                    Distance (m) <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  className="py-3 px-4 cursor-pointer hover:text-emerald-400 transition-colors"
                  onClick={() => handleSort("max_speed_kmh")}
                >
                  <div className="flex items-center gap-1">
                    Max Speed (km/h) <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  className="py-3 px-4 cursor-pointer hover:text-emerald-400 transition-colors"
                  onClick={() => handleSort("sprint_count")}
                >
                  <div className="flex items-center gap-1">
                    Sprints <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-4">Avg Pitch Coord</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs text-slate-200">
              {filteredPlayers.map((p) => {
                const isSelected = selectedPlayer?.track_id === p.track_id;
                const isHome =
                  (p.team || "").toLowerCase().includes("red") ||
                  (p.team || "").toLowerCase().includes("home") ||
                  p.track_id % 2 !== 0;

                return (
                  <tr
                    key={p.track_id}
                    onClick={() => onSelectPlayer && onSelectPlayer(p)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-emerald-500/10 border-l-2 border-emerald-400"
                        : "hover:bg-slate-800/40"
                    }`}
                  >
                    <td className="py-3 px-4 font-bold flex items-center gap-2">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] text-white shadow-sm ${
                          isHome ? "bg-red-600" : "bg-blue-600"
                        }`}
                      >
                        #{p.jersey_number ?? p.track_id}
                      </span>
                      {p.player_name || `Track #${p.track_id}`}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{p.team || (isHome ? "Team Home" : "Team Away")}</td>
                    <td className="py-3 px-4 font-mono font-semibold text-cyan-300">
                      {p.distance_covered_meters.toLocaleString()} m
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-emerald-400">{p.max_speed_kmh} km/h</td>
                    <td className="py-3 px-4 font-mono">{p.sprint_count}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      (X: {p.average_pitch_x}%, Y: {p.average_pitch_y}%)
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
