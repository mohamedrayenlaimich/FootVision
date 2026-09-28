"""
FootVision AI — M2: Player Tracking
Script: player_tracker.py

PURPOSE
-------
Extends M1 player detection with ByteTrack multi-object tracking.
Each detected player on the pitch is assigned a temporary tracking ID
that persists across frames, enabling downstream modules (M3+) to
accumulate per-player statistics over time.

TRACKING ALGORITHM: ByteTrack
------------------------------
ByteTrack (Zhang et al., 2022) works in two matching stages per frame:

  Stage 1 — HIGH-CONFIDENCE detections (conf >= high_thresh):
    Match these against existing tracks using IoU + Kalman-predicted positions.
    High-conf detections are reliable; we prefer these for re-association.

  Stage 2 — LOW-CONFIDENCE detections (low_thresh <= conf < high_thresh):
    Any tracks NOT matched in Stage 1 get a second chance here.
    Low-conf detections are noisy but often correspond to partially occluded
    players — ByteTrack's key innovation is using them instead of discarding.

  Kalman filter:
    Each track maintains a Kalman state (x, y, w, h, vx, vy) to predict
    where the player will be in the next frame even without a detection.
    Tracks survive up to `track_buffer` missed frames before being deleted.

PIPELINE
--------
    Video frame
        ↓
    YOLO + ByteTrack (model.track())
        ↓
    PitchFilter  (keep only on-pitch tracks)
        ↓
    Draw boxes + tracking IDs + HUD
        ↓
    Display  +  Save to Data/processed/tracked_<video>.mp4

NO player identification, No Re-ID, No jersey OCR, No homography.

RUN
---
From FootVision/ root (with venv active):

    python AI/tracking/player_tracker.py

CONTROLS
--------
    Q  — quit
    D  — toggle debug mode (shows filtered-out persons in blue)

OUTPUTS
-------
    Console : live metrics and final summary
    Window  : annotated video with tracking IDs
    File    : Data/processed/tracked_test.mp4
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Allow sibling imports:  AI/detection/pitch_filter.py
# ---------------------------------------------------------------------------
_AI_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_AI_ROOT, "detection"))
from pitch_filter import PitchFilter  # noqa: E402


# =============================================================================
# SECTION 1 — CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]   # FootVision/

MODEL_PATH   = PROJECT_ROOT / "AI" / "models" / "yolov8s.pt"
VIDEO_PATH   = PROJECT_ROOT / "Data" / "raw" / "test.mp4"
OUTPUT_DIR   = PROJECT_ROOT / "Data" / "processed"
POLYGON_PATH = PROJECT_ROOT / "Data" / "processed" / "pitch_polygon.json"

# ── ByteTrack tuning ──────────────────────────────────────────────────────────
#
# tracker   : "bytetrack" — built into Ultralytics
# conf      : minimum YOLO detection confidence threshold
# iou       : NMS IoU threshold
# classes   : [0] = only 'person'
# persist   : True ensures track IDs persist across frames
#
BYTETRACK_CONFIG: Dict = {
    "tracker": "bytetrack.yaml",
    "conf": 0.35,
    "iou": 0.45,
    "classes": [0],
    "persist": True,
    "verbose": False,
}

# ── Pitch filter ──────────────────────────────────────────────────────────────
PITCH_MARGIN = 20          # Extra pixel tolerance on the polygon boundary

# ── Display ───────────────────────────────────────────────────────────────────
WINDOW_NAME   = "FootVision — Player Tracker  [Q quit | D debug]"
PROCESS_EVERY = 1          # Run tracker on every Nth frame (1 = every frame)

# Colour palette — indexed by (track_id % len(PALETTE))
# Gives each player a consistent visual color across the entire video.
PALETTE = [
    (0, 255, 100),   # green
    (0, 180, 255),   # sky-blue
    (255, 180, 0),   # amber
    (180, 0, 255),   # purple
    (255, 60, 100),  # pink-red
    (0, 220, 220),   # cyan
    (255, 220, 0),   # yellow
    (160, 255, 0),   # lime
    (255, 120, 40),  # orange
    (100, 100, 255), # lavender
    (0, 255, 200),   # mint
    (220, 60, 220),  # magenta
]

TEXT_COLOR     = (255, 255, 255)
FONT           = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_ID  = 0.55
FONT_SCALE_HUD = 0.50
FONT_THICKNESS = 1
BOX_THICKNESS  = 2

DEBUG_BOX_COLOR = (50, 50, 200)   # Blue for filtered-out off-pitch people


# =============================================================================
# SECTION 2 — HELPERS
# =============================================================================

def _track_color(track_id: int) -> Tuple[int, int, int]:
    """Return a consistent BGR colour for a given track ID."""
    return PALETTE[track_id % len(PALETTE)]


def _build_output_path(video_path: Path, output_dir: Path) -> Path:
    """Derive output video path from input filename."""
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"tracked_{video_path.stem}.mp4"


def _make_video_writer(
    output_path: Path,
    frame_w: int,
    frame_h: int,
    fps: float,
) -> cv2.VideoWriter:
    """Create an OpenCV VideoWriter."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (frame_w, frame_h))
    if not writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        alt_path = output_path.with_suffix(".avi")
        writer = cv2.VideoWriter(str(alt_path), fourcc, fps, (frame_w, frame_h))
        print(f"[Tracker] ⚠️ mp4v fallback to {alt_path}")
        return writer
    return writer


# =============================================================================
# SECTION 3 — DRAWING
# =============================================================================

def draw_tracked_player(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    track_id: int,
    conf: float,
) -> None:
    """Draw a coloured bounding box and tracking ID above the box."""
    color = _track_color(track_id)
    label = f"P{track_id} ({conf:.2f})"

    # Bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, BOX_THICKNESS)

    # Label background
    (tw, th), baseline = cv2.getTextSize(label, FONT, FONT_SCALE_ID, FONT_THICKNESS)
    label_y = max(y1 - 4, th + 4)
    bg_color = tuple(max(0, c - 90) for c in color)
    cv2.rectangle(
        frame,
        (x1, label_y - th - baseline - 2),
        (x1 + tw + 4, label_y + 2),
        bg_color,
        cv2.FILLED,
    )
    cv2.putText(
        frame,
        label,
        (x1 + 2, label_y - baseline),
        FONT,
        FONT_SCALE_ID,
        TEXT_COLOR,
        FONT_THICKNESS,
    )


def draw_hud(
    frame: np.ndarray,
    frame_idx: int,
    tracked_count: int,
    proc_fps: float,
    unique_ids: int,
    debug: bool,
    elapsed_s: float,
) -> None:
    """HUD overlay on top-left of the screen."""
    lines = [
        "FootVision — M2 Tracking",
        f"Frame        : {frame_idx}",
        f"Tracked now  : {tracked_count}",
        f"Proc. FPS    : {proc_fps:.1f}",
        f"Unique IDs   : {unique_ids}",
        f"Elapsed      : {elapsed_s:.0f}s",
        f"Debug        : {'ON' if debug else 'OFF'}",
        "[Q] Quit  [D] Debug",
    ]
    x, y = 10, 24
    for line in lines:
        cv2.putText(frame, line, (x + 1, y + 1), FONT, FONT_SCALE_HUD, (0, 0, 0), FONT_THICKNESS + 1)
        cv2.putText(frame, line, (x, y), FONT, FONT_SCALE_HUD, (255, 255, 255), FONT_THICKNESS)
        y += 20


# =============================================================================
# SECTION 4 — SESSION METRICS
# =============================================================================

class TrackingSession:
    """Accumulates tracking statistics across the video session."""

    def __init__(self) -> None:
        self.frames_processed: int = 0
        self.unique_ids: set[int] = set()
        self.fps_samples: list[float] = []
        self.tracked_counts: list[int] = []
        self.start_time: float = time.perf_counter()

    def update(self, track_ids: List[int], proc_fps: float) -> None:
        self.frames_processed += 1
        self.unique_ids.update(track_ids)
        self.tracked_counts.append(len(track_ids))
        if proc_fps > 0:
            self.fps_samples.append(proc_fps)

    @property
    def avg_fps(self) -> float:
        return float(np.mean(self.fps_samples)) if self.fps_samples else 0.0

    @property
    def avg_tracked_per_frame(self) -> float:
        return float(np.mean(self.tracked_counts)) if self.tracked_counts else 0.0

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("  FootVision M2 — Tracking Session Summary")
        print("=" * 60)
        print(f"  Frames processed        : {self.frames_processed}")
        print(f"  Avg tracked / frame     : {self.avg_tracked_per_frame:.1f}")
        print(f"  Unique tracking IDs seen: {len(self.unique_ids)}")
        print(f"  Average Processing FPS  : {self.avg_fps:.1f}")
        print(f"  Min Processing FPS      : {min(self.fps_samples, default=0):.1f}")
        print(f"  Max Processing FPS      : {max(self.fps_samples, default=0):.1f}")
        print(f"  Elapsed wall time       : {self.elapsed:.1f}s")
        print("=" * 60)


# =============================================================================
# SECTION 5 — CORE TRACKER CLASS
# =============================================================================

class PlayerTracker:
    """
    Multi-object player tracker combining YOLO + ByteTrack and PitchFilter.
    """

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        video_path: Path = VIDEO_PATH,
        polygon_path: Path = POLYGON_PATH,
        output_dir: Path = OUTPUT_DIR,
        pitch_margin: int = PITCH_MARGIN,
        process_every: int = PROCESS_EVERY,
    ) -> None:
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        self.process_every = process_every

        print(f"[Tracker] Loading model: {model_path}")
        assert Path(model_path).exists(), f"❌ Model not found: {model_path}"
        self.model = YOLO(str(model_path))
        print(f"[Tracker] ✅ Model loaded  task={self.model.task}")

        print(f"[Tracker] Opening video: {video_path}")
        assert self.video_path.exists(), f"❌ Video not found: {video_path}"
        self.cap = cv2.VideoCapture(str(self.video_path))
        assert self.cap.isOpened(), f"❌ Could not open video: {video_path}"

        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0
        self.frame_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(
            f"[Tracker] ✅ Video: {self.frame_w}x{self.frame_h} @ {self.video_fps:.1f} FPS "
            f"({self.total_frames} frames)"
        )

        self.pitch_filter = PitchFilter(
            video_path=str(self.video_path),
            polygon_path=str(polygon_path),
            margin=pitch_margin,
            show_overlay=True,
            debug=False,
        )

        self.output_path = _build_output_path(self.video_path, self.output_dir)
        self.writer = _make_video_writer(self.output_path, self.frame_w, self.frame_h, self.video_fps)
        print(f"[Tracker] Output will be saved to: {self.output_path}")

        self.session = TrackingSession()
        self.debug = False

        self._last_on_pitch_tracks: List[Dict] = []
        self._last_off_pitch_tracks: List[Dict] = []
        self._last_proc_fps: float = 0.0

    def run(self) -> None:
        """Main tracking execution loop."""
        print("\n[Tracker] Starting tracking loop...")
        print("  Controls: Q = quit  |  D = toggle debug\n")

        frame_idx = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Tracker] End of video.")
                break

            frame_idx += 1

            if frame_idx % self.process_every == 0:
                t0 = time.perf_counter()
                on_pitch, off_pitch = self._track_frame(frame)
                t1 = time.perf_counter()
                self._last_proc_fps = 1.0 / max(t1 - t0, 1e-9)
                self._last_on_pitch_tracks = on_pitch
                self._last_off_pitch_tracks = off_pitch
            else:
                on_pitch = self._last_on_pitch_tracks
                off_pitch = self._last_off_pitch_tracks

            ids_this_frame = [t["track_id"] for t in on_pitch]
            self.session.update(ids_this_frame, self._last_proc_fps)

            # Drawing
            self.pitch_filter.draw_overlay(frame)
            self._draw_tracks(frame, on_pitch, off_pitch)
            draw_hud(
                frame,
                frame_idx=frame_idx,
                tracked_count=len(on_pitch),
                proc_fps=self._last_proc_fps,
                unique_ids=len(self.session.unique_ids),
                debug=self.debug,
                elapsed_s=self.session.elapsed,
            )

            # Save and display
            self.writer.write(frame)
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[Tracker] Q pressed. Stopping session.")
                break
            elif key == ord("d"):
                self.debug = not self.debug
                print(f"[Tracker] Debug mode {'ON' if self.debug else 'OFF'}")

        self._cleanup()

    def _track_frame(self, frame: np.ndarray) -> Tuple[List[Dict], List[Dict]]:
        """Run YOLO + ByteTrack on a single frame and partition by pitch region."""
        results = self.model.track(
            source=frame,
            **BYTETRACK_CONFIG,
        )

        if not results or len(results) == 0:
            return [], []

        result = results[0]
        if result.boxes is None or result.boxes.id is None:
            return [], []

        raw_tracks: List[Dict] = []
        for box, track_id in zip(result.boxes, result.boxes.id):
            cls_id = int(box.cls[0])
            if cls_id != 0:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            raw_tracks.append({
                "track_id": int(track_id),
                "xyxy": (x1, y1, x2, y2),
                "conf": float(box.conf[0]),
                "on_pitch": True,
            })

        on_pitch: List[Dict] = []
        off_pitch: List[Dict] = []

        for track in raw_tracks:
            foot = self._foot_point(track["xyxy"])
            if self.pitch_filter.polygon is not None:
                dist = cv2.pointPolygonTest(
                    self.pitch_filter.polygon,
                    (float(foot[0]), float(foot[1])),
                    measureDist=True,
                )
                is_on = dist >= -self.pitch_filter.margin
            else:
                is_on = True

            track["on_pitch"] = is_on
            if is_on:
                on_pitch.append(track)
            else:
                off_pitch.append(track)

        return on_pitch, off_pitch

    @staticmethod
    def _foot_point(xyxy: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Compute bottom-center of bounding box."""
        x1, _, x2, y2 = xyxy
        return ((x1 + x2) // 2, y2)

    def _draw_tracks(
        self,
        frame: np.ndarray,
        on_pitch: List[Dict],
        off_pitch: List[Dict],
    ) -> None:
        """Render player tracks on the frame."""
        for track in on_pitch:
            x1, y1, x2, y2 = track["xyxy"]
            draw_tracked_player(frame, x1, y1, x2, y2, track["track_id"], track["conf"])

        if self.debug:
            for track in off_pitch:
                x1, y1, x2, y2 = track["xyxy"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), DEBUG_BOX_COLOR, 1)
                label = f"[off] P{track['track_id']} ({track['conf']:.2f})"
                cv2.putText(
                    frame, label, (x1 + 2, max(y1 - 6, 12)),
                    FONT, 0.45, DEBUG_BOX_COLOR, 1,
                )

    def _cleanup(self) -> None:
        """Release video streams and print performance report."""
        self.cap.release()
        self.writer.release()
        cv2.destroyAllWindows()
        print(f"\n[Tracker] Processed video saved to: {self.output_path}")
        self.session.print_summary()


# =============================================================================
# SECTION 6 — ENTRY POINT
# =============================================================================

def main() -> None:
    tracker = PlayerTracker()
    tracker.run()


if __name__ == "__main__":
    main()
