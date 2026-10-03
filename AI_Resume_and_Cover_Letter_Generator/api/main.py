from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.generator import generate_application


# ==========================================
# Create FastAPI application
# ==========================================

app = FastAPI(
    title="AI Resume & Cover Letter Generator API",
    description=(
        "API for generating job-tailored resumes, "
        "cover letters, skills matching, and improvement areas."
    ),
    version="1.0.0"
)


# ==========================================
# Request model
# ==========================================

class ApplicationRequest(BaseModel):

    resume: str
    job_description: str


# ==========================================
# Root endpoint
# ==========================================

@app.get("/")
def root():

    return {
        "message": "AI Resume & Cover Letter Generator API",
        "status": "running",
        "docs": "/docs"
    }


# ==========================================
# Health check
# ==========================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ==========================================
# Generate application
# ==========================================

@app.post("/generate")
def generate(request: ApplicationRequest):

    if not request.resume.strip():

        raise HTTPException(
            status_code=400,
            detail="Resume cannot be empty."
        )

    if not request.job_description.strip():

        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    try:

        result = generate_application(
            request.resume,
            request.job_description
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )