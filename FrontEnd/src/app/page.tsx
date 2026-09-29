"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import TacticalPitch from "@/components/TacticalPitch";
import VideoProcessor from "@/components/VideoProcessor";
import PlayerStatsTable from "@/components/PlayerStatsTable";
import PredictionPanel from "@/components/PredictionPanel";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("analytics");
  const [apiConnected, setApiConnected] = useState<boolean>(false);

  const checkApiConnection = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/health", { method: "GET" });
      if (res.ok) {
        setApiConnected(true);
      } else {
        setApiConnected(false);
      }
    } catch {
      setApiConnected(false);
    }
  };

  useEffect(() => {
    checkApiConnection();
    const interval = setInterval(checkApiConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col">
      {/* Header Bar */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiConnected={apiConnected}
        onRefreshApi={checkApiConnection}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col gap-6">
        {/* TAB 1: TACTICAL ANALYTICS */}
        {activeTab === "analytics" && (
          <div className="flex flex-col gap-6">
            <TacticalPitch />
            <PlayerStatsTable />
          </div>
        )}

        {/* TAB 2: VIDEO PROCESSING PIPELINE */}
        {activeTab === "video" && (
          <div className="flex flex-col gap-6">
            <VideoProcessor />
            <TacticalPitch />
          </div>
        )}

        {/* TAB 3: AI MATCH FORECAST */}
        {activeTab === "prediction" && (
          <div className="flex flex-col gap-6">
            <PredictionPanel />
            <PlayerStatsTable />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        FootVision AI &copy; 2026. Computer Vision & Machine Learning Football Analytics Platform.
      </footer>
    </div>
  );
}
