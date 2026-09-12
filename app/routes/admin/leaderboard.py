"""Leaderboard (public) and judge health check (admin)."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.database import get_db
from app.models import Question, QuestionType, Team, TeamQuestionState, QuestionStateStatus
from app.schemas import LeaderboardRow
from app.routes.admin.deps import verify_admin
from app.services.access import time_state
from app.services.judge import get_judge

router = APIRouter()


@router.get("/leaderboard", response_model=List[LeaderboardRow])
async def leaderboard(db: AsyncSession = Depends(get_db)):
    """Public-ish board. MAIN score = sum of best score per question."""
    teams = (await db.execute(select(Team).order_by(Team.id))).scalars().all()
    main_questions = (
        await db.execute(select(Question.id).where(Question.type == QuestionType.MAIN))
    ).scalars().all()

    rows = []
    for team in teams:
        states = (
            await db.execute(
                select(TeamQuestionState).where(
                    TeamQuestionState.team_id == team.id,
                    TeamQuestionState.question_id.in_(main_questions or [-1]),
                )
            )
        ).scalars().all()

        main_score = sum(s.best_score or 0 for s in states)
        solved = sum(1 for s in states if s.status == QuestionStateStatus.SOLVED)
        attempts = sum(s.attempts or 0 for s in states)
        started, remaining, expired = time_state(team)

        rows.append(
            LeaderboardRow(
                team_id=team.id,
                team_name=team.name,
                points=team.points or 0,
                main_score=main_score,
                solved=solved,
                attempts=attempts,
                started=started,
                expired=expired,
                seconds_remaining=remaining if started else None,
            )
        )

    rows.sort(key=lambda r: (-r.points, r.attempts, r.team_id))
    return rows


@router.get("/judge/health")
async def judge_health(_: None = Depends(verify_admin)):
    client = get_judge()
    healthy = await client.health()
    detail = {"backend": settings.JUDGE_BACKEND, "healthy": healthy}
    if healthy and hasattr(client, "ensure_languages"):
        detail["languages"] = await client.ensure_languages()
    return detail
