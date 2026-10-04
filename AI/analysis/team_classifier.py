"""
FootVision AI — Team Jersey Classification Module
Script: team_classifier.py

PURPOSE
-------
Classifies detected players into Team A (Blue) or Team B (Red),
or identifies Goalkeepers based on jersey-region color feature extraction.

KEY FEATURES
------------
1. Upper-torso region isolation (excludes head, legs, shorts, and background).
2. Grass, skin, and shadow pixel filtering via HSV segmentation.
3. Dominant kit color extraction in CIE-Lab color space (perceptually uniform).
4. Unsupervised clustering (K-Means / Centroid distance) with pure NumPy fallback.
5. Track-level temporal smoothing to ensure consistent team identity across frames.
6. Support for goalkeeper differentiation and explainable confidence scoring.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class TeamClassifier:
    """
    Jersey color feature extractor and team assignment classifier.
    """

    def __init__(
        self,
        history_window: int = 30,
        min_cluster_samples: int = 6,
    ) -> None:
        self.history_window = history_window
        self.min_cluster_samples = min_cluster_samples

        # Track history: track_id -> list of raw Lab color vectors
        self.track_color_history: Dict[int, List[np.ndarray]] = {}
        # Track smoothed assignment: track_id -> {"team": str, "conf": float, "is_gk": bool}
        self.track_team_cache: Dict[int, Dict] = {}

        # Centroids in Lab color space: [L, a, b]
        self.centroid_a: Optional[np.ndarray] = None
        self.centroid_b: Optional[np.ndarray] = None
        self.is_calibrated: bool = False

        # Configurable team labels
        self.team_a_name: str = "TEAM A"
        self.team_b_name: str = "TEAM B"

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def extract_jersey_feature(
        self,
        frame: np.ndarray,
        xyxy: Tuple[int, int, int, int],
    ) -> Optional[np.ndarray]:
        """
        Extract the dominant kit color vector in Lab color space for a player bbox.

        Steps:
        1. Crop upper-torso region (15% to 50% height, 20% to 80% width).
        2. Convert crop to HSV to create a clean mask excluding:
           - Green grass (pitch background leaks)
           - Skin tones (neck, arms, face)
           - Deep shadows / pitch lines
        3. Convert filtered pixels to CIE-Lab space and compute the median/mean.
        """
        x1, y1, x2, y2 = xyxy
        h, w = y2 - y1, x2 - x1
        if h < 20 or w < 10:
            return None

        # Torso bounding box
        tx1 = max(0, int(x1 + 0.20 * w))
        tx2 = min(frame.shape[1], int(x2 - 0.20 * w))
        ty1 = max(0, int(y1 + 0.15 * h))
        ty2 = min(frame.shape[0], int(y1 + 0.52 * h))

        if tx2 <= tx1 or ty2 <= ty1:
            return None

        torso_crop = frame[ty1:ty2, tx1:tx2]
        if torso_crop.size == 0:
            return None

        # Convert to HSV for masking
        hsv = cv2.cvtColor(torso_crop, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)

        # 1. Mask out green pitch grass (H: 35-85, S >= 35, V >= 25)
        grass_mask = (h_channel >= 35) & (h_channel <= 85) & (s_channel >= 35) & (v_channel >= 25)

        # 2. Mask out skin tones (H: 0-25 or 160-180, S: 25-180, V: 40-240)
        skin_mask = ((h_channel <= 25) | (h_channel >= 160)) & (s_channel >= 25) & (s_channel <= 180) & (v_channel >= 40)

        # 3. Mask out extreme shadows / black clips
        shadow_mask = v_channel < 25

        # 4. Valid fabric pixels
        valid_mask = ~(grass_mask | skin_mask | shadow_mask)

        # If too strict and almost all pixels removed, fallback to inner torso without grass mask
        if np.count_nonzero(valid_mask) < 25:
            valid_mask = ~shadow_mask
            if np.count_nonzero(valid_mask) < 15:
                # Fallback to whole torso
                valid_mask = np.ones((torso_crop.shape[0], torso_crop.shape[1]), dtype=bool)

        # Convert crop to CIE-Lab for perceptual color measurement
        lab_crop = cv2.cvtColor(torso_crop, cv2.COLOR_BGR2Lab)
        jersey_pixels = lab_crop[valid_mask]

        if len(jersey_pixels) == 0:
            return None

        # Return median color vector [L, a, b]
        median_lab = np.median(jersey_pixels, axis=0).astype(np.float32)
        return median_lab

    def update_and_classify(
        self,
        frame: np.ndarray,
        track_id: int,
        xyxy: Tuple[int, int, int, int],
        is_referee: bool = False,
    ) -> Dict:
        """
        Extract features, update track history, and return team classification.
        """
        if is_referee:
            return {
                "team": "REFEREE",
                "label": "REFEREE",
                "confidence": 0.95,
                "color_code": "yellow",
                "is_gk": False,
            }

        feat = self.extract_jersey_feature(frame, xyxy)
        if feat is not None:
            if track_id not in self.track_color_history:
                self.track_color_history[track_id] = []
            self.track_color_history[track_id].append(feat)
            if len(self.track_color_history[track_id]) > self.history_window:
                self.track_color_history[track_id].pop(0)

        # Calibrate or update centroids if enough samples collected
        if not self.is_calibrated:
            self._try_calibrate()

        # If calibrated, classify against centroids
        if self.is_calibrated and track_id in self.track_color_history and len(self.track_color_history[track_id]) > 0:
            avg_feat = np.mean(self.track_color_history[track_id], axis=0)
            dist_a = float(np.linalg.norm(avg_feat - self.centroid_a))
            dist_b = float(np.linalg.norm(avg_feat - self.centroid_b))

            total_dist = dist_a + dist_b + 1e-6
            conf_a = 1.0 - (dist_a / total_dist)
            conf_b = 1.0 - (dist_b / total_dist)

            # Check if goalkeeper outlier (significantly distinct from both centroids)
            is_gk = (dist_a > 45.0 and dist_b > 45.0)

            if dist_a < dist_b:
                assigned_team = "Team A"
                confidence = round(conf_a, 2)
                color_code = "blue"
            else:
                assigned_team = "Team B"
                confidence = round(conf_b, 2)
                color_code = "red"

            res = {
                "team": assigned_team,
                "label": f"{'GK ' if is_gk else ''}{assigned_team}",
                "confidence": confidence,
                "color_code": color_code,
                "is_gk": is_gk,
            }
            self.track_team_cache[track_id] = res
            return res

        # Fallback if uncalibrated or no feature yet
        cached = self.track_team_cache.get(track_id)
        if cached:
            return cached

        # Unclassified / initial
        return {
            "team": "UNKNOWN",
            "label": f"Player #{track_id}",
            "confidence": 0.50,
            "color_code": "gray",
            "is_gk": False,
        }

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _try_calibrate(self) -> None:
        """
        Unsupervised 2-cluster separation of collected player jersey colors.
        Uses pure NumPy K-Means so there are no hard dependencies.
        """
        samples = []
        for tid, history in self.track_color_history.items():
            if len(history) >= 1:
                samples.append(np.mean(history, axis=0))

        if len(samples) < self.min_cluster_samples:
            return

        X = np.array(samples, dtype=np.float32)

        # Check that samples have sufficient color variation (two distinct kit colors)
        dists = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=-1)
        max_dist = float(np.max(dists)) if len(dists) > 0 else 0.0
        if max_dist < 20.0:
            # Not enough color diversity yet (all from same team), wait for opponent
            return

        # Pure NumPy 2-means clustering
        c1, c2 = self._kmeans_2(X)
        if c1 is not None and c2 is not None:
            # Ensure centroids are meaningfully separated
            centroid_sep = float(np.linalg.norm(c1 - c2))
            if centroid_sep >= 15.0:
                # Sort centroids so Team A and Team B have stable assignment
                # Sort by 'b' channel in Lab (lower b = bluer, higher b = yellower/redder)
                if c1[2] < c2[2]:  # c1 is bluer
                    self.centroid_a = c1
                    self.centroid_b = c2
                else:
                    self.centroid_a = c2
                    self.centroid_b = c1

                self.is_calibrated = True

    @staticmethod
    def _kmeans_2(X: np.ndarray, max_iter: int = 15) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Lightweight robust 2-means clustering in NumPy."""
        if len(X) < 2:
            return None, None

        # Initialize with two most distant points
        dists = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=-1)
        i, j = np.unravel_index(np.argmax(dists), dists.shape)
        c1, c2 = X[i].copy(), X[j].copy()

        for _ in range(max_iter):
            d1 = np.linalg.norm(X - c1, axis=1)
            d2 = np.linalg.norm(X - c2, axis=1)
            cluster1 = X[d1 <= d2]
            cluster2 = X[d2 < d1]

            if len(cluster1) == 0 or len(cluster2) == 0:
                break

            new_c1 = np.mean(cluster1, axis=0)
            new_c2 = np.mean(cluster2, axis=0)

            if np.allclose(c1, new_c1, atol=0.5) and np.allclose(c2, new_c2, atol=0.5):
                break

            c1, c2 = new_c1, new_c2

        return c1, c2
