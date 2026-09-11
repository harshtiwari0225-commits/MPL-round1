"""MAIN round: the coding arena.

Three endpoints the editor UI needs:

    GET  /api/main/questions        -> the team's MAIN questions (visible tests only)
    POST /api/main/run              -> execute against VISIBLE tests, no score
    POST /api/main/submit           -> execute against ALL tests, award partial credit

The pipelines live in app/services: arena.py (question views), judging.py
(run/submit), validation.py (guards), progress.py (best-score accounting),
results.py (outcome mapping). Scoring rules are documented in judging.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.database import get_db
from app.models import Submission, Team
from app.schemas import CodeSubmitRequest, MainQuestionPublic, SubmissionOut
from app.services.access import get_current_team, time_state
from app.services.arena import team_question_views
from app.services.judging import judge_submission

router = APIRouter()


# ── endpoints ────────────────────────────────────────────────────────────────


@router.get("/questions", response_model=list[MainQuestionPublic])
async def list_main_questions(
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """The team's MAIN questions. Hidden tests are stripped in the service."""
    return await team_question_views(db, team)


@router.post("/run", response_model=SubmissionOut)
async def run_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against the VISIBLE test cases only. Never writes a score."""
    return await judge_submission(payload, team, db, scored=False)


@router.post("/submit", response_model=SubmissionOut)
async def submit_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against every test case and award partial credit."""
    return await judge_submission(payload, team, db, scored=True)


@router.get("/submissions")
async def my_submissions(
    question_id: int | None = None,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """This team's own submission history."""
    query = select(Submission).where(Submission.team_id == team.id)
    if question_id:
        query = query.where(Submission.question_id == question_id)
    rows = (await db.execute(query.order_by(Submission.id.desc()).limit(50))).scalars().all()
    return [
        {
            "id": s.id,
            "question_id": s.question_id,
            "language": s.language,
            "verdict": s.verdict,
            "scored": s.scored,
            "score": s.score,
            "score_delta": s.score_delta,
            "tests_passed": s.tests_passed,
            "tests_total": s.tests_total,
            "error_message": s.error_message,
            "created_at": s.created_at,
        }
        for s in rows
    ]


@router.get("/clock")
async def my_clock(team: Team = Depends(get_current_team)):
    started, remaining, expired = time_state(team)
    return {
        "started": started,
        "seconds_remaining": remaining,
        "total_allowed_seconds": settings.EVENT_DURATION_SECONDS + (team.extra_time_seconds or 0),
        "extra_time_seconds": team.extra_time_seconds or 0,
        "expired": expired,
    }
