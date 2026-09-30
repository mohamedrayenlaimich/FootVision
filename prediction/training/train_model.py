import json
import math
import os
from typing import Any, Dict, List

# Create data and models directories if missing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Historical matches dataset
SAMPLE_HISTORICAL_DATA: List[Dict[str, Any]] = [
    {"date": "2025-09-10", "home_team_id": 529, "away_team_id": 541, "home_goals": 2, "away_goals": 1},
    {"date": "2025-09-17", "home_team_id": 42, "away_team_id": 49, "home_goals": 3, "away_goals": 1},
    {"date": "2025-09-24", "home_team_id": 65, "away_team_id": 64, "home_goals": 2, "away_goals": 2},
    {"date": "2025-10-01", "home_team_id": 541, "away_team_id": 157, "home_goals": 1, "away_goals": 0},
    {"date": "2025-10-15", "home_team_id": 529, "away_team_id": 42, "home_goals": 1, "away_goals": 1},
    {"date": "2025-11-05", "home_team_id": 64, "away_team_id": 541, "home_goals": 0, "away_goals": 2},
]


def train_poisson_baseline():
    """
    Trains and saves FootVision Poisson xG Baseline model metadata.
    """
    dataset_path = os.path.join(DATA_DIR, "matches.json")
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_HISTORICAL_DATA, f, indent=2)

    total_matches = len(SAMPLE_HISTORICAL_DATA)
    total_home = sum(m["home_goals"] for m in SAMPLE_HISTORICAL_DATA)
    total_away = sum(m["away_goals"] for m in SAMPLE_HISTORICAL_DATA)

    avg_home = total_home / total_matches
    avg_away = total_away / total_matches

    model_metadata = {
        "model_version": "footvision-poisson-v1.0",
        "training_matches_count": total_matches,
        "avg_league_home_goals": round(avg_home, 3),
        "avg_league_away_goals": round(avg_away, 3),
        "home_advantage_multiplier": 1.12,
    }

    model_path = os.path.join(MODELS_DIR, "poisson_model.json")
    with open(model_path, "w", encoding="utf-8") as f:
        json.dump(model_metadata, f, indent=2)

    print(f"Model training complete. Metadata saved to {model_path}")
    return model_metadata


if __name__ == "__main__":
    train_poisson_baseline()
