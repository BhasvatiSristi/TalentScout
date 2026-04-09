"""Service module for resume extraction and scoring workflows."""

from io import BytesIO
from datetime import datetime

import pdfplumber
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.interview_session import InterviewSession
from app.models.resume import Resume
from app.services.llm_service import generate_questions
from app.services.scoring_service import calculate_ats_score, extract_skills, get_required_skills, match_skills


class CandidateNotFoundError(Exception):
    """Raised when resume upload references a missing candidate."""


class ResumeProcessingError(Exception):
    """Raised for invalid resume content or role matching input."""


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract all text from a PDF file."""
    try:
        pdf_file = BytesIO(file_content)
        extracted_text = ""

        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF file is empty (no pages found).")

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    extracted_text += f"\n--- Page {page_num} ---\n{text}"

        return extracted_text.strip()

    except pdfplumber.exceptions.PDFException as e:
        raise ValueError(f"Error reading PDF: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error while extracting text: {str(e)}")


def process_resume_upload(
    db: Session,
    candidate_id: int,
    job_role: str,
    file_name: str,
    file_content: bytes,
) -> dict:
    """Run resume extraction and scoring workflow, then persist results."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise CandidateNotFoundError("Candidate not found.")

    try:
        extracted_text = extract_text_from_pdf(file_content)
        extracted_skills = extract_skills(extracted_text)
        required_skills = get_required_skills(job_role)
        matched_skills = match_skills(extracted_skills, required_skills)
        missing_skills = [skill for skill in required_skills if skill not in matched_skills]
        ats_score = calculate_ats_score(matched_skills, required_skills)
        interview_questions = generate_questions(
            job_role=job_role,
            resume_text=extracted_text,
            skills=extracted_skills,
            missing_skills=missing_skills,
        )
        interview_started_at = datetime.utcnow()

        resume_record = Resume(
            candidate_id=candidate_id,
            file_name=file_name,
            extracted_text=extracted_text,
            ats_score=ats_score,
        )
        db.add(resume_record)

        existing_session = (
            db.query(InterviewSession)
            .filter(InterviewSession.candidate_id == candidate_id)
            .first()
        )
        if existing_session:
            existing_session.started_at = interview_started_at
            existing_session.submitted_at = None
            existing_session.total_time_seconds = None
        else:
            db.add(InterviewSession(candidate_id=candidate_id, started_at=interview_started_at))

        db.commit()
        db.refresh(resume_record)

        return {
            "resume_record": resume_record,
            "job_role": job_role,
            "extracted_skills": extracted_skills,
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "interview_questions": interview_questions,
            "ats_score": ats_score,
        }
    except ValueError as exc:
        db.rollback()
        raise ResumeProcessingError(str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise RuntimeError("An unexpected error occurred while processing the resume.") from exc
