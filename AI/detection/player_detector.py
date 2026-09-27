"""
FootVision AI — M1: Player Detection
Script: player_detector.py

PURPOSE
-------
Opens a football video, runs YOLOv8s person detection on each frame,
then applies a pitch-region filter (PitchFilter) to remove spectators,
coaches, and substitutes who are clearly off the pitch.

PIPELINE
--------
    Video frame
        ↓
    YOLO  (detects all 'person' instances)
        ↓
    PitchFilter  (keeps only feet-on-pitch detections)
        ↓
    Draw + Display

NO tracking, No Re-ID, No OCR, No pitch mapping — detection + filtering only.

RUN
---
Activate your virtual environment first, then from FootVision/ root:

    python AI/detection/player_detector.py

FIRST RUN
---------
An interactive window opens on the first frame.  Click the corners of
the pitch (4–6 clicks), then press ENTER to save the polygon.  All
subsequent runs load the polygon from Data/processed/pitch_polygon.json
automatically — no clicking needed.

CONTROLS (live video window)
----------------------------
    Q  — quit
    D  — toggle debug mode (shows foot-points coloured green/red)
    R  — re-define the pitch polygon (opens setup window again)
"""

import os
import sys
import time

import cv2
from ultralytics import YOLO

# Allow importing from sibling module (AI/detection/pitch_filter.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pitch_filter import PitchFilter

# =============================================================================
# SECTION 1 — CONFIGURATION
# =============================================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_PATH   = os.path.join(PROJECT_ROOT, "AI", "models", "yolov8s.pt")
VIDEO_PATH   = os.path.join(PROJECT_ROOT, "Data", "raw", "test.mp4")

# Saved pitch polygon (created interactively on first run)
POLYGON_PATH = os.path.join(PROJECT_ROOT, "Data", "processed", "pitch_polygon.json")

# ── Detection settings ────────────────────────────────────────────────────────
PERSON_CLASS_ID   = 0       # COCO class 0 = 'person'
CONFIDENCE_THRESH = 0.40    # Minimum YOLO confidence to keep a detection
PROCESS_EVERY_N   = 2       # Run YOLO on every Nth frame (CPU speed optimisation)

# ── Pitch filter settings ─────────────────────────────────────────────────────
# PITCH_MARGIN: extra pixel tolerance around the polygon edge.
# Increase if players on the touchline are being incorrectly removed.
PITCH_MARGIN = 15

# ── Display settings ──────────────────────────────────────────────────────────
WINDOW_NAME        = "FootVision — Player Detector  [Q quit | D debug | R reset polygon]"
BOX_COLOR_ON       = (0, 255, 100)    # Green  — player on pitch
BOX_COLOR_OFF      = (0, 80, 200)     # Blue   — person off-pitch (debug only)
TEXT_COLOR         = (255, 255, 255)
TEXT_BG_ON         = (0, 80, 30)
TEXT_BG_OFF        = (80, 30, 0)
FONT               = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE         = 0.52
FONT_THICKNESS     = 1
BOX_THICKNESS      = 2


# =============================================================================
# SECTION 2 — MODEL LOADER
# =============================================================================

def load_model(model_path: str) -> YOLO:
    """Load YOLOv8s from disk.  Raises a clear error if the file is missing."""
    print(f"[FootVision] Loading model: {model_path}")
    assert os.path.exists(model_path), (
        f"❌ Model not found: {model_path}\n"
        f"   Run:  python AI/models/setup_model.py"
    )
    model = YOLO(model_path)
    print(f"[FootVision] ✅ Model loaded  task={model.task}  classes={len(model.names)}")
    return model


# =============================================================================
# SECTION 3 — VIDEO READER
# =============================================================================

def open_video(video_path: str) -> cv2.VideoCapture:
    """Open the video file and print its metadata."""
    print(f"[FootVision] Opening video: {video_path}")
    assert os.path.exists(video_path), (
        f"❌ Video not found: {video_path}\n"
        f"   Place your football video at  Data/raw/test.mp4"
    )
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"❌ OpenCV could not open: {video_path}"

    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[FootVision] ✅ Video  {width}x{height} @ {fps:.1f} fps  {total} frames")
    return cap


# =============================================================================
# SECTION 4 — YOLO INFERENCE
# =============================================================================

def detect_persons(model: YOLO, frame, conf_thresh: float) -> list:
    """
    Run YOLO on one frame, return ALL person detections above conf_thresh.

    NOTE: This returns every 'person' YOLO sees — spectators included.
    Pitch filtering happens in the next step (PitchFilter.filter).

    Returns list of dicts: { xyxy, conf, cls_id, on_pitch }
    """
    results = model(frame, verbose=False)[0]
    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        if cls_id == PERSON_CLASS_ID and conf >= conf_thresh:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append({
                "xyxy":     (x1, y1, x2, y2),
                "conf":     conf,
                "cls_id":   cls_id,
                "on_pitch": True,   # default; overwritten by PitchFilter
            })
    return detections


# =============================================================================
# SECTION 5 — DRAWING
# =============================================================================

def draw_detections(frame, detections: list, debug: bool = False) -> None:
    """
    Draw bounding boxes onto the frame.

    In normal mode  : only on-pitch detections are drawn (green).
    In debug mode   : all detections drawn; off-pitch ones in blue so
                      you can see what the filter is removing.
    """
    for det in detections:
        on_pitch = det.get("on_pitch", True)

        # In normal mode, skip off-pitch detections entirely
        if not debug and not on_pitch:
            continue

        x1, y1, x2, y2 = det["xyxy"]
        conf  = det["conf"]
        color = BOX_COLOR_ON if on_pitch else BOX_COLOR_OFF
        bg    = TEXT_BG_ON   if on_pitch else TEXT_BG_OFF
        label = f"{'player' if on_pitch else 'FILTERED'}  {conf:.2f}"

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, BOX_THICKNESS)

        # Label background
        (tw, th), baseline = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICKNESS)
        label_y = max(y1 - 4, th + 4)
        cv2.rectangle(
            frame,
            (x1, label_y - th - baseline - 2),
            (x1 + tw + 4, label_y + 2),
            bg, cv2.FILLED,
        )
        cv2.putText(frame, label, (x1 + 2, label_y - baseline),
                    FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)


def draw_hud(frame, frame_idx: int, raw_count: int, filtered_count: int,
             fps: float, debug: bool, filter_active: bool) -> None:
    """
    HUD overlay — top-left corner.

    Shows raw vs filtered counts so you can immediately see how many
    detections the pitch filter is removing each frame.
    """
    filter_str = "ON" if filter_active else "OFF (ESC skipped)"
    debug_str  = "ON" if debug else "OFF"
    lines = [
        f"Frame        : {frame_idx}",
        f"Raw persons  : {raw_count}",
        f"On-pitch     : {filtered_count}",
        f"Proc. FPS    : {fps:.1f}",
        f"Pitch filter : {filter_str}",
        f"Debug mode   : {debug_str}",
        "[Q] Quit  [D] Debug  [R] Reset polygon",
    ]
    x, y = 10, 24
    for line in lines:
        cv2.putText(frame, line, (x + 1, y + 1), FONT, FONT_SCALE, (0, 0, 0), FONT_THICKNESS + 1)
        cv2.putText(frame, line, (x, y), FONT, FONT_SCALE, (255, 255, 255), FONT_THICKNESS)
        y += 20


# =============================================================================
# SECTION 6 — MAIN LOOP
# =============================================================================

def run_detector():
    """
    Main detection + filtering loop.

    Flow per frame:
        read frame
          → (every Nth frame) YOLO → all person detections
          → PitchFilter → on-pitch detections only
          → draw boxes + polygon overlay + HUD
          → display
          → handle keypresses (Q / D / R)
    """
    model        = load_model(MODEL_PATH)
    cap          = open_video(VIDEO_PATH)
    pitch_filter = PitchFilter(
        video_path   = VIDEO_PATH,
        polygon_path = POLYGON_PATH,
        margin       = PITCH_MARGIN,
        show_overlay = True,
        debug        = False,
    )

    frame_idx       = 0
    raw_detections  = []    # All YOLO person detections (unfiltered)
    kept_detections = []    # After pitch filter
    fps_display     = 0.0
    debug_mode      = False

    print("\n[FootVision] Detection loop started.")
    print("  Controls: Q = quit  |  D = toggle debug  |  R = reset pitch polygon\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[FootVision] End of video.")
            break

        frame_idx += 1

        # ── Run YOLO + pitch filter every Nth frame ───────────────────────────
        if frame_idx % PROCESS_EVERY_N == 0:
            t0              = time.perf_counter()
            raw_detections  = detect_persons(model, frame, CONFIDENCE_THRESH)
            kept_detections = pitch_filter.filter(raw_detections)
            t1              = time.perf_counter()
            fps_display     = 1.0 / max(t1 - t0, 1e-9)

        # ── Draw pitch polygon overlay ────────────────────────────────────────
        pitch_filter.draw_overlay(frame)

        # ── Draw bounding boxes ───────────────────────────────────────────────
        # In debug mode pass raw_detections (includes filtered-out ones in blue)
        # In normal mode pass kept_detections (green only)
        draw_detections(
            frame,
            raw_detections if debug_mode else kept_detections,
            debug=debug_mode,
        )

        # ── Draw foot points in debug mode ────────────────────────────────────
        if debug_mode:
            pitch_filter.draw_foot_points(frame, raw_detections)

        # ── HUD ───────────────────────────────────────────────────────────────
        draw_hud(
            frame,
            frame_idx    = frame_idx,
            raw_count    = len(raw_detections),
            filtered_count = len(kept_detections),
            fps          = fps_display,
            debug        = debug_mode,
            filter_active= pitch_filter.is_active(),
        )

        # ── Display ───────────────────────────────────────────────────────────
        cv2.imshow(WINDOW_NAME, frame)

        # ── Keypresses ────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("[FootVision] Q pressed — stopping.")
            break

        elif key == ord("d"):
            debug_mode = not debug_mode
            print(f"[FootVision] Debug mode {'ON' if debug_mode else 'OFF'}")

        elif key == ord("r"):
            # Delete saved polygon and re-run interactive setup
            if os.path.exists(POLYGON_PATH):
                os.remove(POLYGON_PATH)
                print("[FootVision] Polygon deleted — opening setup...")
            pitch_filter = PitchFilter(
                video_path   = VIDEO_PATH,
                polygon_path = POLYGON_PATH,
                margin       = PITCH_MARGIN,
                show_overlay = True,
                debug        = False,
            )

    # ── Cleanup ───────────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print(f"[FootVision] Done.  Processed {frame_idx} frames.")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run_detector()
