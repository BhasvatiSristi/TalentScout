"""
Purpose: Saves interview answers and updates interview session timing.

Inputs:

* Candidate id and submitted question-answer pairs

Outputs:

* Saved interview answer rows and updated session timing data

Used in:

* Called by the interview answers route after the user submits answers
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.interview_answer import InterviewAnswer
from app.models.interview_session import InterviewSession
from app.schemas.interview_answer import InterviewAnswerItem


class CandidateNotFoundError(Exception):
    """
    Raised when a candidate id does not exist.
    """


class InterviewSessionNotFoundError(Exception):
    """
    Raised when interview session was not initialized before answer submission.
    """


def save_interview_answers(
    db: Session,
    candidate_id: int,
    responses: list[InterviewAnswerItem],
) -> list[InterviewAnswer]:
    """
    Save interview answers and update the interview session.

    Parameters:

    * db: SQLAlchemy database session
    * candidate_id: Candidate id linked to the interview
    * responses: List of submitted question and answer items

    Returns:

    * list[InterviewAnswer]: Saved answer rows

    Steps:

    1. Confirm the candidate exists
    2. Load the interview session started during resume upload
    3. Mark the submission time and compute total interview time
    4. Save each answer row
    5. Commit the changes and refresh the saved rows
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise CandidateNotFoundError("Candidate not found.")

    interview_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate_id)
        .first()
    )
    if interview_session is None:
        raise InterviewSessionNotFoundError("Interview session not found. Please upload resume first.")

    started_at = interview_session.started_at
    submitted_at = datetime.utcnow()
    total_time_seconds = round(max(0.0, (submitted_at - started_at).total_seconds()), 2)

    interview_session.submitted_at = submitted_at
    interview_session.total_time_seconds = total_time_seconds

    saved_answers: list[InterviewAnswer] = []

    try:
        for item in responses:
            answer_row = InterviewAnswer(
                candidate_id=candidate_id,
                question=item.question.strip(),
                answer=item.answer.strip(),
                interview_started_at=started_at,
                interview_submitted_at=submitted_at,
            )
            db.add(answer_row)
            saved_answers.append(answer_row)

        db.commit()

        for item in saved_answers:
            db.refresh(item)

        return saved_answers
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Could not save interview answers.") from exc
