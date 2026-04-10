from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)
    confidence_score: int = Field(..., ge=1, le=10)
    experience_rating: str = Field(..., min_length=1, max_length=255)