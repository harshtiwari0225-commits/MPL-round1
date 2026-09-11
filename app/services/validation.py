"""Request guards for the MAIN-round judge pipeline.

Every rule here answers with an HTTP error BEFORE any code is executed:
question exists and is MAIN, language allowed and known, source within the
size cap, submit cooldown elapsed, and the question has samples to Run.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models import Question, QuestionType, TeamQuestionState, TestCase
from app.schemas import CodeSubmitRequest
from app.services.access import now_naive_utc
from app.services.questions import allowed_languages


async def load_main_question(db: AsyncSession, question_id: int) -> Question:
    question = (
        (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.type != QuestionType.MAIN:
        raise HTTPException(status_code=400, detail="This endpoint is for MAIN questions only")
    return question


def validate_language(question: Question, payload: CodeSubmitRequest) -> None:
    allowed = allowed_languages(question)
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


def validate_source_size(payload: CodeSubmitRequest) -> None:
    if len(payload.source_code.encode()) > settings.MAX_SOURCE_BYTES:
        raise HTTPException(status_code=413, detail="Source code is too large")


def enforce_cooldown(state: TeamQuestionState, scored: bool) -> None:
    # Cooldown protects the judge queue. It is not an attempt limit.
    if scored and state.last_submission_at and settings.SUBMIT_COOLDOWN_SECONDS > 0:
        since = (now_naive_utc() - state.last_submission_at).total_seconds()
        if since < settings.SUBMIT_COOLDOWN_SECONDS:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {int(settings.SUBMIT_COOLDOWN_SECONDS - since)}s "
                "before submitting again.",
            )


def select_cases(cases: list[TestCase], scored: bool) -> list[TestCase]:
    """Submit runs every case; Run only the visible ones (and needs at least one)."""
    if scored:
        return cases
    selected = [c for c in cases if not c.is_hidden]
    if not selected:
        raise HTTPException(status_code=400, detail="This question has no sample tests to run.")
    return selected
