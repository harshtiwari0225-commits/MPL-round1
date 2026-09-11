"""Run / Submit pipeline for the MAIN round.

Backs POST /api/main/run and POST /api/main/submit.

Scoring rules (confirmed with the organiser):
  * partial credit - 20% of hidden tests passed = 20% of the question's points
  * each of the 3 questions has its own independent points
  * no negative marking, unlimited attempts
  * a team's score for a question is the BEST score across all attempts
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models import CompareMode, Submission, SubmissionVerdict, Team, TestCase
from app.schemas import CodeSubmitRequest, SubmissionOut, TestResultOut
from app.services import scoring, validation
from app.services.access import now_naive_utc, require_running
from app.services.judge import JudgeJob, get_judge
from app.services.progress import apply_score, get_state, record_error_attempt
from app.services.results import build_result, propagate_compile_error


async def judge_submission(
    payload: CodeSubmitRequest,
    team: Team,
    db: AsyncSession,
    scored: bool,
) -> SubmissionOut:
    require_running(team)

    question = await validation.load_main_question(db, payload.question_id)
    validation.validate_language(question, payload)
    validation.validate_source_size(payload)

    state = await get_state(db, team.id, question.id)
    validation.enforce_cooldown(state, scored)

    cases = (
        (
            await db.execute(
                select(TestCase)
                .where(TestCase.question_id == question.id)
                .order_by(TestCase.position, TestCase.id)
            )
        )
        .scalars()
        .all()
    )
    selected = validation.select_cases(cases, scored)

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
    error_message: str | None = None

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
        build_result(case, outcome, mode, visible=not case.is_hidden)
        for case, outcome in zip(selected, outcomes)
    ]
    propagate_compile_error(results, outcomes)

    judge_error = any(o.status_id == 13 for o in outcomes)
    if judge_error:
        error_message = "Judge internal error. No score was changed - an admin can rejudge."

    points_pool = question.points or question.reward_value or 0
    score, passed, total = scoring.score_submission(points_pool, results, selected)

    for r in results:
        r.submission_id = submission.id
        db.add(r)

    submission.tests_passed = passed
    submission.tests_total = total
    submission.score = 0 if not scored else score
    submission.finished_at = now_naive_utc()
    submission.verdict = scoring.verdict_for(passed, total, judge_error)
    submission.error_message = error_message

    if scored and not judge_error:
        await apply_score(db, team, state, submission, score, passed, total)
    elif scored:
        # Count the attempt, but never change the score on a judge error.
        record_error_attempt(state, submission)

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
