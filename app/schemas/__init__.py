"""Pydantic request/response models.

Split into one module per domain so every file stays small; this package
re-exports everything, so existing imports such as
``from app.schemas import TeamLogin, SubmissionOut`` keep working unchanged.
"""

from app.schemas.admin import (
    LeaderboardRow,
    RejudgeResponse,
)
from app.schemas.questions import (
    MainQuestionPublic,
    QuestionBase,
    QuestionCreate,
    QuestionResponse,
    TestCaseAdmin,
    TestCaseBase,
    TestCaseCreate,
    TestCasePublic,
)
from app.schemas.submissions import (
    CodeSubmitRequest,
    SubmissionOut,
    TestResultOut,
)
from app.schemas.teams import (
    AddTimeRequest,
    AdminLogin,
    AssignBoost,
    ChallengeCreate,
    ReviewMarkSolved,
    TeamBase,
    TeamCreate,
    TeamLogin,
    TeamStatusResponse,
)

__all__ = [
    "QuestionBase",
    "QuestionCreate",
    "QuestionResponse",
    "TestCaseBase",
    "TestCaseCreate",
    "TestCaseAdmin",
    "TestCasePublic",
    "MainQuestionPublic",
    "TeamBase",
    "TeamCreate",
    "TeamLogin",
    "TeamStatusResponse",
    "AdminLogin",
    "ChallengeCreate",
    "AssignBoost",
    "ReviewMarkSolved",
    "AddTimeRequest",
    "CodeSubmitRequest",
    "TestResultOut",
    "SubmissionOut",
    "LeaderboardRow",
    "RejudgeResponse",
]
