"""Pydantic request/response models.

Split into one module per domain so every file stays small; this package
re-exports everything, so existing imports such as
``from app.schemas import TeamLogin, SubmissionOut`` keep working unchanged.
"""
from app.schemas.questions import (
    QuestionBase,
    QuestionCreate,
    QuestionResponse,
    TestCaseBase,
    TestCaseCreate,
    TestCaseAdmin,
    TestCasePublic,
    MainQuestionPublic,
)
from app.schemas.teams import (
    TeamBase,
    TeamCreate,
    TeamLogin,
    TeamStatusResponse,
    AdminLogin,
    ChallengeCreate,
    AssignBoost,
    ReviewMarkSolved,
    AddTimeRequest,
)
from app.schemas.submissions import (
    CodeSubmitRequest,
    TestResultOut,
    SubmissionOut,
)
from app.schemas.admin import (
    LeaderboardRow,
    RejudgeResponse,
)

__all__ = [
    "QuestionBase", "QuestionCreate", "QuestionResponse",
    "TestCaseBase", "TestCaseCreate", "TestCaseAdmin", "TestCasePublic",
    "MainQuestionPublic",
    "TeamBase", "TeamCreate", "TeamLogin", "TeamStatusResponse", "AdminLogin",
    "ChallengeCreate", "AssignBoost", "ReviewMarkSolved", "AddTimeRequest",
    "CodeSubmitRequest", "TestResultOut", "SubmissionOut",
    "LeaderboardRow", "RejudgeResponse",
]
