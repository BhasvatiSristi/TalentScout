from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterviewAnswerItem(BaseModel):
    question: str = Field(..., min_length=3)
    answer: str = Field(..., min_length=1)


class InterviewAnswersCreateRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)
    responses: list[InterviewAnswerItem] = Field(..., min_length=1)


class InterviewAnswerSaved(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    question: str
    answer: str
    interview_started_at: datetime | None = None
    interview_submitted_at: datetime | None = None
    created_at: datetime


class InterviewAnswersCreateResponse(BaseModel):
    message: str = "Interview answers saved successfully"
    data: list[InterviewAnswerSaved]
