from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.resume import ResumeCreateResponse, ResumeExtractResponse
from app.services.resume_service import (
    CandidateNotFoundError,
    ResumeProcessingError,
    process_resume_upload,
)

router = APIRouter()


@router.post("/upload", response_model=ResumeExtractResponse)
async def upload_and_extract_resume(
    candidate_id: int = Form(...),
    job_role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeExtractResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    file_content = await file.read()
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        result = process_resume_upload(
            db=db,
            candidate_id=candidate_id,
            job_role=job_role,
            file_name=file.filename,
            file_content=file_content,
        )

        resume_record = result["resume_record"]

        return ResumeExtractResponse(
            data=ResumeCreateResponse(
                id=resume_record.id,
                candidate_id=resume_record.candidate_id,
                file_name=resume_record.file_name,
                extracted_text=resume_record.extracted_text,
                job_role=result["job_role"],
                extracted_skills=result["extracted_skills"],
                required_skills=result["required_skills"],
                matched_skills=result["matched_skills"],
                interview_questions=result["interview_questions"],
                ats_score=result["ats_score"],
                created_at=resume_record.created_at,
            ),
        )
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ResumeProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
