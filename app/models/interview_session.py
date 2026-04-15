"""
Purpose: Stores interview timing information in the database.

Inputs:

* Candidate id, start time, submit time, and total interview duration

Outputs:

* SQLAlchemy interview session rows

Used in:

* Resume upload and interview answer submission services
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer

from app.database import Base


class InterviewSession(Base):
    """
    Define the interview_sessions table structure.

    Parameters:

    * None

    Returns:

    * InterviewSession: SQLAlchemy model class for interview session rows

    Steps:

    1. Declare the table name
    2. Define the columns used to track interview timing
    """
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    total_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
