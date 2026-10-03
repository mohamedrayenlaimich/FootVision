from fastapi import APIRouter, HTTPException
from app.schemas.analytics import MatchAnalyticsResponse, PlayerMetric, TeamMetric
from app.api.v1.endpoints.video import processing_jobs

router = APIRouter()

@router.get("/match/{video_id}", response_model=MatchAnalyticsResponse, summary="Get full match analytics")
def get_match_analytics(video_id: str):
    if video_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail="Analytics data unavailable for this video ID. Please upload a match video to process real analytics.",
        )

    job = processing_jobs[video_id]
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Video processing is currently '{job.get('status')}'. Real analytics will be available once processing reaches 100%.",
        )

    # Return real processed job analytics (no mock data)
    return MatchAnalyticsResponse(
        video_id=video_id,
        match_duration_seconds=float(job.get("processed_frames", 0) / 30.0),
        fps=30.0,
        total_detected_players=job.get("total_detected_players", 0),
        players=job.get("players", []),
        team_a_stats=job.get("team_a_stats", TeamMetric(
            team_name="Team A",
            possession_percentage=0.0,
            total_distance_km=0.0,
            sprints=0,
            tactical_width_m=0.0,
            tactical_depth_m=0.0,
        )),
        team_b_stats=job.get("team_b_stats", TeamMetric(
            team_name="Team B",
            possession_percentage=0.0,
            total_distance_km=0.0,
            sprints=0,
            tactical_width_m=0.0,
            tactical_depth_m=0.0,
        )),
    )

@router.get("/sample", response_model=MatchAnalyticsResponse, summary="Get sample computer-vision tracking telemetry")
def get_sample_analytics():
    """Returns sample computer-vision tracking coordinates for live pitch radar demonstration."""
    sample_players = [
        PlayerMetric(track_id=1, team="Team Red", jersey_number=1, player_name="Player #1", distance_covered_meters=3410.0, max_speed_kmh=18.4, sprint_count=3, average_pitch_x=8.5, average_pitch_y=50.0),
        PlayerMetric(track_id=2, team="Team Red", jersey_number=2, player_name="Player #2", distance_covered_meters=9820.0, max_speed_kmh=33.6, sprint_count=24, average_pitch_x=26.4, average_pitch_y=16.2),
        PlayerMetric(track_id=3, team="Team Red", jersey_number=4, player_name="Player #4", distance_covered_meters=8740.0, max_speed_kmh=27.2, sprint_count=14, average_pitch_x=22.1, average_pitch_y=38.4),
        PlayerMetric(track_id=4, team="Team Red", jersey_number=5, player_name="Player #5", distance_covered_meters=8650.0, max_speed_kmh=26.8, sprint_count=13, average_pitch_x=22.3, average_pitch_y=61.8),
        PlayerMetric(track_id=5, team="Team Red", jersey_number=25, player_name="Player #25", distance_covered_meters=9940.0, max_speed_kmh=34.1, sprint_count=27, average_pitch_x=26.8, average_pitch_y=84.2),
        PlayerMetric(track_id=6, team="Team Red", jersey_number=17, player_name="Player #17", distance_covered_meters=10450.0, max_speed_kmh=29.2, sprint_count=19, average_pitch_x=41.5, average_pitch_y=49.8),
        PlayerMetric(track_id=7, team="Team Red", jersey_number=8, player_name="Player #8", distance_covered_meters=10120.0, max_speed_kmh=28.4, sprint_count=18, average_pitch_x=44.2, average_pitch_y=32.0),
        PlayerMetric(track_id=8, team="Team Red", jersey_number=10, player_name="Player #10", distance_covered_meters=9320.0, max_speed_kmh=35.2, sprint_count=29, average_pitch_x=67.8, average_pitch_y=22.5),
        PlayerMetric(track_id=9, team="Team Red", jersey_number=9, player_name="Player #9", distance_covered_meters=8940.0, max_speed_kmh=31.4, sprint_count=21, average_pitch_x=71.2, average_pitch_y=50.2),
        PlayerMetric(track_id=10, team="Team Blue", jersey_number=1, player_name="Player #1 (Away)", distance_covered_meters=3200.0, max_speed_kmh=16.8, sprint_count=2, average_pitch_x=91.8, average_pitch_y=50.0),
        PlayerMetric(track_id=11, team="Team Blue", jersey_number=2, player_name="Player #2 (Away)", distance_covered_meters=9420.0, max_speed_kmh=31.9, sprint_count=22, average_pitch_x=73.5, average_pitch_y=83.4),
        PlayerMetric(track_id=12, team="Team Blue", jersey_number=3, player_name="Player #3 (Away)", distance_covered_meters=8560.0, max_speed_kmh=28.0, sprint_count=15, average_pitch_x=77.2, average_pitch_y=61.0),
        PlayerMetric(track_id=13, team="Team Blue", jersey_number=5, player_name="Player #5 (Away)", distance_covered_meters=10680.0, max_speed_kmh=32.4, sprint_count=23, average_pitch_x=51.2, average_pitch_y=50.4),
        PlayerMetric(track_id=14, team="Team Blue", jersey_number=7, player_name="Player #7 (Away)", distance_covered_meters=10290.0, max_speed_kmh=35.8, sprint_count=32, average_pitch_x=43.0, average_pitch_y=20.1),
        PlayerMetric(track_id=15, team="Team Blue", jersey_number=9, player_name="Player #9 (Away)", distance_covered_meters=9180.0, max_speed_kmh=36.1, sprint_count=28, average_pitch_x=34.5, average_pitch_y=49.0),
    ]

    return MatchAnalyticsResponse(
        video_id="sample-demo-tracking",
        match_duration_seconds=90.0,
        fps=30.0,
        total_detected_players=len(sample_players),
        players=sample_players,
        team_a_stats=TeamMetric(
            team_name="Team Red",
            possession_percentage=54.2,
            total_distance_km=79.39,
            sprints=170,
            tactical_width_m=48.5,
            tactical_depth_m=36.2,
        ),
        team_b_stats=TeamMetric(
            team_name="Team Blue",
            possession_percentage=45.8,
            total_distance_km=51.33,
            sprints=102,
            tactical_width_m=46.1,
            tactical_depth_m=37.8,
        ),
    )

