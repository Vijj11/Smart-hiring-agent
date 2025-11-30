"""
Resume service for handling resume-related business logic.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from sqlalchemy.orm import Session

from backend.db.models import Resume, Candidate, JobPosting
from backend.services.orchestrator import Orchestrator
from utils.schemas import ParsedResumeData

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = Orchestrator()
        self.upload_dir = "data/uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def upload_resume(
        self,
        file_content: bytes,
        filename: str,
        candidate_id: Optional[int] = None,
        target_jd_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a resume.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            candidate_id: Optional candidate ID
            target_jd_id: Optional target job description ID
            
        Returns:
            Resume data with parsing and scoring results
        """
        logger.info(f"Uploading resume: {filename}")
        
        # Save file
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Get job description if provided
        job_description = None
        if target_jd_id:
            job = self.db.query(JobPosting).filter(JobPosting.id == target_jd_id).first()
            if job:
                job_description = {
                    "required_skills": job.required_skills or [],
                    "seniority_level": job.seniority_level,
                    "keywords": job.keywords or [],
                    "description": job.description
                }
        
        # Process resume through orchestrator
        result = self.orchestrator.process_resume_upload(
            file_path=file_path,
            job_description=job_description,
            use_llm=True
        )
        
        # Create or get candidate
        candidate = None
        if candidate_id:
            candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate and result["parsed_data"].get("emails"):
            # Try to find by email
            email = result["parsed_data"]["emails"][0]
            candidate = self.db.query(Candidate).filter(Candidate.email == email).first()
        
        if not candidate:
            # Create new candidate
            candidate = Candidate(
                name=result["parsed_data"].get("name"),
                email=result["parsed_data"].get("emails", [None])[0] if result["parsed_data"].get("emails") else None,
                phone=result["parsed_data"].get("phones", [None])[0] if result["parsed_data"].get("phones") else None
            )
            self.db.add(candidate)
            self.db.flush()
        
        # Create resume record
        resume = Resume(
            candidate_id=candidate.id,
            filename=filename,
            file_path=file_path,
            file_type=Path(filename).suffix.lower().lstrip('.'),
            parsed_data=result["parsed_data"],
            raw_text=result["parsed_data"].get("raw_text", ""),
            score=result.get("score"),
            score_breakdown=result.get("score_breakdown"),
            matched_skills=result.get("top_matched_skills", []),
            evidence_spans=result.get("evidence_spans", []),
            vector_id=result.get("vector_id"),
            target_jd_id=target_jd_id
        )
        
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        
        # Update vector DB metadata with resume_id
        if resume.vector_id:
            from utils.vector_db import get_vector_db
            vector_db = get_vector_db()
            existing = vector_db.get_by_id(resume.vector_id)
            if existing:
                existing["metadata"]["resume_id"] = resume.id
                vector_db.upsert(resume.vector_id, result["embedding"], existing["metadata"])
        
        logger.info(f"Resume uploaded successfully: resume_id={resume.id}")
        
        return {
            "resume_id": resume.id,
            "parsed_data": ParsedResumeData(**result["parsed_data"]).dict(),
            "score": result.get("score"),
            "score_breakdown": result.get("score_breakdown"),
            "top_matched_skills": result.get("top_matched_skills", []),
            "evidence_spans": result.get("evidence_spans", [])
        }
    
    def get_resume(self, resume_id: int) -> Optional[Resume]:
        """Get resume by ID."""
        return self.db.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_resume_embedding(self, resume_id: int) -> Optional[List[float]]:
        """Get resume embedding from vector DB."""
        resume = self.get_resume(resume_id)
        if not resume or not resume.vector_id:
            return None
        
        from utils.vector_db import get_vector_db
        vector_db = get_vector_db()
        result = vector_db.get_by_id(resume.vector_id)
        
        if result:
            # Need to get embedding - vector DB might not return it
            # For now, we'll need to re-embed if needed
            # This is a limitation - in production, store embeddings in DB or cache
            return None
        
        return None

