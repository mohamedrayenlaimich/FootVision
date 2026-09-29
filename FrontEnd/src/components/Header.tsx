"use client";

import React, { useState, useEffect } from "react";
import { Activity, ShieldAlert, Cpu, Video, BarChart2, Sparkles, RefreshCw } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  apiConnected: boolean;
  onRefreshApi: () => void;
}

export default function Header({ activeTab, setActiveTab, apiConnected, onRefreshApi }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <Activity className="w-6 h-6 text-slate-950 font-bold animate-pulse-glow" />
        </div>
        <div>
          <h1 className="text-xl font-black tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            FootVision <span className="text-emerald-400">AI</span>
          </h1>
          <p className="text-xs text-slate-400">Real-Time Football Analytics & Match Forecasting</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveTab("analytics")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeTab === "analytics"
              ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-900/40"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Tactical Analytics
        </button>
        <button
          onClick={() => setActiveTab("video")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeTab === "video"
              ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-900/40"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Video className="w-4 h-4" />
          Video Pipeline
        </button>
        <button
          onClick={() => setActiveTab("prediction")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeTab === "prediction"
              ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-900/40"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          AI Forecast & xG
        </button>
      </nav>

      {/* System API Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              apiConnected ? "bg-emerald-400 animate-ping" : "bg-amber-500"
            }`}
          />
          <span className="text-slate-300 font-medium">
            FastAPI: {apiConnected ? "Connected (v1.0.0)" : "Offline (Mock Data)"}
          </span>
          <button
            onClick={onRefreshApi}
            title="Check API Connection"
            className="ml-1 text-slate-400 hover:text-emerald-400 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-emerald-400 text-xs font-semibold">
          <Cpu className="w-3.5 h-3.5" />
          YOLOv8 + BoT-SORT
        </div>
      </div>
    </header>
  );
}
