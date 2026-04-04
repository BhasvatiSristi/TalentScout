from fastapi import FastAPI

from app.database import Base, engine
from app.models.resume import Resume
from app.routes.candidates import router as candidates_router
from app.routes.resume import router as resume_router

app = FastAPI(title="TalentScout - AI Hiring Assistant", version="1.0.0")

app.include_router(candidates_router, prefix="/candidates", tags=["Candidates"])
app.include_router(resume_router, prefix="/candidates/resume", tags=["Resume"])


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict:
    return {"message": "TalentScout API is running"}
