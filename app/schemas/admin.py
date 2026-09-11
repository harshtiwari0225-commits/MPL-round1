"""Pydantic models for admin views (leaderboard, rejudge)."""

from pydantic import BaseModel

from app.models import SubmissionVerdict


class LeaderboardRow(BaseModel):
    team_id: int
    team_name: str
    points: int
    main_score: int
    solved: int
    attempts: int
    started: bool
    expired: bool
    seconds_remaining: int | None = None


class RejudgeResponse(BaseModel):
    submission_id: int
    verdict: SubmissionVerdict
    old_score: int
    new_score: int
    score_delta: int
