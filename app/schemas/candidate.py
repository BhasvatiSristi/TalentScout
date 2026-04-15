"""
Purpose: Defines request and response shapes for candidate intake.

Inputs:

* Candidate name, email, phone, and job role from the client

Outputs:

* Validated intake requests and serialized candidate responses

Used in:

* Candidate intake route and candidate creation service
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateIntakeRequest(BaseModel):
    """
    Validate the candidate intake request body.

    Parameters:

    * name: Candidate name
    * email: Candidate email address
    * phone: Candidate phone number
    * job_role: Job role the candidate is applying for

    Returns:

    * CandidateIntakeRequest: Validated request model

    Steps:

    1. Check each required field
    2. Apply length and format limits
    3. Make the data available to the API route
    """
    name: str = Field(..., min_length=2, max_length=100, description="Enter your name", examples=["Asha Khan"])
    email: EmailStr = Field(..., description="Enter your email address", examples=["asha@example.com"])
    phone: str = Field(..., min_length=10, max_length=10, description="Enter your phone number", examples=["9876543210"])
    job_role: str = Field(..., min_length=2, max_length=100, description="Enter the job role you are applying for", examples=["Frontend Developer"])


class CandidateCreateResponse(BaseModel):
    """
    Shape the candidate data returned after creation.

    Parameters:

    * id: Database id
    * name: Candidate name
    * email: Candidate email address
    * phone: Candidate phone number
    * job_role: Job role applied for
    * created_at: Timestamp when the row was created

    Returns:

    * CandidateCreateResponse: Response model for a saved candidate

    Steps:

    1. Read values from the ORM object
    2. Serialize them for the API response
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str
    job_role: str
    created_at: datetime


class CandidateIntakeResponse(BaseModel):
    """
    Wrap the candidate creation message and data.

    Parameters:

    * message: Simple success message
    * data: Created candidate details

    Returns:

    * CandidateIntakeResponse: Full response model for the intake endpoint

    Steps:

    1. Store the success message
    2. Attach the candidate response payload
    """
    message: str
    data: CandidateCreateResponse

