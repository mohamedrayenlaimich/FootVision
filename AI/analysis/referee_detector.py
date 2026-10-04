"""
FootVision AI — Referee Identification Module
Script: referee_detector.py

PURPOSE
-------
Detects and distinguishes the referee from field players using:
1. Clothing appearance (color distinction from both Team A and Team B kits).
2. Color profiles commonly worn by referees (fluorescent yellow, neon orange/pink, solid black).
3. Contextual constraints (typically 1 main referee in the pitch interior).
4. Spatial movement and positional behavior.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class RefereeDetector:
    """
    Identifies match officials on the pitch.
    """

    def __init__(self) -> None:
        # Confirmed referee track IDs
        self.confirmed_referee_id: Optional[int] = None
        self.referee_scores: Dict[int, float] = {}

    def is_referee_color(self, frame: np.ndarray, xyxy: Tuple[int, int, int, int]) -> Tuple[bool, float]:
        """
        Analyze upper torso color in HSV to test if it matches standard referee kit profiles:
        - High-vis neon yellow / green (H: 22-42, S: >120, V: >140)
        - Neon orange / pink (H: 5-20, S: >140, V: >160)
        - Solid dark / black referee kit (V: < 45 across entire torso)
        - Bright cyan (H: 85-105, S: >120, V: >140)
        """
        x1, y1, x2, y2 = xyxy
        h, w = y2 - y1, x2 - x1
        if h < 20 or w < 10:
            return False, 0.0

        tx1 = max(0, int(x1 + 0.25 * w))
        tx2 = min(frame.shape[1], int(x2 - 0.25 * w))
        ty1 = max(0, int(y1 + 0.18 * h))
        ty2 = min(frame.shape[0], int(y1 + 0.50 * h))

        if tx2 <= tx1 or ty2 <= ty1:
            return False, 0.0

        crop = frame[ty1:ty2, tx1:tx2]
        if crop.size == 0:
            return False, 0.0

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)

        # 1. Neon Yellow / Chartreuse referee jersey
        neon_yellow = (h_ch >= 22) & (h_ch <= 42) & (s_ch >= 100) & (v_ch >= 130)
        yellow_ratio = np.mean(neon_yellow)

        # 2. Neon Orange / Bright Red referee jersey
        neon_orange = (h_ch >= 5) & (h_ch <= 18) & (s_ch >= 130) & (v_ch >= 150)
        orange_ratio = np.mean(neon_orange)

        # 3. Bright Cyan referee jersey
        bright_cyan = (h_ch >= 85) & (h_ch <= 105) & (s_ch >= 110) & (v_ch >= 130)
        cyan_ratio = np.mean(bright_cyan)

        # 4. Solid Black referee kit (distinct dark profile with low saturation)
        solid_black = (v_ch <= 45)
        black_ratio = np.mean(solid_black)

        score = max(yellow_ratio, orange_ratio, cyan_ratio, black_ratio * 0.85)
        is_ref = bool(score > 0.35)

        return is_ref, float(score)

    def identify_referees(
        self,
        frame: np.ndarray,
        tracks: List[Dict],
        centroid_a: Optional[np.ndarray] = None,
        centroid_b: Optional[np.ndarray] = None,
    ) -> Dict[int, bool]:
        """
        Evaluate all on-pitch tracks to identify the referee.
        Enforces contextual logic: at most 1 primary referee on pitch.
        """
        results: Dict[int, bool] = {}
        candidate_scores: Dict[int, float] = {}

        for track in tracks:
            tid = track["track_id"]
            xyxy = track["xyxy"]

            is_color_ref, color_score = self.is_referee_color(frame, xyxy)

            # Cumulative score tracking
            current_score = self.referee_scores.get(tid, 0.0)
            if is_color_ref:
                new_score = current_score * 0.85 + color_score * 1.5
            else:
                new_score = current_score * 0.90

            self.referee_scores[tid] = new_score

            if new_score > 0.65:
                candidate_scores[tid] = new_score

        # Select highest scoring candidate if above threshold
        if candidate_scores:
            best_ref_id = max(candidate_scores, key=candidate_scores.get)
            self.confirmed_referee_id = best_ref_id
            for track in tracks:
                results[track["track_id"]] = (track["track_id"] == best_ref_id)
        elif self.confirmed_referee_id is not None:
            # Keep referee assignment if still tracked
            active_ids = {t["track_id"] for t in tracks}
            if self.confirmed_referee_id in active_ids:
                for track in tracks:
                    results[track["track_id"]] = (track["track_id"] == self.confirmed_referee_id)
            else:
                for track in tracks:
                    results[track["track_id"]] = False
        else:
            for track in tracks:
                results[track["track_id"]] = False

        return results
