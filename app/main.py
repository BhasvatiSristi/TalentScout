from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine
from app.models.candidate import Candidate
from app.models.interview_answer import InterviewAnswer
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.routes.candidates import router as candidates_router
from app.routes.interview_answers import router as interview_answers_router
from app.routes.resume import router as resume_router

app = FastAPI(title="TalentScout - AI Hiring Assistant", version="1.0.0")

app.include_router(candidates_router, prefix="/candidates", tags=["Candidates"])
app.include_router(resume_router, prefix="/candidates/resume", tags=["Resume"])
app.include_router(interview_answers_router, prefix="/candidates/interview-answers", tags=["Interview Answers"])


def _ensure_interview_answers_columns() -> None:
    with engine.begin() as connection:
        rows = connection.execute(text("PRAGMA table_info(interview_answers)")).fetchall()
        column_names = {row[1] for row in rows}
        if "interview_started_at" not in column_names:
            connection.execute(text("ALTER TABLE interview_answers ADD COLUMN interview_started_at DATETIME"))
        if "interview_submitted_at" not in column_names:
            connection.execute(text("ALTER TABLE interview_answers ADD COLUMN interview_submitted_at DATETIME"))


def _ensure_resumes_columns() -> None:
    with engine.begin() as connection:
        rows = connection.execute(text("PRAGMA table_info(resumes)")).fetchall()
        column_names = {row[1] for row in rows}
        if "candidate_id" not in column_names:
            connection.execute(text("ALTER TABLE resumes ADD COLUMN candidate_id INTEGER"))


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_interview_answers_columns()
    _ensure_resumes_columns()


@app.get("/")
def root() -> dict:
    return {"message": "TalentScout API is running"}
