from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateIntakeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Enter your name", examples=["Asha Khan"])
    email: EmailStr = Field(..., description="Enter your email address", examples=["asha@example.com"])
    phone: str = Field(..., min_length=10, max_length=10, description="Enter your phone number", examples=["9876543210"])
    job_role: str = Field(..., min_length=2, max_length=100, description="Enter the job role you are applying for", examples=["Frontend Developer"])


class CandidateCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str
    job_role: str
    created_at: datetime


class CandidateIntakeResponse(BaseModel):
    message: str
    data: CandidateCreateResponse

