"""
Resume upload and extraction API routes.

This module handles HTTP requests for resume file uploads.
It calls resume_service to do the actual work and stores the extracted text in the database.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeCreateResponse, ResumeExtractResponse
from app.services.resume_service import extract_text_from_pdf

router = APIRouter()


@router.post("/upload", response_model=ResumeExtractResponse)
async def upload_and_extract_resume(
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
        resume_record = Resume(file_name=file.filename, extracted_text=extracted_text)

        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        return ResumeExtractResponse(
            data=ResumeCreateResponse.model_validate(resume_record),
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
