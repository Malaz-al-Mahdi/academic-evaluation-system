from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from jinja2 import Template, FileSystemLoader, Environment
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .routers import students, reports, evaluations, auth
from .services.rubric_service import RubricService
from .models import User
from .routers.auth import get_password_hash
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduTec - Academic Evaluation Tool",
    description="A centralized, web-based evaluation tool for academic submissions",
    version="1.0.0"
)

static_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
templates_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "templates")

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

if os.path.exists(templates_path):
    jinja_env = Environment(loader=FileSystemLoader(templates_path))
else:
    jinja_env = None

app.include_router(students.router)
app.include_router(reports.router)
app.include_router(evaluations.router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup_event():
    """Initialize default data on startup"""
    db = next(get_db())
    try:
        RubricService.initialize_default_rubrics(db)
        
        existing_user = db.query(User).filter(
            (User.email == "demo@test.de") | (User.username == "demo")
        ).first()
        
        if not existing_user:
            try:
                import bcrypt
                password = "demo123"
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password_bytes, salt)
                hashed_str = hashed.decode('utf-8')
                
                demo_user = User(
                    username="demo",
                    email="demo@test.de",
                    hashed_password=hashed_str,
                    is_admin=True
                )
                db.add(demo_user)
                db.commit()
                print("Default demo user created: demo@test.de / demo123")
            except Exception as e:
                print(f"Error creating demo user: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
        else:
            print(f"Default demo user already exists: {existing_user.email}")
    except Exception as e:
        print(f"Warning: Could not initialize default data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def render_template(template_name: str, context: dict = None) -> str:
    """Render a Jinja2 template"""
    if not jinja_env:
        return f"<h1>Template not found: {template_name}</h1>"
    template = jinja_env.get_template(template_name)
    return template.render(context or {})


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return HTMLResponse(content=render_template("index.html"))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    return HTMLResponse(content=render_template("login.html"))


@app.get("/evaluate", response_class=HTMLResponse)
async def evaluate_page(request: Request):
    """Serve the evaluation page (step 1: student and report details)"""
    return HTMLResponse(content=render_template("evaluate.html"))


@app.get("/evaluate-step2", response_class=HTMLResponse)
async def evaluate_step2_page(request: Request):
    """Serve the evaluation step 2 page (rubrics and submit)"""
    return HTMLResponse(content=render_template("evaluate_step2.html"))


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve the admin page"""
    return HTMLResponse(content=render_template("admin.html"))


@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    """Serve the statistics page"""
    return HTMLResponse(content=render_template("statistics.html"))


@app.get("/student-history", response_class=HTMLResponse)
async def student_history_page(request: Request):
    """Serve the student history page"""
    return HTMLResponse(content=render_template("student_history.html"))


@app.get("/my-evaluations", response_class=HTMLResponse)
async def my_evaluations_page(request: Request):
    """Serve the my evaluations page"""
    return HTMLResponse(content=render_template("my_evaluations.html"))


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

