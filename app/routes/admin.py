from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.config import settings
from app.models import (
    Team, Question, TeamQuestionState, ChallengeSession, QuestionType,
    QuestionStateStatus, ChallengeStatus, TestCase, Submission, SubmissionResult,
    SubmissionVerdict,
)
from app.schemas import (
    TeamCreate, QuestionCreate, ChallengeCreate, AssignBoost, ReviewMarkSolved,
    TestCaseCreate, TestCaseAdmin, AddTimeRequest, LeaderboardRow, RejudgeResponse,
)
from app.services.access import now_naive_utc, time_state
from app.services.judge import get_judge

router = APIRouter()


def verify_admin(admin_passcode: str = Header(...)):
    if admin_passcode != settings.ADMIN_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── teams ────────────────────────────────────────────────────────────────────

@router.post("/teams")
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    existing = (await db.execute(select(Team).where(Team.name == team.name))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="A team with that name already exists")
    new_team = Team(name=team.name, passcode=team.passcode)
    db.add(new_team)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="A team with that name already exists")
    return {"message": "Team created successfully", "id": new_team.id}


@router.get("/teams")
async def list_teams(db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    teams = (await db.execute(select(Team).order_by(Team.id))).scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "passcode": t.passcode,
            "points": t.points,
            "timer_start_time": t.timer_start_time,
            "extra_time_seconds": t.extra_time_seconds,
            "started": t.timer_start_time is not None,
        }
        for t in teams
    ]


@router.post("/teams/{team_id}/add-time")
async def add_time(
    team_id: int,
    payload: AddTimeRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Grant extra minutes to one team (or all teams with team_id=0)."""
    if payload.seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be positive")

    updated = []
    if team_id == 0:
        teams = (await db.execute(select(Team))).scalars().all()
    else:
        team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        teams = [team]

    for team in teams:
        team.extra_time_seconds = (team.extra_time_seconds or 0) + payload.seconds
        db.add(team)
        updated.append({"id": team.id, "name": team.name,
                        "extra_time_seconds": team.extra_time_seconds})
    await db.commit()
    return {"message": f"Added {payload.seconds}s", "teams": updated}


# ── questions ────────────────────────────────────────────────────────────────

@router.post("/questions")
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    new_question = Question(**question.model_dump())
    db.add(new_question)
    await db.commit()
    return {"message": "Question created", "id": new_question.id}


@router.patch("/questions/{question_id}")
async def update_question(
    question_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    question = (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    allowed = {c.name for c in Question.__table__.columns} - {"id"}
    for key, value in payload.items():
        if key in allowed:
            setattr(question, key, value)
    await db.commit()
    return {"message": "Question updated", "id": question.id}


# ── test cases ───────────────────────────────────────────────────────────────

@router.get("/questions/{question_id}/test-cases", response_model=List[TestCaseAdmin])
async def list_test_cases(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Admin sees hidden tests too."""
    return (
        await db.execute(
            select(TestCase)
            .where(TestCase.question_id == question_id)
            .order_by(TestCase.position, TestCase.id)
        )
    ).scalars().all()


@router.post("/questions/{question_id}/test-cases")
async def add_test_cases(
    question_id: int,
    cases: List[TestCaseCreate],
    replace: bool = Query(False, description="Delete existing test cases first"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    question = (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if replace:
        existing = (
            await db.execute(select(TestCase).where(TestCase.question_id == question_id))
        ).scalars().all()
        for row in existing:
            await db.delete(row)
        await db.flush()

    for index, case in enumerate(cases):
        db.add(
            TestCase(
                question_id=question_id,
                stdin=case.stdin,
                expected_output=case.expected_output,
                is_hidden=case.is_hidden,
                weight=case.weight,
                position=case.position or index,
            )
        )
    await db.commit()
    return {"message": f"{len(cases)} test case(s) saved", "question_id": question_id}


@router.delete("/test-cases/{case_id}")
async def delete_test_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    case = (await db.execute(select(TestCase).where(TestCase.id == case_id))).scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    await db.delete(case)
    await db.commit()
    return {"message": "Test case deleted"}


# ── submissions / rejudge ────────────────────────────────────────────────────

@router.get("/submissions")
async def list_submissions(
    team_id: Optional[int] = None,
    question_id: Optional[int] = None,
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
        await db.execute(select(Submission).where(Submission.id == submission_id))
    ).scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    results = (
        await db.execute(
            select(SubmissionResult).where(SubmissionResult.submission_id == submission_id)
        )
    ).scalars().all()
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
    """Re-run a submission. Used after a Judge0 internal error (status 13).

    Recomputes the score, then adjusts the team's best score and points so the
    total stays consistent.
    """
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

    from app.routes.main import _build_result, _score
    from app.services.judge import JudgeJob

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
        _build_result(c, o, question.compare_mode, visible=not c.is_hidden)
        for c, o in zip(cases, outcomes)
    ]
    new_score, passed, total = _score(
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


# ── leaderboard ──────────────────────────────────────────────────────────────

@router.get("/leaderboard", response_model=List[LeaderboardRow])
async def leaderboard(db: AsyncSession = Depends(get_db)):
    """Public-ish board. MAIN score = sum of best score per question."""
    teams = (await db.execute(select(Team).order_by(Team.id))).scalars().all()
    main_questions = (
        await db.execute(select(Question.id).where(Question.type == QuestionType.MAIN))
    ).scalars().all()

    rows = []
    for team in teams:
        states = (
            await db.execute(
                select(TeamQuestionState).where(
                    TeamQuestionState.team_id == team.id,
                    TeamQuestionState.question_id.in_(main_questions or [-1]),
                )
            )
        ).scalars().all()

        main_score = sum(s.best_score or 0 for s in states)
        solved = sum(1 for s in states if s.status == QuestionStateStatus.SOLVED)
        attempts = sum(s.attempts or 0 for s in states)
        started, remaining, expired = time_state(team)

        rows.append(
            LeaderboardRow(
                team_id=team.id,
                team_name=team.name,
                points=team.points or 0,
                main_score=main_score,
                solved=solved,
                attempts=attempts,
                started=started,
                expired=expired,
                seconds_remaining=remaining if started else None,
            )
        )

    rows.sort(key=lambda r: (-r.points, r.attempts, r.team_id))
    return rows


@router.get("/judge/health")
async def judge_health(_: None = Depends(verify_admin)):
    client = get_judge()
    healthy = await client.health()
    detail = {"backend": settings.JUDGE_BACKEND, "healthy": healthy}
    if healthy and hasattr(client, "ensure_languages"):
        detail["languages"] = await client.ensure_languages()
    return detail


# ── unchanged legacy endpoints (CHALLENGE / TIME_BOOST - out of scope for now) ─

@router.post("/teams/{team_id}/assign-boost")
async def assign_boost(team_id: int, boost: AssignBoost, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    question = (await db.execute(select(Question).where(Question.id == boost.question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.question_id == boost.question_id,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="That question is already assigned to this team")

    db.add(
        TeamQuestionState(
            team_id=team_id,
            question_id=boost.question_id,
            status=QuestionStateStatus.ASSIGNED,
        )
    )
    await db.commit()
    return {"message": "Time boost assigned"}


@router.post("/challenge/create")
async def create_challenge(challenge: ChallengeCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    new_challenge = ChallengeSession(**challenge.model_dump())
    db.add(new_challenge)
    await db.commit()
    return {"message": "Challenge created", "id": new_challenge.id}


@router.post("/review/mark-solved")
async def mark_solved(review: ReviewMarkSolved, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    q_result = await db.execute(select(Question).where(Question.id == review.question_id))
    question = q_result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    team_result = await db.execute(select(Team).where(Team.id == review.team_id))
    team = team_result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if question.type == QuestionType.TIME_BOOST:
        state_result = await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == review.team_id,
                TeamQuestionState.question_id == review.question_id,
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
        state = state_result.scalars().first()
        if state:
            state.status = QuestionStateStatus.SOLVED
            team.extra_time_seconds = (team.extra_time_seconds or 0) + question.reward_value
            db.add(state)
            db.add(team)
            await db.commit()
            return {"message": "Time boost solved, time added"}

    elif question.type == QuestionType.CHALLENGE:
        challenge_result = await db.execute(
            select(ChallengeSession).where(
                ChallengeSession.question_id == review.question_id,
                ChallengeSession.status == ChallengeStatus.ONGOING,
                (
                    (ChallengeSession.team1_id == review.team_id)
                    | (ChallengeSession.team2_id == review.team_id)
                    | (ChallengeSession.team3_id == review.team_id)
                ),
            )
        )
        challenge = challenge_result.scalars().first()
        if challenge:
            challenge.status = ChallengeStatus.COMPLETED
            challenge.winner_team_id = review.team_id
            team.points = (team.points or 0) + question.reward_value
            db.add(challenge)
            db.add(team)
            await db.commit()
            return {"message": "Challenge won, points added"}

    if question.type == QuestionType.MAIN:
        return {
            "message": "MAIN questions are graded automatically by the judge. "
                       "Use GET /api/admin/leaderboard to see scores."
        }

    return {"message": "No active assignment found for this question"}
