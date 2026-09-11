from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


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
