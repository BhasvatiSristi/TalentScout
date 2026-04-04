from pydantic import BaseModel, EmailStr, Field


class CandidateIntakeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Enter your name", examples=["Asha Khan"])
    email: EmailStr = Field(..., description="Enter your email address", examples=["asha@example.com"])
    phone: str = Field(..., min_length=10, max_length=10, description="Enter your phone number", examples=["9876543210"])
    job_role: str = Field(..., min_length=2, max_length=100, description="Enter the job role you are applying for", examples=["Frontend Developer"])


class CandidateIntakeResponse(BaseModel):
    message: str
    data: CandidateIntakeRequest


class ResumeExtractResponse(BaseModel):
    """Response schema for resume text extraction."""
    extracted_text: str = Field(..., description="Extracted text from the PDF resume")
    file_name: str = Field(..., description="Name of the uploaded PDF file")
    message: str = Field(default="Resume text extracted successfully")
