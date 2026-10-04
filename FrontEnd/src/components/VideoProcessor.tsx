"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Upload, Play, Pause, CheckCircle2, AlertCircle, Film, Activity,
  Download, Eye, EyeOff, Sparkles, RefreshCw, Layers, Shield,
  Radio, Compass, ChevronDown, ChevronUp, Clock, Cpu, Sliders
} from "lucide-react";

interface VideoStatus {
  video_id: string;
  filename: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  progress_percentage: number;
  total_frames: number;
  processed_frames: number;
  error_message?: string;
  current_stage?: string;
  current_fps?: number;
  total_detected_players?: number;
  team_a_players_count?: number;
  team_b_players_count?: number;
  referee_detected?: boolean;
  ball_detected?: boolean;
  ball_visibility_percentage?: number;
  duration_seconds?: number;
  processed_video_url?: string;
  original_video_url?: string;
  download_url?: string;
  telemetry_url?: string;
}

interface FrameTrack {
  track_id: number;
  team: string;
  is_referee: boolean;
  bbox: number[];
  conf: number;
}

interface TelemetryData {
  summary: any;
  frames: Array<{
    frame_index: number;
    timestamp: number;
    tracks: FrameTrack[];
    ball: {
      detected: boolean;
      center?: number[];
      conf?: number;
    };
  }>;
}

export default function VideoProcessor() {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<VideoStatus | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);

  // Playback & view states
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"side-by-side" | "annotated" | "original">("side-by-side");
  const [playbackTime, setPlaybackTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);

  // Overlay toggles
  const [showPlayerBoxes, setShowPlayerBoxes] = useState<boolean>(true);
  const [showTrackingIds, setShowTrackingIds] = useState<boolean>(true);
  const [showReferee, setShowReferee] = useState<boolean>(true);
  const [showBall, setShowBall] = useState<boolean>(true);
  const [showTrails, setShowTrails] = useState<boolean>(true);

  // Advanced configuration
  const [frameStride, setFrameStride] = useState<number>(1);
  const [maxFramesOption, setMaxFramesOption] = useState<number>(180); // 180 frames = 6 seconds preview, fast on CPU
  const [showTelemetryTable, setShowTelemetryTable] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const originalVideoRef = useRef<HTMLVideoElement>(null);
  const processedVideoRef = useRef<HTMLVideoElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const steps = [
    { title: "Ingestion & Geometry", desc: "Frame parsing & pitch polygon validation" },
    { title: "YOLO + ByteTrack", desc: "Multi-object player & ball tracking" },
    { title: "Kit Classification", desc: "Jersey HSV & CIE-Lab color clustering" },
    { title: "Referee Detection", desc: "Official kit & contextual isolation" },
    { title: "Visual Overlays", desc: "High-definition MP4 rendering & HUD" },
  ];

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const startPollingStatus = (videoId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/video/status/${videoId}`);
        if (res.ok) {
          const data: VideoStatus = await res.json();
          setJobStatus(data);
          const pct = data.progress_percentage || 0;
          setProgress(pct);

          if (pct >= 15 && pct < 40) setCurrentStep(1);
          else if (pct >= 40 && pct < 65) setCurrentStep(2);
          else if (pct >= 65 && pct < 85) setCurrentStep(3);
          else if (pct >= 85 && pct <= 100) setCurrentStep(4);

          if (data.status === "completed") {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            setIsProcessing(false);
            setStatusMessage("AI Video Tracking Analysis Complete!");

            // Fetch structured telemetry data
            fetch(`http://localhost:8000/api/v1/video/tracking/${videoId}`)
              .then((r) => (r.ok ? r.json() : null))
              .then((tel) => {
                if (tel) setTelemetry(tel);
              })
              .catch(() => {});
          } else if (data.status === "failed") {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            setIsProcessing(false);
            setError(data.error_message || "Video analysis pipeline failed");
          }
        }
      } catch (err: any) {
        // Transient network error
      }
    }, 600);
  };

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setProgress(3);
    setCurrentStep(0);
    setError(null);
    setStatusMessage(`Uploading ${file.name}...`);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const queryParams = new URLSearchParams();
      if (maxFramesOption > 0) queryParams.set("max_frames", String(maxFramesOption));
      queryParams.set("process_every_n", String(frameStride));

      const res = await fetch(`http://localhost:8000/api/v1/video/upload?${queryParams.toString()}`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errData.detail || "Upload failed");
      }

      const data = await res.json();
      setStatusMessage("Video ingested. Running computer vision & tracking models...");
      startPollingStatus(data.video_id);
    } catch (err: any) {
      setError(err.message || "Failed to process video");
      setIsProcessing(false);
    }
  };

  const handleProcessSample = async () => {
    setIsProcessing(true);
    setProgress(5);
    setCurrentStep(0);
    setError(null);
    setStatusMessage("Ingesting project sample video (Data/raw/test.mp4)...");

    try {
      const queryParams = new URLSearchParams();
      if (maxFramesOption > 0) queryParams.set("max_frames", String(maxFramesOption));
      queryParams.set("process_every_n", String(frameStride));

      const res = await fetch(`http://localhost:8000/api/v1/video/process-sample?${queryParams.toString()}`, {
        method: "POST",
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Sample processing failed" }));
        throw new Error(errData.detail || "Failed to load sample");
      }

      const data = await res.json();
      setStatusMessage("Sample loaded. Running ByteTrack & team kit classifiers...");
      startPollingStatus(data.video_id);
    } catch (err: any) {
      setError(err.message || "Failed to start sample analysis");
      setIsProcessing(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  // Synchronized playback controls
  const togglePlay = () => {
    const nextState = !isPlaying;
    setIsPlaying(nextState);

    if (processedVideoRef.current) {
      if (nextState) {
        processedVideoRef.current.play().catch((e) => console.warn("Processed play failed:", e));
      } else {
        processedVideoRef.current.pause();
      }
    }
    if (originalVideoRef.current) {
      if (nextState) {
        originalVideoRef.current.play().catch((e) => console.warn("Original play failed:", e));
      } else {
        originalVideoRef.current.pause();
      }
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const target = parseFloat(e.target.value);
    setPlaybackTime(target);
    if (processedVideoRef.current) processedVideoRef.current.currentTime = target;
    if (originalVideoRef.current) originalVideoRef.current.currentTime = target;
  };

  const handleTimeUpdate = () => {
    if (processedVideoRef.current) {
      setPlaybackTime(processedVideoRef.current.currentTime);
      setDuration(processedVideoRef.current.duration || 0);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-6 md:p-8 flex flex-col gap-8 border border-white/[0.08]">
      {/* ── HEADER & TITLE ─────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold mb-2">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            AI Computer Vision &amp; Visual Tracking Pipeline
          </div>
          <h2 className="text-2xl font-black text-slate-100 flex items-center gap-3">
            <Film className="w-6 h-6 text-emerald-400" />
            Match Video Intelligence &amp; Visual Overlays
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Multi-object ByteTrack tracking with jersey HSV color clustering (Team A Blue vs Team B Red),
            isolated referee identification, and temporal ball motion tracking.
          </p>
        </div>

        {/* Quick Sample Match CTA */}
        <div className="flex items-center gap-3">
          <button
            id="use-sample-video-btn"
            onClick={handleProcessSample}
            disabled={isProcessing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-bold transition-all shadow-[0_0_15px_rgba(16,185,129,0.15)] disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-emerald-400" />
            Process Project Sample Clip
          </button>
        </div>
      </div>

      {/* ── ERROR ALERT ────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <span className="font-bold">Pipeline Error: </span>
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="px-2 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-[10px] font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── PROCESSING SETTINGS ACCORDION ───────────────────────────── */}
      <div className="bg-slate-900/40 rounded-2xl border border-slate-800/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-semibold">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span>Inference Settings:</span>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            {/* Frame Stride */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Processing Mode:</span>
              <select
                value={frameStride}
                onChange={(e) => setFrameStride(Number(e.target.value))}
                disabled={isProcessing}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-emerald-500"
              >
                <option value={1}>Every Frame (1x Full Tracking)</option>
                <option value={2}>Fast CPU Mode (Every 2nd Frame)</option>
                <option value={3}>Ultra Fast (Every 3rd Frame)</option>
              </select>
            </div>

            {/* Frame limit */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Sample Duration:</span>
              <select
                value={maxFramesOption}
                onChange={(e) => setMaxFramesOption(Number(e.target.value))}
                disabled={isProcessing}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-emerald-500"
              >
                <option value={150}>150 Frames (~5 sec Preview - Fast)</option>
                <option value={300}>300 Frames (~10 sec Action)</option>
                <option value={600}>600 Frames (~20 sec Half-minute)</option>
                <option value={0}>Complete Video (Full Duration)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* ── UPLOAD DROP ZONE ────────────────────────────────────────── */}
      {!jobStatus?.processed_video_url && (
        <div
          onClick={() => !isProcessing && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
            isProcessing
              ? "border-emerald-500/50 bg-emerald-950/10 cursor-wait"
              : "border-slate-700/80 hover:border-emerald-500/60 bg-slate-900/30 hover:bg-slate-900/70"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/avi,video/mov,video/mkv"
            onChange={handleFileChange}
            className="hidden"
            disabled={isProcessing}
          />
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
            <Upload className="w-8 h-8" />
          </div>
          <p className="text-base font-bold text-slate-200">
            {isProcessing ? "Processing Video in Progress..." : "Drag & Drop or Click to Upload Match Video"}
          </p>
          <p className="text-xs text-slate-500 mt-1 max-w-md">
            Compatible formats: MP4 (H.264), AVI, MOV, MKV. Analyzes player jerseys, referee official kit, and ball tracking.
          </p>
          {statusMessage && (
            <div className="mt-3 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold animate-pulse">
              {statusMessage}
            </div>
          )}
        </div>
      )}

      {/* ── PIPELINE STEPPER & PROGRESS BAR ─────────────────────────── */}
      {isProcessing && (
        <div className="flex flex-col gap-4 bg-slate-950/60 p-6 rounded-2xl border border-emerald-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-bold text-slate-200">
                {jobStatus?.current_stage || "Processing Frames..."}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono text-emerald-400">
              {jobStatus?.current_fps ? <span>{jobStatus.current_fps} FPS</span> : null}
              {jobStatus?.processed_frames ? (
                <span>
                  {jobStatus.processed_frames} / {jobStatus.total_frames || "?"} frames
                </span>
              ) : null}
              <span className="font-bold">{progress}%</span>
            </div>
          </div>

          <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-emerald-500 via-cyan-400 to-teal-400 h-full transition-all duration-300 shadow-[0_0_15px_#10b981]"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mt-2">
            {steps.map((st, i) => {
              const done = progress === 100 || i < currentStep;
              const active = isProcessing && i === currentStep;
              return (
                <div
                  key={i}
                  className={`p-3 rounded-xl border transition-all ${
                    done
                      ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300"
                      : active
                      ? "bg-cyan-950/40 border-cyan-500/60 text-cyan-200 animate-pulse"
                      : "bg-slate-900/30 border-slate-800 text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {done ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <span className="w-3.5 h-3.5 rounded-full border border-current text-[9px] font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                    )}
                    <span className="text-[11px] font-bold leading-tight">{st.title}</span>
                  </div>
                  <p className="text-[9px] text-slate-400 leading-normal">{st.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── VIDEO PLAYER & VISUAL OVERLAYS ──────────────────────────── */}
      {jobStatus && jobStatus.status === "completed" && (
        <div className="flex flex-col gap-6">
          {/* Top Controls Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/80 border border-slate-800">
            {/* View layout selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-semibold mr-1">Display:</span>
              <button
                id="view-side-by-side"
                onClick={() => setViewMode("side-by-side")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  viewMode === "side-by-side"
                    ? "bg-emerald-500 text-slate-950 shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                Side-by-Side Dual View
              </button>
              <button
                id="view-annotated"
                onClick={() => setViewMode("annotated")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  viewMode === "annotated"
                    ? "bg-emerald-500 text-slate-950 shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                Annotated Video Only
              </button>
              <button
                id="view-original"
                onClick={() => setViewMode("original")}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  viewMode === "original"
                    ? "bg-emerald-500 text-slate-950 shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                Original Video Only
              </button>
            </div>

            {/* Video Download Button */}
            <div className="flex items-center gap-3">
              <a
                id="download-processed-video"
                href={`http://localhost:8000/api/v1/video/download/${jobStatus.video_id}`}
                download={`annotated_${jobStatus.filename || "match.mp4"}`}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 font-black text-xs hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                Download Annotated MP4
              </a>
            </div>
          </div>

          {/* Color Legend Bar */}
          <div className="flex flex-wrap items-center gap-3 p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 text-xs">
            <span className="text-slate-400 font-bold flex items-center gap-1.5 mr-2">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              Visual Tracking Legend:
            </span>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/15 border border-blue-500/40 text-blue-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              Team A Players (Blue)
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/15 border border-red-500/40 text-red-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              Team B Players (Red)
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-500/15 border border-yellow-500/40 text-yellow-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
              Referee (Yellow / Amber)
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              Ball (Green Bullseye)
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-500/15 border border-slate-500/40 text-slate-400 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
              Unclassified (Neutral Gray)
            </div>
          </div>

          {/* Video Frames Container */}
          <div
            className={`grid gap-4 ${
              viewMode === "side-by-side" ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1"
            }`}
          >
            {/* Original Video Frame */}
            {(viewMode === "side-by-side" || viewMode === "original") && (
              <div className="flex flex-col gap-2 rounded-2xl overflow-hidden border border-slate-800 bg-black/60 relative group">
                <div className="absolute top-3 left-3 z-10 px-2.5 py-1 rounded-md bg-black/75 border border-white/10 text-[11px] font-bold text-slate-300 backdrop-blur-md pointer-events-none">
                  Original Source Video
                </div>
                <video
                  key={`orig-${jobStatus.video_id}`}
                  ref={originalVideoRef}
                  src={`http://localhost:8000/api/v1/video/original/${jobStatus.video_id}`}
                  className="w-full aspect-video object-contain bg-black rounded-xl"
                  controls
                  playsInline
                  preload="auto"
                  muted
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={(e) => {
                    const d = e.currentTarget.duration;
                    if (d && !isNaN(d) && d > 0) setDuration(d);
                  }}
                  onError={(e) => {
                    console.warn("Original video load warning:", e);
                  }}
                />
              </div>
            )}

            {/* AI Processed Annotated Video Frame */}
            {(viewMode === "side-by-side" || viewMode === "annotated") && (
              <div className="flex flex-col gap-2 rounded-2xl overflow-hidden border border-emerald-500/30 bg-black/60 relative group shadow-[0_0_30px_rgba(16,185,129,0.06)]">
                <div className="absolute top-3 left-3 z-10 px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-500/30 text-[11px] font-bold text-emerald-300 backdrop-blur-md flex items-center gap-1.5 pointer-events-none">
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  AI Visual Tracking &amp; Overlays
                </div>
                <video
                  key={`proc-${jobStatus.video_id}`}
                  ref={processedVideoRef}
                  src={`http://localhost:8000/api/v1/video/stream/${jobStatus.video_id}`}
                  className="w-full aspect-video object-contain bg-black rounded-xl"
                  controls
                  playsInline
                  preload="auto"
                  muted
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={(e) => {
                    const d = e.currentTarget.duration;
                    if (d && !isNaN(d) && d > 0) setDuration(d);
                  }}
                  onEnded={() => setIsPlaying(false)}
                  onError={(e) => {
                    console.warn("Processed video stream load warning:", e);
                  }}
                />
              </div>
            )}
          </div>

          {/* Unified Playback Controls Bar */}
          <div className="flex items-center gap-4 p-4 rounded-2xl bg-slate-900/90 border border-slate-800">
            <button
              id="video-play-pause-btn"
              onClick={togglePlay}
              className="w-10 h-10 rounded-xl bg-emerald-500 text-slate-950 flex items-center justify-center font-bold hover:bg-emerald-400 transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
            </button>

            {/* Seek Bar */}
            <div className="flex-1 flex items-center gap-3">
              <span className="text-xs font-mono text-slate-400 w-12 text-right">
                {Math.floor(playbackTime / 60)}:
                {String(Math.floor(playbackTime % 60)).padStart(2, "0")}
              </span>
              <input
                type="range"
                min={0}
                max={duration || 100}
                step={0.1}
                value={playbackTime}
                onChange={handleSeek}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <span className="text-xs font-mono text-slate-400 w-12">
                {Math.floor(duration / 60)}:
                {String(Math.floor(duration % 60)).padStart(2, "0")}
              </span>
            </div>
          </div>

          {/* ── LIVE TRACKING METRICS CARDS ──────────────────────────── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-panel p-4 rounded-2xl border border-white/[0.06] flex flex-col gap-1">
              <span className="text-[11px] text-slate-400 font-medium">Total Unique Players</span>
              <span className="text-2xl font-black text-slate-100">
                {jobStatus.total_detected_players ?? "—"}
              </span>
              <span className="text-[10px] text-slate-500">ByteTrack Associated IDs</span>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-blue-500/20 flex flex-col gap-1">
              <span className="text-[11px] text-blue-300 font-medium">Team A Players (Blue)</span>
              <span className="text-2xl font-black text-blue-400">
                {jobStatus.team_a_players_count ?? "—"}
              </span>
              <span className="text-[10px] text-slate-500">Torso HSV Clustered</span>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-red-500/20 flex flex-col gap-1">
              <span className="text-[11px] text-red-300 font-medium">Team B Players (Red)</span>
              <span className="text-2xl font-black text-red-400">
                {jobStatus.team_b_players_count ?? "—"}
              </span>
              <span className="text-[10px] text-slate-500">Torso HSV Clustered</span>
            </div>

            <div className="glass-panel p-4 rounded-2xl border border-yellow-500/20 flex flex-col gap-1">
              <span className="text-[11px] text-yellow-300 font-medium">Referee Detections</span>
              <span className="text-2xl font-black text-yellow-400">
                {jobStatus.referee_detected ? "Identified" : "Not Found"}
              </span>
              <span className="text-[10px] text-slate-500">Contextual Kit Analysis</span>
            </div>
          </div>

          {/* Ball & Precision Info Banner */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
                ⚽
              </div>
              <div>
                <span className="font-bold text-slate-200">Ball Tracking Reliability: </span>
                <span className="text-emerald-400 font-bold">
                  {jobStatus.ball_visibility_percentage ?? 0}% frames tracked
                </span>
                <p className="text-[11px] text-slate-400">
                  Kalman filter smoothing applied during occlusions. Detections missing in tight scrambles are left unassigned.
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowTelemetryTable(!showTelemetryTable)}
              className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
            >
              <span>{showTelemetryTable ? "Hide" : "Inspect"} Per-Frame Telemetry Log</span>
              {showTelemetryTable ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {/* ── EXPANDABLE PER-FRAME TELEMETRY TABLE ─────────────────── */}
          {showTelemetryTable && telemetry && (
            <div className="bg-slate-950 rounded-2xl border border-slate-800 p-4 max-h-80 overflow-y-auto">
              <div className="flex items-center justify-between mb-3 text-xs font-bold text-slate-300">
                <span>Per-Frame Tracking Telemetry (Sampled Frames)</span>
                <span className="text-slate-500 font-mono">{telemetry.frames.length} samples</span>
              </div>
              <table className="w-full text-left text-[11px]">
                <thead className="text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="pb-2">Frame</th>
                    <th className="pb-2">Time (s)</th>
                    <th className="pb-2">Active Players</th>
                    <th className="pb-2">Ball State</th>
                    <th className="pb-2">Sampled Tracks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-slate-300 font-mono">
                  {telemetry.frames.slice(0, 30).map((fr, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/50">
                      <td className="py-1.5">{fr.frame_index}</td>
                      <td className="py-1.5">{fr.timestamp}</td>
                      <td className="py-1.5">{fr.tracks.length}</td>
                      <td className="py-1.5">
                        {fr.ball?.detected ? (
                          <span className="text-emerald-400">Tracked ({fr.ball.conf})</span>
                        ) : (
                          <span className="text-slate-500">Missing</span>
                        )}
                      </td>
                      <td className="py-1.5 text-[10px] text-slate-400 truncate max-w-xs">
                        {fr.tracks.map((t) => `#${t.track_id}(${t.team})`).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {telemetry.frames.length > 30 && (
                <p className="text-[10px] text-slate-500 mt-2 text-center">
                  Showing first 30 frames. Full JSON available via /api/v1/video/tracking/{jobStatus.video_id}
                </p>
              )}
            </div>
          )}

          {/* Reset / Process Another Video */}
          <div className="flex justify-end pt-2">
            <button
              onClick={() => {
                setJobStatus(null);
                setTelemetry(null);
                setIsProcessing(false);
                setProgress(0);
                setStatusMessage("");
              }}
              className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Analyze Another Video
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
