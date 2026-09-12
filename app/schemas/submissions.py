"""Pydantic models for Run/Submit requests and submission responses."""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List

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
