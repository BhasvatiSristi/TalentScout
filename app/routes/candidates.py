"""
Purpose: Handles candidate intake requests.

Inputs:

* Candidate intake data from the frontend or API client

Outputs:

* Saved candidate data or validation and conflict errors

Used in:

* Called by the Streamlit frontend to create a candidate record
"""

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
    """
    Create a new candidate intake record.

    Parameters:

    * payload: Candidate details submitted by the client
    * db: Database session from the dependency injection system

    Returns:

    * CandidateIntakeResponse: Saved candidate information and message

    Steps:

    1. Save the candidate using the service layer
    2. Convert duplicate email errors into an HTTP conflict response
    3. Return the stored candidate data to the caller
    """
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
