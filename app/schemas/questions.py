"""Pydantic models for questions and test cases."""

from pydantic import BaseModel, ConfigDict

from app.models import (
    CompareMode,
    MainSubType,
    QuestionDifficulty,
    QuestionStateStatus,
    QuestionType,
)


class QuestionBase(BaseModel):
    title: str
    description: str
    test_cases: str = "[]"
    type: QuestionType = QuestionType.MAIN
    difficulty: QuestionDifficulty | None = None
    reward_value: int = 0
    sub_type: MainSubType | None = None
    starter_code: str | None = None
    allowed_languages: str | None = None
    compare_mode: CompareMode = CompareMode.TRIM
    points: int = 0
    cpu_time_limit: float | None = None
    wall_time_limit: float | None = None
    memory_limit_kb: int | None = None
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
    sub_type: MainSubType | None = None
    difficulty: QuestionDifficulty | None = None
    points: int = 0
    compare_mode: CompareMode = CompareMode.TRIM
    starter_code: str | None = None
    allowed_languages: str | None = None
    order_index: int = 0
    visible_tests: list[TestCasePublic] = []
    attempts: int = 0
    best_score: int = 0
    status: QuestionStateStatus = QuestionStateStatus.ASSIGNED
    model_config = ConfigDict(from_attributes=True)
