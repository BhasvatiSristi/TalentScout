"""
Purpose: Stores generated interview questions in order for conversational flow.

Inputs:

* Candidate id, question text, and display order

Outputs:

* SQLAlchemy interview question rows

Used in:

* Resume processing and conversational interview flow
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from app.database import Base


class InterviewQuestion(Base):
    """
    Define the interview_questions table structure.
    """

    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    question_order = Column(Integer, nullable=False, index=True)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
