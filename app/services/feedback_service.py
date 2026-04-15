"""
Purpose: Saves final feedback and sends the summary email.

Inputs:

* Candidate id and confidence score from the feedback form

Outputs:

* Saved feedback row, ATS score, and email delivery status

Used in:

* Called by the feedback route after the interview is complete
"""

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.feedback import Feedback
from app.models.resume import Resume
from app.services.email_service import send_email


class CandidateNotFoundError(Exception):
    """
    Raised when a candidate id does not exist.
    """


def save_feedback_and_send_email(
    db: Session,
    candidate_id: int,
    confidence_score: int,
) -> dict:
    """
    Save feedback and send a summary email.

    Parameters:

    * db: SQLAlchemy database session
    * candidate_id: Candidate id linked to the feedback
    * confidence_score: Final confidence score from the user

    Returns:

    * dict: Saved feedback row, ATS score, email success flag, and email error text

    Steps:

    1. Confirm the candidate exists
    2. Read the latest resume ATS score
    3. Save the feedback row
    4. Build the email body
    5. Send the email and record whether it succeeded
    6. Return the collected result data
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise CandidateNotFoundError("Candidate not found.")

    latest_resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    ats_score = latest_resume.ats_score if latest_resume is not None else 0.0

    feedback_row = Feedback(
        candidate_id=candidate_id,
        confidence_score=confidence_score,
    )

    try:
        db.add(feedback_row)
        db.commit()
        db.refresh(feedback_row)
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Could not save feedback.") from exc

    subject = "TalentScout Interview Feedback"
    body = (
        f"Hello {candidate.name},\n\n"
        "Thank you for completing your interview process.\n\n"
        f"ATS Score: {ats_score}\n"
        f"Confidence Score: {confidence_score}/10\n"
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
        "feedback_row": feedback_row,
        "ats_score": ats_score,
        "email_sent": email_sent,
        "email_error": email_error,
    }