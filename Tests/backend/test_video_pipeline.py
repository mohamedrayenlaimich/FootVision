import os
import sys
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure BackEnd is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "BackEnd")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "AI", "detection")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "AI", "analysis")))

from main import app
from team_classifier import TeamClassifier
from referee_detector import RefereeDetector
from ball_tracker import BallTracker
from pitch_filter import PitchFilter
from app.services.video_analysis_service import StaticAdFilter

client = TestClient(app)


def test_team_classifier_kmeans():
    """Test pure NumPy 2-means clustering for Team A vs Team B."""
    clf = TeamClassifier(min_cluster_samples=4)

    # Synthetic Team A: Blue kit in BGR (high Blue, low Red)
    frame_blue = np.zeros((100, 100, 3), dtype=np.uint8)
    frame_blue[:, :] = (220, 80, 20)  # BGR blue

    # Synthetic Team B: Red kit in BGR (high Red, low Blue)
    frame_red = np.zeros((100, 100, 3), dtype=np.uint8)
    frame_red[:, :] = (20, 20, 220)  # BGR red

    # Update history for several players
    for i in range(1, 5):
        clf.update_and_classify(frame_blue, track_id=i, xyxy=(10, 10, 90, 90))
    for j in range(5, 9):
        clf.update_and_classify(frame_red, track_id=j, xyxy=(10, 10, 90, 90))

    assert clf.is_calibrated is True
    assert clf.centroid_a is not None
    assert clf.centroid_b is not None

    # Test classification consistency
    res_blue = clf.update_and_classify(frame_blue, track_id=1, xyxy=(10, 10, 90, 90))
    res_red = clf.update_and_classify(frame_red, track_id=5, xyxy=(10, 10, 90, 90))

    assert res_blue["team"] != res_red["team"]
    assert res_blue["color_code"] in ("blue", "red")
    assert res_red["color_code"] in ("blue", "red")


def test_referee_detector():
    """Test referee detection via bright neon/yellow official shirt profile."""
    detector = RefereeDetector()

    # Synthetic neon yellow frame (BGR: Blue=0, Green=240, Red=240)
    frame_yellow = np.zeros((100, 100, 3), dtype=np.uint8)
    frame_yellow[:, :] = (0, 240, 240)

    is_ref, score = detector.is_referee_color(frame_yellow, (10, 10, 90, 90))
    assert is_ref is True
    assert score > 0.35

    # Outfield ordinary dark green frame
    frame_pitch = np.zeros((100, 100, 3), dtype=np.uint8)
    frame_pitch[:, :] = (40, 140, 40)
    is_ref_pitch, _ = detector.is_referee_color(frame_pitch, (10, 10, 90, 90))
    assert is_ref_pitch is False


def test_ball_tracker_temporal():
    """Test ball tracker detection update and temporal occlusion prediction."""
    tracker = BallTracker(max_missing_frames=4)

    # Frame 1: Detected at (100, 100)
    det1 = [{"xyxy": (90, 90, 110, 110), "conf": 0.85}]
    res1 = tracker.update(det1, [], (720, 1280))
    assert res1["detected"] is True
    assert res1["center"] == (100, 100)
    assert res1["is_interpolated"] is False

    # Frame 2: Detected at (110, 105) (moving right & slightly down)
    det2 = [{"xyxy": (100, 95, 120, 115), "conf": 0.88}]
    res2 = tracker.update(det2, [], (720, 1280))
    assert res2["detected"] is True
    assert res2["center"] == (110, 105)

    # Frame 3: Occluded (no detection) -> Kalman temporal prediction kicks in
    res3 = tracker.update([], [], (720, 1280))
    assert res3["detected"] is True
    assert res3["is_interpolated"] is True
    # Position should have moved according to velocity
    assert res3["center"][0] >= 110


def test_video_api_invalid_file():
    """Test video upload endpoint rejection of invalid file extensions."""
    files = {"file": ("test.txt", b"plain text content", "text/plain")}
    response = client.post("/api/v1/video/upload", files=files)
    assert response.status_code == 400
    assert "Invalid video format" in response.json()["detail"]


def test_video_api_status_not_found():
    """Test 404 for unknown video job ID."""
    response = client.get("/api/v1/video/status/non-existent-uuid-12345")
    assert response.status_code == 404


def test_single_goalkeeper_enforcement():
    """Verify that at most 1 goalkeeper is allowed per team and goalmouth player is chosen."""
    clf = TeamClassifier(min_cluster_samples=2)
    # Set mock calibrated centroids
    clf.centroid_a = np.array([50.0, 10.0, -40.0], dtype=np.float32)  # Blue
    clf.centroid_b = np.array([50.0, 50.0, 30.0], dtype=np.float32)   # Red
    clf.is_calibrated = True

    # 3 tracks:
    # 131: Real GK in goal mouth (x=100, defending left)
    # 204: Ad / outlier on the right touchline (x=900)
    # 246: Outlier near top banner (x=120, y=50)
    tracks = [
        {
            "track_id": 131,
            "xyxy": (90, 240, 130, 340),  # In goalmouth, left end
            "conf": 0.85,
            "classification": {"team": "Team A", "is_gk": True, "label": "TEAM A (GK) | Player #131"},
        },
        {
            "track_id": 204,
            "xyxy": (880, 300, 920, 400), # Far right touchline
            "conf": 0.55,
            "classification": {"team": "Team A", "is_gk": True, "label": "TEAM A (GK) | Player #204"},
        },
        {
            "track_id": 246,
            "xyxy": (100, 30, 140, 110),  # Top banner ad
            "conf": 0.45,
            "classification": {"team": "Team A", "is_gk": True, "label": "TEAM A (GK) | Player #246"},
        },
    ]

    # Enforce constraints
    clf.enforce_team_and_gk_constraints(tracks, frame_shape=(720, 1280))

    gk_count = sum(1 for t in tracks if t["classification"].get("is_gk", False))
    # STRICT RULE: exactly 1 GK, NEVER 3!
    assert gk_count == 1
    # The real GK in the goalmouth (131) must be chosen!
    assert tracks[0]["classification"]["is_gk"] is True
    assert "GK" in tracks[0]["classification"]["label"]
    # The ad / outlier tracks must be stripped of GK!
    assert tracks[1]["classification"]["is_gk"] is False
    assert "GK" not in tracks[1]["classification"]["label"]
    assert tracks[2]["classification"]["is_gk"] is False
    assert "GK" not in tracks[2]["classification"]["label"]


def test_static_ad_filter():
    """Verify that stationary billboard / LED ad tracks are filtered out."""
    filter_ad = StaticAdFilter(min_frames=10, max_movement_std=2.5)

    # Track 204 stays at (500, 300) with 0 movement (ad hoarding)
    # Track 171 moves from (200, 200) across the field (running player)
    for frame_idx in range(15):
        tracks = [
            {"track_id": 204, "xyxy": (480, 280, 520, 320)},
            {"track_id": 171, "xyxy": (200 + frame_idx * 10, 200, 240 + frame_idx * 10, 280)},
        ]
        filtered = filter_ad.update_and_filter(tracks)

    # After 15 frames, static ad track 204 must be suppressed
    remaining_ids = [t["track_id"] for t in filtered]
    assert 204 not in remaining_ids
    assert 171 in remaining_ids


def test_aspect_ratio_rejection():
    """Square logos or banners (aspect ratio < 1.35) must be rejected."""
    # Heineken star or square icon: 40x40 -> aspect ratio 1.0
    square_box = (100, 100, 140, 140)
    assert PitchFilter.is_valid_person_box(square_box, (720, 1280)) is False

    # Normal player: 25x80 -> aspect ratio 3.2
    player_box = (100, 100, 125, 180)
    assert PitchFilter.is_valid_person_box(player_box, (720, 1280)) is True


def test_foot_on_grass_filter():
    """Persons whose feet do not touch green pitch grass are rejected."""
    # Synthetic frame: top half dark (ad boards/crowd), bottom half green grass
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:100, :] = (40, 40, 40)       # Dark ad boards / barrier
    frame[100:, :] = (35, 150, 40)      # Green grass (BGR)

    # Bounding box elevated on ad board (feet at y2 = 80, no grass around)
    ad_box = (50, 20, 75, 80)
    assert PitchFilter.is_on_grass_surface(frame, ad_box) is False

    # Player standing on grass (feet at y2 = 160, surrounded by green grass)
    player_box = (50, 110, 75, 170)
    assert PitchFilter.is_on_grass_surface(frame, player_box) is True
