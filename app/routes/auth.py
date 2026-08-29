from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
import random

from app.database import get_db
from app.models import Team, Question, QuestionType
from app.schemas import TeamLogin, TeamStatusResponse

router = APIRouter()

@router.post("/login", response_model=TeamStatusResponse)
async def login(login_data: TeamLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == login_data.name))
    team = result.scalars().first()
    
    if not team or team.passcode != login_data.passcode:
        raise HTTPException(status_code=401, detail="Invalid team name or passcode")
    
    if team.timer_start_time is None:
        # First login, start timer and assign random main question
        team.timer_start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        main_questions_result = await db.execute(select(Question).where(Question.type == QuestionType.MAIN))
        main_questions = main_questions_result.scalars().all()
        
        if main_questions:
            assigned_q = random.choice(main_questions)
            team.main_question_id = assigned_q.id
        
        db.add(team)
        await db.commit()
        await db.refresh(team)
    
    return team
