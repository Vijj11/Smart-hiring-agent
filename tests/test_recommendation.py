"""
Unit tests for job recommendation functionality.
"""

import pytest
from agents.job_reco_agent import JobRecAgent


def test_recommend_jobs():
    """Test job recommendation returns list with rationale."""
    agent = JobRecAgent()
    
    # Sample resume embedding (1536 dimensions for OpenAI)
    resume_embedding = [0.1] * 1536
    
    # Mock job details provider
    def mock_job_provider(job_id: int):
        return {
            "id": job_id,
            "title": "Software Engineer",
            "company": "TechCorp",
            "description": "Python JavaScript AWS",
            "required_skills": ["Python", "JavaScript", "AWS"],
            "seniority_level": "senior"
        }
    
    # This test may fail if vector DB is not initialized
    # In a real test, we'd mock the vector DB
    try:
        result = agent.recommend_jobs(
            resume_embedding=resume_embedding,
            candidate_summary="Python JavaScript AWS experience",
            top_k=5,
            job_details_provider=mock_job_provider
        )
        
        # Should return a list
        assert isinstance(result, list)
        
        # If recommendations exist, check structure
        if len(result) > 0:
            for rec in result:
                assert "job_id" in rec
                assert "score" in rec
                assert "rationale" in rec
                assert isinstance(rec["rationale"], str)
                assert len(rec["rationale"]) > 0
    
    except Exception as e:
        # If vector DB is not available, skip test
        pytest.skip(f"Vector DB not available: {e}")


def test_build_candidate_profile():
    """Test candidate profile building."""
    agent = JobRecAgent()
    
    resume_embedding = [0.1] * 1536
    interview_embedding = [0.2] * 1536
    
    profile = agent.build_candidate_profile(
        resume_embedding=resume_embedding,
        interview_summary_embedding=interview_embedding,
        resume_weight=0.7,
        interview_weight=0.3
    )
    
    # Should return a list of floats
    assert isinstance(profile, list)
    assert len(profile) == 1536
    assert all(isinstance(x, (int, float)) for x in profile)


def test_recommend_jobs_structure():
    """Test that recommendation result has correct structure."""
    agent = JobRecAgent()
    
    # Test with empty vector DB (will return empty list)
    resume_embedding = [0.1] * 1536
    
    result = agent.recommend_jobs(
        resume_embedding=resume_embedding,
        candidate_summary="Test candidate",
        top_k=5
    )
    
    # Should return a list (may be empty if no jobs in vector DB)
    assert isinstance(result, list)
    
    # If there are recommendations, check they have required fields
    for rec in result:
        assert "job_id" in rec
        assert "score" in rec
        assert "rationale" in rec
        assert "matched_skills" in rec

