from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.feedback import FeedbackCreateRequest
from app.services.feedback_service import CandidateNotFoundError, save_feedback_and_send_email

router = APIRouter()


@router.post("/submit-feedback")
def submit_feedback(payload: FeedbackCreateRequest, db: Session = Depends(get_db)) -> dict:
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
