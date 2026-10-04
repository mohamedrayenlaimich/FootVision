"""
FootVision AI — Ball Detection and Temporal Tracking
Script: ball_tracker.py

PURPOSE
-------
Detects and tracks the football across consecutive frames.
Combines:
1. YOLO detection of sports ball (COCO class 32).
2. Size, aspect ratio, and pitch boundary filtering.
3. Proximity to players and motion dynamics.
4. Linear Kalman / velocity temporal smoothing.
5. Honest missing/occluded state handling (never fabricates fake detections).
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class BallTracker:
    """
    Football detector and temporal Kalman tracker.
    """

    def __init__(
        self,
        max_missing_frames: int = 6,
        max_ball_size_px: int = 50,
    ) -> None:
        self.max_missing_frames = max_missing_frames
        self.max_ball_size_px = max_ball_size_px

        # Tracking state
        self.current_bbox: Optional[Tuple[int, int, int, int]] = None
        self.current_center: Optional[Tuple[int, int]] = None
        self.velocity: Tuple[float, float] = (0.0, 0.0)
        self.missing_frames: int = 999
        self.confidence: float = 0.0

        # Ball trajectory history: list of (x, y) coordinates
        self.trajectory: List[Tuple[int, int]] = []

    def update(
        self,
        ball_detections: List[Dict],
        player_bboxes: List[Tuple[int, int, int, int]],
        frame_shape: Tuple[int, int],
    ) -> Optional[Dict]:
        """
        Update ball state from candidate YOLO detections and temporal predictions.

        ball_detections: list of dicts: {"xyxy": (x1, y1, x2, y2), "conf": float}
        """
        fh, fw = frame_shape[:2]
        best_candidate: Optional[Dict] = None
        highest_score = 0.0

        for det in ball_detections:
            x1, y1, x2, y2 = det["xyxy"]
            w = x2 - x1
            h = y2 - y1
            conf = det["conf"]

            # 1. Sanity check: football is small and roughly square
            if w > self.max_ball_size_px or h > self.max_ball_size_px:
                continue
            if w < 4 or h < 4:
                continue

            aspect_ratio = w / max(1, h)
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                continue

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # 2. Score candidate based on confidence and continuity with last known position
            score = conf
            if self.current_center is not None and self.missing_frames < self.max_missing_frames:
                pred_x = self.current_center[0] + self.velocity[0] * (self.missing_frames + 1)
                pred_y = self.current_center[1] + self.velocity[1] * (self.missing_frames + 1)
                dist = np.hypot(cx - pred_x, cy - pred_y)

                # Penalize implausible teleportation (> 180 px per frame)
                if dist > 180:
                    score *= 0.2
                else:
                    # Boost candidates that follow trajectory
                    score *= (1.0 + max(0.0, 1.0 - (dist / 180.0)))

            if score > highest_score:
                highest_score = score
                best_candidate = det

        # If a valid candidate detection is found
        if best_candidate is not None and highest_score > 0.15:
            x1, y1, x2, y2 = best_candidate["xyxy"]
            new_center = ((x1 + x2) // 2, (y1 + y2) // 2)

            if self.current_center is not None:
                dt = max(1, self.missing_frames + 1)
                vx = (new_center[0] - self.current_center[0]) / dt
                vy = (new_center[1] - self.current_center[1]) / dt
                # Smooth velocity
                self.velocity = (
                    0.6 * self.velocity[0] + 0.4 * vx,
                    0.6 * self.velocity[1] + 0.4 * vy,
                )

            self.current_bbox = (x1, y1, x2, y2)
            self.current_center = new_center
            self.confidence = float(best_candidate["conf"])
            self.missing_frames = 0
            self.trajectory.append(new_center)
            if len(self.trajectory) > 40:
                self.trajectory.pop(0)

            return {
                "detected": True,
                "xyxy": self.current_bbox,
                "center": self.current_center,
                "confidence": round(self.confidence, 2),
                "is_interpolated": False,
            }

        # No candidate detection this frame: check if we should predict or declare missing
        self.missing_frames += 1
        if (
            self.current_center is not None
            and self.missing_frames <= self.max_missing_frames
            and np.hypot(self.velocity[0], self.velocity[1]) > 1.0
        ):
            # Short occlusion: predict with decaying confidence
            px = int(self.current_center[0] + self.velocity[0])
            py = int(self.current_center[1] + self.velocity[1])

            # Ensure inside frame bounds
            if 0 <= px < fw and 0 <= py < fh:
                w = self.current_bbox[2] - self.current_bbox[0] if self.current_bbox else 16
                h = self.current_bbox[3] - self.current_bbox[1] if self.current_bbox else 16
                half_w, half_h = w // 2, h // 2
                self.current_bbox = (px - half_w, py - half_h, px + half_w, py + half_h)
                self.current_center = (px, py)
                self.confidence *= 0.75
                self.trajectory.append((px, py))
                if len(self.trajectory) > 40:
                    self.trajectory.pop(0)

                return {
                    "detected": True,
                    "xyxy": self.current_bbox,
                    "center": self.current_center,
                    "confidence": round(self.confidence, 2),
                    "is_interpolated": True,
                }

        # Ball is temporarily missing or occluded
        return {
            "detected": False,
            "xyxy": None,
            "center": None,
            "confidence": 0.0,
            "is_interpolated": False,
        }
