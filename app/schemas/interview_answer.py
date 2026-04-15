"""
Purpose: Defines request and response shapes for interview answers.

Inputs:

* Question and answer pairs submitted by the user

Outputs:

* Validated answer requests and serialized saved answers

Used in:

* Interview answers route and interview service
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterviewAnswerItem(BaseModel):
    """
    Validate one interview question and answer pair.

    Parameters:

    * question: Interview question text
    * answer: Candidate answer text

    Returns:

    * InterviewAnswerItem: Validated answer item

    Steps:

    1. Check that the question is long enough
    2. Check that the answer is not empty
    3. Make the item available to the request model
    """
    question: str = Field(..., min_length=3)
    answer: str = Field(..., min_length=1)


class InterviewAnswersCreateRequest(BaseModel):
    """
    Validate the interview answers submission body.

    Parameters:

    * candidate_id: Candidate id for the interview
    * responses: List of question and answer items

    Returns:

    * InterviewAnswersCreateRequest: Validated request model

    Steps:

    1. Check that the candidate id is valid
    2. Check that at least one answer was submitted
    3. Pass the validated data to the route handler
    """
    candidate_id: int = Field(..., ge=1)
    responses: list[InterviewAnswerItem] = Field(..., min_length=1)


class InterviewAnswerSaved(BaseModel):
    """
    Shape the saved interview answer response.

    Parameters:

    * id: Database id
    * candidate_id: Related candidate id
    * question: Saved question text
    * answer: Saved answer text
    * interview_started_at: Interview start time
    * interview_submitted_at: Interview submission time
    * created_at: Creation timestamp

    Returns:

    * InterviewAnswerSaved: Serialized saved answer data

    Steps:

    1. Read the ORM object values
    2. Convert them into API response data
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    question: str
    answer: str
    interview_started_at: datetime | None = None
    interview_submitted_at: datetime | None = None
    created_at: datetime


class InterviewAnswersCreateResponse(BaseModel):
    """
    Wrap the list of saved interview answers.

    Parameters:

    * message: Success message for the response
    * data: Saved answer items

    Returns:

    * InterviewAnswersCreateResponse: Full response model

    Steps:

    1. Store the success message
    2. Attach the saved answer list
    """
    message: str = "Interview answers saved successfully"
    data: list[InterviewAnswerSaved]
