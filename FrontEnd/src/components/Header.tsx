"use client";

import React from "react";
import {
  Activity,
  Cpu,
  Video,
  BarChart2,
  Sparkles,
  RefreshCw,
  Trophy,
  Wifi,
  WifiOff,
  CalendarDays,
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  apiConnected: boolean;
  onRefreshApi: () => void;
}

const NAV_TABS = [
  { id: "matches",    label: "Matches",        icon: Trophy },
  { id: "calendar",   label: "Match Calendar", icon: CalendarDays },
  { id: "analytics", label: "Tactical AI",    icon: BarChart2 },
  { id: "video",     label: "Video Pipeline", icon: Video },
  { id: "prediction",label: "AI Forecast",    icon: Sparkles },
] as const;

export default function Header({ activeTab, setActiveTab, apiConnected, onRefreshApi }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06]"
      style={{ background: "rgba(6,10,18,0.92)", backdropFilter: "blur(24px)", WebkitBackdropFilter: "blur(24px)" }}>
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 flex flex-wrap items-center justify-between gap-4">

        {/* ── Brand ─────────────────────────────────────── */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-400 blur-md opacity-60 animate-orb" />
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg">
              <Activity className="w-5 h-5 text-slate-950 animate-pulse-glow" />
            </div>
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight leading-none">
              <span className="gradient-text-white">Foot</span>
              <span className="gradient-text-emerald">Vision</span>
              <span className="text-slate-400 font-light text-sm ml-1.5">AI</span>
            </h1>
            <p className="text-[10px] text-slate-500 font-medium mt-0.5">Football Analytics Platform</p>
          </div>
        </div>

        {/* ── Nav Tabs ──────────────────────────────────── */}
        <nav className="flex items-center gap-1 bg-slate-900/70 p-1 rounded-xl border border-white/[0.06]">
          {NAV_TABS.map(({ id, label, icon: Icon }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                id={`tab-${id}`}
                onClick={() => setActiveTab(id)}
                className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-[11px] font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/10 text-emerald-300 border border-emerald-500/30 shadow-inner"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : ""}`} />
                <span className="hidden sm:inline">{label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-[1px] w-5 h-0.5 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* ── System Status ─────────────────────────────── */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* API Status pill */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[11px] font-medium transition-colors ${
            apiConnected
              ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-400"
              : "bg-red-950/40 border-red-800/60 text-red-400"
          }`}>
            <span className={`relative flex h-2 w-2`}>
              {apiConnected && (
                <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${apiConnected ? "bg-emerald-400" : "bg-red-500"}`} />
            </span>
            {apiConnected ? (
              <><Wifi className="w-3 h-3" /> Live</>
            ) : (
              <><WifiOff className="w-3 h-3" /> Offline</>
            )}
            <button
              onClick={onRefreshApi}
              title="Refresh API status"
              className="ml-0.5 hover:text-white transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>

          {/* Engine badge */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-950/30 border border-violet-800/40 text-violet-400 text-[11px] font-semibold">
            <Cpu className="w-3 h-3" />
            YOLOv8
          </div>
        </div>
      </div>
    </header>
  );
}
