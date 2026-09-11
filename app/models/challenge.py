from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum

from app.database import Base
from app.models.enums import ChallengeStatus


class ChallengeSession(Base):
    __tablename__ = "challenge_sessions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.ONGOING)
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    team3_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    winner_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
