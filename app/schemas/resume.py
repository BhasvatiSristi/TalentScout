from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    extracted_text: str
    created_at: datetime


class ResumeExtractResponse(BaseModel):
    message: str = Field(default="Resume text extracted successfully")
    data: ResumeCreateResponse
