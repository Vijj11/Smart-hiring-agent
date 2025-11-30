"""
Dependency injection for FastAPI.
"""

from typing import Generator
from sqlalchemy.orm import Session

from backend.db.session import get_db, init_db
from utils.vector_db import get_vector_db

# Initialize database on import
init_db()


def get_database() -> Generator[Session, None, None]:
    """Dependency for database session."""
    yield from get_db()


def get_vector_database():
    """Dependency for vector database."""
    return get_vector_db()

