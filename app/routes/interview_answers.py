"""
Purpose: Handles submitted interview answers.

Inputs:

* Candidate id and a list of question and answer pairs

Outputs:

* Saved interview answer records and interview timing data

Used in:

* Called after the user finishes answering generated interview questions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.interview_answer import (
    InterviewAnswersCreateRequest,
    InterviewAnswersCreateResponse,
    InterviewAnswerSaved,
)
from app.services.interview_service import (
    CandidateNotFoundError,
    InterviewSessionNotFoundError,
    save_interview_answers,
)

router = APIRouter()


@router.post("/submit", response_model=InterviewAnswersCreateResponse)
def submit_interview_answers(
    payload: InterviewAnswersCreateRequest,
    db: Session = Depends(get_db),
) -> InterviewAnswersCreateResponse:
    """
    Save the interview answers for a candidate.

    Parameters:

    * payload: Candidate id and the submitted responses
    * db: Database session from the dependency injection system

    Returns:

    * InterviewAnswersCreateResponse: Saved answer records

    Steps:

    1. Pass the answers to the service layer
    2. Convert missing candidate or session errors into HTTP responses
    3. Return the saved answer data
    """
    try:
        saved_answers = save_interview_answers(
            db=db,
            candidate_id=payload.candidate_id,
            responses=payload.responses,
        )
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InterviewSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return InterviewAnswersCreateResponse(
        data=[
            InterviewAnswerSaved(
                id=item.id,
                candidate_id=item.candidate_id,
                question=item.question,
                answer=item.answer,
                interview_started_at=item.interview_started_at,
                interview_submitted_at=item.interview_submitted_at,
                created_at=item.created_at,
            )
            for item in saved_answers
        ]
    )
