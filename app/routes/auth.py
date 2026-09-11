from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
import random

from app.database import get_db
from app.models import Team, Question, QuestionType, TeamQuestionState, QuestionStateStatus
from app.schemas import TeamLogin, TeamStatusResponse
from app.services.access import new_session_token, now_naive_utc

router = APIRouter()


@router.post("/login", response_model=TeamStatusResponse)
async def login(login_data: TeamLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == login_data.name))
    team = result.scalars().first()

    if not team or team.passcode != login_data.passcode:
        raise HTTPException(status_code=401, detail="Invalid team name or passcode")

    first_login = team.timer_start_time is None

    if first_login:
        # Start the clock and hand the team every MAIN question.
        team.timer_start_time = now_naive_utc()

        main_questions = (
            await db.execute(
                select(Question)
                .where(Question.type == QuestionType.MAIN)
                .order_by(Question.order_index, Question.id)
            )
        ).scalars().all()

        for question in main_questions:
            existing = (
                await db.execute(
                    select(TeamQuestionState).where(
                        TeamQuestionState.team_id == team.id,
                        TeamQuestionState.question_id == question.id,
                    )
                )
            ).scalars().first()
            if not existing:
                db.add(
                    TeamQuestionState(
                        team_id=team.id,
                        question_id=question.id,
                        status=QuestionStateStatus.ASSIGNED,
                    )
                )

        if main_questions:
            team.main_question_id = random.choice(main_questions).id

    # Always (re)issue a session token so the team can call /api/main/*.
    team.session_token = new_session_token()

    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team
