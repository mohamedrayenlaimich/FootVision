"use client";

import React, { useState, useRef } from "react";
import { Upload, Play, CheckCircle2, AlertCircle, Film, Activity } from "lucide-react";

export default function VideoProcessor() {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    { title: "Video Ingestion", desc: "Frame extraction & resolution validation" },
    { title: "YOLO Detection", desc: "Player & ball boundary box inference" },
    { title: "Multi-Object Tracking", desc: "ByteTrack ID association across frames" },
    { title: "Pitch Mapping", desc: "Homography projection to 2D pitch matrix" },
    { title: "Stats Engine", desc: "Computer vision metrics computation" },
  ];

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setProgress(5);
    setCurrentStep(0);
    setError(null);
    setStatusMessage(`Uploading ${file.name}...`);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/api/v1/video/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errData.detail || "Upload failed");
      }

      const data = await res.json();
      const videoId = data.video_id;
      setStatusMessage("Video uploaded. AI Computer Vision analysis running...");

      // Poll video status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/v1/video/status/${videoId}`);
          if (statusRes.ok) {
            const statusData = await statusRes.json();
            const pct = statusData.progress_percentage || 0;
            setProgress(pct);

            if (pct >= 20 && pct < 40) setCurrentStep(1);
            else if (pct >= 40 && pct < 65) setCurrentStep(2);
            else if (pct >= 65 && pct < 85) setCurrentStep(3);
            else if (pct >= 85 && pct <= 100) setCurrentStep(4);

            if (statusData.status === "completed" || pct >= 100) {
              clearInterval(pollInterval);
              setIsProcessing(false);
              setStatusMessage("AI Video Analysis Completed!");
            } else if (statusData.status === "failed") {
              clearInterval(pollInterval);
              setIsProcessing(false);
              setError(statusData.error_message || "Video processing failed");
            }
          }
        } catch {
          // Ignore transient polling error
        }
      }, 500);

    } catch (err: any) {
      setError(err.message || "Failed to process video");
      setIsProcessing(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <Film className="w-5 h-5 text-emerald-400" />
          Match Video Ingestion & Computer Vision Pipeline
        </h2>
        <p className="text-xs text-slate-400">Upload real football match video clips to analyze player movement & tracking</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Box */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-900/40 hover:bg-slate-900/80"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/avi,video/mov,video/mkv"
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
          <Upload className="w-6 h-6" />
        </div>
        <p className="text-sm font-semibold text-slate-200">Click to Upload Match Video File</p>
        <p className="text-xs text-slate-500 mt-1">Supports MP4, AVI, MOV, MKV formats</p>
        {statusMessage && <p className="text-xs text-emerald-400 font-semibold mt-2">{statusMessage}</p>}
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
