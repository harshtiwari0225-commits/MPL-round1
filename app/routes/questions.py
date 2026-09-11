from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import Question, TestCase
from app.schemas import QuestionResponse, TestCasePublic

router = APIRouter()


class PublicQuestion(QuestionResponse):
    """Question minus test cases.

    ``test_cases`` used to be returned in full, which meant any participant
    could read every hidden test in the bank. Test data now leaves the server
    only through /api/main/questions (visible cases) and the admin API.
    """
    test_cases: str = ""


@router.get("/{question_id}", response_model=PublicQuestion)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    data = PublicQuestion(
        id=question.id,
        title=question.title,
        description=question.description,
        test_cases="",
        type=question.type,
        difficulty=question.difficulty,
        reward_value=question.reward_value,
        sub_type=question.sub_type,
        starter_code=question.starter_code,
        allowed_languages=question.allowed_languages,
        compare_mode=question.compare_mode,
        points=question.points,
        cpu_time_limit=question.cpu_time_limit,
        wall_time_limit=question.wall_time_limit,
        memory_limit_kb=question.memory_limit_kb,
        order_index=question.order_index,
    )
    return data


@router.get("/{question_id}/sample-tests", response_model=list[TestCasePublic])
async def sample_tests(question_id: int, db: AsyncSession = Depends(get_db)):
    """Only the non-hidden test cases."""
    rows = (
        await db.execute(
            select(TestCase)
            .where(TestCase.question_id == question_id, TestCase.is_hidden.is_(False))
            .order_by(TestCase.position, TestCase.id)
        )
    ).scalars().all()
    return [
        TestCasePublic(id=c.id, stdin=c.stdin, expected_output=c.expected_output, position=c.position)
        for c in rows
    ]
