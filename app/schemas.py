from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models import QuestionType, QuestionDifficulty, QuestionStateStatus, ChallengeStatus

class QuestionBase(BaseModel):
    title: str
    description: str
    test_cases: str
    type: QuestionType
    difficulty: Optional[QuestionDifficulty] = None
    reward_value: int = 0

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    passcode: str

class TeamLogin(BaseModel):
    name: str
    passcode: str

class TeamStatusResponse(TeamBase):
    id: int
    points: int
    timer_start_time: Optional[datetime]
    extra_time_seconds: int
    main_question_id: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)

class AdminLogin(BaseModel):
    passcode: str

class ChallengeCreate(BaseModel):
    question_id: int
    team1_id: int
    team2_id: int
    team3_id: Optional[int] = None

class AssignBoost(BaseModel):
    question_id: int

class ReviewMarkSolved(BaseModel):
    team_id: int
    question_id: int
