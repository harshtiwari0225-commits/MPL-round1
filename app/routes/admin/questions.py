"""Admin question management: create and patch questions."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import Question
from app.routes.admin.deps import verify_admin
from app.schemas import QuestionCreate

router = APIRouter()


@router.post("/questions")
async def create_question(
    question: QuestionCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)
):
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
    question = (
        (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    allowed = {c.name for c in Question.__table__.columns} - {"id"}
    for key, value in payload.items():
        if key in allowed:
            setattr(question, key, value)
    await db.commit()
    return {"message": "Question updated", "id": question.id}
