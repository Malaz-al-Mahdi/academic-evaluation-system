from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Student
from ..schemas import StudentCreate, StudentResponse, EvaluationResponse, ReportTypeResponse, RubricWithScores

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    # Validate matriculation number length
    if len(student.matriculation_number) != 7:
        raise HTTPException(
            status_code=400, 
            detail="Matriculation number must be exactly 7 characters long"
        )
    
    if not student.matriculation_number.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Matriculation number must contain only digits"
        )
    
    # Check if student with same matriculation number exists
    existing = db.query(Student).filter(
        Student.matriculation_number == student.matriculation_number
    ).first()
    
    if existing:
        return existing
    
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.get("/", response_model=List[StudentResponse])
def get_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all students"""
    students = db.query(Student).offset(skip).limit(limit).all()
    return students


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get student by ID"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/{student_id}/evaluations")
def get_student_evaluations(student_id: int, db: Session = Depends(get_db)):
    """Get all evaluations for a specific student"""
    from ..models import Evaluation, EvaluationScore
    from sqlalchemy.orm import joinedload
    from ..schemas import EvaluationResponse, RubricWithScores
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    evaluations = db.query(Evaluation)\
        .options(
            joinedload(Evaluation.student),
            joinedload(Evaluation.report_type),
            joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric)
        )\
        .filter(Evaluation.student_id == student_id)\
        .order_by(Evaluation.created_at.desc())\
        .all()
    
    result = []
    for eval in evaluations:
        rubrics_with_scores = []
        for score in eval.scores:
            rubrics_with_scores.append(RubricWithScores(
                id=score.rubric.id,
                report_type_id=score.rubric.report_type_id,
                section_name=score.rubric.section_name,
                max_points=score.rubric.max_points,
                description=score.rubric.description,
                criteria=score.rubric.criteria,
                order=score.rubric.order,
                created_at=score.rubric.created_at,
                score=score.score,
                feedback=score.feedback
            ))
        
        result.append(EvaluationResponse(
            id=eval.id,
            student=StudentResponse(
                id=eval.student.id,
                first_name=eval.student.first_name,
                last_name=eval.student.last_name,
                matriculation_number=eval.student.matriculation_number,
                created_at=eval.student.created_at
            ),
            report_type=ReportTypeResponse(
                id=eval.report_type.id,
                name=eval.report_type.name,
                description=eval.report_type.description,
                created_at=eval.report_type.created_at
            ),
            report_title=eval.report_title,
            oberseminar_date=eval.oberseminar_date,
            oberseminar_time=eval.oberseminar_time,
            total_score=eval.total_score,
            max_possible_score=eval.max_possible_score,
            evaluation_method=eval.evaluation_method,
            created_at=eval.created_at,
            rubrics=rubrics_with_scores
        ))
    
    return result


