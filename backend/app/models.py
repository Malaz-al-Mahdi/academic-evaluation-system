from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportType(Base):
    __tablename__ = "report_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rubrics = relationship("Rubric", back_populates="report_type", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="report_type")


class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    report_type_id = Column(Integer, ForeignKey("report_types.id"), nullable=False)
    section_name = Column(String, nullable=False)
    max_points = Column(Float, nullable=False)
    description = Column(Text)
    criteria = Column(JSON)  # Store detailed criteria as JSON
    order = Column(Integer, default=0)  # For ordering sections
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report_type = relationship("ReportType", back_populates="rubrics")
    scores = relationship("EvaluationScore", back_populates="rubric")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    matriculation_number = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evaluations = relationship("Evaluation", back_populates="student")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    report_type_id = Column(Integer, ForeignKey("report_types.id"), nullable=False)
    report_title = Column(String, nullable=False)
    oberseminar_date = Column(String)
    oberseminar_time = Column(String)
    total_score = Column(Float, default=0.0)
    max_possible_score = Column(Float, default=0.0)
    evaluation_method = Column(String, default="manual")  # manual, rule-based, llm
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="evaluations")
    report_type = relationship("ReportType", back_populates="evaluations")
    evaluator = relationship("User")
    scores = relationship("EvaluationScore", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    rubric_id = Column(Integer, ForeignKey("rubrics.id"), nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evaluation = relationship("Evaluation", back_populates="scores")
    rubric = relationship("Rubric", back_populates="scores")




