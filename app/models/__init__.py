"""ORM models (all tables).

Split into one module per aggregate so every file stays small; this package
re-exports everything, so existing imports such as
``from app.models import Team, Question`` keep working unchanged.

Importing this package registers every table on ``Base.metadata``
(see app/main.py lifespan and reset_db.py).
"""

from app.models.challenge import ChallengeSession
from app.models.enums import (
    ChallengeStatus,
    CompareMode,
    MainSubType,
    QuestionDifficulty,
    QuestionStateStatus,
    QuestionType,
    SubmissionVerdict,
)
from app.models.progress import TeamQuestionState
from app.models.question import Question, TestCase
from app.models.submission import Submission, SubmissionResult
from app.models.team import Team

__all__ = [
    "QuestionType",
    "MainSubType",
    "CompareMode",
    "QuestionDifficulty",
    "QuestionStateStatus",
    "ChallengeStatus",
    "SubmissionVerdict",
    "Team",
    "Question",
    "TestCase",
    "TeamQuestionState",
    "Submission",
    "SubmissionResult",
    "ChallengeSession",
]
