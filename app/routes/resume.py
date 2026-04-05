"""
Resume upload and extraction API routes.

This module handles HTTP requests for resume file uploads.
It calls resume_service to do the actual work and stores the extracted text in the database.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeCreateResponse, ResumeExtractResponse
from app.services.resume_service import extract_text_from_pdf
from app.services.scoring_service import (
    calculate_ats_score,
    extract_skills,
    get_required_skills,
    match_skills,
)

router = APIRouter()


@router.post("/upload", response_model=ResumeExtractResponse)
async def upload_and_extract_resume(
    job_role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeExtractResponse:
    """
    Upload a PDF resume, extract text from it, and store the extracted text in SQLite.

    Args:
        file: PDF file uploaded by the user.
        db: SQLAlchemy session.

    Returns:
        ResumeExtractResponse: Contains the saved resume record.
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
        extracted_text = extract_text_from_pdf(file_content)
        extracted_skills = extract_skills(extracted_text)
        required_skills = get_required_skills(job_role)
        matched_skills = match_skills(extracted_skills, required_skills)
        ats_score = calculate_ats_score(matched_skills, required_skills)

        resume_record = Resume(file_name=file.filename, extracted_text=extracted_text)

        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        return ResumeExtractResponse(
            data=ResumeCreateResponse(
                id=resume_record.id,
                file_name=resume_record.file_name,
                extracted_text=resume_record.extracted_text,
                job_role=job_role,
                extracted_skills=extracted_skills,
                required_skills=required_skills,
                matched_skills=matched_skills,
                ats_score=ats_score,
                created_at=resume_record.created_at,
            ),
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the resume.",
        )
