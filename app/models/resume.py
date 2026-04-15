"""
Purpose: Stores resume processing results in the database.

Inputs:

* Candidate id, file name, extracted text, and ATS score

Outputs:

* SQLAlchemy resume rows for the screening workflow

Used in:

* Resume upload service and feedback summary flow
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


class Resume(Base):
    """
    Define the resumes table structure.

    Parameters:

    * None

    Returns:

    * Resume: SQLAlchemy model class for resume rows

    Steps:

    1. Declare the table name
    2. Define the columns used to store extracted resume data
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=False)
    ats_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
