"use client";

import React, { useState } from "react";
import { Upload, Play, CheckCircle2, AlertCircle, Film, Cpu, Zap, Activity } from "lucide-react";

export default function VideoProcessor() {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [selectedMatch, setSelectedMatch] = useState<string>("Sample Match: PSG vs Real Madrid (1080p)");

  const steps = [
    { title: "Video Ingestion", desc: "Frame extraction & resolution validation" },
    { title: "YOLO Detection", desc: "Player & ball boundary box inference" },
    { title: "Multi-Object Tracking", desc: "BoT-SORT ID association across frames" },
    { title: "Pitch Mapping", desc: "Homography projection to 2D pitch matrix" },
    { title: "Stats & Forecast", desc: "Metrics computation & xG model generation" },
  ];

  const handleStartProcessing = () => {
    setIsProcessing(true);
    setProgress(0);
    setCurrentStep(0);

    let p = 0;
    const interval = setInterval(() => {
      p += 5;
      setProgress(p);
      if (p >= 20 && p < 40) setCurrentStep(1);
      else if (p >= 40 && p < 65) setCurrentStep(2);
      else if (p >= 65 && p < 85) setCurrentStep(3);
      else if (p >= 85 && p <= 100) setCurrentStep(4);

      if (p >= 100) {
        clearInterval(interval);
        setIsProcessing(false);
      }
    }, 200);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <Film className="w-5 h-5 text-emerald-400" />
          Match Video Ingestion & Pipeline Status
        </h2>
        <p className="text-xs text-slate-400">Process uploaded match clips, RTSP streams, or supported video URLs</p>
      </div>

      {/* Select sample match or upload */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Upload Box */}
        <div className="border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-900/40 hover:bg-slate-900/80">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
            <Upload className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-200">Drag & Drop Match Video</p>
          <p className="text-xs text-slate-500 mt-1">Supports MP4, AVI, MOV, MKV (Up to 4K 60fps)</p>
        </div>

        {/* Quick Sample Selector */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Quick Demo Match</span>
            <select
              value={selectedMatch}
              onChange={(e) => setSelectedMatch(e.target.value)}
              className="mt-2 w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg p-2.5 outline-none focus:border-emerald-500"
            >
              <option>Sample Match: PSG vs Real Madrid (1080p)</option>
              <option>El Clasico: Real Madrid vs Barcelona</option>
              <option>Premier League: Man City vs Arsenal</option>
            </select>
          </div>

          <button
            onClick={handleStartProcessing}
            disabled={isProcessing}
            className={`mt-4 w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
              isProcessing
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 hover:from-emerald-400 hover:to-teal-500 shadow-lg shadow-emerald-500/20"
            }`}
          >
            {isProcessing ? (
              <>
                <Activity className="w-4 h-4 animate-spin text-emerald-400" />
                Processing Pipeline Active ({progress}%)
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-slate-950" />
                Run FootVision AI Processing Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* Pipeline Status Stepper */}
      <div className="border-t border-slate-800/80 pt-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-slate-300">Pipeline Stages Status</span>
          <span className="text-xs font-mono text-emerald-400">{progress}% Completed</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden mb-6 border border-slate-800">
          <div
            className="bg-gradient-to-r from-emerald-500 via-cyan-400 to-teal-400 h-full transition-all duration-300 shadow-[0_0_12px_#10b981]"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Stage Nodes */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {steps.map((step, idx) => {
            const isDone = progress === 100 || idx < currentStep;
            const isCurrent = isProcessing && idx === currentStep;

            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border transition-all ${
                  isDone
                    ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300"
                    : isCurrent
                    ? "bg-cyan-950/40 border-cyan-500/60 text-cyan-200 animate-pulse"
                    : "bg-slate-900/40 border-slate-800 text-slate-500"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <div
                      className={`w-4 h-4 rounded-full border text-[10px] font-bold flex items-center justify-center ${
                        isCurrent ? "border-cyan-400 text-cyan-400" : "border-slate-700 text-slate-600"
                      }`}
                    >
                      {idx + 1}
                    </div>
                  )}
                  <span className="text-xs font-bold leading-tight">{step.title}</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-normal">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
