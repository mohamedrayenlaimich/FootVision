"use client";

import React, { useState } from "react";
import { Search, ArrowUpDown, Shield, Zap, Footprints, Activity } from "lucide-react";

interface PlayerStat {
  id: number;
  name: string;
  team: string;
  number: number;
  distanceMeters: number;
  maxSpeedKmh: number;
  sprints: number;
  avgPosition: string;
}

export default function PlayerStatsTable() {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<keyof PlayerStat>("distanceMeters");
  const [sortAsc, setSortAsc] = useState(false);

  const players: PlayerStat[] = [
    { id: 1, name: "G. Donnarumma", team: "Team Red (PSG)", number: 1, distanceMeters: 3120, maxSpeedKmh: 14.2, sprints: 2, avgPosition: "(X: 6.2, Y: 50.0)" },
    { id: 2, name: "A. Hakimi", team: "Team Red (PSG)", number: 2, distanceMeters: 9840, maxSpeedKmh: 34.5, sprints: 28, avgPosition: "(X: 28.1, Y: 15.4)" },
    { id: 3, name: "M. Marquinhos", team: "Team Red (PSG)", number: 4, distanceMeters: 8520, maxSpeedKmh: 28.1, sprints: 12, avgPosition: "(X: 22.4, Y: 38.2)" },
    { id: 5, name: "N. Mendes", team: "Team Red (PSG)", number: 25, distanceMeters: 9910, maxSpeedKmh: 33.8, sprints: 26, avgPosition: "(X: 28.5, Y: 85.1)" },
    { id: 6, name: "Vitinha", team: "Team Red (PSG)", number: 17, distanceMeters: 10420, maxSpeedKmh: 29.6, sprints: 18, avgPosition: "(X: 42.0, Y: 50.1)" },
    { id: 9, name: "O. Dembélé", team: "Team Red (PSG)", number: 10, distanceMeters: 9240, maxSpeedKmh: 35.1, sprints: 31, avgPosition: "(X: 68.2, Y: 20.4)" },
    { id: 13, name: "D. Carvajal", team: "Team Blue (Real Madrid)", number: 2, distanceMeters: 9540, maxSpeedKmh: 31.2, sprints: 22, avgPosition: "(X: 72.1, Y: 85.0)" },
    { id: 18, name: "F. Valverde", team: "Team Blue (Real Madrid)", number: 8, distanceMeters: 11240, maxSpeedKmh: 33.9, sprints: 34, avgPosition: "(X: 58.4, Y: 60.2)" },
    { id: 20, name: "J. Bellingham", team: "Team Blue (Real Madrid)", number: 5, distanceMeters: 10810, maxSpeedKmh: 31.8, sprints: 24, avgPosition: "(X: 50.1, Y: 50.0)" },
    { id: 21, name: "Vinícius Jr.", team: "Team Blue (Real Madrid)", number: 7, distanceMeters: 10410, maxSpeedKmh: 36.2, sprints: 38, avgPosition: "(X: 42.1, Y: 18.2)" },
    { id: 22, name: "K. Mbappé", team: "Team Blue (Real Madrid)", number: 9, distanceMeters: 9320, maxSpeedKmh: 36.8, sprints: 29, avgPosition: "(X: 32.4, Y: 48.1)" },
  ];

  const handleSort = (field: keyof PlayerStat) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const filteredPlayers = players
    .filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()) || p.team.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === "number" && typeof valB === "number") {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(valA));
    });

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
      {/* Team Level Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400">Possession</div>
            <div className="text-lg font-black text-slate-100">54.2% vs 45.8%</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Footprints className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400">Total Distance</div>
            <div className="text-lg font-black text-slate-100">112.5 km</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400">Total Sprints</div>
            <div className="text-lg font-black text-slate-100">298 Sprints</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400">Top Speed Recorded</div>
            <div className="text-lg font-black text-emerald-400">36.8 km/h</div>
          </div>
        </div>
      </div>

      {/* Table Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-800/80 pt-4">
        <div>
          <h3 className="text-base font-bold text-slate-100">Individual Player Telemetry</h3>
          <p className="text-xs text-slate-400">Tracked metrics extracted per player from computer vision pipeline</p>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search player or team..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-xl pl-9 pr-4 py-2 w-64 outline-none focus:border-emerald-500 transition-colors"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-900/90 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
              <th className="py-3 px-4">Player</th>
              <th className="py-3 px-4">Team</th>
              <th
                className="py-3 px-4 cursor-pointer hover:text-emerald-400"
                onClick={() => handleSort("distanceMeters")}
              >
                <div className="flex items-center gap-1">
                  Distance (m) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer hover:text-emerald-400"
                onClick={() => handleSort("maxSpeedKmh")}
              >
                <div className="flex items-center gap-1">
                  Max Speed (km/h) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer hover:text-emerald-400"
                onClick={() => handleSort("sprints")}
              >
                <div className="flex items-center gap-1">
                  Sprints <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Avg Pitch Coord</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs text-slate-200">
            {filteredPlayers.map((p) => (
              <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-4 font-bold flex items-center gap-2">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] text-white ${
                      p.team.includes("Red") ? "bg-red-600" : "bg-blue-600"
                    }`}
                  >
                    #{p.number}
                  </span>
                  {p.name}
                </td>
                <td className="py-3 px-4 text-slate-400">{p.team}</td>
                <td className="py-3 px-4 font-mono font-semibold text-cyan-300">
                  {p.distanceMeters.toLocaleString()} m
                </td>
                <td className="py-3 px-4 font-mono font-semibold text-emerald-400">{p.maxSpeedKmh} km/h</td>
                <td className="py-3 px-4 font-mono">{p.sprints}</td>
                <td className="py-3 px-4 font-mono text-slate-400">{p.avgPosition}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
