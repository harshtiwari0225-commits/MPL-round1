from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from app.models import (
    QuestionType, QuestionDifficulty, QuestionStateStatus, ChallengeStatus,
    MainSubType, CompareMode, SubmissionVerdict,
)


# ── Questions ───────────────────────────────────────────────────────────────

class QuestionBase(BaseModel):
    title: str
    description: str
    test_cases: str = "[]"
    type: QuestionType = QuestionType.MAIN
    difficulty: Optional[QuestionDifficulty] = None
    reward_value: int = 0
    sub_type: Optional[MainSubType] = None
    starter_code: Optional[str] = None
    allowed_languages: Optional[str] = None
    compare_mode: CompareMode = CompareMode.TRIM
    points: int = 0
    cpu_time_limit: Optional[float] = None
    wall_time_limit: Optional[float] = None
    memory_limit_kb: Optional[int] = None
    order_index: int = 0


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TestCaseBase(BaseModel):
    stdin: str = ""
    expected_output: str = ""
    is_hidden: bool = True
    weight: float = 1.0
    position: int = 0


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseAdmin(TestCaseBase):
    """Admin only. Includes hidden tests."""
    id: int
    question_id: int
    model_config = ConfigDict(from_attributes=True)


class TestCasePublic(BaseModel):
    """What a team may see. Hidden tests are never included."""
    id: int
    stdin: str = ""
    expected_output: str = ""
    position: int = 0
    model_config = ConfigDict(from_attributes=True)


class MainQuestionPublic(BaseModel):
    """A MAIN question as the team sees it: no hidden tests, no correct flags."""
    id: int
    title: str
    description: str
    sub_type: Optional[MainSubType] = None
    difficulty: Optional[QuestionDifficulty] = None
    points: int = 0
    compare_mode: CompareMode = CompareMode.TRIM
    starter_code: Optional[str] = None
    allowed_languages: Optional[str] = None
    order_index: int = 0
    visible_tests: List[TestCasePublic] = []
    attempts: int = 0
    best_score: int = 0
    status: QuestionStateStatus = QuestionStateStatus.ASSIGNED
    model_config = ConfigDict(from_attributes=True)


# ── Teams ───────────────────────────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    passcode: str


class TeamLogin(BaseModel):
    name: str
    passcode: str


class TeamStatusResponse(BaseModel):
    id: int
    name: str
    points: int
    timer_start_time: Optional[datetime]
    extra_time_seconds: int
    main_question_id: Optional[int]
    session_token: Optional[str] = None   # returned on login only
    model_config = ConfigDict(from_attributes=True)


class AdminLogin(BaseModel):
    passcode: str


class ChallengeCreate(BaseModel):
    question_id: int
    team1_id: int
    team2_id: int
    team3_id: Optional[int] = None


class AssignBoost(BaseModel):
    question_id: int


class ReviewMarkSolved(BaseModel):
    team_id: int
    question_id: int


class AddTimeRequest(BaseModel):
    seconds: int


# ── Submissions ─────────────────────────────────────────────────────────────

class CodeSubmitRequest(BaseModel):
    question_id: int
    language: str
    source_code: str

    @field_validator("language")
    @classmethod
    def normalise_language(cls, v: str) -> str:
        v = (v or "").strip().lower()
        aliases = {"python3": "python", "py": "python", "c++": "cpp", "g++": "cpp"}
        return aliases.get(v, v)


class TestResultOut(BaseModel):
    passed: bool
    judge_status: Optional[str] = None
    judge_status_id: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    time_seconds: Optional[float] = None
    memory_kb: Optional[float] = None
    is_hidden: bool = True
    # populated for visible tests only
    stdin: Optional[str] = None
    expected_output: Optional[str] = None


class SubmissionOut(BaseModel):
    id: int
    verdict: SubmissionVerdict
    scored: bool
    score: int
    score_delta: int
    tests_passed: int
    tests_total: int
    error_message: Optional[str] = None
    results: List[TestResultOut] = []
    best_score: int = 0
    team_points: int = 0
    model_config = ConfigDict(from_attributes=True)


# ── Admin views ─────────────────────────────────────────────────────────────

class LeaderboardRow(BaseModel):
    team_id: int
    team_name: str
    points: int
    main_score: int
    solved: int
    attempts: int
    started: bool
    expired: bool
    seconds_remaining: Optional[int] = None


class RejudgeResponse(BaseModel):
    submission_id: int
    verdict: SubmissionVerdict
    old_score: int
    new_score: int
    score_delta: int
