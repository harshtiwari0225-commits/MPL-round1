"""Builds the team-facing view of the MAIN questions.

Backs GET /api/main/questions. Hidden tests are stripped here: only
non-hidden TestCase rows are ever placed into the response.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import CompareMode, Question, QuestionType, Team, TestCase
from app.schemas import MainQuestionPublic, TestCasePublic
from app.services.progress import get_state
from app.services.questions import starter_bundle


async def team_question_views(db: AsyncSession, team: Team) -> List[MainQuestionPublic]:
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

        state = await get_state(db, team.id, question.id)
        await db.commit()

        visible = [
            TestCasePublic(
                id=c.id, stdin=c.stdin, expected_output=c.expected_output, position=c.position
            )
            for c in cases
            if not c.is_hidden
        ]

        out.append(
            MainQuestionPublic(
                id=question.id,
                title=question.title,
                description=question.description,
                sub_type=question.sub_type,
                difficulty=question.difficulty,
                points=question.points or question.reward_value or 0,
                compare_mode=question.compare_mode or CompareMode.TRIM,
                starter_code=starter_bundle(question),
                allowed_languages=question.allowed_languages,
                order_index=question.order_index or 0,
                visible_tests=visible,
                attempts=state.attempts or 0,
                best_score=state.best_score or 0,
                status=state.status,
            )
        )
    return out
