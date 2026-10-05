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
        interactive:  bool = False,
    ):
        self.video_path   = video_path
        self.polygon_path = polygon_path
        self.margin       = margin
        self.show_overlay = show_overlay
        self.debug        = debug
        self.interactive  = interactive

        # numpy array of shape (N, 2), dtype int32
        # Each row is one [x, y] vertex of the pitch polygon.
        self.polygon: Optional[np.ndarray] = None

        self._load_or_create_polygon()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    @staticmethod
    def is_in_overlay_zone(xyxy: Tuple[int, int, int, int], frame_shape: Tuple[int, int]) -> bool:
        """
        Check if a bounding box falls within static on-screen overlay zones:
        - Top-left & top-right broadcast scoreboards/banners
        - Bottom corners TV channel watermarks / broadcast station logos
        """
        fh, fw = frame_shape[:2]
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # Top score bug zone: y < 14% of height, and either left or right portion
        if y1 < fh * 0.14 and (x1 < fw * 0.45 or x2 > fw * 0.65):
            return True
        if cy < fh * 0.12 and (cx < fw * 0.45 or cx > fw * 0.65):
            return True

        # Bottom-left watermark / logo zone: y > 84% and x < 24%
        if y2 > fh * 0.84 and x1 < fw * 0.24:
            return True

        # Bottom-right watermark / logo zone: y > 84% and x > 76%
        if y2 > fh * 0.84 and x2 > fw * 0.76:
            return True

        return False

    @staticmethod
    def is_valid_person_box(xyxy: Tuple[int, int, int, int], frame_shape: Tuple[int, int]) -> bool:
        """
        Filter out non-human bounding boxes (TV logos, graphic banners, square icons):
        - Humans are vertically proportioned (height > width).
        - Height must be at least 18px and width at least 7px.
        - Aspect ratio (height / width) must typically be between 1.10 and 4.8.
        - Height should not exceed 45% of the frame (rejects giant false detections).
        """
        fh, fw = frame_shape[:2]
        x1, y1, x2, y2 = xyxy
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)

        if h < 18 or w < 7:
            return False
        if h > fh * 0.45 or w > fw * 0.35:
            return False

        aspect_ratio = h / float(w)
        if aspect_ratio < 1.10 or aspect_ratio > 4.8:
            return False

        return True

    def filter(self, detections: List[Dict], frame_shape: Optional[Tuple[int, int]] = None) -> List[Dict]:
        """
        Keep only valid person detections whose feet are on the pitch
        and are not on-screen logos or broadcast overlays.
        """
        filtered = []
        for det in detections:
            xyxy = det["xyxy"]

            # Filter broadcast overlays and watermarks
            if frame_shape is not None:
                if self.is_in_overlay_zone(xyxy, frame_shape):
                    det["on_pitch"] = False
                    if self.debug:
                        filtered.append(det)
                    continue

                if not self.is_valid_person_box(xyxy, frame_shape):
                    det["on_pitch"] = False
                    if self.debug:
                        filtered.append(det)
                    continue

            # Pitch polygon check
            if self.polygon is not None:
                foot = self._foot_point(xyxy)
                if self._is_on_pitch(foot):
                    det["on_pitch"] = True
                    filtered.append(det)
                else:
                    det["on_pitch"] = False
                    if self.debug:
                        filtered.append(det)
            else:
                det["on_pitch"] = True
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

    @staticmethod
    def _is_dummy_polygon(pts: np.ndarray) -> bool:
        """
        Check if the polygon is just a placeholder rectangle covering the full frame.
        """
        if len(pts) != 4:
            return False
        xs = pts[:, 0]
        ys = pts[:, 1]
        # If vertices are all near (0, 0) and image corners with min(xs) == 0 and min(ys) == 0
        if int(np.min(xs)) == 0 and int(np.min(ys)) == 0 and int(np.max(xs)) == int(np.max(ys)):
            return True
        return False

    def auto_detect_pitch(self, frame: Optional[np.ndarray] = None) -> bool:
        """
        Automatically segment and detect the green playing pitch from video frames:
        1. Samples frames to compute dominant green grass HSV distribution.
        2. Morphologically closes to bridge white pitch lines and players.
        3. Computes convex hull of the primary pitch region.
        """
        if frame is None:
            if not os.path.exists(self.video_path):
                return False
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return False

        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Standard broadcast football pitch green grass profile
        lower_green = np.array([30, 35, 35])
        upper_green = np.array([85, 255, 255])
        grass_mask = cv2.inRange(hsv, lower_green, upper_green)

        # Morphological closing to fill players, lines, and textures inside pitch
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        closed = cv2.morphologyEx(grass_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < 0.20 * (w * h):
            return False

        hull = cv2.convexHull(largest)
        # Squeeze to Nx2
        pts = hull.reshape(-1, 2).astype(np.int32)
        if len(pts) < 3:
            return False

        self.polygon = pts
        print(f"[PitchFilter]  Automatic pitch contour detected ({len(pts)} vertices, {area / (w * h) * 100:.1f}% field area)")
        return True

    def _load_or_create_polygon(self) -> None:
        """
        Load the polygon from JSON if it exists and is valid.
        Otherwise, auto-detect from video, with interactive setup as manual fallback.
        """
        if os.path.exists(self.polygon_path):
            if self._load_polygon():
                return

        # Attempt automatic pitch detection first (works headless & robustly)
        if self.auto_detect_pitch():
            return

        if self.interactive:
            print("[PitchFilter] No saved polygon found — starting interactive setup.")
            self._interactive_setup()
        else:
            print("[PitchFilter]  No manual polygon and auto-detection failed — filter disabled.")

    def _load_polygon(self) -> bool:
        """Load polygon vertices from a JSON file. Returns True if valid custom polygon."""
        try:
            with open(self.polygon_path, "r") as f:
                data = json.load(f)
            pts = np.array(data["polygon"], dtype=np.int32)
            if len(pts) < 3:
                return False
            if self._is_dummy_polygon(pts):
                print(f"[PitchFilter]  Dummy placeholder polygon detected at {self.polygon_path} — overriding with auto-detection.")
                return False
            self.polygon = pts
            print(f"[PitchFilter]  Polygon loaded from {self.polygon_path} ({len(pts)} vertices)")
            return True
        except Exception as e:
            print(f"[PitchFilter]  Error reading polygon from {self.polygon_path}: {e}")
            return False

    def _save_polygon(self) -> None:
        """Persist the current polygon to JSON."""
        if self.polygon is None:
            return
        os.makedirs(os.path.dirname(self.polygon_path), exist_ok=True)
        with open(self.polygon_path, "w") as f:
            json.dump({"polygon": self.polygon.tolist()}, f, indent=2)
        print(f"[PitchFilter]  Polygon saved to {self.polygon_path}")

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
