"""Code-execution sandbox client.

Two interchangeable backends:

  * ``MockJudge``    - runs code locally (no Docker). Development only.
  * ``Judge0Client`` - talks to a self-hosted Judge0 CE instance. Event day.

Switch with the ``JUDGE_BACKEND`` env var ("mock" | "judge0"). Nothing else in
the codebase knows which one is in use.

Submodules:
    base        JudgeJob / JudgeOutcome DTOs + Judge0 status-id constants
    execution   local subprocess helpers (mock backend only, NOT a sandbox)
    mock        MockJudge
    client      Judge0Client (batch submit over HTTP)
    polling     Judge0 batch polling loop + base64 decoding helpers

This package re-exports the public names, so existing imports such as
``from app.services.judge import JudgeJob, get_judge`` keep working.
"""

from app.core.config import settings
from app.services.judge.base import (
    PENDING_STATUS_IDS,
    STATUS_ACCEPTED,
    STATUS_COMPILATION_ERROR,
    STATUS_INTERNAL_ERROR,
    STATUS_TIME_LIMIT,
    STATUS_WRONG_ANSWER,
    JudgeJob,
    JudgeOutcome,
)
from app.services.judge.client import Judge0Client
from app.services.judge.mock import MockJudge

# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

_client = None


def get_judge():
    """Return the configured judge backend (cached)."""
    global _client
    if _client is None:
        if settings.JUDGE_BACKEND.lower() == "judge0":
            _client = Judge0Client()
        else:
            _client = MockJudge()
    return _client


def reset_judge() -> None:
    global _client
    _client = None


__all__ = [
    "JudgeJob",
    "JudgeOutcome",
    "PENDING_STATUS_IDS",
    "STATUS_ACCEPTED",
    "STATUS_WRONG_ANSWER",
    "STATUS_TIME_LIMIT",
    "STATUS_COMPILATION_ERROR",
    "STATUS_INTERNAL_ERROR",
    "MockJudge",
    "Judge0Client",
    "get_judge",
    "reset_judge",
]
