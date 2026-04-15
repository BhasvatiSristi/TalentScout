"""
Purpose: Defines request and response shapes for resume processing.

Inputs:

* Resume data produced after PDF extraction and scoring

Outputs:

* Serialized resume scoring results for the API response

Used in:

* Resume upload route and resume service workflow
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreateResponse(BaseModel):
    """
    Shape the processed resume data returned by the API.

    Parameters:

    * id: Database id of the resume row
    * candidate_id: Related candidate id
    * file_name: Uploaded file name
    * extracted_text: Full extracted text
    * job_role: Job role used for scoring
    * extracted_skills: Skills found in the resume
    * required_skills: Skills expected for the role
    * matched_skills: Skills found in both lists
    * interview_questions: Generated interview questions
    * ats_score: ATS-style score
    * created_at: Creation timestamp

    Returns:

    * ResumeCreateResponse: Response model for the processed resume

    Steps:

    1. Read the stored resume record
    2. Attach the extracted scoring data
    3. Serialize the combined result for the API
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int | None = None
    file_name: str
    extracted_text: str
    job_role: str
    extracted_skills: list[str]
    required_skills: list[str]
    matched_skills: list[str]
    interview_questions: list[str]
    ats_score: float
    created_at: datetime


class ResumeExtractResponse(BaseModel):
    """
    Wrap the resume processing result and success message.

    Parameters:

    * message: Simple success message
    * data: Processed resume details

    Returns:

    * ResumeExtractResponse: Full response model for the resume endpoint

    Steps:

    1. Set a default success message
    2. Include the processed resume payload
    """
    message: str = Field(default="Resume text extracted successfully")
    data: ResumeCreateResponse
