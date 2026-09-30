import logging
from fastapi import APIRouter
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.api_football.prediction_engine import FootVisionPredictionEngine

logger = logging.getLogger(__name__)

router = APIRouter()
engine = FootVisionPredictionEngine()


@router.post("/predict", response_model=PredictionResponse, summary="Generate match forecast")
def predict_match(request: PredictionRequest):
    logger.info(f"Generating FootVision AI forecast for {request.home_team} vs {request.away_team}")
    
    # Calculate Poisson xG prediction dynamically from team parameters
    result = engine.generate_prediction(
        home_team_name=request.home_team,
        away_team_name=request.away_team,
    )

    probs = result.get("probabilities", {})
    xg = result.get("expected_goals", {})
    likely_scores = result.get("likely_scores", [])

    formatted_scorelines = [{item["score"]: item["probability"]} for item in likely_scores]

    return PredictionResponse(
        home_team=request.home_team,
        away_team=request.away_team,
        expected_goals_home=xg.get("home", 1.5),
        expected_goals_away=xg.get("away", 1.1),
        win_probability_home=probs.get("home_win", 45.0),
        draw_probability=probs.get("draw", 25.0),
        win_probability_away=probs.get("away_win", 30.0),
        most_likely_scorelines=formatted_scorelines,
    )
