from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text,
    ForeignKey, Enum as SQLEnum, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class QuestionType(str, enum.Enum):
    MAIN = "MAIN"
    TIME_BOOST = "TIME_BOOST"
    CHALLENGE = "CHALLENGE"


class MainSubType(str, enum.Enum):
    """The three flavours of MAIN coding question."""
    DEBUGGING = "DEBUGGING"      # broken starter code, fix it
    MATH = "MATH"                # implement a formula / numeric routine
    LEETCODE = "LEETCODE"        # classic DSA problem


class CompareMode(str, enum.Enum):
    """How stdout is compared against the expected output.

    Judge0 compares byte-exact. We do our own comparison so that math
    questions are not failed by '0.30000000000000004' vs '0.3'.
    """
    EXACT = "EXACT"      # byte-for-byte
    TRIM = "TRIM"        # strip trailing whitespace on each line + trailing blank lines
    TOKENS = "TOKENS"    # whitespace-insensitive token compare
    FLOAT = "FLOAT"      # numeric compare with tolerance (1e-6 relative)


class QuestionDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionStateStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    SOLVED = "SOLVED"
    FAILED = "FAILED"


class ChallengeStatus(str, enum.Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class SubmissionVerdict(str, enum.Enum):
    QUEUED = "QUEUED"
    JUDGING = "JUDGING"
    PASSED = "PASSED"      # every hidden test accepted
    PARTIAL = "PARTIAL"    # some hidden tests accepted (partial credit)
    FAILED = "FAILED"      # ran, but no hidden test accepted
    ERROR = "ERROR"        # judge internal error / unreachable. No score change.


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    passcode = Column(String)

    # Session token issued at login. Required by X-Team-Token on team routes.
    session_token = Column(String, unique=True, index=True, nullable=True)

    points = Column(Integer, default=1000)
    timer_start_time = Column(DateTime, nullable=True)

    # Extra minutes granted by admin (or by time boosts). Seconds.
    extra_time_seconds = Column(Integer, default=0)

    main_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)

    question_states = relationship("TeamQuestionState", back_populates="team")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    test_cases = Column(String)  # legacy blob, kept for back-compat. New code uses TestCase.

    type = Column(SQLEnum(QuestionType), default=QuestionType.MAIN)
    difficulty = Column(SQLEnum(QuestionDifficulty), nullable=True)
    reward_value = Column(Integer, default=0)

    # ── MAIN-event fields ────────────────────────────────────────────────────
    sub_type = Column(SQLEnum(MainSubType), nullable=True)

    # JSON: {"python": "def solve():\n    pass", "cpp": "...", ...}
    # For DEBUGGING questions this is the BROKEN code the team must fix.
    starter_code = Column(Text, nullable=True)

    # JSON list of our language keys allowed for this question: ["python","cpp"]
    # Empty / NULL means all supported languages are allowed.
    allowed_languages = Column(Text, nullable=True)

    compare_mode = Column(SQLEnum(CompareMode), default=CompareMode.TRIM)

    # Points awarded for a perfect solve. Partial credit = points * hidden_passed/hidden_total
    points = Column(Integer, default=0)

    cpu_time_limit = Column(Float, nullable=True)
    wall_time_limit = Column(Float, nullable=True)
    memory_limit_kb = Column(Integer, nullable=True)

    # Every team gets every MAIN question. This is a display ordering hint.
    order_index = Column(Integer, default=0)

    testcase_rows = relationship(
        "TestCase", back_populates="question", cascade="all, delete-orphan"
    )


class TestCase(Base):
    """One stdin -> expected stdout pair.

    is_hidden=False  -> shown to the team, used by "Run"
    is_hidden=True   -> never leaves the server, used by "Submit"
    """
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), index=True)

    stdin = Column(Text, default="")
    expected_output = Column(Text, default="")

    is_hidden = Column(Boolean, default=True)
    # Weight inside the hidden pool. 1 = equal weighting.
    weight = Column(Float, default=1.0)
    position = Column(Integer, default=0)

    question = relationship("Question", back_populates="testcase_rows")


class TeamQuestionState(Base):
    __tablename__ = "team_question_states"
    __table_args__ = (
        # Prevents the duplicate-assignment double-credit bug.
        UniqueConstraint("team_id", "question_id", name="uq_team_question"),
    )

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    status = Column(SQLEnum(QuestionStateStatus), default=QuestionStateStatus.ASSIGNED)

    # MAIN-event progress
    attempts = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    best_submission_id = Column(Integer, nullable=True)
    first_solved_at = Column(DateTime, nullable=True)
    last_submission_at = Column(DateTime, nullable=True)

    team = relationship("Team", back_populates="question_states")
    question = relationship("Question")


class Submission(Base):
    """One "Run" or "Submit" of code by a team."""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)

    language = Column(String)              # our key: python / c / cpp / java
    source_code = Column(Text)

    scored = Column(Boolean, default=False)   # False for "Run", True for "Submit"
    verdict = Column(SQLEnum(SubmissionVerdict), default=SubmissionVerdict.QUEUED)

    score = Column(Integer, default=0)          # points earned by THIS submission
    score_delta = Column(Integer, default=0)    # points actually added to the team (best-score delta)
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

    judge_status_id = Column(Integer, nullable=True)   # raw Judge0 status id
    judge_status = Column(String, nullable=True)       # raw Judge0 status description
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)      # only echoed for visible tests
    stdin = Column(Text, nullable=True)                # only echoed for visible tests

    time_seconds = Column(Float, nullable=True)
    memory_kb = Column(Float, nullable=True)

    submission = relationship("Submission", back_populates="results")


class ChallengeSession(Base):
    __tablename__ = "challenge_sessions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.ONGOING)
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    team3_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    winner_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)


Index("ix_submissions_team_question", Submission.team_id, Submission.question_id)
