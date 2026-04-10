from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)
    confidence_score: int = Field(..., ge=1, le=10)
