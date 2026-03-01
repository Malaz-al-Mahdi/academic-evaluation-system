from sqlalchemy.orm import Session
from typing import Optional
from ..models import Evaluation
from jinja2 import Template
import os


class ReportService:
    @staticmethod
    def generate_html_report(db: Session, evaluation_id: int) -> str:
        """Generate HTML evaluation report"""
        from sqlalchemy.orm import joinedload
        from ..models import EvaluationScore
        evaluation = db.query(Evaluation)\
            .options(joinedload(Evaluation.student),
                    joinedload(Evaluation.report_type),
                    joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric))\
            .filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise Exception("Evaluation not found")
        
        # Load HTML template
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "frontend", "templates", "report_template.html"
        )
        
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = Template(f.read())
        else:
            # Fallback template
            template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Evaluation Report - {{ evaluation.report_title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin: 20px 0; }
        .score { font-weight: bold; color: #0066cc; }
        .total { font-size: 1.2em; margin-top: 30px; padding-top: 20px; border-top: 2px solid #333; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Academic Evaluation Report</h1>
        <p><strong>Student:</strong> {{ evaluation.student.first_name }} {{ evaluation.student.last_name }}</p>
        <p><strong>Matriculation Number:</strong> {{ evaluation.student.matriculation_number }}</p>
        <p><strong>Report Title:</strong> {{ evaluation.report_title }}</p>
        <p><strong>Report Type:</strong> {{ evaluation.report_type.name }}</p>
        {% if evaluation.oberseminar_date %}
        <p><strong>Oberseminar Date:</strong> {{ evaluation.oberseminar_date }}</p>
        {% endif %}
        {% if evaluation.oberseminar_time %}
        <p><strong>Oberseminar Time:</strong> {{ evaluation.oberseminar_time }}</p>
        {% endif %}
    </div>
    
    <h2>Evaluation Details</h2>
    {% for score in evaluation.scores %}
    <div class="section">
        <h3>{{ score.rubric.section_name }}</h3>
        <p><strong>Score:</strong> <span class="score">{{ score.score }} / {{ score.rubric.max_points }}</span></p>
        {% if score.feedback %}
        <p><strong>Feedback:</strong> {{ score.feedback }}</p>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="total">
        <h2>Total Score</h2>
        <p><strong>{{ evaluation.total_score }} / {{ evaluation.max_possible_score }}</strong></p>
        <p><strong>Percentage:</strong> {{ "%.2f"|format((evaluation.total_score / evaluation.max_possible_score * 100) if evaluation.max_possible_score > 0 else 0) }}%</p>
        <p><strong>Evaluation Method:</strong> {{ evaluation.evaluation_method }}</p>
    </div>
</body>
</html>
            """)
        
        return template.render(evaluation=evaluation)

    @staticmethod
    def generate_pdf_report(db: Session, evaluation_id: int, output_path: Optional[str] = None) -> str:
        """Generate PDF evaluation report using WeasyPrint (HTML to PDF)"""
        from sqlalchemy.orm import joinedload
        from ..models import EvaluationScore
        from weasyprint import HTML, CSS
        from datetime import datetime
        import base64
        
        evaluation = db.query(Evaluation)\
            .options(joinedload(Evaluation.student),
                    joinedload(Evaluation.report_type),
                    joinedload(Evaluation.scores).joinedload(EvaluationScore.rubric))\
            .filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise Exception("Evaluation not found")
        
        if not output_path:
            output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"evaluation_{evaluation_id}.pdf")
        
        # Generate HTML report first
        html_content = ReportService.generate_html_report(db, evaluation_id)
        
        # Embed logos as base64 for PDF generation
        logo_paths = {
            'dipf_logo.png': os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "static", "images", "dipf_logo.png"),
            'goethe_logo.png': os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "static", "images", "goethe_logo.png")
        }
        
        for logo_name, logo_path in logo_paths.items():
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as img_file:
                    base64_data = base64.b64encode(img_file.read()).decode('utf-8')
                    data_uri = f"data:image/png;base64,{base64_data}"
                    html_content = html_content.replace(f"file:///app/frontend/static/images/{logo_name}", data_uri)
        
        # Convert HTML to PDF using WeasyPrint
        HTML(string=html_content).write_pdf(output_path)
        
        return output_path

