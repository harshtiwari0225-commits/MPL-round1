from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class QuestionType(str, enum.Enum):
    MAIN = "MAIN"
    TIME_BOOST = "TIME_BOOST"
    CHALLENGE = "CHALLENGE"

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

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    passcode = Column(String)
    points = Column(Integer, default=1000)
    timer_start_time = Column(DateTime, nullable=True)
    extra_time_seconds = Column(Integer, default=0)
    main_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    
    question_states = relationship("TeamQuestionState", back_populates="team")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    test_cases = Column(String) # Could be JSON or Text
    type = Column(SQLEnum(QuestionType), default=QuestionType.MAIN)
    difficulty = Column(SQLEnum(QuestionDifficulty), nullable=True)
    reward_value = Column(Integer, default=0) # Points for challenge, seconds for time boost

class TeamQuestionState(Base):
    __tablename__ = "team_question_states"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    status = Column(SQLEnum(QuestionStateStatus), default=QuestionStateStatus.ASSIGNED)
    
    team = relationship("Team", back_populates="question_states")
    question = relationship("Question")

class ChallengeSession(Base):
    __tablename__ = "challenge_sessions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.ONGOING)
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    team3_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    winner_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
