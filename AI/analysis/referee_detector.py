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
        # Confirmed referee track ID (locked to prevent jumping)
        self.confirmed_referee_id: Optional[int] = None
        self.confirmed_referee_missing_frames: int = 0
        self.referee_scores: Dict[int, float] = {}
        self.ref_streaks: Dict[int, int] = {}

    def is_referee_color(
        self,
        frame: np.ndarray,
        xyxy: Tuple[int, int, int, int],
        centroid_a: Optional[np.ndarray] = None,
        centroid_b: Optional[np.ndarray] = None,
    ) -> Tuple[bool, float]:
        """
        Analyze upper torso color to test if it matches standard referee kit profiles:
        - High-vis neon yellow / chartreuse (H: 22-42, S: >80, V: >110)
        - High-vis neon orange / pink (H: 5-18, S: >120, V: >135)
        - High-vis bright cyan (H: 85-105, S: >100, V: >120)
        - High-vis magenta / purple (H: 165-180, S: >120, V: >135)
        - Black official kit ONLY when neither outfield team wears a dark/black kit
        """
        x1, y1, x2, y2 = xyxy
        h, w = y2 - y1, x2 - x1
        if h < 15 or w < 6:
            return False, 0.0

        # Reject extreme non-human aspect ratios (e.g. very wide horizontal banners)
        aspect = h / max(1.0, float(w))
        if aspect < 0.75 or aspect > 5.5:
            return False, 0.0

        tx1 = max(0, int(x1 + 0.20 * w))
        tx2 = min(frame.shape[1], int(x2 - 0.20 * w))
        ty1 = max(0, int(y1 + 0.16 * h))
        ty2 = min(frame.shape[0], int(y1 + 0.52 * h))

        if tx2 <= tx1 or ty2 <= ty1:
            return False, 0.0

        crop = frame[ty1:ty2, tx1:tx2]
        if crop.size == 0:
            return False, 0.0

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)

        # 1. Neon Yellow / Chartreuse referee jersey (FIFA / UEFA standard)
        neon_yellow = (h_ch >= 22) & (h_ch <= 42) & (s_ch >= 80) & (v_ch >= 110)
        yellow_ratio = float(np.mean(neon_yellow))

        # 2. Neon Orange / Bright Pink referee jersey
        neon_orange = (h_ch >= 5) & (h_ch <= 18) & (s_ch >= 120) & (v_ch >= 135)
        orange_ratio = float(np.mean(neon_orange))

        # 3. Bright Cyan referee jersey
        bright_cyan = (h_ch >= 85) & (h_ch <= 105) & (s_ch >= 100) & (v_ch >= 120)
        cyan_ratio = float(np.mean(bright_cyan))

        # 4. Neon Magenta / Red referee jersey
        neon_magenta = (h_ch >= 165) & (h_ch <= 180) & (s_ch >= 120) & (v_ch >= 135)
        magenta_ratio = float(np.mean(neon_magenta))

        # 5. Solid Black referee kit:
        # Strictly disallowed if either Team A or Team B wears a dark kit (L < 45)
        black_allowed = True
        if centroid_a is not None and centroid_a[0] < 45.0:
            black_allowed = False
        if centroid_b is not None and centroid_b[0] < 45.0:
            black_allowed = False

        black_ratio = 0.0
        if black_allowed:
            solid_black = (v_ch <= 40) & (s_ch <= 60)
            if float(np.mean(solid_black)) > 0.60:
                black_ratio = float(np.mean(solid_black)) * 0.70

        color_score = max(yellow_ratio, orange_ratio, cyan_ratio, magenta_ratio, black_ratio)

        # Contrast against Team kit colors if centroids are calibrated
        if (centroid_a is not None or centroid_b is not None) and color_score > 0.30:
            lab_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2Lab)
            med_lab = np.median(lab_crop.reshape(-1, 3), axis=0).astype(np.float32)
            if centroid_a is not None:
                dist_a = float(np.linalg.norm(med_lab - centroid_a))
                if dist_a < 22.0:
                    # Too close to Team A kit — not referee
                    return False, 0.0
            if centroid_b is not None:
                dist_b = float(np.linalg.norm(med_lab - centroid_b))
                if dist_b < 22.0:
                    # Too close to Team B kit — not referee
                    return False, 0.0

        is_ref = bool(color_score > 0.35)
        return is_ref, color_score

    def identify_referees(
        self,
        frame: np.ndarray,
        tracks: List[Dict],
        centroid_a: Optional[np.ndarray] = None,
        centroid_b: Optional[np.ndarray] = None,
    ) -> Dict[int, bool]:
        """
        Evaluate all on-pitch tracks to identify the referee.
        Enforces contextual logic:
        - At most 1 primary referee on pitch.
        - Track ID is locked once confirmed to eliminate identity flapping.
        - Requires persistent detection streaks before confirming.
        """
        results: Dict[int, bool] = {}
        active_ids = {t["track_id"] for t in tracks}
        candidate_scores: Dict[int, float] = {}

        for track in tracks:
            tid = track["track_id"]
            xyxy = track["xyxy"]

            is_color_ref, color_score = self.is_referee_color(
                frame, xyxy, centroid_a=centroid_a, centroid_b=centroid_b
            )

            # Cumulative score tracking & streak
            current_score = self.referee_scores.get(tid, 0.0)
            if is_color_ref:
                self.ref_streaks[tid] = self.ref_streaks.get(tid, 0) + 1
                new_score = current_score * 0.85 + color_score * 1.5
            else:
                self.ref_streaks[tid] = max(0, self.ref_streaks.get(tid, 0) - 1)
                new_score = current_score * 0.85

            self.referee_scores[tid] = new_score

            # Candidate qualification: requires consistency (streak >= 3) and score
            if self.ref_streaks.get(tid, 0) >= 3 and new_score > 1.2:
                candidate_scores[tid] = new_score * (1.0 + 0.1 * min(10, self.ref_streaks[tid]))

        # Check if the existing confirmed referee is currently visible
        if self.confirmed_referee_id is not None:
            if self.confirmed_referee_id in active_ids:
                self.confirmed_referee_missing_frames = 0
                for track in tracks:
                    results[track["track_id"]] = (track["track_id"] == self.confirmed_referee_id)
                return results
            else:
                self.confirmed_referee_missing_frames += 1
                # Referee temporarily occluded or out of view: do not reassign immediately
                if self.confirmed_referee_missing_frames < 45:
                    for track in tracks:
                        results[track["track_id"]] = False
                    return results
                else:
                    # Lost track for over 45 frames: release lock to allow re-acquisition
                    self.confirmed_referee_id = None

        # Confirm new referee from high-scoring persistent candidates
        if candidate_scores:
            best_ref_id = max(candidate_scores, key=candidate_scores.get)
            self.confirmed_referee_id = best_ref_id
            self.confirmed_referee_missing_frames = 0
            for track in tracks:
                results[track["track_id"]] = (track["track_id"] == best_ref_id)
        else:
            for track in tracks:
                results[track["track_id"]] = False

        return results
