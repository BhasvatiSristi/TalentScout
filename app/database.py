"""
Purpose: Configures the database connection and session helpers.

Inputs:

* DATABASE_URL environment variable or a local SQLite fallback

Outputs:

* SQLAlchemy engine, session factory, and database session dependency

Used in:

* Shared by routers and services that need database access
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./talentscout.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Provide a database session for request handlers.

    Parameters:

    * None

    Returns:

    * Generator: Yields one SQLAlchemy session and closes it afterward

    Steps:

    1. Create a new session
    2. Yield it to the caller
    3. Close the session after the request finishes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
