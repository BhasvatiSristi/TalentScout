from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateIntakeRequest, CandidateIntakeResponse

router = APIRouter()


@router.post("/intake", response_model=CandidateIntakeResponse)
def create_candidate_intake(
    payload: CandidateIntakeRequest,
    db: Session = Depends(get_db),
) -> CandidateIntakeResponse:
    candidate = Candidate(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        job_role=payload.job_role,
    )

    db.add(candidate)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists.",
        )

    return CandidateIntakeResponse(
        message="Candidate intake received successfully",
        data=payload,
    )
