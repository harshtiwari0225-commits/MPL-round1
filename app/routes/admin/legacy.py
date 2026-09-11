"""Unchanged legacy endpoints (CHALLENGE / TIME_BOOST - out of scope for now).

These power boost.html and challenge.html: the admin assigns a boost question
or opens a challenge session, and manually marks it solved after reviewing
the team's answer. MAIN questions are graded automatically instead.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import (
    Team, Question, TeamQuestionState, ChallengeSession, QuestionType,
    QuestionStateStatus, ChallengeStatus,
)
from app.schemas import ChallengeCreate, AssignBoost, ReviewMarkSolved
from app.routes.admin.deps import verify_admin

router = APIRouter()


@router.post("/teams/{team_id}/assign-boost")
async def assign_boost(team_id: int, boost: AssignBoost, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    question = (await db.execute(select(Question).where(Question.id == boost.question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.question_id == boost.question_id,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="That question is already assigned to this team")

    db.add(
        TeamQuestionState(
            team_id=team_id,
            question_id=boost.question_id,
            status=QuestionStateStatus.ASSIGNED,
        )
    )
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
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
        state = state_result.scalars().first()
        if state:
            state.status = QuestionStateStatus.SOLVED
            team.extra_time_seconds = (team.extra_time_seconds or 0) + question.reward_value
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
                    (ChallengeSession.team1_id == review.team_id)
                    | (ChallengeSession.team2_id == review.team_id)
                    | (ChallengeSession.team3_id == review.team_id)
                ),
            )
        )
        challenge = challenge_result.scalars().first()
        if challenge:
            challenge.status = ChallengeStatus.COMPLETED
            challenge.winner_team_id = review.team_id
            team.points = (team.points or 0) + question.reward_value
            db.add(challenge)
            db.add(team)
            await db.commit()
            return {"message": "Challenge won, points added"}

    if question.type == QuestionType.MAIN:
        return {
            "message": "MAIN questions are graded automatically by the judge. "
                       "Use GET /api/admin/leaderboard to see scores."
        }

    return {"message": "No active assignment found for this question"}
