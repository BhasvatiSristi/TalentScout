from fastapi import APIRouter

from app.schemas.candidate import CandidateIntakeRequest, CandidateIntakeResponse

router = APIRouter()


@router.post("/intake", response_model=CandidateIntakeResponse)
def create_candidate_intake(payload: CandidateIntakeRequest) -> CandidateIntakeResponse:
    return CandidateIntakeResponse(
        message="Candidate intake received successfully",
        data=payload,
    )
