from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateIntakeRequest


class CandidateAlreadyExistsError(Exception):
    """Raised when a candidate with the same email already exists."""


def create_candidate(db: Session, payload: CandidateIntakeRequest) -> Candidate:
    """Create and persist a candidate intake record."""
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
