"""
Purpose: Handles resume upload and text extraction requests.

Inputs:

* Candidate id, job role, and uploaded PDF file

Outputs:

* Extracted resume text, skills, ATS score, and interview questions

Used in:

* Called after candidate intake to process the resume PDF
"""

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
    """
    Upload a resume, extract text, and run scoring.

    Parameters:

    * candidate_id: Candidate id from the intake flow
    * job_role: Job role selected for scoring and question generation
    * file: Uploaded PDF resume file
    * db: Database session from the dependency injection system

    Returns:

    * ResumeExtractResponse: Resume data, scores, and generated questions

    Steps:

    1. Validate that the file is a PDF and has a name
    2. Read the file bytes from the upload
    3. Send the data to the service layer for processing
    4. Convert service errors into HTTP responses
    """
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
