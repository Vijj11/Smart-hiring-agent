"""
Unit tests for resume scoring functionality.
"""

import pytest
from agents.resume_agent import ResumeAgent


def test_score_resume():
    """Test resume scoring against a job description."""
    agent = ResumeAgent()
    
    # Sample resume data
    resume_data = {
        "skills": ["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "React", "Node.js"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "start": "2020",
                "end": "Present",
                "bullets": ["Led microservices development", "Implemented CI/CD pipelines"],
                "duration_years": 4.0
            }
        ],
        "raw_text": "Python JavaScript AWS Docker Kubernetes React Node.js microservices CI/CD"
    }
    
    # Sample job description
    job_description = {
        "required_skills": ["Python", "JavaScript", "AWS", "Docker", "Kubernetes"],
        "seniority_level": "senior",
        "keywords": ["python", "aws", "docker", "kubernetes", "microservices", "ci/cd"]
    }
    
    result = agent.score_resume(resume_data, job_description)
    
    # Assert score is between 0 and 100
    assert "score" in result
    assert 0 <= result["score"] <= 100
    
    # Assert breakdown exists
    assert "breakdown" in result
    breakdown = result["breakdown"]
    assert "skill_match" in breakdown
    assert "seniority_match" in breakdown
    assert "recency" in breakdown
    assert "keywords" in breakdown
    
    # Assert all breakdown scores are between 0 and 100
    for key, value in breakdown.items():
        assert 0 <= value <= 100, f"{key} score out of range: {value}"
    
    # Assert matched skills
    assert "top_matched_skills" in result
    assert isinstance(result["top_matched_skills"], list)


def test_score_resume_low_match():
    """Test scoring with low skill match."""
    agent = ResumeAgent()
    
    resume_data = {
        "skills": ["Java", "C++"],
        "experience": [],
        "raw_text": "Java C++ programming"
    }
    
    job_description = {
        "required_skills": ["Python", "JavaScript", "AWS"],
        "seniority_level": "senior",
        "keywords": ["python", "javascript", "aws"]
    }
    
    result = agent.score_resume(resume_data, job_description)
    
    # Should have lower score due to skill mismatch
    assert result["score"] < 50
    assert result["breakdown"]["skill_match"] < 50


def test_score_resume_high_match():
    """Test scoring with high skill match."""
    agent = ResumeAgent()
    
    resume_data = {
        "skills": ["Python", "JavaScript", "AWS", "Docker", "React", "Node.js"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "start": "2020",
                "end": "Present",
                "bullets": ["Built microservices with Python and AWS", "Used Docker for deployment"],
                "duration_years": 5.0
            }
        ],
        "raw_text": "Python JavaScript AWS Docker React Node.js microservices"
    }
    
    job_description = {
        "required_skills": ["Python", "JavaScript", "AWS", "Docker"],
        "seniority_level": "senior",
        "keywords": ["python", "javascript", "aws", "docker", "microservices"]
    }
    
    result = agent.score_resume(resume_data, job_description)
    
    # Should have higher score due to good match
    assert result["score"] >= 60
    assert result["breakdown"]["skill_match"] >= 70

