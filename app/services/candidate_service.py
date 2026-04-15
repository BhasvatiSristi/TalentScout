"""
Purpose: Creates candidate records in the database.

Inputs:

* Candidate intake data from the API layer

Outputs:

* Stored candidate rows or a duplicate-email error

Used in:

* Called by the candidate intake route
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateIntakeRequest


class CandidateAlreadyExistsError(Exception):
    """
    Raised when a candidate with the same email already exists.
    """


def create_candidate(db: Session, payload: CandidateIntakeRequest) -> Candidate:
    """
    Create and save a candidate intake record.

    Parameters:

    * db: SQLAlchemy database session
    * payload: Candidate intake details from the request body

    Returns:

    * Candidate: The saved candidate row

    Steps:

    1. Build a candidate object from the payload
    2. Add it to the session and commit it
    3. Roll back and raise a friendly error if the email already exists
    4. Refresh the object and return it
    """
    candidate = Candidate(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        job_role=payload.job_role,
    )

    db.add(candidate)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CandidateAlreadyExistsError("A candidate with this email already exists.") from exc

    db.refresh(candidate)
    return candidate
