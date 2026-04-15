"""
Purpose: Handles final interview feedback submission.

Inputs:

* Candidate id and a confidence score from the frontend

Outputs:

* Saved feedback data plus email delivery status

Used in:

* Called after interview answers are submitted and the process is complete
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.feedback import FeedbackCreateRequest
from app.services.feedback_service import CandidateNotFoundError, save_feedback_and_send_email

router = APIRouter()


@router.post("/submit-feedback")
def submit_feedback(payload: FeedbackCreateRequest, db: Session = Depends(get_db)) -> dict:
    """
    Save feedback and send the summary email.

    Parameters:

    * payload: Candidate id and confidence score
    * db: Database session from the dependency injection system

    Returns:

    * dict: Message and saved feedback details

    Steps:

    1. Save the feedback through the service layer
    2. Convert service errors into HTTP responses
    3. Return the stored feedback and email status
    """
    try:
        result = save_feedback_and_send_email(
            db=db,
            candidate_id=payload.candidate_id,
            confidence_score=payload.confidence_score,
        )
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": "Feedback submitted successfully",
        "data": {
            "feedback_id": result["feedback_row"].id,
            "candidate_id": result["feedback_row"].candidate_id,
            "confidence_score": result["feedback_row"].confidence_score,
            "ats_score": result["ats_score"],
            "email_sent": result["email_sent"],
            "email_error": result["email_error"],
        },
    }
