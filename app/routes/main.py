"""MAIN round: the coding arena.

Three endpoints the editor UI needs:

    GET  /api/main/questions        -> the team's MAIN questions (visible tests only)
    POST /api/main/run              -> execute against VISIBLE tests, no score
    POST /api/main/submit           -> execute against ALL tests, award partial credit

Scoring rules (confirmed with the organiser):
  * partial credit - 20% of hidden tests passed = 20% of the question's points
  * each of the 3 questions has its own independent points
  * no negative marking, unlimited attempts
  * a team's score for a question is the BEST score across all attempts
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.database import get_db
from app.models import (
    Question, QuestionType, Team, TeamQuestionState, TestCase, Submission,
    SubmissionResult, SubmissionVerdict, QuestionStateStatus, CompareMode,
)
from app.schemas import (
    CodeSubmitRequest, MainQuestionPublic, SubmissionOut, TestCasePublic, TestResultOut,
)
from app.services.access import get_current_team, now_naive_utc, require_running, time_state
from app.services import scoring
from app.services.judge import JudgeJob, get_judge

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

def _allowed_languages(question: Question) -> Optional[List[str]]:
    if not question.allowed_languages:
        return None
    try:
        value = json.loads(question.allowed_languages)
        return [str(v).strip().lower() for v in value] if isinstance(value, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _starter_code(question: Question, language: str) -> Optional[str]:
    if not question.starter_code:
        return None
    try:
        data = json.loads(question.starter_code)
        return data.get(language) if isinstance(data, dict) else question.starter_code
    except (json.JSONDecodeError, TypeError):
        return question.starter_code


async def _get_state(db: AsyncSession, team_id: int, question_id: int) -> TeamQuestionState:
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


def _score(points: int, results: List[SubmissionResult], cases: List[TestCase]) -> Tuple[int, int, int]:
    """Weighted partial credit.

    The POINTS come from the hidden pool only (visible tests are practice),
    but the pass COUNT reported to the team covers every test that ran.

    Returns (score, passed_count, total_count).
    """
    pairs = [(r, c) for r, c in zip(results, cases)]
    if not pairs:
        return 0, 0, 0

    hidden = [(r, c) for r, c in pairs if c.is_hidden]
    pool = hidden if hidden else pairs

    total_weight = sum(float(c.weight or 1.0) for _, c in pool)
    passed_weight = sum(float(c.weight or 1.0) for r, c in pool if r.passed)

    score = 0
    if total_weight > 0:
        score = int(round(points * (passed_weight / total_weight)))

    passed = sum(1 for r, _ in pairs if r.passed)
    return score, passed, len(pairs)


def _build_result(case: TestCase, outcome, mode: CompareMode, visible: bool) -> SubmissionResult:
    """Map one Judge0 outcome onto a stored result.

    Judge0 decides errors (compile / TLE / runtime). We decide correctness with
    our own comparator so floats and trailing whitespace behave sensibly.
    """
    status_id = outcome.status_id
    passed = False
    error_statuses = {5, 6, 7, 8, 9, 10, 11, 12, 13, 14}

    if status_id not in error_statuses:
        # Judge0 is authoritative for ERRORS. Correctness is decided here, with
        # the question's compare_mode, so trailing newlines and float formatting
        # cannot fail an otherwise correct answer.
        passed = scoring.outputs_match(outcome.stdout, case.expected_output, mode)

    return SubmissionResult(
        test_case_id=case.id,
        is_hidden=case.is_hidden,
        passed=bool(passed) and status_id not in error_statuses,
        judge_status_id=status_id,
        judge_status=outcome.status,
        stdout=outcome.stdout,
        stderr=outcome.stderr,
        compile_output=outcome.compile_output,
        # Hidden test inputs/answers are stored for admin/rejudge but are never
        # returned to the team - see scoring.public_results().
        expected_output=case.expected_output,
        stdin=case.stdin,
        time_seconds=outcome.time,
        memory_kb=outcome.memory,
    )


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/questions", response_model=List[MainQuestionPublic])
async def list_main_questions(
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """The team's MAIN questions. Hidden tests are stripped here."""
    questions = (
        await db.execute(
            select(Question)
            .where(Question.type == QuestionType.MAIN)
            .order_by(Question.order_index, Question.id)
        )
    ).scalars().all()

    out: List[MainQuestionPublic] = []
    for question in questions:
        cases = (
            await db.execute(
                select(TestCase)
                .where(TestCase.question_id == question.id)
                .order_by(TestCase.position, TestCase.id)
            )
        ).scalars().all()

        state = await _get_state(db, team.id, question.id)
        await db.commit()

        visible = [
            TestCasePublic(
                id=c.id, stdin=c.stdin, expected_output=c.expected_output, position=c.position
            )
            for c in cases
            if not c.is_hidden
        ]

        languages = _allowed_languages(question)
        starter = {lang: _starter_code(question, lang) for lang in (languages or ["python"])}
        starter = {k: v for k, v in starter.items() if v}

        out.append(
            MainQuestionPublic(
                id=question.id,
                title=question.title,
                description=question.description,
                sub_type=question.sub_type,
                difficulty=question.difficulty,
                points=question.points or question.reward_value or 0,
                compare_mode=question.compare_mode or CompareMode.TRIM,
                starter_code=json.dumps(starter) if starter else None,
                allowed_languages=question.allowed_languages,
                order_index=question.order_index or 0,
                visible_tests=visible,
                attempts=state.attempts or 0,
                best_score=state.best_score or 0,
                status=state.status,
            )
        )
    return out


@router.post("/run", response_model=SubmissionOut)
async def run_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against the VISIBLE test cases only. Never writes a score."""
    return await _judge(payload, team, db, scored=False)


@router.post("/submit", response_model=SubmissionOut)
async def submit_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against every test case and award partial credit."""
    return await _judge(payload, team, db, scored=True)


async def _judge(
    payload: CodeSubmitRequest,
    team: Team,
    db: AsyncSession,
    scored: bool,
) -> SubmissionOut:
    require_running(team)

    question = (
        await db.execute(select(Question).where(Question.id == payload.question_id))
    ).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.type != QuestionType.MAIN:
        raise HTTPException(
            status_code=400, detail="This endpoint is for MAIN questions only"
        )

    allowed = _allowed_languages(question)
    if allowed and payload.language not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{payload.language}' is not allowed. Allowed: {', '.join(allowed)}",
        )
    if payload.language not in settings.LANGUAGE_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown language '{payload.language}'. Supported: "
                   f"{', '.join(settings.LANGUAGE_NAMES)}",
        )
    if len(payload.source_code.encode()) > settings.MAX_SOURCE_BYTES:
        raise HTTPException(status_code=413, detail="Source code is too large")

    state = await _get_state(db, team.id, question.id)

    # Cooldown protects the judge queue. It is not an attempt limit.
    if scored and state.last_submission_at and settings.SUBMIT_COOLDOWN_SECONDS > 0:
        since = (now_naive_utc() - state.last_submission_at).total_seconds()
        if since < settings.SUBMIT_COOLDOWN_SECONDS:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {int(settings.SUBMIT_COOLDOWN_SECONDS - since)}s "
                       "before submitting again.",
            )

    cases = (
        await db.execute(
            select(TestCase)
            .where(TestCase.question_id == question.id)
            .order_by(TestCase.position, TestCase.id)
        )
    ).scalars().all()

    if scored:
        selected = cases
    else:
        selected = [c for c in cases if not c.is_hidden]
        if not selected:
            raise HTTPException(
                status_code=400, detail="This question has no sample tests to run."
            )

    mode = question.compare_mode or CompareMode.TRIM
    jobs = [
        JudgeJob(
            source_code=payload.source_code,
            language=payload.language,
            stdin=case.stdin or "",
            expected_output=case.expected_output or "",
            cpu_time_limit=question.cpu_time_limit or settings.DEFAULT_CPU_TIME_LIMIT,
            wall_time_limit=question.wall_time_limit or settings.DEFAULT_WALL_TIME_LIMIT,
            memory_limit_kb=question.memory_limit_kb or settings.DEFAULT_MEMORY_LIMIT_KB,
        )
        for case in selected
    ]

    submission = Submission(
        team_id=team.id,
        question_id=question.id,
        language=payload.language,
        source_code=payload.source_code,
        scored=scored,
        verdict=SubmissionVerdict.JUDGING,
        tests_total=len(selected),
        created_at=now_naive_utc(),
    )
    db.add(submission)
    await db.flush()

    judge = get_judge()
    error_message: Optional[str] = None

    try:
        outcomes = await judge.run_batch(jobs)
    except Exception as exc:
        # Judge unreachable: no score change, team can retry.
        outcomes = None
        error_message = f"Judge backend unavailable: {exc}"

    if outcomes is None:
        submission.verdict = SubmissionVerdict.ERROR
        submission.error_message = error_message
        submission.finished_at = now_naive_utc()
        await db.commit()
        return SubmissionOut(
            id=submission.id,
            verdict=submission.verdict,
            scored=scored,
            score=0,
            score_delta=0,
            tests_passed=0,
            tests_total=len(selected),
            error_message=error_message,
            results=[],
            best_score=state.best_score or 0,
            team_points=team.points,
        )

    results = [
        _build_result(case, outcome, mode, visible=not case.is_hidden)
        for case, outcome in zip(selected, outcomes)
    ]

    # A compilation error affects every test; surface it once.
    compile_errors = [o for o in outcomes if o.status_id == 6]
    if compile_errors:
        for r in results:
            r.compile_output = r.compile_output or compile_errors[0].compile_output

    judge_error = any(o.status_id == 13 for o in outcomes)
    if judge_error:
        error_message = "Judge internal error. No score was changed - an admin can rejudge."

    points_pool = question.points or question.reward_value or 0
    score, passed, total = _score(points_pool, results, selected)

    for r in results:
        r.submission_id = submission.id
        db.add(r)

    submission.tests_passed = passed
    submission.tests_total = total
    submission.score = 0 if not scored else score
    submission.finished_at = now_naive_utc()
    submission.verdict = scoring.verdict_for(passed, total, judge_error)
    submission.error_message = error_message

    score_delta = 0
    if scored and not judge_error:
        # Lock the team row so concurrent submits cannot lose an update.
        locked = (
            await db.execute(select(Team).where(Team.id == team.id).with_for_update())
        ).scalars().first()

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
    elif scored:
        # Count the attempt, but never change the score on a judge error.
        state.attempts = (state.attempts or 0) + 1
        state.last_submission_at = now_naive_utc()
        submission.score = 0
        submission.score_delta = 0

    await db.commit()
    await db.refresh(submission)

    return SubmissionOut(
        id=submission.id,
        verdict=submission.verdict,
        scored=scored,
        score=submission.score,
        score_delta=submission.score_delta,
        tests_passed=submission.tests_passed,
        tests_total=submission.tests_total,
        error_message=submission.error_message,
        results=[TestResultOut(**row) for row in scoring.public_results(results)],
        best_score=state.best_score or 0,
        team_points=team.points,
    )


@router.get("/submissions")
async def my_submissions(
    question_id: Optional[int] = None,
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
