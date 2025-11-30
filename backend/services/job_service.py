"""
Job service for handling job-related business logic.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.db.models import JobPosting, Resume, InterviewSession
from backend.services.orchestrator import Orchestrator
from utils.embeddings import get_embedding_provider
from utils.vector_db import get_vector_db
from utils.job_api_client import JobAPIClient

logger = logging.getLogger(__name__)


class JobService:
    """Service for job operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = Orchestrator()
        self.embedding_provider = get_embedding_provider()
        self.vector_db = get_vector_db()
        self.job_api_client = JobAPIClient()
    
    def get_job(self, job_id: int) -> Optional[JobPosting]:
        """Get job posting by ID."""
        return self.db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    def get_all_jobs(self, active_only: bool = True) -> List[JobPosting]:
        """Get all job postings."""
        query = self.db.query(JobPosting)
        if active_only:
            query = query.filter(JobPosting.is_active == True)
        return query.all()
    
    def create_job(
        self,
        title: str,
        company: str,
        description: str,
        location: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        seniority_level: Optional[str] = None,
        application_url: Optional[str] = None
    ) -> JobPosting:
        """
        Create a new job posting.
        
        Args:
            title: Job title
            company: Company name
            description: Job description
            location: Job location
            required_skills: List of required skills
            seniority_level: Seniority level
            application_url: Application URL
            
        Returns:
            Created job posting
        """
        logger.info(f"Creating job posting: {title} at {company}")
        
        job = JobPosting(
            title=title,
            company=company,
            location=location,
            description=description,
            required_skills=required_skills or [],
            seniority_level=seniority_level,
            application_url=application_url,
            is_active=True
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Generate embedding and store in vector DB
        job_text = f"{title} {description} {' '.join(required_skills or [])}"
        embedding = self.embedding_provider.embed(job_text)
        
        vector_id = f"job_{job.id}"
        metadata = {
            "type": "job",
            "job_id": job.id,
            "title": title,
            "company": company,
            "required_skills": required_skills or []
        }
        
        self.vector_db.upsert(vector_id, embedding, metadata)
        
        job.vector_id = vector_id
        self.db.commit()
        
        logger.info(f"Job posting created: job_id={job.id}")
        return job
    
    def recommend_jobs(
        self,
        resume_id: int,
        interview_session_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend jobs for a candidate.
        
        Args:
            resume_id: Resume ID
            interview_session_id: Optional interview session ID
            top_k: Number of recommendations
            
        Returns:
            List of job recommendations
        """
        logger.info(f"Generating job recommendations: resume_id={resume_id}")
        
        # Get resume
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")
        
        # Get resume embedding
        resume_embedding = None
        if resume.vector_id:
            # Try to get from vector DB (we'll need to re-embed if not available)
            # For now, re-embed the resume text
            resume_text = resume.raw_text or str(resume.parsed_data)
            resume_embedding = self.embedding_provider.embed(resume_text)
        else:
            resume_text = resume.raw_text or str(resume.parsed_data)
            resume_embedding = self.embedding_provider.embed(resume_text)
        
        # Get interview summary embedding if available
        interview_summary_embedding = None
        candidate_summary = ""
        
        if interview_session_id:
            session = self.db.query(InterviewSession).filter(
                InterviewSession.id == interview_session_id
            ).first()
            
            if session and session.summary:
                candidate_summary = f"Resume: {resume_text[:500]}\nInterview Summary: {session.summary}"
                interview_summary_embedding = self.embedding_provider.embed(session.summary)
        else:
            candidate_summary = resume_text[:1000]
        
        # Build candidate summary
        if not candidate_summary:
            skills = resume.parsed_data.get("skills", []) if resume.parsed_data else []
            experience = resume.parsed_data.get("experience", [])[:2] if resume.parsed_data else []
            candidate_summary = f"Skills: {', '.join(skills[:10])}\n"
            for exp in experience:
                candidate_summary += f"{exp.get('title', '')} at {exp.get('company', '')}\n"
        
        # Job details provider function
        def get_job_details(job_id: int) -> Optional[Dict[str, Any]]:
            job = self.get_job(job_id)
            if job:
                return {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "description": job.description,
                    "required_skills": job.required_skills or [],
                    "seniority_level": job.seniority_level,
                    "application_url": job.application_url
                }
            return None
        
        # Get recommendations from local database first
        recommendations = []
        
        # Check if vector DB is available, if not use simple fallback immediately
        vector_db_available = self.vector_db.client is not None
        
        if vector_db_available:
            try:
                result = self.orchestrator.recommend_jobs(
                    resume_embedding=resume_embedding,
                    interview_summary_embedding=interview_summary_embedding,
                    candidate_summary=candidate_summary,
                    top_k=top_k,
                    job_details_provider=get_job_details
                )
                
                for rec in result.get("recommendations", []):
                    job = self.get_job(rec["job_id"])
                    if job:
                        recommendations.append({
                            "job_id": job.id,
                            "title": job.title,
                            "company": job.company,
                            "location": job.location,
                            "score": rec["score"],
                            "rationale": rec["rationale"],
                            "matched_skills": rec["matched_skills"],
                            "application_url": job.application_url,
                            "source": "local"
                        })
            except Exception as e:
                logger.warning(f"Vector-based recommendation failed: {e}. Using simple fallback.")
                recommendations = []  # Clear to trigger fallback
        
        # Use simple fallback if vector DB not available or no recommendations found
        if not recommendations or not vector_db_available:
            logger.info(f"Vector DB available: {vector_db_available}. Using simple fallback to return all jobs.")
            all_jobs = self.get_all_jobs(active_only=True)
            logger.info(f"Found {len(all_jobs)} jobs in database, using simple fallback mode")
            
            if not all_jobs:
                logger.warning("No jobs found in database")
            else:
                # Extract skills from resume for simple matching
                resume_skills = []
                if resume.parsed_data and resume.parsed_data.get("skills"):
                    resume_skills = [s.lower() for s in resume.parsed_data["skills"]]
                
                for job in all_jobs[:top_k]:
                    # Simple skill matching
                    job_skills = [s.lower() for s in (job.required_skills or [])]
                    matched_skills = [s for s in resume_skills if any(s in js or js in s for js in job_skills)]
                    match_score = min(100, 50 + (len(matched_skills) * 10))
                    
                    recommendations.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "score": float(match_score),
                        "rationale": f"Match based on available job posting. {len(matched_skills)} skills aligned." if matched_skills else "Match based on available job posting.",
                        "matched_skills": matched_skills[:5] if matched_skills else (job.required_skills or [])[:5],
                        "application_url": job.application_url,
                        "source": "local"
                    })
        
        # If we don't have enough recommendations, fetch from external APIs
        if len(recommendations) < top_k:
            logger.info(f"Only {len(recommendations)} local jobs found. Fetching from external APIs...")
            
            try:
                # Extract skills from resume for API search
                skills = []
                if resume.parsed_data and resume.parsed_data.get("skills"):
                    skills = resume.parsed_data["skills"]
                
                # Get location from resume if available
                location = None
                if resume.parsed_data:
                    contact = resume.parsed_data.get("contact", {})
                    if isinstance(contact, dict):
                        location = contact.get("address") or contact.get("location")
                
                # If no skills found, use default keywords based on resume content
                if not skills:
                    resume_text = resume.raw_text or str(resume.parsed_data)
                    # Extract common tech keywords as fallback
                    common_keywords = ["software", "developer", "engineer", "programming", "technology"]
                    skills = [kw for kw in common_keywords if kw.lower() in resume_text.lower()][:3]
                    if not skills:
                        skills = ["software developer"]  # Default search term
                
                logger.info(f"Searching for jobs with skills: {skills}, location: {location}")
                
                # Fetch jobs from external APIs
                api_jobs = self.job_api_client.fetch_jobs_by_skills(
                    skills=skills[:5] if skills else ["software developer"],
                    location=location,
                    limit=top_k * 3  # Fetch more to have better matches
                )
                
                if api_jobs:
                    logger.info(f"Fetched {len(api_jobs)} jobs from external APIs")
                    
                    # Store API jobs temporarily in vector DB and process them
                    api_recommendations = self._process_api_jobs(
                        api_jobs=api_jobs,
                        resume_embedding=resume_embedding,
                        interview_summary_embedding=interview_summary_embedding,
                        candidate_summary=candidate_summary,
                        top_k=top_k - len(recommendations)
                    )
                    
                    if api_recommendations:
                        logger.info(f"Successfully processed {len(api_recommendations)} API job recommendations")
                        recommendations.extend(api_recommendations)
                    else:
                        logger.warning("No API jobs matched after processing")
                else:
                    logger.warning("No jobs returned from external APIs. Check API keys configuration.")
            
            except Exception as e:
                logger.error(f"Error fetching jobs from external APIs: {e}", exc_info=True)
                # Continue with whatever recommendations we have
        
        # Limit to top_k total
        recommendations = recommendations[:top_k]
        
        logger.info(f"Generated {len(recommendations)} total job recommendations ({len([r for r in recommendations if r.get('source') == 'external'])}) from APIs)")
        return recommendations
    
    def _process_api_jobs(
        self,
        api_jobs: List[Dict[str, Any]],
        resume_embedding: List[float],
        interview_summary_embedding: Optional[List[float]] = None,
        candidate_summary: str = "",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Process API-fetched jobs and match them against candidate profile.
        
        Args:
            api_jobs: List of jobs from external APIs
            resume_embedding: Resume embedding vector
            interview_summary_embedding: Interview summary embedding (optional)
            candidate_summary: Candidate summary text
            top_k: Number of recommendations to return
            
        Returns:
            List of matched job recommendations
        """
        if not api_jobs:
            return []
        
        logger.info(f"Processing {len(api_jobs)} API jobs for matching")
        
        try:
            # Store jobs temporarily in vector DB for similarity search
            temp_job_ids = []
            for job in api_jobs:
                job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('required_skills', []))}"
                embedding = self.embedding_provider.embed(job_text)
                
                temp_id = f"api_job_{job.get('external_id', id(job))}"
                metadata = {
                    "type": "job",
                    "source": "external_api",
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", "")[:500],  # Limit description for metadata
                    "required_skills": job.get("required_skills", []),
                    "application_url": job.get("application_url", ""),
                    "external_id": job.get("external_id", "")
                }
                
                self.vector_db.upsert(temp_id, embedding, metadata)
                temp_job_ids.append((temp_id, job))
            
            # Build candidate profile
            from agents.job_reco_agent import JobRecAgent
            job_agent = JobRecAgent()
            profile = job_agent.build_candidate_profile(
                resume_embedding=resume_embedding,
                interview_summary_embedding=interview_summary_embedding
            )
            
            # Find similar jobs using vector search
            similar_results = job_agent.find_similar_jobs(
                candidate_profile=profile,
                top_k=min(top_k * 2, len(api_jobs))
            )
            
        except Exception as e:
            logger.warning(f"Vector matching failed, using simple fallback: {e}")
            # Fallback: return jobs directly without vector matching
            similar_results = []
            temp_job_ids = [(f"api_job_{i}", job) for i, job in enumerate(api_jobs)]
        
        # Match vector search results with API jobs, or use all jobs if no results
        recommendations = []
        
        # If no vector results, use all jobs with simple scoring
        if not similar_results:
            logger.info("No vector results, using simple fallback scoring")
            for temp_id, api_job in temp_job_ids[:top_k]:
                recommendations.append({
                    "job_id": None,
                    "title": api_job.get("title", ""),
                    "company": api_job.get("company", ""),
                    "location": api_job.get("location", ""),
                    "score": 70.0,  # Default score
                    "rationale": "Match based on job availability.",
                    "matched_skills": api_job.get("required_skills", [])[:5],
                    "application_url": api_job.get("application_url", ""),
                    "source": "external_api",
                    "description": api_job.get("description", "")[:500]
                })
            return recommendations
        
        for result in similar_results:
            vector_id = result.get("id", "")
            
            # Find corresponding API job
            api_job = None
            for temp_id, job in temp_job_ids:
                if temp_id == vector_id:
                    api_job = job
                    break
            
            if api_job:
                # Use LLM to score the match (if available) or use vector score
                score = result.get("score", 0) * 100
                
                # Try to get better score with LLM re-ranking
                try:
                    from utils.prompts import format_job_re_ranker_prompt
                    from utils.llm_client import get_llm_client
                    
                    llm_client = get_llm_client()
                    if llm_client.api_key:
                        prompt = format_job_re_ranker_prompt(
                            candidate_summary=candidate_summary[:500],
                            job_title=api_job.get("title", ""),
                            job_company=api_job.get("company", ""),
                            job_description=api_job.get("description", "")[:1000],
                            required_skills=", ".join(api_job.get("required_skills", [])),
                            seniority_level=api_job.get("seniority_level", "")
                        )
                        
                        llm_result = llm_client.complete_json(prompt)
                        llm_score = float(llm_result.get("score", score))
                        
                        # Weighted combination
                        score = (llm_score * 0.6) + (score * 0.4)
                        rationale = llm_result.get("rationale", "Good match based on skills and experience.")
                        matched_skills = llm_result.get("matched_skills", api_job.get("required_skills", [])[:5])
                    else:
                        rationale = "Match based on vector similarity."
                        matched_skills = api_job.get("required_skills", [])[:5]
                except Exception as e:
                    logger.warning(f"Failed to re-rank API job with LLM: {e}")
                    rationale = "Match based on vector similarity."
                    matched_skills = api_job.get("required_skills", [])[:5]
                
                recommendations.append({
                    "job_id": None,  # Not in local DB
                    "title": api_job.get("title", ""),
                    "company": api_job.get("company", ""),
                    "location": api_job.get("location", ""),
                    "score": round(score, 2),
                    "rationale": rationale,
                    "matched_skills": matched_skills,
                    "application_url": api_job.get("application_url", ""),
                    "source": "external_api",
                    "description": api_job.get("description", "")[:500]
                })
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # Clean up temp vector entries (optional - could keep for caching)
        # for temp_id, _ in temp_job_ids:
        #     self.vector_db.delete(temp_id)
        
        return recommendations[:top_k]

