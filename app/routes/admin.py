from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.database import get_db
from app.core.config import settings
from app.models import Team, Question, TeamQuestionState, ChallengeSession, QuestionType, QuestionStateStatus, ChallengeStatus
from app.schemas import TeamCreate, QuestionCreate, ChallengeCreate, AssignBoost, ReviewMarkSolved

router = APIRouter()

def verify_admin(admin_passcode: str = Header(...)):
    if admin_passcode != settings.ADMIN_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/teams")
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    new_team = Team(name=team.name, passcode=team.passcode)
    db.add(new_team)
    await db.commit()
    return {"message": "Team created successfully", "id": new_team.id}

@router.get("/teams")
async def list_teams(db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    result = await db.execute(select(Team))
    return result.scalars().all()

@router.post("/questions")
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    new_question = Question(**question.model_dump())
    db.add(new_question)
    await db.commit()
    return {"message": "Question created", "id": new_question.id}

@router.post("/teams/{team_id}/assign-boost")
async def assign_boost(team_id: int, boost: AssignBoost, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    state = TeamQuestionState(team_id=team_id, question_id=boost.question_id, status=QuestionStateStatus.ASSIGNED)
    db.add(state)
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
    # Check if it's a time boost or a challenge
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
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED
            )
        )
        state = state_result.scalars().first()
        if state:
            state.status = QuestionStateStatus.SOLVED
            team.extra_time_seconds += question.reward_value
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
                    (ChallengeSession.team1_id == review.team_id) |
                    (ChallengeSession.team2_id == review.team_id) |
                    (ChallengeSession.team3_id == review.team_id)
                )
            )
        )
        challenge = challenge_result.scalars().first()
        if challenge:
            challenge.status = ChallengeStatus.COMPLETED
            challenge.winner_team_id = review.team_id
            team.points += question.reward_value
            db.add(challenge)
            db.add(team)
            await db.commit()
            return {"message": "Challenge won, points added"}

    return {"message": "No active assignment found for this question"}
