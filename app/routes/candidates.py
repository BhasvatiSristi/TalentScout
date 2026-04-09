from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.candidate import CandidateCreateResponse, CandidateIntakeRequest, CandidateIntakeResponse
from app.services.candidate_service import CandidateAlreadyExistsError, create_candidate

router = APIRouter()


@router.post("/intake", response_model=CandidateIntakeResponse)
def create_candidate_intake(
    payload: CandidateIntakeRequest,
    db: Session = Depends(get_db),
) -> CandidateIntakeResponse:
    try:
        candidate = create_candidate(db=db, payload=payload)
    except CandidateAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CandidateIntakeResponse(
        message="Candidate intake received successfully",
        data=CandidateCreateResponse(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            job_role=candidate.job_role,
            created_at=candidate.created_at,
        ),
    )
