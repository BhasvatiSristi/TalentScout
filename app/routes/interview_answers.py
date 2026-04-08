from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.interview_answer import InterviewAnswer
from app.models.interview_session import InterviewSession
from app.schemas.interview_answer import (
    InterviewAnswersCreateRequest,
    InterviewAnswersCreateResponse,
    InterviewAnswerSaved,
)

router = APIRouter()


@router.post("/submit", response_model=InterviewAnswersCreateResponse)
def submit_interview_answers(
    payload: InterviewAnswersCreateRequest,
    db: Session = Depends(get_db),
) -> InterviewAnswersCreateResponse:
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    interview_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == payload.candidate_id)
        .first()
    )
    if interview_session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session not found. Please upload resume first.",
        )

    started_at = interview_session.started_at
    submitted_at = datetime.utcnow()
    total_time_seconds = round(max(0.0, (submitted_at - started_at).total_seconds()), 2)

    interview_session.submitted_at = submitted_at
    interview_session.total_time_seconds = total_time_seconds

    saved_answers: list[InterviewAnswer] = []

    try:
        for item in payload.responses:
            answer_row = InterviewAnswer(
                candidate_id=payload.candidate_id,
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
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save interview answers.",
        )
