from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.feedback import Feedback
from app.models.resume import Resume
from app.services.email_service import send_email

router = APIRouter()


class FeedbackRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)
    confidence_score: int = Field(..., ge=1, le=10)
    experience_rating: str = Field(..., min_length=1, max_length=255)


@router.post("/submit-feedback")
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> dict:
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    latest_resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == payload.candidate_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    ats_score = latest_resume.ats_score if latest_resume is not None else 0.0

    feedback_row = Feedback(
        candidate_id=payload.candidate_id,
        confidence_score=payload.confidence_score,
        experience_rating=payload.experience_rating.strip(),
    )

    try:
        db.add(feedback_row)
        db.commit()
        db.refresh(feedback_row)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save feedback.",
        ) from exc

    subject = "TalentScout Interview Feedback"
    body = (
        f"Hello {candidate.name},\n\n"
        "Thank you for completing your interview process.\n\n"
        f"ATS Score: {ats_score}\n"
        f"Confidence Score: {payload.confidence_score}/10\n"
        f"Experience Rating: {payload.experience_rating.strip()}\n\n"
        "Regards,\n"
        "TalentScout Team"
    )

    email_sent = True
    email_error = ""
    try:
        send_email(
            to_email=candidate.email,
            subject=subject,
            body=body,
        )
    except RuntimeError as exc:
        email_sent = False
        email_error = str(exc)

    return {
        "message": "Feedback submitted successfully",
        "data": {
            "feedback_id": feedback_row.id,
            "candidate_id": feedback_row.candidate_id,
            "confidence_score": feedback_row.confidence_score,
            "experience_rating": feedback_row.experience_rating,
            "ats_score": ats_score,
            "email_sent": email_sent,
            "email_error": email_error,
        },
    }
