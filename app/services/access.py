"""Team authentication and clock helpers.

Previously every team endpoint took a raw ``team_id`` from the URL with no
credential at all, so any team could read any other team's state. Team routes
now require the ``X-Team-Token`` header issued at login.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Tuple

from typing import Optional

from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.database import get_db
from app.models import Team


def now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


async def get_current_team(
    x_team_token: Optional[str] = Header(None, alias="X-Team-Token"),
    db: AsyncSession = Depends(get_db),
) -> Team:
    if not x_team_token:
        raise HTTPException(status_code=401, detail="Missing X-Team-Token header")
    result = await db.execute(
        select(Team).where(Team.session_token == x_team_token)
    )
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=401, detail="Invalid or missing team token")
    return team


def time_state(team: Team) -> Tuple[bool, int, bool]:
    """Return (started, seconds_remaining, expired) for a team."""
    if team.timer_start_time is None:
        return False, 0, False
    elapsed = (now_naive_utc() - team.timer_start_time).total_seconds()
    total_allowed = settings.EVENT_DURATION_SECONDS + (team.extra_time_seconds or 0)
    remaining = max(0, int(total_allowed - elapsed))
    return True, remaining, remaining <= 0


def require_running(team: Team) -> None:
    """Reject submissions once the team's clock has run out."""
    started, remaining, expired = time_state(team)
    if not started:
        raise HTTPException(
            status_code=403, detail="Your clock has not started. Log in first."
        )
    if expired:
        raise HTTPException(
            status_code=403,
            detail="Your time is up. Ask an admin if you were granted extra minutes.",
        )
