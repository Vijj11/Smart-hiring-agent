"""
Pytest configuration and fixtures.
"""

import pytest
import os
import tempfile
from pathlib import Path

# Set test environment variables
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("VECTOR_DB", "chroma")
os.environ.setdefault("CHROMA_DIR", str(Path(tempfile.gettempdir()) / "test_chroma"))


@pytest.fixture
def sample_resume_path():
    """Fixture for sample resume path."""
    return Path(__file__).parent.parent / "data" / "sample_resumes" / "resume1.txt"


@pytest.fixture
def sample_job_data():
    """Fixture for sample job description."""
    return {
        "title": "Software Engineer",
        "company": "TechCorp",
        "description": "We are looking for a software engineer...",
        "required_skills": ["Python", "JavaScript", "AWS"],
        "seniority_level": "senior",
        "keywords": ["python", "javascript", "aws"]
    }

