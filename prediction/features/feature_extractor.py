from typing import Any, Dict, List, Optional


class HistoricalFeatureExtractor:
    """
    Extracts time-aware historical features for a match strictly using
    matches prior to the fixture date to prevent future data leakage.
    """

    def extract_match_features(
        self,
        home_team_id: int,
        away_team_id: int,
        historical_matches: List[Dict[str, Any]],
        fixture_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Filter historical matches prior to fixture date if provided
        valid_matches = []
        for m in historical_matches:
            if fixture_date and m.get("date") and m["date"] >= fixture_date:
                continue
            valid_matches.append(m)

        home_matches = [
            m for m in valid_matches
            if m.get("home_team_id") == home_team_id or m.get("away_team_id") == home_team_id
        ]
        away_matches = [
            m for m in valid_matches
            if m.get("home_team_id") == away_team_id or m.get("away_team_id") == away_team_id
        ]

        def get_team_stats(team_id: int, team_m_list: List[Dict[str, Any]]):
            last_5 = team_m_list[-5:] if team_m_list else []
            if not last_5:
                return {"avg_scored": 1.5, "avg_conceded": 1.1, "wins": 2, "draws": 1, "losses": 2}

            scored = 0
            conceded = 0
            wins = 0
            draws = 0
            losses = 0

            for m in last_5:
                is_home = (m.get("home_team_id") == team_id)
                s = m.get("home_goals", 0) if is_home else m.get("away_goals", 0)
                c = m.get("away_goals", 0) if is_home else m.get("home_goals", 0)

                scored += s
                conceded += c

                if s > c:
                    wins += 1
                elif s == c:
                    draws += 1
                else:
                    losses += 1

            count = len(last_5)
            return {
                "avg_scored": round(scored / count, 2),
                "avg_conceded": round(conceded / count, 2),
                "wins": wins,
                "draws": draws,
                "losses": losses,
            }

        home_stats = get_team_stats(home_team_id, home_matches)
        away_stats = get_team_stats(away_team_id, away_matches)

        # H2H features
        h2h_matches = [
            m for m in valid_matches
            if (m.get("home_team_id") == home_team_id and m.get("away_team_id") == away_team_id)
            or (m.get("home_team_id") == away_team_id and m.get("away_team_id") == home_team_id)
        ]

        h2h_home_wins = 0
        h2h_draws = 0
        h2h_away_wins = 0
        for m in h2h_matches[-5:]:
            h_id = m.get("home_team_id")
            hg = m.get("home_goals", 0)
            ag = m.get("away_goals", 0)
            if hg == ag:
                h2h_draws += 1
            elif (h_id == home_team_id and hg > ag) or (h_id == away_team_id and ag > hg):
                h2h_home_wins += 1
            else:
                h2h_away_wins += 1

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_form": home_stats,
            "away_form": away_stats,
            "h2h": {
                "home_wins": h2h_home_wins,
                "draws": h2h_draws,
                "away_wins": h2h_away_wins,
                "meetings_count": len(h2h_matches),
            },
        }
