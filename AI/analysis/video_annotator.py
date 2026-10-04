"""
FootVision AI — Production Visual Annotator
Script: video_annotator.py

PURPOSE
-------
Renders high-definition visual overlays on match video frames:
1. Team A players: Blue bounding boxes, blue headers ("TEAM A | Player #ID").
2. Team B players: Red bounding boxes, red headers ("TEAM B | Player #ID").
3. Referee: Yellow bounding box, yellow header ("REFEREE").
4. Ball: Green glowing circle / bullseye ("BALL").
5. Unknown: Neutral gray headers.
6. Player movement trails (fading path lines).
7. Top match analytics HUD with live counts.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


# =============================================================================
# COLOR PALETTE (BGR format for OpenCV)
# =============================================================================
PALETTE = {
    "team_a": {
        "box": (245, 130, 30),       # Blue (BGR: B=245, G=130, R=30)
        "header_bg": (180, 80, 15),
        "text": (255, 255, 255),
        "name": "TEAM A",
    },
    "team_b": {
        "box": (35, 35, 235),        # Red (BGR: B=35, G=35, R=235)
        "header_bg": (20, 20, 160),
        "text": (255, 255, 255),
        "name": "TEAM B",
    },
    "referee": {
        "box": (0, 215, 255),        # Yellow/Amber (BGR: B=0, G=215, R=255)
        "header_bg": (0, 140, 180),
        "text": (10, 10, 10),
        "name": "REFEREE",
    },
    "ball": {
        "box": (50, 255, 80),        # Vibrant Green (BGR: B=50, G=255, R=80)
        "glow": (100, 255, 130),
        "text": (255, 255, 255),
        "name": "BALL",
    },
    "unknown": {
        "box": (160, 160, 160),      # Neutral gray
        "header_bg": (90, 90, 90),
        "text": (255, 255, 255),
        "name": "PLAYER",
    },
}

FONT = cv2.FONT_HERSHEY_SIMPLEX


class VideoAnnotator:
    """
    Renders visual overlays for football tracking.
    """

    def __init__(
        self,
        show_boxes: bool = True,
        show_ids: bool = True,
        show_referee: bool = True,
        show_ball: bool = True,
        show_trails: bool = True,
        show_hud: bool = True,
    ) -> None:
        self.show_boxes = show_boxes
        self.show_ids = show_ids
        self.show_referee = show_referee
        self.show_ball = show_ball
        self.show_trails = show_trails
        self.show_hud = show_hud

        # Trail history: track_id -> list of bottom-center foot coordinates
        self.trails: Dict[int, List[Tuple[int, int]]] = {}
        self.max_trail_len = 18

    def annotate_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        tracks: List[Dict],
        ball_info: Optional[Dict],
        team_stats: Optional[Dict] = None,
        proc_fps: float = 0.0,
    ) -> np.ndarray:
        """
        Draw all tracking visual overlays onto the frame in-place.
        """
        out = frame.copy()

        # 1. Draw player trails (beneath bounding boxes)
        if self.show_trails:
            self._update_and_draw_trails(out, tracks)

        # 2. Draw players and referee
        team_a_count = 0
        team_b_count = 0
        ref_count = 0

        for tr in tracks:
            xyxy = tr["xyxy"]
            tid = tr["track_id"]
            team_info = tr.get("classification", {})
            team = team_info.get("team", "UNKNOWN")
            is_ref = tr.get("is_referee", False) or (team == "REFEREE")
            conf = tr.get("conf", 0.8)

            if is_ref:
                ref_count += 1
                if not self.show_referee:
                    continue
                color_cfg = PALETTE["referee"]
                label = "REFEREE"
            elif team == "Team A":
                team_a_count += 1
                color_cfg = PALETTE["team_a"]
                is_gk = team_info.get("is_gk", False)
                prefix = "TEAM A (GK)" if is_gk else "TEAM A"
                label = f"{prefix} | Player #{tid}"
            elif team == "Team B":
                team_b_count += 1
                color_cfg = PALETTE["team_b"]
                is_gk = team_info.get("is_gk", False)
                prefix = "TEAM B (GK)" if is_gk else "TEAM B"
                label = f"{prefix} | Player #{tid}"
            else:
                color_cfg = PALETTE["unknown"]
                label = f"Player #{tid}"

            if self.show_boxes:
                self._draw_player_box(out, xyxy, color_cfg, label, conf)

        # 3. Draw ball overlay
        ball_detected = False
        if self.show_ball and ball_info and ball_info.get("detected"):
            ball_detected = True
            self._draw_ball(out, ball_info)

        # 4. Draw HUD banner
        if self.show_hud:
            self._draw_hud(
                out,
                frame_idx=frame_idx,
                team_a_count=team_a_count,
                team_b_count=team_b_count,
                ref_count=ref_count,
                ball_detected=ball_detected,
                fps=proc_fps,
            )

        return out

    def _draw_player_box(
        self,
        img: np.ndarray,
        xyxy: Tuple[int, int, int, int],
        color_cfg: Dict,
        label: str,
        conf: float,
    ) -> None:
        """
        Draws sleek rounded corner box and modern header badge with anti-aliasing.
        """
        x1, y1, x2, y2 = xyxy
        color = color_cfg["box"]
        header_bg = color_cfg["header_bg"]
        text_color = color_cfg["text"]

        # Main bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2, lineType=cv2.LINE_AA)

        # Corner brackets for premium visual aesthetics
        corner_len = min(14, max(6, (x2 - x1) // 4))
        # Top-left
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 3, cv2.LINE_AA)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 3, cv2.LINE_AA)
        # Top-right
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), (255, 255, 255), 3, cv2.LINE_AA)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), (255, 255, 255), 3, cv2.LINE_AA)
        # Bottom-left
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), (255, 255, 255), 3, cv2.LINE_AA)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), (255, 255, 255), 3, cv2.LINE_AA)
        # Bottom-right
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 3, cv2.LINE_AA)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 3, cv2.LINE_AA)

        # Header badge above the box
        if self.show_ids:
            scale = 0.44
            thick = 1
            (tw, th), baseline = cv2.getTextSize(label, FONT, scale, thick)
            badge_y2 = max(y1 - 2, th + 6)
            badge_y1 = badge_y2 - th - baseline - 4
            badge_x1 = x1
            badge_x2 = x1 + tw + 10

            # Badge background
            cv2.rectangle(img, (badge_x1, badge_y1), (badge_x2, badge_y2), header_bg, cv2.FILLED)
            cv2.rectangle(img, (badge_x1, badge_y1), (badge_x2, badge_y2), color, 1, cv2.LINE_AA)

            # Badge text
            cv2.putText(
                img,
                label,
                (badge_x1 + 5, badge_y2 - baseline - 1),
                FONT,
                scale,
                text_color,
                thick,
                cv2.LINE_AA,
            )

    def _draw_ball(self, img: np.ndarray, ball_info: Dict) -> None:
        """
        Draws distinctive green bullseye with glowing ring and label.
        """
        center = ball_info.get("center")
        if center is None:
            xyxy = ball_info.get("xyxy")
            if xyxy:
                center = ((xyxy[0] + xyxy[2]) // 2, (xyxy[1] + xyxy[3]) // 2)

        if center is None:
            return

        cx, cy = center
        conf = ball_info.get("confidence", 0.0)
        is_interp = ball_info.get("is_interpolated", False)

        # Outer pulse ring
        cv2.circle(img, (cx, cy), 14, PALETTE["ball"]["glow"], 2, lineType=cv2.LINE_AA)
        # Solid core dot
        cv2.circle(img, (cx, cy), 6, PALETTE["ball"]["box"], cv2.FILLED, lineType=cv2.LINE_AA)

        # Ball label
        lbl = f"BALL{' ~' if is_interp else ''}"
        (tw, th), baseline = cv2.getTextSize(lbl, FONT, 0.42, 1)
        bx1 = cx - tw // 2 - 4
        by2 = cy - 16
        by1 = by2 - th - 4
        cv2.rectangle(img, (bx1, by1), (bx1 + tw + 8, by2), (20, 60, 20), cv2.FILLED)
        cv2.rectangle(img, (bx1, by1), (bx1 + tw + 8, by2), PALETTE["ball"]["box"], 1, cv2.LINE_AA)
        cv2.putText(
            img,
            lbl,
            (bx1 + 4, by2 - 2),
            FONT,
            0.42,
            PALETTE["ball"]["text"],
            1,
            cv2.LINE_AA,
        )

    def _update_and_draw_trails(self, img: np.ndarray, tracks: List[Dict]) -> None:
        """
        Maintains trail coordinates and draws fading gradient trail lines.
        """
        active_ids = set()
        for tr in tracks:
            tid = tr["track_id"]
            active_ids.add(tid)
            x1, y1, x2, y2 = tr["xyxy"]
            foot = ((x1 + x2) // 2, y2)

            if tid not in self.trails:
                self.trails[tid] = []
            self.trails[tid].append(foot)
            if len(self.trails[tid]) > self.max_trail_len:
                self.trails[tid].pop(0)

            pts = self.trails[tid]
            if len(pts) >= 2:
                team = tr.get("classification", {}).get("team", "UNKNOWN")
                is_ref = tr.get("is_referee", False) or (team == "REFEREE")
                if is_ref:
                    col = PALETTE["referee"]["box"]
                elif team == "Team A":
                    col = PALETTE["team_a"]["box"]
                elif team == "Team B":
                    col = PALETTE["team_b"]["box"]
                else:
                    col = PALETTE["unknown"]["box"]

                for i in range(len(pts) - 1):
                    alpha = (i + 1) / len(pts)
                    thick = max(1, int(alpha * 2))
                    cv2.line(img, pts[i], pts[i + 1], col, thick, lineType=cv2.LINE_AA)

        # Cleanup disappeared tracks
        dead_ids = [tid for tid in self.trails if tid not in active_ids]
        for tid in dead_ids:
            del self.trails[tid]

    def _draw_hud(
        self,
        img: np.ndarray,
        frame_idx: int,
        team_a_count: int,
        team_b_count: int,
        ref_count: int,
        ball_detected: bool,
        fps: float,
    ) -> None:
        """
        Draws clean, modern HUD bar on top edge of video frame.
        """
        fh, fw = img.shape[:2]
        hud_h = 42

        # Semi-transparent dark banner
        banner = img[:hud_h, :].copy()
        cv2.rectangle(banner, (0, 0), (fw, hud_h), (8, 14, 24), cv2.FILLED)
        cv2.addWeighted(banner, 0.78, img[:hud_h, :], 0.22, 0, img[:hud_h, :])
        cv2.line(img, (0, hud_h), (fw, hud_h), (30, 45, 70), 1, cv2.LINE_AA)

        # Brand
        cv2.putText(img, "FootVision AI", (14, 26), FONT, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "· Visual Tracking", (135, 26), FONT, 0.44, (120, 160, 200), 1, cv2.LINE_AA)

        # Team A badge
        cv2.circle(img, (310, 22), 6, PALETTE["team_a"]["box"], -1, cv2.LINE_AA)
        cv2.putText(img, f"Team A: {team_a_count}", (322, 26), FONT, 0.46, (230, 240, 255), 1, cv2.LINE_AA)

        # Team B badge
        cv2.circle(img, (440, 22), 6, PALETTE["team_b"]["box"], -1, cv2.LINE_AA)
        cv2.putText(img, f"Team B: {team_b_count}", (452, 26), FONT, 0.46, (255, 230, 230), 1, cv2.LINE_AA)

        # Referee
        cv2.circle(img, (570, 22), 6, PALETTE["referee"]["box"], -1, cv2.LINE_AA)
        cv2.putText(img, f"Ref: {ref_count}", (582, 26), FONT, 0.46, (255, 255, 220), 1, cv2.LINE_AA)

        # Ball Status
        ball_col = PALETTE["ball"]["box"] if ball_detected else (100, 100, 100)
        ball_txt = "Ball: Active" if ball_detected else "Ball: Searching"
        cv2.circle(img, (670, 22), 6, ball_col, -1, cv2.LINE_AA)
        cv2.putText(img, ball_txt, (682, 26), FONT, 0.46, (200, 240, 200) if ball_detected else (140, 150, 160), 1, cv2.LINE_AA)

        # Frame counter & FPS
        fps_txt = f"Frame {frame_idx} | {fps:.1f} FPS"
        (tw, th), _ = cv2.getTextSize(fps_txt, FONT, 0.42, 1)
        cv2.putText(img, fps_txt, (fw - tw - 16, 26), FONT, 0.42, (180, 190, 210), 1, cv2.LINE_AA)
