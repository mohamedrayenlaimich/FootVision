from pydantic import BaseModel
from typing import Dict, List, Optional

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str
    home_recent_form: Optional[List[str]] = None
    away_recent_form: Optional[List[str]] = None

class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    expected_goals_home: float
    expected_goals_away: float
    win_probability_home: float
    draw_probability: float
    win_probability_away: float
    most_likely_scorelines: List[Dict[str, float]]
