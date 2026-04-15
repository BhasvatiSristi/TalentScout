"""
Purpose: Stores candidate records in the database.

Inputs:

* Candidate name, email, phone, job role, and creation time

Outputs:

* SQLAlchemy candidate rows for the screening workflow

Used in:

* Candidate intake service and downstream resume and feedback flows
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Candidate(Base):
    """
    Define the candidates table structure.

    Parameters:

    * None

    Returns:

    * Candidate: SQLAlchemy model class for candidate rows

    Steps:

    1. Declare the table name
    2. Define the columns stored for each candidate
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    job_role = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)