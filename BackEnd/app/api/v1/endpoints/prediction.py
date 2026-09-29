from fastapi import APIRouter
from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse, summary="Generate match forecast")
def predict_match(request: PredictionRequest):
    # Poisson / ML model forecasting simulation
    return PredictionResponse(
        home_team=request.home_team,
        away_team=request.away_team,
        expected_goals_home=1.85,
        expected_goals_away=1.12,
        win_probability_home=54.5,
        draw_probability=24.3,
        win_probability_away=21.2,
        most_likely_scorelines=[
            {"2-1": 13.5},
            {"1-1": 12.1},
            {"2-0": 11.4},
            {"1-0": 10.8},
            {"3-1": 7.2}
        ]
    )
