from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TeamInfoSchema(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    winner: Optional[bool] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class LeagueInfoSchema(BaseModel):
    id: int
    name: str
    country: Optional[str] = None
    logo: Optional[str] = None
    flag: Optional[str] = None
    season: Optional[int] = None
    round: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class VenueInfoSchema(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class FixtureStatusSchema(BaseModel):
    long: Optional[str] = None
    short: Optional[str] = None
    elapsed: Optional[int] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class GoalsInfoSchema(BaseModel):
    home: Optional[int] = None
    away: Optional[int] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ScorePeriodSchema(BaseModel):
    home: Optional[int] = None
    away: Optional[int] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ScoreInfoSchema(BaseModel):
    halftime: Optional[ScorePeriodSchema] = None
    fulltime: Optional[ScorePeriodSchema] = None
    extratime: Optional[ScorePeriodSchema] = None
    penalty: Optional[ScorePeriodSchema] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class FixtureItemSchema(BaseModel):
    fixture_id: int
    date: str
    status: Optional[FixtureStatusSchema] = None
    venue: Optional[VenueInfoSchema] = None
    league: Optional[LeagueInfoSchema] = None
    home_team: TeamInfoSchema
    away_team: TeamInfoSchema
    goals: Optional[GoalsInfoSchema] = None
    score: Optional[ScoreInfoSchema] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class FixtureListResponseSchema(BaseModel):
    results: int = Field(default=0)
    fixtures: List[FixtureItemSchema] = Field(default_factory=list)
    note: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
