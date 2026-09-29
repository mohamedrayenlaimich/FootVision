from fastapi import APIRouter, HTTPException
from app.schemas.analytics import MatchAnalyticsResponse, PlayerMetric, TeamMetric

router = APIRouter()

@router.get("/match/{video_id}", response_model=MatchAnalyticsResponse, summary="Get full match analytics")
def get_match_analytics(video_id: str):
    # Mock / Demo responses structure for frontend integration testing
    mock_players = [
        PlayerMetric(
            track_id=1,
            team="Team Red",
            jersey_number=10,
            player_name="K. De Bruyne",
            distance_covered_meters=9840.5,
            max_speed_kmh=31.2,
            sprint_count=18,
            average_pitch_x=52.4,
            average_pitch_y=34.1
        ),
        PlayerMetric(
            track_id=2,
            team="Team Blue",
            jersey_number=7,
            player_name="V. Junior",
            distance_covered_meters=10420.0,
            max_speed_kmh=34.8,
            sprint_count=24,
            average_pitch_x=68.2,
            average_pitch_y=18.5
        )
    ]
    
    return MatchAnalyticsResponse(
        video_id=video_id,
        match_duration_seconds=5400.0,
        fps=30.0,
        total_detected_players=22,
        players=mock_players,
        team_a_stats=TeamMetric(
            team_name="Team Red",
            possession_percentage=54.2,
            total_distance_km=112.5,
            sprints=142,
            tactical_width_m=58.4,
            tactical_depth_m=38.2
        ),
        team_b_stats=TeamMetric(
            team_name="Team Blue",
            possession_percentage=45.8,
            total_distance_km=108.9,
            sprints=156,
            tactical_width_m=55.1,
            tactical_depth_m=41.0
        )
    )
