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
