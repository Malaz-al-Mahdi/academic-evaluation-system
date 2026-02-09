FROM python:3.12-slim

WORKDIR /app

# System dependencies (for WeasyPrint/PDF, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend and frontend (backend serves frontend)
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Persistent dirs (overridden by volumes in compose)
RUN mkdir -p /app/data /app/reports

ENV PYTHONPATH=/app

EXPOSE 8000

# Backend (FastAPI) serves API + frontend static/templates
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]




