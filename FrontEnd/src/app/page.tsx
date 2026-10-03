"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import VideoProcessor from "@/components/VideoProcessor";
import PredictionPanel from "@/components/PredictionPanel";
import FootballMatchList from "@/components/FootballMatchList";
import LiveMatchAnalytics from "@/components/LiveMatchAnalytics";
import MatchCalendar from "@/components/MatchCalendar";
import { fetchFixtures } from "@/lib/api/football";
import {
  Trophy, Activity, Zap, Video, Sparkles, ArrowRight,
  BarChart2, Layers, CalendarDays,
} from "lucide-react";



// ── Hero stat card ─────────────────────────────────────────────────────────
function HeroStatCard({
  icon: Icon, label, value, color, delay = "0ms",
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
  delay?: string;
}) {
  return (
    <div
      className="glass-panel rounded-2xl p-4 flex items-center gap-4 border border-white/[0.07] animate-slide-in-up"
      style={{ animationDelay: delay }}
    >
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-xl font-black text-slate-100 leading-none animate-hero-counter">{value}</div>
        <div className="text-[11px] text-slate-400 font-medium mt-0.5">{label}</div>
      </div>
    </div>
  );
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("matches");
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [liveCount, setLiveCount] = useState<number>(0);
  const [todayCount, setTodayCount] = useState<number>(0);
  const [loadingStats, setLoadingStats] = useState<boolean>(true);

  const checkApiConnection = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/health", { method: "GET" });
      setApiConnected(res.ok);
    } catch {
      setApiConnected(false);
    }
  };

  const fetchHeroStats = async () => {
    setLoadingStats(true);
    try {
      const today = new Date().toISOString().split("T")[0];
      const [liveRes, todayRes] = await Promise.allSettled([
        fetchFixtures({ status: "1H" }),
        fetchFixtures({ date: today }),
      ]);
      setLiveCount(liveRes.status === "fulfilled" ? (liveRes.value.fixtures?.length ?? 0) : 0);
      setTodayCount(todayRes.status === "fulfilled" ? (todayRes.value.fixtures?.length ?? 0) : 0);
    } catch {
      setLiveCount(0);
      setTodayCount(0);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    checkApiConnection();
    fetchHeroStats();
    const apiInterval = setInterval(checkApiConnection, 12000);
    const statsInterval = setInterval(fetchHeroStats, 60000);
    return () => { clearInterval(apiInterval); clearInterval(statsInterval); };
  }, []);

  const heroStats = [
    {
      icon: Trophy,
      label: "Live Matches Right Now",
      value: loadingStats ? "—" : liveCount,
      color: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
      delay: "0ms",
    },
    {
      icon: Activity,
      label: "Fixtures Today",
      value: loadingStats ? "—" : todayCount,
      color: "bg-cyan-500/15 text-cyan-400 border border-cyan-500/20",
      delay: "80ms",
    },
    {
      icon: Zap,
      label: "AI Predictions Engine",
      value: "Poisson xG",
      color: "bg-violet-500/15 text-violet-400 border border-violet-500/20",
      delay: "160ms",
    },
    {
      icon: Video,
      label: "Computer Vision Model",
      value: "YOLOv8",
      color: "bg-amber-500/15 text-amber-400 border border-amber-500/20",
      delay: "240ms",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--background)" }}>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiConnected={apiConnected}
        onRefreshApi={checkApiConnection}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-6 py-6 flex flex-col gap-8">

        {/* ── HERO BANNER ─────────────────────────────────────────── */}
        <section
          className="relative overflow-hidden rounded-3xl border border-white/[0.06] animate-fade-in"
          style={{ background: "linear-gradient(135deg, rgba(10,20,38,0.95) 0%, rgba(6,10,18,0.98) 100%)" }}
        >
          {/* Decorative glows */}
          <div className="absolute -top-16 -left-16 w-72 h-72 bg-emerald-500/[0.07] rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-16 -right-16 w-72 h-72 bg-cyan-500/[0.05] rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-px bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent" />

          <div className="relative z-10 p-8 md:p-10">
            <div className="flex flex-col md:flex-row md:items-center gap-8">
              {/* Left: headline */}
              <div className="flex-1">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold mb-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-live-blip" />
                  Real-Time Football Intelligence
                </div>
                <h2 className="text-3xl md:text-4xl font-black leading-tight mb-3">
                  <span className="gradient-text-white">Next-Gen </span>
                  <span className="gradient-text-emerald">Football</span>
                  <br />
                  <span className="gradient-text-white">Analytics Platform</span>
                </h2>
                <p className="text-slate-400 text-sm leading-relaxed max-w-md mb-6">
                  AI-powered match intelligence combining YOLOv8 computer vision, Poisson xG models, and live football
                  data — all in one dashboard.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    id="hero-explore-matches"
                    onClick={() => setActiveTab("matches")}
                    className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs"
                  >
                    <Trophy className="w-3.5 h-3.5" />
                    Explore Live Matches
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    id="hero-match-calendar"
                    onClick={() => setActiveTab("calendar")}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-emerald-500/40 hover:text-emerald-400 transition-all text-xs font-semibold"
                  >
                    <CalendarDays className="w-3.5 h-3.5 text-emerald-400" />
                    Match Calendar
                  </button>
                  <button
                    id="hero-ai-forecast"
                    onClick={() => setActiveTab("prediction")}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-emerald-500/40 hover:text-emerald-400 transition-all text-xs font-semibold"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Forecast
                  </button>
                  <button
                    id="hero-analytics"
                    onClick={() => setActiveTab("analytics")}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-cyan-500/40 hover:text-cyan-400 transition-all text-xs font-semibold"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Tactical Radar
                  </button>
                </div>
              </div>

              {/* Right: hero stat cards */}
              <div className="grid grid-cols-2 gap-3 md:min-w-[340px]">
                {heroStats.map((stat) => (
                  <HeroStatCard key={stat.label} {...stat} />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── TAB CONTENT ─────────────────────────────────────────── */}

        {/* TAB: MATCHES */}
        {activeTab === "matches" && (
          <div className="animate-slide-in-up flex flex-col gap-6">
            <FootballMatchList />
          </div>
        )}

        {/* TAB: MATCH CALENDAR */}
        {activeTab === "calendar" && (
          <div className="animate-slide-in-up flex flex-col gap-6">
            <MatchCalendar />
          </div>
        )}

        {/* TAB: ANALYTICS */}
        {activeTab === "analytics" && (
          <div className="animate-slide-in-up">
            <LiveMatchAnalytics />
          </div>
        )}

        {/* TAB: VIDEO PIPELINE */}
        {activeTab === "video" && (
          <div className="animate-slide-in-up flex flex-col gap-6">
            <VideoProcessor />
          </div>
        )}

        {/* TAB: AI FORECAST */}
        {activeTab === "prediction" && (
          <div className="animate-slide-in-up flex flex-col gap-6">
            <PredictionPanel />
          </div>
        )}
      </main>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.05] py-5 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-600">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center">
              <BarChart2 className="w-3 h-3 text-slate-950" />
            </div>
            <span>FootVision AI © 2026 — Computer Vision &amp; Machine Learning Football Analytics</span>
          </div>
          <div className="flex items-center gap-4 text-slate-700">
            <span>Powered by YOLOv8 · BoT-SORT · Poisson xG</span>
            <span>·</span>
            <span>API-Football · football-data.org</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
