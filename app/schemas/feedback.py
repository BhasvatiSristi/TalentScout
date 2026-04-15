"""
Purpose: Defines the request body for final feedback submission.

Inputs:

* Candidate id and confidence score from the frontend

Outputs:

* Validated feedback request data

Used in:

* Feedback route and feedback service
"""

from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    """
    Validate the feedback form submission.

    Parameters:

    * candidate_id: Candidate id for the finished interview
    * confidence_score: Final score from 1 to 10

    Returns:

    * FeedbackCreateRequest: Validated feedback request model

    Steps:

    1. Check the candidate id
    2. Check that the score is in range
    3. Pass the data to the route handler
    """
    candidate_id: int = Field(..., ge=1)
    confidence_score: int = Field(..., ge=1, le=10)
