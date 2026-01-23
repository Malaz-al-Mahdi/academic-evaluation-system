# EduTec - Academic Evaluation Tool

A centralized, web-based evaluation tool for assessing academic submissions with structured rubrics and automated report generation.

## Features

- **Student Data Management**: Collect and store student information (name, matriculation number)
- **Report Type Selection**: Support for multiple report types (Research-driven, Design-driven, ML/NLP, Seminar reports)
- **Structured Rubrics**: Predefined grading rubrics with multiple sections and point allocations
- **Flexible Evaluation**: Manual, rule-based, or language model-assisted evaluation
- **Report Generation**: Automatic generation of HTML/PDF evaluation reports
- **Rubric Management**: Hardcoded rubrics or dynamic loading from CSV/Excel files
- **Containerized**: Fully dockerized application for easy deployment
- **Optional Authentication**: Login system and admin panel for rubric management

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── evaluation_service.py
│   │   │   ├── rubric_service.py
│   │   │   └── report_service.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── students.py
│   │       ├── reports.py
│   │       ├── evaluations.py
│   │       └── auth.py
│   └── rubrics/
│       └── default_rubrics.json
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/
│       ├── index.html
│       ├── evaluate.html
│       └── admin.html
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Setup

### Using Docker (Recommended)

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Manual Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

1. Navigate to the web interface
2. Enter student information (name, matriculation number)
3. Select the report type
4. Fill in report details
5. Evaluate each rubric section
6. Generate and download the evaluation report

## API Endpoints

- `GET /` - Home page
- `GET /api/report-types` - Get all report types
- `GET /api/report-types/{type_id}/rubrics` - Get rubrics for a report type
- `POST /api/evaluations` - Create a new evaluation
- `GET /api/evaluations/{evaluation_id}/report` - Generate evaluation report
- `POST /api/auth/login` - User login (optional)
- `GET /api/admin/rubrics` - Admin: Get all rubrics
- `POST /api/admin/rubrics` - Admin: Create/update rubric

## Environment Variables

Create a `.env` file in the backend directory:

```
DATABASE_URL=sqlite:///./evaluations.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional, for language model evaluation
```

## License

MIT




