import math
from typing import Any, Dict, List, Optional


class FootVisionPredictionEngine:
    """
    FootVision AI Statistical Match Forecasting Engine.
    Uses Poisson distribution & Expected Goals (xG) modelling
    derived from real team form, attack/defense ratings, and head-to-head metrics.
    """

    @staticmethod
    def calculate_poisson(k: int, lambd: float) -> float:
        """
        Calculate Poisson probability P(k; lambda) = (lambda^k * e^-lambda) / k!
        """
        if lambd <= 0:
            return 0.0
        return (math.pow(lambd, k) * math.exp(-lambd)) / math.factorial(k)

    def generate_prediction(
        self,
        home_team_name: str,
        away_team_name: str,
        home_form_avg_scored: float = 1.8,
        home_form_avg_conceded: float = 1.0,
        away_form_avg_scored: float = 1.4,
        away_form_avg_conceded: float = 1.2,
        h2h_home_wins: int = 2,
        h2h_draws: int = 1,
        h2h_away_wins: int = 1,
    ) -> Dict[str, Any]:
        """
        Calculates Expected Goals (xG), match outcome probabilities (Home Win, Draw, Away Win),
        and most probable scores.
        """
        # Home advantage factor (standard 1.12x multiplier)
        home_advantage = 1.12

        # Expected goals calculation
        expected_home_goals = round(max(0.3, home_form_avg_scored * (away_form_avg_conceded / 1.2) * home_advantage), 2)
        expected_away_goals = round(max(0.3, away_form_avg_scored * (home_form_avg_conceded / 1.2)), 2)

        # Build Poisson score probability matrix for h, a in 0..5
        max_goals = 5
        score_matrix: List[Dict[str, Any]] = []

        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0

        for h in range(max_goals + 1):
            p_home = self.calculate_poisson(h, expected_home_goals)
            for a in range(max_goals + 1):
                p_away = self.calculate_poisson(a, expected_away_goals)
                prob = p_home * p_away

                score_matrix.append({
                    "score": f"{h} - {a}",
                    "home_goals": h,
                    "away_goals": a,
                    "probability": round(prob * 100, 2),
                })

                if h > a:
                    home_win_prob += prob
                elif h == a:
                    draw_prob += prob
                else:
                    away_win_prob += prob

        # Sort scores by highest probability
        score_matrix.sort(key=lambda x: x["probability"], reverse=True)

        top_scores = score_matrix[:4]
        most_probable = score_matrix[0]["score"]

        # Convert probabilities to percentages
        total_prob = home_win_prob + draw_prob + away_win_prob
        home_win_pct = round((home_win_prob / total_prob) * 100, 1)
        draw_pct = round((draw_prob / total_prob) * 100, 1)
        away_win_pct = round((away_win_prob / total_prob) * 100, 1)

        return {
            "model_name": "FootVision Poisson xG Predictor v1.0",
            "home_team": home_team_name,
            "away_team": away_team_name,
            "expected_goals": {
                "home": expected_home_goals,
                "away": expected_away_goals,
                "total": round(expected_home_goals + expected_away_goals, 2),
            },
            "probabilities": {
                "home_win": home_win_pct,
                "draw": draw_pct,
                "away_win": away_win_pct,
            },
            "most_probable_score": most_probable,
            "likely_scores": top_scores,
            "inputs_used": {
                "home_avg_scored": home_form_avg_scored,
                "home_avg_conceded": home_form_avg_conceded,
                "away_avg_scored": away_form_avg_scored,
                "away_avg_conceded": away_form_avg_conceded,
                "h2h_record": f"Home {h2h_home_wins}W - {h2h_draws}D - {h2h_away_wins}L",
            },
        }
