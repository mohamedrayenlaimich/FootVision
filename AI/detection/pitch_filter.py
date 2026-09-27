"""
FootVision AI — M1: Player Detection
Module: pitch_filter.py

PURPOSE
-------
Filters YOLO person detections to keep only people whose feet land
inside the defined pitch polygon.  This removes spectators, coaches,
and substitutes sitting in the stands while retaining players and
touchline referees.

DESIGN PRINCIPLES
-----------------
1. Modular — this file is a self-contained class.  player_detector.py
   imports it; nothing else needs to change when we later upgrade to
   automatic pitch segmentation.

2. Interactive setup — on first run the user clicks the four (or more)
   corners of the pitch on the first video frame.  The polygon is saved
   to a JSON file so subsequent runs load it instantly.

3. Bottom-center heuristic — we test the foot point of each bounding
   box, not the box center or box area.  See PitchFilter.is_on_pitch()
   for the full explanation.

4. CPU-only — no GPU dependencies.  Uses only NumPy + OpenCV.

USAGE
-----
    from AI.detection.pitch_filter import PitchFilter

    pf = PitchFilter(video_path="Data/raw/test.mp4",
                     polygon_path="Data/processed/pitch_polygon.json")

    # First run: interactive window opens so you can click the pitch corners.
    # Subsequent runs: loads saved polygon automatically.

    filtered = pf.filter(detections)
"""

import json
import os
from typing import List, Dict, Tuple, Optional

import cv2
import numpy as np


# =============================================================================
# CONSTANTS
# =============================================================================

# Colour scheme for the polygon overlay drawn on the frame
POLYGON_COLOR       = (0, 200, 255)   # BGR: amber/yellow
POLYGON_ALPHA       = 0.18            # Transparency of the filled overlay (0=invisible, 1=opaque)
POLYGON_LINE_COLOR  = (0, 200, 255)
POLYGON_LINE_THICK  = 2

# Foot-point marker (drawn in debug mode)
FOOT_COLOR_INSIDE   = (0, 255, 100)   # Green — person is on pitch
FOOT_COLOR_OUTSIDE  = (0, 0, 255)     # Red   — person is off pitch
FOOT_RADIUS         = 4

# Interactive setup window
SETUP_WINDOW = "FootVision — Define Pitch Region  (click corners, ENTER to confirm, R to reset)"


# =============================================================================
# CLASS
# =============================================================================

class PitchFilter:
    """
    Pitch-region filter for YOLO person detections.

    Workflow
    --------
    1. On first instantiation (no saved polygon), grab the first frame of
       the video and open an interactive window where the user clicks the
       pitch boundary corners.  The polygon is saved to JSON.

    2. On all subsequent runs, the saved polygon is loaded from JSON —
       no user interaction needed.

    3. Each call to `filter(detections)` tests every detection's foot
       point against the polygon using cv2.pointPolygonTest and returns
       only those that are inside (or on the boundary of) the polygon.

    Parameters
    ----------
    video_path   : Path to the input video.  Used only to grab the first
                   frame for the interactive setup.
    polygon_path : Path to the JSON file where the polygon is saved/loaded.
    margin       : Extra pixels of tolerance added around the polygon edge.
                   Positive value → keeps players slightly outside the line.
                   Useful for players standing right on the touchline.
    show_overlay : If True, draw the pitch polygon overlay on every frame
                   when draw_overlay() is called.
    debug        : If True, draw foot-points coloured green/red to show
                   which detections pass the filter.
    """

    def __init__(
        self,
        video_path:   str,
        polygon_path: str,
        margin:       int  = 15,
        show_overlay: bool = True,
        debug:        bool = False,
    ):
        self.video_path   = video_path
        self.polygon_path = polygon_path
        self.margin       = margin
        self.show_overlay = show_overlay
        self.debug        = debug

        # numpy array of shape (N, 2), dtype int32
        # Each row is one [x, y] vertex of the pitch polygon.
        self.polygon: Optional[np.ndarray] = None

        self._load_or_create_polygon()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def filter(self, detections: List[Dict]) -> List[Dict]:
        """
        Keep only detections whose foot point is inside the pitch polygon.

        Parameters
        ----------
        detections : List of dicts from detect_players(), each with key 'xyxy'.

        Returns
        -------
        Filtered list — same dict format, only on-pitch detections retained.
        """
        if self.polygon is None:
            # No polygon defined — pass everything through (safe fallback)
            return detections

        filtered = []
        for det in detections:
            foot = self._foot_point(det["xyxy"])
            if self._is_on_pitch(foot):
                det["on_pitch"] = True
                filtered.append(det)
            else:
                det["on_pitch"] = False
                # Keep in list only if debug=True so we can visualise rejects
                if self.debug:
                    filtered.append(det)

        return filtered

    def draw_overlay(self, frame: np.ndarray) -> None:
        """
        Draw the pitch polygon and (optionally) foot points onto frame in-place.

        Call this after filter() so foot-point colours reflect the latest pass/fail.

        Parameters
        ----------
        frame : BGR image array from cv2.  Modified in-place.
        """
        if self.polygon is None or not self.show_overlay:
            return

        pts = self.polygon.reshape((-1, 1, 2))

        # ── Semi-transparent filled region ───────────────────────────────────
        # OpenCV has no native alpha drawing — we blend a filled copy.
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], POLYGON_COLOR)
        cv2.addWeighted(overlay, POLYGON_ALPHA, frame, 1 - POLYGON_ALPHA, 0, frame)

        # ── Polygon outline ───────────────────────────────────────────────────
        cv2.polylines(frame, [pts], isClosed=True, color=POLYGON_LINE_COLOR, thickness=POLYGON_LINE_THICK)

    def draw_foot_points(self, frame: np.ndarray, detections: List[Dict]) -> None:
        """
        Draw a small dot at each detection's foot point, coloured by filter result.
        Only useful in debug mode for diagnosing edge cases.
        """
        for det in detections:
            foot  = self._foot_point(det["xyxy"])
            color = FOOT_COLOR_INSIDE if det.get("on_pitch", True) else FOOT_COLOR_OUTSIDE
            cv2.circle(frame, foot, FOOT_RADIUS, color, -1)

    def is_active(self) -> bool:
        """Return True if a polygon has been defined."""
        return self.polygon is not None

    # =========================================================================
    # CORE LOGIC
    # =========================================================================

    @staticmethod
    def _foot_point(xyxy: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Compute the bottom-center point of a bounding box.

        WHY BOTTOM-CENTER?
        ------------------
        A person's bounding box spans from the top of their head (y1) to
        the bottom of their feet (y2), and from their left side (x1) to
        their right (x2).

        The CENTER of the box ((x1+x2)/2, (y1+y2)/2) is roughly at the
        player's waist — which is fine most of the time but causes problems
        near the pitch boundary:

          • A player standing just inside the touchline has their upper body
            partially over the out-of-bounds area — box center might fall
            outside the pitch polygon even though they are clearly playing.

          • A spectator leaning over the advertising hoardings might have
            their box center inside the pitch if the polygon is loose.

        BOTTOM-CENTER ((x1+x2)/2, y2) corresponds to where the person's
        feet touch the ground — which is exactly the point we care about
        for determining whether they are standing ON the pitch surface.

        This is the same heuristic used in most sports analytics pipelines
        before proper camera calibration / homography is available.

        Parameters
        ----------
        xyxy : (x1, y1, x2, y2) bounding box in pixel coordinates.

        Returns
        -------
        (cx, y2) — bottom-center pixel coordinate.
        """
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) // 2
        return (cx, y2)

    def _is_on_pitch(self, point: Tuple[int, int]) -> bool:
        """
        Test whether a pixel point is inside or on the boundary of the polygon.

        Uses cv2.pointPolygonTest which returns:
            +distance  if inside
             0         if exactly on boundary
            -distance  if outside

        We keep points where the result >= -self.margin, which allows a
        configurable tolerance band around the pitch edge.  This prevents
        players standing right on the touchline from being wrongly rejected.

        Parameters
        ----------
        point  : (x, y) pixel to test.

        Returns
        -------
        True if the point is within the pitch (+ margin), False otherwise.
        """
        dist = cv2.pointPolygonTest(self.polygon, (float(point[0]), float(point[1])), measureDist=True)
        return dist >= -self.margin

    # =========================================================================
    # POLYGON SETUP — LOAD / SAVE / INTERACTIVE
    # =========================================================================

    def _load_or_create_polygon(self) -> None:
        """
        Load the polygon from JSON if it exists, otherwise run interactive setup.
        """
        if os.path.exists(self.polygon_path):
            self._load_polygon()
        else:
            print("[PitchFilter] No saved polygon found — starting interactive setup.")
            self._interactive_setup()

    def _load_polygon(self) -> None:
        """Load polygon vertices from a JSON file."""
        with open(self.polygon_path, "r") as f:
            data = json.load(f)
        pts = np.array(data["polygon"], dtype=np.int32)
        if len(pts) < 3:
            print("[PitchFilter] ⚠️  Saved polygon has fewer than 3 points — ignoring.")
            self.polygon = None
            return
        self.polygon = pts
        print(f"[PitchFilter] ✅ Polygon loaded from {self.polygon_path}  ({len(pts)} vertices)")

    def _save_polygon(self) -> None:
        """Persist the current polygon to JSON."""
        os.makedirs(os.path.dirname(self.polygon_path), exist_ok=True)
        with open(self.polygon_path, "w") as f:
            json.dump({"polygon": self.polygon.tolist()}, f, indent=2)
        print(f"[PitchFilter] ✅ Polygon saved to {self.polygon_path}")

    def _interactive_setup(self) -> None:
        """
        Open the first video frame in a window and let the user click the
        pitch boundary corners to define the polygon.

        INSTRUCTIONS shown in window title:
            Left-click  — add a vertex
            R           — reset (clear all points)
            ENTER       — confirm and save
            ESC         — skip (no filter will be applied this run)

        The polygon does NOT need to be a perfect rectangle — you can click
        as many points as needed to follow the curved edges of the pitch.
        Typically 4–6 clicks are enough for a broadcast angle.
        """
        # ── Grab first frame ─────────────────────────────────────────────────
        cap = cv2.VideoCapture(self.video_path)
        ret, first_frame = cap.read()
        cap.release()

        if not ret:
            print("[PitchFilter] ⚠️  Could not read first frame — pitch filter disabled.")
            return

        frame_h, frame_w = first_frame.shape[:2]
        points: List[Tuple[int, int]] = []
        base_frame = first_frame.copy()   # clean copy to redraw on

        def _draw_state(img: np.ndarray) -> np.ndarray:
            """Render current click state onto a display copy."""
            display = img.copy()
            # Draw edges
            if len(points) >= 2:
                for i in range(len(points) - 1):
                    cv2.line(display, points[i], points[i + 1], POLYGON_LINE_COLOR, 2)
                # Close polygon preview once ≥3 points
                if len(points) >= 3:
                    cv2.line(display, points[-1], points[0], POLYGON_LINE_COLOR, 1)
                    # Semi-transparent fill preview
                    overlay = display.copy()
                    pts_arr = np.array(points, dtype=np.int32)
                    cv2.fillPoly(overlay, [pts_arr], POLYGON_COLOR)
                    cv2.addWeighted(overlay, POLYGON_ALPHA, display, 1 - POLYGON_ALPHA, 0, display)
            # Draw vertex dots + numbers
            for i, pt in enumerate(points):
                cv2.circle(display, pt, 6, POLYGON_LINE_COLOR, -1)
                cv2.putText(display, str(i + 1), (pt[0] + 8, pt[1] - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            # Instructions overlay
            instructions = [
                "DEFINE PITCH REGION",
                "Left-click: add corner",
                "R: reset all points",
                "ENTER: confirm & save",
                "ESC: skip (no filter)",
                f"Points: {len(points)}",
            ]
            y = 28
            for line in instructions:
                cv2.putText(display, line, (11, y + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
                cv2.putText(display, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 200), 1)
                y += 22
            return display

        def _on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                cv2.imshow(SETUP_WINDOW, _draw_state(base_frame))

        cv2.namedWindow(SETUP_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(SETUP_WINDOW, min(frame_w, 1280), min(frame_h, 720))
        cv2.setMouseCallback(SETUP_WINDOW, _on_mouse)
        cv2.imshow(SETUP_WINDOW, _draw_state(base_frame))

        print("\n" + "=" * 60)
        print("  PITCH SETUP — click the corners of the pitch")
        print("  Left-click : add vertex")
        print("  R          : reset")
        print("  ENTER      : confirm")
        print("  ESC        : skip (no filter this run)")
        print("=" * 60 + "\n")

        while True:
            key = cv2.waitKey(50) & 0xFF

            if key == 13:   # ENTER
                if len(points) < 3:
                    print("[PitchFilter] Need at least 3 points — keep clicking.")
                    continue
                self.polygon = np.array(points, dtype=np.int32)
                self._save_polygon()
                break

            elif key in (ord("r"), ord("R")):
                points.clear()
                cv2.imshow(SETUP_WINDOW, _draw_state(base_frame))
                print("[PitchFilter] Points reset.")

            elif key == 27:  # ESC
                print("[PitchFilter] Setup skipped — pitch filter disabled for this run.")
                self.polygon = None
                break

        cv2.destroyWindow(SETUP_WINDOW)
