"""
Resume API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.deps import get_database
from backend.services.resume_service import ResumeService
from utils.schemas import ResumeUploadResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    target_jd_id: Optional[int] = Form(None),
    db: Session = Depends(get_database)
):
    """
    Upload and process a resume.
    
    - **file**: Resume file (PDF, DOCX, or TXT)
    - **target_jd_id**: Optional target job description ID for scoring
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process resume
        service = ResumeService(db)
        result = service.upload_resume(
            file_content=content,
            filename=file.filename,
            target_jd_id=target_jd_id
        )
        
        logger.info(f"Resume uploaded successfully: resume_id={result['resume_id']}")
        
        # Handle optional score_breakdown
        score_breakdown = result.get("score_breakdown")
        if score_breakdown and isinstance(score_breakdown, dict):
            from utils.schemas import ScoreBreakdown
            score_breakdown = ScoreBreakdown(**score_breakdown)
        
        return ResumeUploadResponse(
            resume_id=result["resume_id"],
            parsed_data=result["parsed_data"],
            score=result.get("score"),
            score_breakdown=score_breakdown,
            top_matched_skills=result.get("top_matched_skills", []),
            evidence_spans=result.get("evidence_spans", [])
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_database)
):
    """Get resume by ID."""
    service = ResumeService(db)
    resume = service.get_resume(resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume not found: {resume_id}")
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "parsed_data": resume.parsed_data,
        "score": resume.score,
        "score_breakdown": resume.score_breakdown,
        "matched_skills": resume.matched_skills,
        "created_at": resume.created_at
    }

