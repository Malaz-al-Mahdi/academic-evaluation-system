from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import ReportType, Rubric
from ..schemas import ReportTypeResponse, RubricResponse
from ..services.rubric_service import RubricService

router = APIRouter(prefix="/api/report-types", tags=["report-types"])


@router.get("/", response_model=List[ReportTypeResponse])
def get_report_types(db: Session = Depends(get_db)):
    """Get all report types"""
    report_types = db.query(ReportType).all()
    return report_types


@router.get("/{type_id}", response_model=ReportTypeResponse)
def get_report_type(type_id: int, db: Session = Depends(get_db)):
    """Get report type by ID"""
    report_type = db.query(ReportType).filter(ReportType.id == type_id).first()
    if not report_type:
        raise HTTPException(status_code=404, detail="Report type not found")
    return report_type


@router.get("/{type_id}/rubrics", response_model=List[RubricResponse])
def get_rubrics_for_report_type(type_id: int, db: Session = Depends(get_db)):
    """Get all rubrics for a specific report type"""
    report_type = db.query(ReportType).filter(ReportType.id == type_id).first()
    if not report_type:
        raise HTTPException(status_code=404, detail="Report type not found")
    
    rubrics = RubricService.get_rubrics_for_report_type(db, type_id)
    return rubrics


@router.get("/{type_id}/statistics")
def get_report_type_statistics(type_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific report type"""
    from ..models import Evaluation
    from sqlalchemy import func
    
    report_type = db.query(ReportType).filter(ReportType.id == type_id).first()
    if not report_type:
        raise HTTPException(status_code=404, detail="Report type not found")
    
    evaluations = db.query(Evaluation).filter(Evaluation.report_type_id == type_id).all()
    
    if not evaluations:
        return {
            "report_type_id": type_id,
            "report_type_name": report_type.name,
            "total_evaluations": 0,
            "average_score": 0.0,
            "average_percentage": 0.0,
            "max_possible_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0
        }
    
    total_evaluations = len(evaluations)
    total_scores = [e.total_score for e in evaluations]
    max_scores = [e.max_possible_score for e in evaluations]
    
    average_score = sum(total_scores) / total_evaluations if total_evaluations > 0 else 0.0
    average_max_score = sum(max_scores) / total_evaluations if total_evaluations > 0 else 0.0
    average_percentage = (average_score / average_max_score * 100) if average_max_score > 0 else 0.0
    
    return {
        "report_type_id": type_id,
        "report_type_name": report_type.name,
        "total_evaluations": total_evaluations,
        "average_score": round(average_score, 2),
        "average_percentage": round(average_percentage, 2),
        "max_possible_score": round(average_max_score, 2),
        "min_score": round(min(total_scores), 2) if total_scores else 0.0,
        "max_score": round(max(total_scores), 2) if total_scores else 0.0
    }


@router.get("/statistics/all")
def get_all_report_type_statistics(db: Session = Depends(get_db)):
    """Get statistics for all report types"""
    from ..models import Evaluation
    from sqlalchemy import func
    
    report_types = db.query(ReportType).all()
    statistics = []
    
    for report_type in report_types:
        evaluations = db.query(Evaluation).filter(Evaluation.report_type_id == report_type.id).all()
        
        if not evaluations:
            statistics.append({
                "report_type_id": report_type.id,
                "report_type_name": report_type.name,
                "total_evaluations": 0,
                "average_score": 0.0,
                "average_percentage": 0.0,
                "max_possible_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0
            })
            continue
        
        total_evaluations = len(evaluations)
        total_scores = [e.total_score for e in evaluations]
        max_scores = [e.max_possible_score for e in evaluations]
        
        average_score = sum(total_scores) / total_evaluations if total_evaluations > 0 else 0.0
        average_max_score = sum(max_scores) / total_evaluations if total_evaluations > 0 else 0.0
        average_percentage = (average_score / average_max_score * 100) if average_max_score > 0 else 0.0
        
        statistics.append({
            "report_type_id": report_type.id,
            "report_type_name": report_type.name,
            "total_evaluations": total_evaluations,
            "average_score": round(average_score, 2),
            "average_percentage": round(average_percentage, 2),
            "max_possible_score": round(average_max_score, 2),
            "min_score": round(min(total_scores), 2) if total_scores else 0.0,
            "max_score": round(max(total_scores), 2) if total_scores else 0.0
        })
    
    return statistics




