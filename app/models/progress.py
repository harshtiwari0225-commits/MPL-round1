from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import QuestionStateStatus


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
