"""
Purpose: Stores submitted interview answers in the database.

Inputs:

* Candidate id, question text, answer text, and timestamps

Outputs:

* SQLAlchemy interview answer rows

Used in:

* Interview answer submission service
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from app.database import Base


class InterviewAnswer(Base):
    """
    Define the interview_answers table structure.

    Parameters:

    * None

    Returns:

    * InterviewAnswer: SQLAlchemy model class for answer rows

    Steps:

    1. Declare the table name
    2. Define the columns used to store each answer
    """
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    interview_started_at = Column(DateTime, nullable=True)
    interview_submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
