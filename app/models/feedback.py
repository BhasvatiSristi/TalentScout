"""
Purpose: Stores the final feedback score in the database.

Inputs:

* Candidate id, confidence score, and creation time

Outputs:

* SQLAlchemy feedback rows for the screening workflow

Used in:

* Feedback submission service and email summary flow
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer

from app.database import Base


class Feedback(Base):
    """
    Define the feedback table structure.

    Parameters:

    * None

    Returns:

    * Feedback: SQLAlchemy model class for feedback rows

    Steps:

    1. Declare the table name
    2. Define the columns used to store the final score
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    confidence_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
