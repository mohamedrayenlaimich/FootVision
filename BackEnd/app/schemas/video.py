from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    status: str
    message: str
    file_size_bytes: int


class VideoStatusResponse(BaseModel):
    video_id: str
    filename: str
    status: str
    progress_percentage: float
    total_frames: int
    processed_frames: int
    error_message: Optional[str] = None
    current_stage: Optional[str] = None
    current_fps: Optional[float] = None
    total_detected_players: Optional[int] = None
    team_a_players_count: Optional[int] = None
    team_b_players_count: Optional[int] = None
    referee_detected: Optional[bool] = None
    ball_detected: Optional[bool] = None
    ball_visibility_percentage: Optional[float] = None
    duration_seconds: Optional[float] = None
    processed_video_url: Optional[str] = None
    original_video_url: Optional[str] = None
    download_url: Optional[str] = None
    telemetry_url: Optional[str] = None
    players: Optional[List[Dict[str, Any]]] = None
    team_a_stats: Optional[Dict[str, Any]] = None
    team_b_stats: Optional[Dict[str, Any]] = None


class VideoTelemetryResponse(BaseModel):
    video_id: str
    summary: Dict[str, Any]
    frames: List[Dict[str, Any]]
