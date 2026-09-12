"""Pydantic models for Run/Submit requests and submission responses."""

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import SubmissionVerdict


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
    judge_status: str | None = None
    judge_status_id: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    compile_output: str | None = None
    time_seconds: float | None = None
    memory_kb: float | None = None
    is_hidden: bool = True
    # populated for visible tests only
    stdin: str | None = None
    expected_output: str | None = None


class SubmissionOut(BaseModel):
    id: int
    verdict: SubmissionVerdict
    scored: bool
    score: int
    score_delta: int
    tests_passed: int
    tests_total: int
    error_message: str | None = None
    results: list[TestResultOut] = []
    best_score: int = 0
    team_points: int = 0
    model_config = ConfigDict(from_attributes=True)
