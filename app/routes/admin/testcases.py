"""Admin test-case CRUD. Admin sees hidden tests; teams never do."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import Question, TestCase
from app.routes.admin.deps import verify_admin
from app.schemas import TestCaseAdmin, TestCaseCreate

router = APIRouter()


@router.get("/questions/{question_id}/test-cases", response_model=list[TestCaseAdmin])
async def list_test_cases(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Admin sees hidden tests too."""
    return (
        (
            await db.execute(
                select(TestCase)
                .where(TestCase.question_id == question_id)
                .order_by(TestCase.position, TestCase.id)
            )
        )
        .scalars()
        .all()
    )


@router.post("/questions/{question_id}/test-cases")
async def add_test_cases(
    question_id: int,
    cases: list[TestCaseCreate],
    replace: bool = Query(False, description="Delete existing test cases first"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    question = (
        (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if replace:
        existing = (
            (await db.execute(select(TestCase).where(TestCase.question_id == question_id)))
            .scalars()
            .all()
        )
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
