"""
Job recommendation API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.deps import get_database
from backend.services.job_service import JobService
from utils.schemas import JobRecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/recommend", response_model=JobRecommendationResponse)
async def recommend_jobs(
    resume_id: int = Query(..., description="Resume ID"),
    interview_session_id: Optional[int] = Query(None, description="Optional interview session ID"),
    top_k: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    db: Session = Depends(get_database)
):
    """
    Get job recommendations for a candidate.
    
    - **resume_id**: Resume ID (required)
    - **interview_session_id**: Optional interview session ID for enhanced matching
    - **top_k**: Number of recommendations (default: 5, max: 20)
    """
    try:
        service = JobService(db)
        recommendations = service.recommend_jobs(
            resume_id=resume_id,
            interview_session_id=interview_session_id,
            top_k=top_k
        )
        
        logger.info(f"Generated {len(recommendations)} job recommendations for resume_id={resume_id}")
        
        return JobRecommendationResponse(
            recommendations=recommendations,
            candidate_profile_summary=None  # Could add summary here
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("/")
async def list_jobs(
    active_only: bool = Query(True, description="Show only active jobs"),
    db: Session = Depends(get_database)
):
    """List all job postings."""
    service = JobService(db)
    jobs = service.get_all_jobs(active_only=active_only)
    
    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description[:500] + "..." if len(job.description) > 500 else job.description,
            "required_skills": job.required_skills,
            "seniority_level": job.seniority_level,
            "application_url": job.application_url,
            "is_active": job.is_active,
            "created_at": job.created_at
        }
        for job in jobs
    ]


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: Session = Depends(get_database)
):
    """Get job posting by ID."""
    service = JobService(db)
    job = service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job posting not found: {job_id}")
    
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
        "required_skills": job.required_skills,
        "seniority_level": job.seniority_level,
        "keywords": job.keywords,
        "application_url": job.application_url,
        "is_active": job.is_active,
        "created_at": job.created_at
    }

