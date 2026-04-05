from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    extracted_text: str
    job_role: str
    extracted_skills: list[str]
    required_skills: list[str]
    matched_skills: list[str]
    ats_score: float
    created_at: datetime


class ResumeExtractResponse(BaseModel):
    message: str = Field(default="Resume text extracted successfully")
    data: ResumeCreateResponse
