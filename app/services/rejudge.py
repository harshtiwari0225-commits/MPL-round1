"""Admin rejudge pipeline.

Re-runs a scored submission (used after a Judge0 internal error, status 13,
or after fixing a test case), recomputes the score, then adjusts the team's
best score and points so the total stays consistent.

Backs POST /api/admin/submissions/{id}/rejudge.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models import (
    Question, Submission, SubmissionResult, SubmissionVerdict, Team,
    TeamQuestionState, TestCase,
)
from app.schemas import RejudgeResponse
from app.services import scoring
from app.services.judge import JudgeJob, get_judge
from app.services.results import build_result


async def rejudge_submission(db: AsyncSession, submission_id: int) -> RejudgeResponse:
    submission = (
        await db.execute(select(Submission).where(Submission.id == submission_id))
    ).scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if not submission.scored:
        raise HTTPException(status_code=400, detail="Only scored submissions can be rejudged")

    question = (
        await db.execute(select(Question).where(Question.id == submission.question_id))
    ).scalars().first()
    state = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == submission.team_id,
                TeamQuestionState.question_id == submission.question_id,
            )
        )
    ).scalars().first()

    cases = (
        await db.execute(
            select(TestCase)
            .where(TestCase.question_id == question.id)
            .order_by(TestCase.position, TestCase.id)
        )
    ).scalars().all()

    jobs = [
        JudgeJob(
            source_code=submission.source_code,
            language=submission.language,
            stdin=c.stdin or "",
            expected_output=c.expected_output or "",
            cpu_time_limit=question.cpu_time_limit or settings.DEFAULT_CPU_TIME_LIMIT,
            wall_time_limit=question.wall_time_limit or settings.DEFAULT_WALL_TIME_LIMIT,
            memory_limit_kb=question.memory_limit_kb or settings.DEFAULT_MEMORY_LIMIT_KB,
        )
        for c in cases
    ]

    try:
        outcomes = await get_judge().run_batch(jobs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Judge backend unavailable: {exc}")

    new_results = [
        build_result(c, o, question.compare_mode, visible=not c.is_hidden)
        for c, o in zip(cases, outcomes)
    ]
    new_score, passed, total = scoring.score_submission(
        question.points or question.reward_value or 0, new_results, cases
    )

    old_results = (
        await db.execute(
            select(SubmissionResult).where(SubmissionResult.submission_id == submission_id)
        )
    ).scalars().all()
    for row in old_results:
        await db.delete(row)

    for r in new_results:
        r.submission_id = submission.id
        db.add(r)

    old_score = submission.score or 0
    submission.score = new_score
    submission.tests_passed = passed
    submission.tests_total = total
    submission.verdict = SubmissionVerdict.ERROR if any(
        o.status_id == 13 for o in outcomes
    ) else (
        SubmissionVerdict.PASSED if passed == total and total
        else SubmissionVerdict.PARTIAL if passed
        else SubmissionVerdict.FAILED
    )

    score_delta = 0
    if state is not None:
        previous_best = state.best_score or 0
        candidate = max(previous_best, new_score)
        if candidate != previous_best:
            score_delta = candidate - previous_best
            state.best_score = candidate
            team = (
                await db.execute(
                    select(Team).where(Team.id == submission.team_id).with_for_update()
                )
            ).scalars().first()
            if team:
                team.points = (team.points or 0) + score_delta

    await db.commit()
    return RejudgeResponse(
        submission_id=submission.id,
        verdict=submission.verdict,
        old_score=old_score,
        new_score=new_score,
        score_delta=score_delta,
    )
