from pydantic import BaseModel
from typing import List, Optional

class PlayerMetric(BaseModel):
    track_id: int
    team: Optional[str] = "unknown"
    jersey_number: Optional[int] = None
    player_name: Optional[str] = None
    distance_covered_meters: float
    max_speed_kmh: float
    sprint_count: int
    average_pitch_x: float
    average_pitch_y: float

class TeamMetric(BaseModel):
    team_name: str
    possession_percentage: float
    total_distance_km: float
    sprints: int
    tactical_width_m: float
    tactical_depth_m: float

class MatchAnalyticsResponse(BaseModel):
    video_id: str
    match_duration_seconds: float
    fps: float
    total_detected_players: int
    players: List[PlayerMetric]
    team_a_stats: TeamMetric
    team_b_stats: TeamMetric
