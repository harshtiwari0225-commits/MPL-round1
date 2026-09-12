from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any
from datetime import datetime, timezone

from app.database import get_db
from app.core.config import settings
from app.models import Team, TeamQuestionState, ChallengeSession, QuestionStateStatus, ChallengeStatus
from app.schemas import TeamStatusResponse

router = APIRouter()

# NOTE: these two routes take a raw team_id and require no credential, which is
# the pre-existing IDOR (any team can read any other team). They are kept
# working because the challenge/boost pages still call them. The MAIN round does
# not use them - it uses the token-authenticated /api/main/* routes instead.
# TODO: migrate those pages to X-Team-Token, then lock these down.


@router.get("/{team_id}/status")
async def get_team_status(team_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # Fetch team
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Fetch assigned time boost questions
    boost_result = await db.execute(
        select(TeamQuestionState).where(
            TeamQuestionState.team_id == team_id,
            TeamQuestionState.status == QuestionStateStatus.ASSIGNED
        )
    )
    assigned_boosts = boost_result.scalars().all()
    
    # Fetch active challenge session
    challenge_result = await db.execute(
        select(ChallengeSession).where(
            (ChallengeSession.status == ChallengeStatus.ONGOING) & 
            (
                (ChallengeSession.team1_id == team_id) |
                (ChallengeSession.team2_id == team_id) |
                (ChallengeSession.team3_id == team_id)
            )
        )
    )
    active_challenge = challenge_result.scalars().first()
    
    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "points": team.points,
            "timer_start_time": team.timer_start_time,
            "extra_time_seconds": team.extra_time_seconds,
            "main_question_id": team.main_question_id,
        },
        "assigned_time_boosts": [boost.question_id for boost in assigned_boosts],
        "active_challenge_session": {
            "id": active_challenge.id,
            "question_id": active_challenge.question_id
        } if active_challenge else None
    }

@router.get("/{team_id}/time-remaining")
async def get_time_remaining(team_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.timer_start_time is None:
        return {
            "started": False,
            "seconds_remaining": None,
            "total_allowed_seconds": None,
            "expired": False,
        }

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    elapsed = (now - team.timer_start_time).total_seconds()
    total_allowed = settings.EVENT_DURATION_SECONDS + team.extra_time_seconds
    seconds_remaining = max(0, total_allowed - elapsed)

    return {
        "started": True,
        "seconds_remaining": int(seconds_remaining),
        "total_allowed_seconds": total_allowed,
        "extra_time_seconds": team.extra_time_seconds,
        "expired": seconds_remaining <= 0,
    }
