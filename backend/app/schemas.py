from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Student Schemas
class StudentBase(BaseModel):
    first_name: str
    last_name: str
    matriculation_number: str
    
    @validator('matriculation_number')
    def validate_matriculation_number(cls, v):
        if len(v) != 7:
            raise ValueError('Matriculation number must be exactly 7 characters long')
        if not v.isdigit():
            raise ValueError('Matriculation number must contain only digits')
        return v


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Report Type Schemas
class ReportTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class ReportTypeCreate(ReportTypeBase):
    pass


class ReportTypeResponse(ReportTypeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Rubric Schemas
class RubricBase(BaseModel):
    section_name: str
    max_points: float
    description: Optional[str] = None
    criteria: Optional[dict] = None
    order: int = 0


class RubricCreate(RubricBase):
    report_type_id: int


class RubricResponse(RubricBase):
    id: int
    report_type_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RubricWithScores(RubricResponse):
    score: Optional[float] = None
    feedback: Optional[str] = None


# Evaluation Schemas
class EvaluationScoreCreate(BaseModel):
    rubric_id: int
    score: float
    feedback: Optional[str] = None


class EvaluationCreate(BaseModel):
    student_id: int
    report_type_id: int
    report_title: str
    oberseminar_date: Optional[str] = None
    oberseminar_time: Optional[str] = None
    evaluation_method: str = "manual"
    scores: List[EvaluationScoreCreate]


class EvaluationResponse(BaseModel):
    id: int
    student: StudentResponse
    report_type: ReportTypeResponse
    report_title: str
    oberseminar_date: Optional[str]
    oberseminar_time: Optional[str]
    total_score: float
    max_possible_score: float
    evaluation_method: str
    created_at: datetime
    rubrics: List[RubricWithScores]

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


