from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text,
    ForeignKey, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import QuestionType, MainSubType, CompareMode, QuestionDifficulty


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
