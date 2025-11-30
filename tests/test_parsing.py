"""
Unit tests for resume parsing functionality.
"""

import pytest
import os
from pathlib import Path
from utils.parsing import parse_resume, parse_resume_basic, extract_text


def test_parse_txt_resume():
    """Test parsing a text resume."""
    # Use sample resume
    sample_resume_path = Path(__file__).parent.parent / "data" / "sample_resumes" / "resume1.txt"
    
    if not sample_resume_path.exists():
        pytest.skip("Sample resume not found")
    
    parsed = parse_resume(str(sample_resume_path), use_llm=False)
    
    # Assert required fields are present
    assert "name" in parsed
    assert "skills" in parsed
    assert "experience" in parsed
    assert "education" in parsed
    
    # Assert skills list is not empty
    assert isinstance(parsed["skills"], list)
    assert len(parsed["skills"]) > 0
    
    # Assert experience list is not empty
    assert isinstance(parsed["experience"], list)
    assert len(parsed["experience"]) > 0


def test_parse_resume_basic():
    """Test basic resume parsing with sample text."""
    sample_text = """
    JOHN DOE
    Software Engineer
    Email: john.doe@email.com | Phone: (555) 123-4567
    
    SKILLS
    Python, JavaScript, AWS, Docker
    
    EXPERIENCE
    Senior Software Engineer | TechCorp | 2020 - Present
    • Led development of microservices
    • Implemented CI/CD pipelines
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of California | 2014 - 2018
    """
    
    parsed = parse_resume_basic(sample_text)
    
    # Check email extraction
    assert len(parsed["emails"]) > 0
    assert "john.doe@email.com" in parsed["emails"]
    
    # Check skills extraction
    assert len(parsed["skills"]) > 0
    assert any("python" in skill.lower() for skill in parsed["skills"])
    
    # Check experience extraction
    assert len(parsed["experience"]) > 0
    assert any("engineer" in exp.get("title", "").lower() for exp in parsed["experience"])


def test_extract_text_txt():
    """Test text extraction from TXT file."""
    sample_resume_path = Path(__file__).parent.parent / "data" / "sample_resumes" / "resume1.txt"
    
    if not sample_resume_path.exists():
        pytest.skip("Sample resume not found")
    
    text = extract_text(str(sample_resume_path))
    
    assert isinstance(text, str)
    assert len(text) > 0
    assert "JOHN DOE" in text or "Software" in text


def test_parse_resume_fields():
    """Test that parsed resume has expected structure."""
    sample_resume_path = Path(__file__).parent.parent / "data" / "sample_resumes" / "resume2.txt"
    
    if not sample_resume_path.exists():
        pytest.skip("Sample resume not found")
    
    parsed = parse_resume(str(sample_resume_path), use_llm=False)
    
    # Check structure
    required_keys = ["name", "emails", "phones", "education", "experience", "skills", "certifications"]
    for key in required_keys:
        assert key in parsed, f"Missing key: {key}"
    
    # Check types
    assert isinstance(parsed["emails"], list)
    assert isinstance(parsed["skills"], list)
    assert isinstance(parsed["experience"], list)
    assert isinstance(parsed["education"], list)

