"""Per-team question progress: state rows and best-score accounting.

Extracted from the MAIN-round routes so run/submit and any future arena
share one implementation of "best score wins, points move by the delta only".
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Submission, Team, TeamQuestionState, QuestionStateStatus
from app.services.access import now_naive_utc


async def get_state(db: AsyncSession, team_id: int, question_id: int) -> TeamQuestionState:
    result = await db.execute(
        select(TeamQuestionState).where(
            TeamQuestionState.team_id == team_id,
            TeamQuestionState.question_id == question_id,
        )
    )
    state = result.scalars().first()
    if state is None:
        state = TeamQuestionState(
            team_id=team_id,
            question_id=question_id,
            status=QuestionStateStatus.ASSIGNED,
        )
        db.add(state)
        await db.flush()
    return state


async def apply_score(
    db: AsyncSession,
    team: Team,
    state: TeamQuestionState,
    submission: Submission,
    score: int,
    passed: int,
    total: int,
) -> int:
    """Best-score-wins accounting for a scored submission. Returns score_delta."""
    # Lock the team row so concurrent submits cannot lose an update.
    locked = (
        await db.execute(select(Team).where(Team.id == team.id).with_for_update())
    ).scalars().first()

    score_delta = 0
    previous_best = state.best_score or 0
    if score > previous_best:
        score_delta = score - previous_best
        state.best_score = score
        state.best_submission_id = submission.id
        locked.points = (locked.points or 0) + score_delta
        team.points = locked.points

    if passed == total and total > 0:
        state.status = QuestionStateStatus.SOLVED
        if state.first_solved_at is None:
            state.first_solved_at = now_naive_utc()

    state.attempts = (state.attempts or 0) + 1
    state.last_submission_at = now_naive_utc()
    submission.score_delta = score_delta
    return score_delta


def record_error_attempt(state: TeamQuestionState, submission: Submission) -> None:
    """Judge error on a scored submit: count the attempt, never change score."""
    state.attempts = (state.attempts or 0) + 1
    state.last_submission_at = now_naive_utc()
    submission.score = 0
    submission.score_delta = 0
