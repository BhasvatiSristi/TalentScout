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
    InterviewAnswerStepRequest,
    InterviewAnswersCreateRequest,
    InterviewAnswersCreateResponse,
    InterviewNextQuestionData,
    InterviewNextQuestionResponse,
    InterviewAnswerSaved,
)
from app.services.interview_service import (
    CandidateNotFoundError,
    InterviewSessionNotFoundError,
    get_next_interview_question,
    save_interview_answers,
    submit_interview_answer_step,
)

router = APIRouter()


@router.get("/next", response_model=InterviewNextQuestionResponse)
def get_next_question(candidate_id: int, db: Session = Depends(get_db)) -> InterviewNextQuestionResponse:
    """
    Return the next conversational interview question for a candidate.
    """
    try:
        payload = get_next_interview_question(db=db, candidate_id=candidate_id)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return InterviewNextQuestionResponse(
        message="Next interview question fetched successfully",
        data=InterviewNextQuestionData(**payload),
    )


@router.post("/submit-step", response_model=InterviewNextQuestionResponse)
def submit_interview_answer_stepwise(
    payload: InterviewAnswerStepRequest,
    db: Session = Depends(get_db),
) -> InterviewNextQuestionResponse:
    """
    Save one answer and return the next conversational question.
    """
    try:
        result = submit_interview_answer_step(
            db=db,
            candidate_id=payload.candidate_id,
            answer=payload.answer,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return InterviewNextQuestionResponse(
        message="Interview answer saved successfully",
        data=InterviewNextQuestionData(**result),
    )


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
