from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Evaluation, EvaluationScore, Student, Rubric
from ..schemas import EvaluationCreate, EvaluationScoreCreate
import os
from openai import OpenAI


class EvaluationService:
    def __init__(self):
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)

    def create_evaluation(
        self, db: Session, evaluation_data: EvaluationCreate, evaluator_id: Optional[int] = None
    ) -> Evaluation:
        """Create a new evaluation"""
        # Calculate total and max scores
        total_score = sum(score.score for score in evaluation_data.scores)
        
        # Get max possible score
        rubric_ids = [score.rubric_id for score in evaluation_data.scores]
        rubrics = db.query(Rubric).filter(Rubric.id.in_(rubric_ids)).all()
        max_possible_score = sum(rubric.max_points for rubric in rubrics)
        
        # Create evaluation
        evaluation = Evaluation(
            student_id=evaluation_data.student_id,
            report_type_id=evaluation_data.report_type_id,
            report_title=evaluation_data.report_title,
            oberseminar_date=evaluation_data.oberseminar_date,
            oberseminar_time=evaluation_data.oberseminar_time,
            total_score=total_score,
            max_possible_score=max_possible_score,
            evaluation_method=evaluation_data.evaluation_method,
            evaluator_id=evaluator_id
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        # Create evaluation scores
        for score_data in evaluation_data.scores:
            score = EvaluationScore(
                evaluation_id=evaluation.id,
                rubric_id=score_data.rubric_id,
                score=score_data.score,
                feedback=score_data.feedback
            )
            db.add(score)
        
        db.commit()
        # Reload with relationships
        from sqlalchemy.orm import joinedload
        evaluation = db.query(Evaluation)\
            .options(joinedload(Evaluation.student),
                    joinedload(Evaluation.report_type),
                    joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric))\
            .filter(Evaluation.id == evaluation.id).first()
        return evaluation

    def evaluate_with_llm(
        self, db: Session, student_id: int, report_type_id: int, 
        report_title: str, report_content: str
    ) -> Optional[Evaluation]:
        """Evaluate using language model"""
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")
        
        # Get rubrics for this report type
        rubrics = db.query(Rubric).filter(
            Rubric.report_type_id == report_type_id
        ).order_by(Rubric.order).all()
        
        if not rubrics:
            raise Exception("No rubrics found for this report type")
        
        rubric_text = "\n".join([
            f"{r.section_name} (Max: {r.max_points} points): {r.description or ''}"
            for r in rubrics
        ])
        
        prompt = f"""Evaluate the following report based on the provided rubrics.

Report Title: {report_title}

Report Content:
{report_content[:4000]}  # Limit content length

Rubrics:
{rubric_text}

For each rubric section, provide:
1. A score (0 to max_points)
2. Brief feedback (1-2 sentences)

Format your response as JSON:
{{
  "scores": [
    {{"section_name": "...", "score": X.X, "feedback": "..."}},
    ...
  ]
}}
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Create evaluation scores
            evaluation_scores = []
            for score_data in result.get("scores", []):
                rubric = next((r for r in rubrics if r.section_name == score_data["section_name"]), None)
                if rubric:
                    evaluation_scores.append(EvaluationScoreCreate(
                        rubric_id=rubric.id,
                        score=min(score_data["score"], rubric.max_points),  # Ensure score doesn't exceed max
                        feedback=score_data.get("feedback")
                    ))
            
            # Create evaluation
            evaluation_data = EvaluationCreate(
                student_id=student_id,
                report_type_id=report_type_id,
                report_title=report_title,
                evaluation_method="llm",
                scores=evaluation_scores
            )
            
            return self.create_evaluation(db, evaluation_data)
            
        except Exception as e:
            raise Exception(f"Language model evaluation failed: {str(e)}")

    def evaluate_rule_based(
        self, db: Session, student_id: int, report_type_id: int,
        report_title: str, report_content: str
    ) -> Optional[Evaluation]:
        """Evaluate using rule-based approach (simple keyword matching)"""
        rubrics = db.query(Rubric).filter(
            Rubric.report_type_id == report_type_id
        ).order_by(Rubric.order).all()
        
        if not rubrics:
            raise Exception("No rubrics found for this report type")
        
        evaluation_scores = []
        content_lower = report_content.lower()
        
        for rubric in rubrics:
            score = 0.0
            feedback = ""
            
            section_name_lower = rubric.section_name.lower()
            if "introduction" in section_name_lower:
                if any(word in content_lower for word in ["introduction", "introduce", "overview"]):
                    score = rubric.max_points * 0.7  # Basic presence
                    feedback = "Introduction section found."
            
            elif "objective" in section_name_lower or "overview" in section_name_lower:
                if any(word in content_lower for word in ["objective", "goal", "aim", "purpose"]):
                    score = rubric.max_points * 0.7
                    feedback = "Objectives section found."
            
            elif "requirement" in section_name_lower:
                if any(word in content_lower for word in ["requirement", "specification", "spec"]):
                    score = rubric.max_points * 0.7
                    feedback = "Requirements section found."
            
            elif "design" in section_name_lower:
                if any(word in content_lower for word in ["design", "architecture", "structure"]):
                    score = rubric.max_points * 0.7
                    feedback = "Design section found."
            
            elif "result" in section_name_lower or "discussion" in section_name_lower:
                if any(word in content_lower for word in ["result", "discussion", "finding"]):
                    score = rubric.max_points * 0.7
                    feedback = "Results/discussion section found."
            
            else:
                if section_name_lower in content_lower:
                    score = rubric.max_points * 0.5
                    feedback = f"{rubric.section_name} section found."
            
            evaluation_scores.append(EvaluationScoreCreate(
                rubric_id=rubric.id,
                score=score,
                feedback=feedback or f"Rule-based evaluation for {rubric.section_name}"
            ))
        
        evaluation_data = EvaluationCreate(
            student_id=student_id,
            report_type_id=report_type_id,
            report_title=report_title,
            evaluation_method="rule-based",
            scores=evaluation_scores
        )
        
        return self.create_evaluation(db, evaluation_data)

    def get_evaluation(self, db: Session, evaluation_id: int) -> Optional[Evaluation]:
        """Get evaluation by ID with relationships"""
        from sqlalchemy.orm import joinedload
        return db.query(Evaluation)\
            .options(joinedload(Evaluation.student),
                    joinedload(Evaluation.report_type),
                    joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric))\
            .filter(Evaluation.id == evaluation_id).first()

    def get_all_evaluations(self, db: Session, skip: int = 0, limit: int = 100) -> List[Evaluation]:
        """Get all evaluations"""
        return db.query(Evaluation).offset(skip).limit(limit).all()

