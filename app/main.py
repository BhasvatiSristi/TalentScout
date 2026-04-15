"""
Purpose: Creates and configures the FastAPI application.

Inputs:

* API routers imported from the route modules
* Database models imported so tables can be created on startup

Outputs:

* A running FastAPI app with routes and startup setup

Used in:

* Main backend entry point for the screening API
"""

from fastapi import FastAPI

from app.database import Base, engine
from app.models.candidate import Candidate
from app.models.feedback import Feedback
from app.models.interview_answer import InterviewAnswer
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.routes.candidates import router as candidates_router
from app.routes.feedback import router as feedback_router
from app.routes.interview_answers import router as interview_answers_router
from app.routes.resume import router as resume_router

app = FastAPI(title="TalentScout - AI Hiring Assistant", version="1.0.0")

app.include_router(candidates_router, prefix="/candidates", tags=["Candidates"])
app.include_router(resume_router, prefix="/candidates/resume", tags=["Resume"])
app.include_router(interview_answers_router, prefix="/candidates/interview-answers", tags=["Interview Answers"])
app.include_router(feedback_router, tags=["Feedback"])


@app.on_event("startup")
def create_tables() -> None:
    """
    Create database tables when the app starts.

    Parameters:

    * None

    Returns:

    * None

    Steps:

    1. Read the SQLAlchemy models
    2. Create any missing tables in the database
    3. Finish startup so the API can serve requests
    """
    # For a fresh SQLite database, this creates every table from the models.
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict:
    """
    Return a simple health message for the API root.

    Parameters:

    * None

    Returns:

    * dict: Small JSON message showing the API is running

    Steps:

    1. Receive a request to the root path
    2. Return a basic status message
    """
    return {"message": "TalentScout API is running"}
