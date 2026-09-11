"""Pydantic models for teams, login, and the legacy challenge/boost flows."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    passcode: str


class TeamLogin(BaseModel):
    name: str
    passcode: str


class TeamStatusResponse(BaseModel):
    id: int
    name: str
    points: int
    timer_start_time: datetime | None
    extra_time_seconds: int
    main_question_id: int | None
    session_token: str | None = None  # returned on login only
    model_config = ConfigDict(from_attributes=True)


class AdminLogin(BaseModel):
    passcode: str


class ChallengeCreate(BaseModel):
    question_id: int
    team1_id: int
    team2_id: int
    team3_id: int | None = None


class AssignBoost(BaseModel):
    question_id: int


class ReviewMarkSolved(BaseModel):
    team_id: int
    question_id: int


class AddTimeRequest(BaseModel):
    seconds: int
