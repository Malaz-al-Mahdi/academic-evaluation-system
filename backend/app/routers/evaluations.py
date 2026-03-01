from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ..database import get_db
from ..models import Evaluation, EvaluationScore, User
from ..schemas import EvaluationCreate, EvaluationResponse, RubricWithScores
from ..services.evaluation_service import EvaluationService
from ..services.report_service import ReportService
from ..routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

evaluation_service = EvaluationService()
report_service = ReportService()


def format_evaluation_response(evaluation: Evaluation) -> EvaluationResponse:
    """Format evaluation with rubrics and scores for response"""
    rubrics_with_scores = []
    for score in evaluation.scores:
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
    
    return EvaluationResponse(
        id=evaluation.id,
        student=evaluation.student,
        report_type=evaluation.report_type,
        report_title=evaluation.report_title,
        oberseminar_date=evaluation.oberseminar_date,
        oberseminar_time=evaluation.oberseminar_time,
        total_score=evaluation.total_score,
        max_possible_score=evaluation.max_possible_score,
        evaluation_method=evaluation.evaluation_method,
        created_at=evaluation.created_at,
        rubrics=rubrics_with_scores
    )


class LLMEvaluationRequest(BaseModel):
    student_id: int
    report_type_id: int
    report_title: str
    report_content: str


class RuleBasedEvaluationRequest(BaseModel):
    student_id: int
    report_type_id: int
    report_title: str
    report_content: str


@router.get("/my", response_model=List[EvaluationResponse])
def get_my_evaluations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all evaluations created by the current user"""
    evaluations = db.query(Evaluation)\
        .options(
            joinedload(Evaluation.student),
            joinedload(Evaluation.report_type),
            joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric)
        )\
        .filter(Evaluation.evaluator_id == current_user.id)\
        .order_by(Evaluation.created_at.desc())\
        .all()
    return [format_evaluation_response(e) for e in evaluations]


@router.post("/", response_model=EvaluationResponse)
def create_evaluation(evaluation: EvaluationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new manual evaluation"""
    evaluation_obj = evaluation_service.create_evaluation(db, evaluation, evaluator_id=current_user.id)
    
    db.refresh(evaluation_obj)
    return format_evaluation_response(evaluation_obj)


@router.post("/llm", response_model=EvaluationResponse)
def create_llm_evaluation(request: LLMEvaluationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create an evaluation using language model"""
    import traceback
    try:
        evaluation = evaluation_service.evaluate_with_llm(
            db,
            request.student_id,
            request.report_type_id,
            request.report_title,
            request.report_content,
            evaluator_id=current_user.id
        )
        if not evaluation:
            raise HTTPException(status_code=500, detail="Language model evaluation failed")
        return format_evaluation_response(evaluation)
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Language model evaluation failed: {error_detail}")


@router.post("/rule-based", response_model=EvaluationResponse)
def create_rule_based_evaluation(request: RuleBasedEvaluationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a rule-based evaluation"""
    try:
        evaluation = evaluation_service.evaluate_rule_based(
            db,
            request.student_id,
            request.report_type_id,
            request.report_title,
            request.report_content,
            evaluator_id=current_user.id
        )
        if not evaluation:
            raise HTTPException(status_code=500, detail="Rule-based evaluation failed")
        return format_evaluation_response(evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get evaluation by ID"""
    evaluation = evaluation_service.get_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return format_evaluation_response(evaluation)


@router.get("/{evaluation_id}/report/html")
def get_html_report(evaluation_id: int, db: Session = Depends(get_db)):
    """Generate and return HTML evaluation report"""
    try:
        html_content = report_service.generate_html_report(db, evaluation_id)
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}/report/pdf")
def get_pdf_report(evaluation_id: int, db: Session = Depends(get_db)):
    """Generate and return PDF evaluation report"""
    try:
        pdf_path = report_service.generate_pdf_report(db, evaluation_id)
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        return Response(content=pdf_content, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

