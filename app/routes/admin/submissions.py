"""Admin submission views and rejudge.

The rejudge pipeline itself lives in app/services/rejudge.py so it shares
result-building and scoring with the team submit path.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import Submission, SubmissionResult
from app.routes.admin.deps import verify_admin
from app.schemas import RejudgeResponse
from app.services.rejudge import rejudge_submission

router = APIRouter()


@router.get("/submissions")
async def list_submissions(
    team_id: int | None = None,
    question_id: int | None = None,
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    query = select(Submission)
    if team_id:
        query = query.where(Submission.team_id == team_id)
    if question_id:
        query = query.where(Submission.question_id == question_id)
    rows = (await db.execute(query.order_by(Submission.id.desc()).limit(limit))).scalars().all()
    return [
        {
            "id": s.id,
            "team_id": s.team_id,
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
            "finished_at": s.finished_at,
        }
        for s in rows
    ]


@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    submission = (
        (await db.execute(select(Submission).where(Submission.id == submission_id)))
        .scalars()
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    results = (
        (
            await db.execute(
                select(SubmissionResult).where(SubmissionResult.submission_id == submission_id)
            )
        )
        .scalars()
        .all()
    )
    return {
        "submission": {
            "id": submission.id,
            "team_id": submission.team_id,
            "question_id": submission.question_id,
            "language": submission.language,
            "source_code": submission.source_code,
            "verdict": submission.verdict,
            "scored": submission.scored,
            "score": submission.score,
            "score_delta": submission.score_delta,
        },
        "results": [
            {
                "passed": r.passed,
                "is_hidden": r.is_hidden,
                "judge_status": r.judge_status,
                "stdin": r.stdin,
                "expected_output": r.expected_output,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "compile_output": r.compile_output,
                "time_seconds": r.time_seconds,
            }
            for r in results
        ],
    }


@router.post("/submissions/{submission_id}/rejudge", response_model=RejudgeResponse)
async def rejudge(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Re-run a submission. Used after a Judge0 internal error (status 13)."""
    return await rejudge_submission(db, submission_id)
