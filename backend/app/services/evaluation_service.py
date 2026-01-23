from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Evaluation, EvaluationScore, Student, Rubric
from ..schemas import EvaluationCreate, EvaluationScoreCreate
import os
import json
from dotenv import load_dotenv

load_dotenv()


class EvaluationService:
    def __init__(self):
        self.openai_client = None

    def create_evaluation(
        self, db: Session, evaluation_data: EvaluationCreate, evaluator_id: Optional[int] = None
    ) -> Evaluation:
        """Create a new evaluation"""
        total_score = sum(score.score for score in evaluation_data.scores)
        
        rubric_ids = [score.rubric_id for score in evaluation_data.scores]
        rubrics = db.query(Rubric).filter(Rubric.id.in_(rubric_ids)).all()
        max_possible_score = sum(rubric.max_points for rubric in rubrics)
        
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
        
        for score_data in evaluation_data.scores:
            score = EvaluationScore(
                evaluation_id=evaluation.id,
                rubric_id=score_data.rubric_id,
                score=score_data.score,
                feedback=score_data.feedback
            )
            db.add(score)
        
        db.commit()
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
        """Evaluate using language model based on defined criteria"""
        try:
            import sys
            import importlib.util
            
            try:
                import httpx
                import inspect
                client_init = inspect.signature(httpx.Client.__init__)
                if 'proxies' not in client_init.parameters:
                    pass
            except Exception:
                pass
            
            from openai import OpenAI
        except ImportError:
            raise Exception("OpenAI package not installed. Please install it with: pip install openai")
        except Exception as import_error:
            if "proxies" in str(import_error) or "httpx" in str(import_error).lower():
                raise Exception(
                    "OpenAI package compatibility issue detected. "
                    "Please update packages by running: "
                    "pip install --upgrade openai httpx>=0.27.0"
                )
            raise Exception(f"Failed to import OpenAI: {str(import_error)}")
        
        if not self.openai_client:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            
            if api_key.startswith("gsk_"):
                base_url = "https://api.groq.com/openai/v1"
                try:
                    import httpx
                    http_client = httpx.Client(
                        timeout=httpx.Timeout(60.0, connect=10.0),
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    )
                    self.openai_client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
                except Exception as e1:
                    try:
                        self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
                    except Exception as e2:
                        raise Exception(f"Failed to initialize Groq client: {str(e2)}")
            else:
                initialization_errors = []
                
                try:
                    import httpx
                    http_client = httpx.Client(
                        timeout=httpx.Timeout(60.0, connect=10.0),
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                    )
                    self.openai_client = OpenAI(api_key=api_key, http_client=http_client)
                except Exception as e1:
                    initialization_errors.append(f"Strategy 1 (with http_client): {str(e1)}")
                    
                    try:
                        self.openai_client = OpenAI(api_key=api_key)
                    except Exception as e2:
                        initialization_errors.append(f"Strategy 2 (direct): {str(e2)}")
                        raise Exception(
                            f"OpenAI client initialization failed. "
                            f"Please update packages: pip install --upgrade openai httpx>=0.27.0\n"
                            f"Errors: {'; '.join(initialization_errors)}"
                        )
        
        rubrics = db.query(Rubric).filter(
            Rubric.report_type_id == report_type_id
        ).order_by(Rubric.order).all()
        
        if not rubrics:
            raise Exception("No rubrics found for this report type")
        
        rubric_sections = []
        for r in rubrics:
            section_text = f"## {r.section_name} (Max: {r.max_points} points)\n"
            section_text += f"Description: {r.description or 'No description provided'}\n"
            
            if r.criteria and isinstance(r.criteria, dict):
                section_text += "\nEvaluation Criteria:\n"
                for score_range, criterion_desc in r.criteria.items():
                    section_text += f"- Score {score_range}: {criterion_desc}\n"
            
            rubric_sections.append(section_text)
        
        rubric_text = "\n\n".join(rubric_sections)
        
        content_length = min(len(report_content), 8000)
        report_content_limited = report_content[:content_length]
        
        prompt = f"""You are an academic evaluator. Evaluate the following report based on the detailed rubrics and criteria provided.

Report Title: {report_title}

Report Content:
{report_content_limited}

---

EVALUATION RUBRICS AND CRITERIA:

{rubric_text}

---

INSTRUCTIONS:
1. For each rubric section, carefully assess the report content against the provided criteria
2. Match the quality of the work to the appropriate score range based on the criteria
3. Assign a precise score (0 to max_points) that reflects where the work falls within the criteria
4. Provide constructive feedback (2-3 sentences) that:
   - Explains why this score was assigned
   - References specific aspects from the criteria
   - Mentions strengths and areas for improvement

IMPORTANT:
- Base your evaluation strictly on the criteria provided for each section
- Be consistent and fair in your assessment
- Ensure scores are within the valid range (0 to max_points for each section)
- Provide specific, actionable feedback

Format your response as valid JSON:
{{
  "scores": [
    {{
      "section_name": "exact section name from rubrics",
      "score": X.X,
      "feedback": "Detailed feedback explaining the score based on criteria"
    }}
  ]
}}
"""
        
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key.startswith("gsk_"):
                groq_models = [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "gemma2-9b-it",
                    "llama-3.2-3b-instruct"
                ]
                model = groq_models[0]
            else:
                model = "gpt-4"
            
            response = None
            last_error = None
            
            for attempt_model in (groq_models if api_key.startswith("gsk_") else [model]):
                try:
                    try:
                        response = self.openai_client.chat.completions.create(
                            model=attempt_model,
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are an expert academic evaluator. You evaluate student reports based on detailed rubrics and criteria. Always respond with valid JSON only, no additional text."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.2,
                            response_format={"type": "json_object"}
                        )
                        model = attempt_model
                        break
                    except Exception as format_error:
                        if "response_format" in str(format_error).lower() or "json_object" in str(format_error).lower():
                            print(f"Warning: response_format not supported for {attempt_model}, using fallback: {format_error}")
                            response = self.openai_client.chat.completions.create(
                                model=attempt_model,
                                messages=[
                                    {
                                        "role": "system", 
                                        "content": "You are an expert academic evaluator. You evaluate student reports based on detailed rubrics and criteria. Always respond with valid JSON only, no additional text. Your response must be a valid JSON object with a 'scores' array."
                                    },
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.2
                            )
                            model = attempt_model
                            break
                        else:
                            last_error = format_error
                            if "decommissioned" in str(format_error).lower():
                                print(f"Model {attempt_model} is decommissioned, trying next model...")
                                continue
                            raise
                except Exception as e:
                    last_error = e
                    if "decommissioned" in str(e).lower() and attempt_model != groq_models[-1]:
                        print(f"Model {attempt_model} failed: {e}, trying next model...")
                        continue
                    raise
            
            if response is None:
                raise Exception(f"All models failed. Last error: {str(last_error)}")
            
            response_content = response.choices[0].message.content
            if not response_content:
                raise Exception("Empty response from language model")
            
            if isinstance(response_content, str):
                if "```json" in response_content:
                    response_content = response_content.split("```json")[1].split("```")[0].strip()
                elif "```" in response_content:
                    response_content = response_content.split("```")[1].split("```")[0].strip()
                
                response_content = response_content.strip()
                
                try:
                    result = json.loads(response_content)
                except json.JSONDecodeError as json_err:
                    print(f"JSON parsing error. Content preview: {response_content[:500]}")
                    raise Exception(f"Invalid JSON response from language model: {str(json_err)}")
            else:
                result = response_content
            
            if "scores" not in result:
                raise Exception(f"Invalid response format: missing 'scores' field. Response: {str(result)[:200]}")
            
            if not isinstance(result["scores"], list):
                raise Exception(f"Invalid response format: 'scores' must be a list. Got: {type(result['scores'])}")
            
            evaluation_scores = []
            for score_data in result.get("scores", []):
                if not isinstance(score_data, dict):
                    continue
                    
                section_name = score_data.get("section_name")
                if not section_name:
                    continue
                    
                rubric = next((r for r in rubrics if r.section_name == section_name), None)
                if rubric:
                    try:
                        score = max(0.0, min(float(score_data.get("score", 0)), rubric.max_points))
                        evaluation_scores.append(EvaluationScoreCreate(
                            rubric_id=rubric.id,
                            score=score,
                            feedback=score_data.get("feedback", "")
                        ))
                    except (ValueError, TypeError) as e:
                        print(f"Error processing score for {section_name}: {e}")
                        continue
            
            if len(evaluation_scores) < len(rubrics):
                evaluated_sections = {s.get("section_name") for s in result.get("scores", []) if isinstance(s, dict)}
                missing_sections = [r.section_name for r in rubrics if r.section_name not in evaluated_sections]
                if missing_sections:
                    raise Exception(f"Missing evaluations for sections: {', '.join(missing_sections)}. Received {len(evaluation_scores)} scores for {len(rubrics)} rubrics.")
            
            evaluation_data = EvaluationCreate(
                student_id=student_id,
                report_type_id=report_type_id,
                report_title=report_title,
                evaluation_method="llm",
                scores=evaluation_scores
            )
            
            return self.create_evaluation(db, evaluation_data)
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
            if 'response' in locals() and response.choices:
                error_msg += f". Response preview: {response.choices[0].message.content[:300]}"
            raise Exception(error_msg)
        except KeyError as e:
            raise Exception(f"Missing required field in LLM response: {str(e)}")
        except Exception as e:
            import traceback
            error_msg = f"Language model evaluation failed: {str(e)}"
            print(f"LLM Evaluation Error: {error_msg}")
            traceback.print_exc()
            raise Exception(error_msg)

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

