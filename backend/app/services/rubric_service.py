from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
import pandas as pd
from ..models import Rubric, ReportType
from ..schemas import RubricCreate


class RubricService:
    @staticmethod
    def load_default_rubrics() -> dict:
        """Load default rubrics from JSON file"""
        # Try multiple possible paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "rubrics", "default_rubrics.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "rubrics", "default_rubrics.json"),
            os.path.join(os.getcwd(), "backend", "rubrics", "default_rubrics.json"),
        ]
        default_rubrics_path = None
        for path in possible_paths:
            if os.path.exists(path):
                default_rubrics_path = path
                break
        
        if default_rubrics_path and os.path.exists(default_rubrics_path):
            with open(default_rubrics_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @staticmethod
    def load_rubrics_from_csv(file_path: str) -> List[dict]:
        """Load rubrics from CSV file"""
        try:
            df = pd.read_csv(file_path)
            rubrics = []
            for _, row in df.iterrows():
                rubrics.append({
                    "report_type": row.get("report_type", ""),
                    "section_name": row.get("section_name", ""),
                    "max_points": float(row.get("max_points", 0)),
                    "description": row.get("description", ""),
                    "criteria": json.loads(row.get("criteria", "{}")) if isinstance(row.get("criteria"), str) else row.get("criteria", {}),
                    "order": int(row.get("order", 0))
                })
            return rubrics
        except Exception as e:
            raise Exception(f"Error loading rubrics from CSV: {str(e)}")

    @staticmethod
    def load_rubrics_from_excel(file_path: str) -> List[dict]:
        """Load rubrics from Excel file"""
        try:
            df = pd.read_excel(file_path)
            rubrics = []
            for _, row in df.iterrows():
                rubrics.append({
                    "report_type": row.get("report_type", ""),
                    "section_name": row.get("section_name", ""),
                    "max_points": float(row.get("max_points", 0)),
                    "description": row.get("description", ""),
                    "criteria": json.loads(row.get("criteria", "{}")) if isinstance(row.get("criteria"), str) else row.get("criteria", {}),
                    "order": int(row.get("order", 0))
                })
            return rubrics
        except Exception as e:
            raise Exception(f"Error loading rubrics from Excel: {str(e)}")

    @staticmethod
    def get_rubrics_for_report_type(db: Session, report_type_id: int) -> List[Rubric]:
        """Get all rubrics for a specific report type"""
        return db.query(Rubric).filter(
            Rubric.report_type_id == report_type_id
        ).order_by(Rubric.order).all()

    @staticmethod
    def create_rubric(db: Session, rubric: RubricCreate) -> Rubric:
        """Create a new rubric"""
        db_rubric = Rubric(**rubric.dict())
        db.add(db_rubric)
        db.commit()
        db.refresh(db_rubric)
        return db_rubric

    @staticmethod
    def initialize_default_rubrics(db: Session):
        """Initialize database with default rubrics"""
        default_rubrics = RubricService.load_default_rubrics()
        
        for report_type_name, rubrics_data in default_rubrics.items():
            # Get or create report type
            report_type = db.query(ReportType).filter(
                ReportType.name == report_type_name
            ).first()
            
            if not report_type:
                report_type = ReportType(
                    name=report_type_name,
                    description=f"Default {report_type_name} report type"
                )
                db.add(report_type)
                db.commit()
                db.refresh(report_type)
            
            # Check if rubrics already exist
            existing_rubrics = db.query(Rubric).filter(
                Rubric.report_type_id == report_type.id
            ).count()
            
            if existing_rubrics == 0:
                # Create rubrics for this report type
                for rubric_data in rubrics_data:
                    rubric = Rubric(
                        report_type_id=report_type.id,
                        section_name=rubric_data["section_name"],
                        max_points=rubric_data["max_points"],
                        description=rubric_data.get("description"),
                        criteria=rubric_data.get("criteria", {}),
                        order=rubric_data.get("order", 0)
                    )
                    db.add(rubric)
            
            db.commit()

