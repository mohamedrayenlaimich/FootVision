"""
FootVision AI — Match Video Analysis & Visual Tracking Service
Script: video_analysis_service.py

PURPOSE
-------
Asynchronous background pipeline service that processes football match video clips:
1. Ingests video stream frame-by-frame (memory safe).
2. Runs YOLOv8 person & sports ball detection + ByteTrack tracking.
3. Filters off-pitch detections using PitchFilter polygon.
4. Identifies referee with RefereeDetector.
5. Classifies field players into Team A (Blue) vs Team B (Red) with TeamClassifier.
6. Tracks football dynamics and short occlusions with BallTracker.
7. Renders colored overlays and HUD with VideoAnnotator.
8. Encodes annotated video to MP4 and stores structured JSON tracking telemetry.
9. Updates job progress percentages and stage statuses for the frontend.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

import cv2
import numpy as np
from ultralytics import YOLO

# Ensure AI packages can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "AI" / "detection"))
sys.path.insert(0, str(PROJECT_ROOT / "AI" / "analysis"))
sys.path.insert(0, str(PROJECT_ROOT / "AI" / "tracking"))

from pitch_filter import PitchFilter
from team_classifier import TeamClassifier
from referee_detector import RefereeDetector
from ball_tracker import BallTracker
from video_annotator import VideoAnnotator

logger = logging.getLogger("footvision.video_analysis")


class VideoAnalysisPipeline:
    """
    Production-grade video analysis and multi-object tracking pipeline.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        polygon_path: Optional[str] = None,
        process_every_n: int = 1,
        conf_thresh: float = 0.30,
        iou_thresh: float = 0.45,
    ) -> None:
        self.model_path = model_path or str(PROJECT_ROOT / "AI" / "models" / "yolov8s.pt")
        self.polygon_path = polygon_path or str(PROJECT_ROOT / "Data" / "processed" / "pitch_polygon.json")
        self.process_every_n = max(1, process_every_n)
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh

        logger.info(f"Initializing YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)

    def process_video(
        self,
        video_id: str,
        input_path: str,
        output_video_path: str,
        output_telemetry_path: str,
        progress_callback: Optional[Callable[[Dict], None]] = None,
        max_frames: Optional[int] = None,
    ) -> Dict:
        """
        Processes the input video file and writes:
        - Annotated MP4 video file
        - JSON telemetry file
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open input video file: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if max_frames is not None and max_frames > 0:
            total_frames = min(total_frames, max_frames)

        logger.info(f"Video {video_id}: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")

        # Initialize sub-modules
        pitch_filter = PitchFilter(
            video_path=input_path,
            polygon_path=self.polygon_path,
            margin=15,
            show_overlay=False,
            debug=False,
        )
        team_classifier = TeamClassifier(history_window=30)
        referee_detector = RefereeDetector()
        ball_tracker = BallTracker()
        annotator = VideoAnnotator(
            show_boxes=True,
            show_ids=True,
            show_referee=True,
            show_ball=True,
            show_trails=True,
            show_hud=True,
        )

        # Video writer setup
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        if not writer.isOpened():
            # Fallback to XVID
            alt_path = output_video_path.replace(".mp4", ".avi")
            writer = cv2.VideoWriter(alt_path, cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height))
            output_video_path = alt_path

        frame_idx = 0
        ball_detected_count = 0
        all_unique_ids = set()
        team_a_ids = set()
        team_b_ids = set()
        referee_ids = set()
        per_frame_telemetry = []

        last_tracks: List[Dict] = []
        last_ball: Optional[Dict] = None

        t_start = time.perf_counter()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if max_frames and frame_idx > max_frames:
                break

            timestamp_sec = round(frame_idx / max(1.0, fps), 3)

            # Every Nth frame: run inference and full tracking
            if frame_idx % self.process_every_n == 0 or frame_idx == 1:
                t0 = time.perf_counter()

                # Run YOLO tracking (person class 0, sports ball class 32)
                # tracker="bytetrack.yaml" provides stable tracking IDs
                results = self.model.track(
                    source=frame,
                    tracker="bytetrack.yaml",
                    conf=self.conf_thresh,
                    iou=self.iou_thresh,
                    classes=[0, 32],
                    persist=True,
                    verbose=False,
                )

                person_tracks: List[Dict] = []
                ball_detections: List[Dict] = []

                if results and len(results) > 0 and results[0].boxes is not None:
                    res_boxes = results[0].boxes
                    track_ids = res_boxes.id.cpu().numpy() if res_boxes.id is not None else None

                    for i, box in enumerate(res_boxes):
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        if cls_id == 0:  # person
                            tid = int(track_ids[i]) if track_ids is not None else (1000 + i)
                            person_tracks.append({
                                "track_id": tid,
                                "xyxy": (x1, y1, x2, y2),
                                "conf": round(conf, 2),
                                "cls_id": cls_id,
                            })
                        elif cls_id == 32:  # sports ball
                            ball_detections.append({
                                "xyxy": (x1, y1, x2, y2),
                                "conf": round(conf, 2),
                                "cls_id": cls_id,
                            })

                # Pitch filtering: keep only valid players with feet on the pitch (rejects TV logos, scoreboards, stands)
                on_pitch_tracks = pitch_filter.filter(person_tracks, frame_shape=(height, width))

                # Referee identification with kit separation against team kit colors
                ref_map = referee_detector.identify_referees(
                    frame=frame,
                    tracks=on_pitch_tracks,
                    centroid_a=team_classifier.centroid_a,
                    centroid_b=team_classifier.centroid_b,
                )

                # Team classification
                for pt in on_pitch_tracks:
                    tid = pt["track_id"]
                    all_unique_ids.add(tid)
                    is_ref = ref_map.get(tid, False)
                    pt["is_referee"] = is_ref

                    if is_ref:
                        if referee_detector.confirmed_referee_id == tid:
                            referee_ids.add(tid)
                        pt["classification"] = {
                            "team": "REFEREE",
                            "label": "REFEREE",
                            "confidence": 0.95,
                            "color_code": "yellow",
                            "is_gk": False,
                        }
                    else:
                        classification = team_classifier.update_and_classify(
                            frame,
                            tid,
                            pt["xyxy"],
                            is_referee=False,
                        )
                        pt["classification"] = classification
                        if classification["team"] == "Team A":
                            team_a_ids.add(tid)
                        elif classification["team"] == "Team B":
                            team_b_ids.add(tid)

                # Ball tracking update with pitch constraint and overlay rejection
                player_boxes = [t["xyxy"] for t in on_pitch_tracks]
                ball_info = ball_tracker.update(
                    ball_detections=ball_detections,
                    player_bboxes=player_boxes,
                    frame_shape=(height, width),
                    pitch_polygon=pitch_filter.polygon,
                )
                if ball_info and ball_info.get("detected"):
                    ball_detected_count += 1

                t1 = time.perf_counter()
                current_fps = 1.0 / max(t1 - t0, 1e-6)

                last_tracks = on_pitch_tracks
                last_ball = ball_info
            else:
                # Skipped frame: reuse last tracks and ball for smooth visual continuity
                current_fps = fps

            # Render overlays onto frame
            annotated_frame = annotator.annotate_frame(
                frame=frame,
                frame_idx=frame_idx,
                tracks=last_tracks,
                ball_info=last_ball,
                proc_fps=current_fps,
            )

            # Write annotated frame
            writer.write(annotated_frame)

            # Record per-frame telemetry (sample every 3 frames for telemetry compactness)
            if frame_idx % 3 == 0 or frame_idx == total_frames:
                frame_telemetry = {
                    "frame_index": frame_idx,
                    "timestamp": timestamp_sec,
                    "tracks": [
                        {
                            "track_id": t["track_id"],
                            "team": t.get("classification", {}).get("team", "UNKNOWN"),
                            "is_referee": t.get("is_referee", False),
                            "bbox": list(t["xyxy"]),
                            "conf": t.get("conf", 0.0),
                        }
                        for t in last_tracks
                    ],
                    "ball": {
                        "detected": bool(last_ball.get("detected")) if last_ball else False,
                        "center": list(last_ball["center"]) if last_ball and last_ball.get("center") else None,
                        "conf": last_ball.get("confidence", 0.0) if last_ball else 0.0,
                    } if last_ball else {"detected": False},
                }
                per_frame_telemetry.append(frame_telemetry)

            # Report progress via callback
            if progress_callback and (frame_idx % 10 == 0 or frame_idx == total_frames):
                pct = round((frame_idx / max(1, total_frames)) * 100, 1)
                progress_callback({
                    "video_id": video_id,
                    "processed_frames": frame_idx,
                    "total_frames": total_frames,
                    "progress_percentage": pct,
                    "status": "processing",
                    "current_fps": round(current_fps, 1),
                    "players_tracked_now": len(last_tracks),
                    "team_a_count": len(team_a_ids),
                    "team_b_count": len(team_b_ids),
                    "referee_detected": bool(len(referee_ids) > 0),
                    "ball_detected": bool(last_ball.get("detected")) if last_ball else False,
                })

        cap.release()
        writer.release()

        # Convert to Web-compatible H.264 (yuv420p + faststart) for HTML5 video playback
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            web_output_path = output_video_path.replace(".mp4", "_web.mp4")
            cmd = [
                ffmpeg_exe, "-y",
                "-i", output_video_path,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                web_output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            if os.path.exists(web_output_path) and os.path.getsize(web_output_path) > 0:
                os.replace(web_output_path, output_video_path)
                logger.info(f"Successfully converted {output_video_path} to H.264 web MP4.")
        except Exception as e:
            logger.warning(f"H.264 web transcoding notice: {e}")

        elapsed_total = round(time.perf_counter() - t_start, 2)
        ball_visibility_pct = round((ball_detected_count / max(1, frame_idx)) * 100, 1)

        summary_data = {
            "video_id": video_id,
            "status": "completed",
            "progress_percentage": 100.0,
            "total_frames": frame_idx,
            "processed_frames": frame_idx,
            "duration_seconds": round(frame_idx / max(1.0, fps), 2),
            "fps": round(fps, 1),
            "width": width,
            "height": height,
            "elapsed_processing_seconds": elapsed_total,
            "total_unique_players": len(all_unique_ids),
            "team_a_players_count": len(team_a_ids),
            "team_b_players_count": len(team_b_ids),
            "referee_detected": len(referee_ids) > 0,
            "referee_ids": list(referee_ids),
            "ball_visibility_percentage": ball_visibility_pct,
            "output_video_path": output_video_path,
            "telemetry_samples_count": len(per_frame_telemetry),
        }

        # Save structured telemetry JSON
        os.makedirs(os.path.dirname(output_telemetry_path), exist_ok=True)
        with open(output_telemetry_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary_data,
                "frames": per_frame_telemetry,
            }, f, indent=2)

        logger.info(f"Video {video_id} processing complete in {elapsed_total}s: {summary_data}")

        if progress_callback:
            progress_callback(summary_data)

        return summary_data
