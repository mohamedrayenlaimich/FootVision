from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CompetitionSchema(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    type: Optional[str] = None
    emblem: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class TeamSchema(BaseModel):
    id: int
    name: str
    shortName: Optional[str] = None
    tla: Optional[str] = None
    crest: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ScoreTimeSchema(BaseModel):
    home: Optional[int] = None
    away: Optional[int] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class MatchScoreSchema(BaseModel):
    winner: Optional[str] = None
    duration: Optional[str] = None
    fullTime: Optional[ScoreTimeSchema] = None
    halfTime: Optional[ScoreTimeSchema] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class MatchSchema(BaseModel):
    id: int
    utcDate: str
    status: str
    matchday: Optional[int] = None
    stage: Optional[str] = None
    group: Optional[str] = None
    competition: Optional[CompetitionSchema] = None
    homeTeam: TeamSchema
    awayTeam: TeamSchema
    score: Optional[MatchScoreSchema] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class MatchListResponseSchema(BaseModel):
    count: int = Field(default=0)
    matches: List[MatchSchema] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
