from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import SubmissionVerdict


class Submission(Base):
    """One "Run" or "Submit" of code by a team."""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)

    language = Column(String)  # our key: python / c / cpp / java
    source_code = Column(Text)

    scored = Column(Boolean, default=False)  # False for "Run", True for "Submit"
    verdict = Column(SQLEnum(SubmissionVerdict), default=SubmissionVerdict.QUEUED)

    score = Column(Integer, default=0)  # points earned by THIS submission
    score_delta = Column(Integer, default=0)  # points actually added to the team (best-score delta)
    tests_passed = Column(Integer, default=0)
    tests_total = Column(Integer, default=0)

    judge_tokens = Column(Text, nullable=True)  # JSON list of Judge0 tokens
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    results = relationship(
        "SubmissionResult", back_populates="submission", cascade="all, delete-orphan"
    )


class SubmissionResult(Base):
    """Per-test-case outcome of a submission."""

    __tablename__ = "submission_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)

    is_hidden = Column(Boolean, default=True)
    passed = Column(Boolean, default=False)

    judge_status_id = Column(Integer, nullable=True)  # raw Judge0 status id
    judge_status = Column(String, nullable=True)  # raw Judge0 status description
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)  # only echoed for visible tests
    stdin = Column(Text, nullable=True)  # only echoed for visible tests

    time_seconds = Column(Float, nullable=True)
    memory_kb = Column(Float, nullable=True)

    submission = relationship("Submission", back_populates="results")


Index("ix_submissions_team_question", Submission.team_id, Submission.question_id)
