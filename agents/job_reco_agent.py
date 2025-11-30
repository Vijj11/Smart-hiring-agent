"""
Job Recommendation Agent: Recommends jobs based on candidate profile.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np

from agents.agent_base import AgentBase
from utils.vector_db import get_vector_db
from utils.embeddings import get_embedding_provider
from utils.llm_client import get_llm_client
from utils.prompts import format_job_re_ranker_prompt

logger = logging.getLogger(__name__)


class JobRecAgent(AgentBase):
    """Agent for job recommendations."""
    
    def __init__(self):
        super().__init__("JobRecAgent")
        self.vector_db = get_vector_db()
        self.embedding_provider = get_embedding_provider()
        self.llm_client = get_llm_client()
    
    def build_candidate_profile(
        self,
        resume_embedding: List[float],
        interview_summary_embedding: Optional[List[float]] = None,
        resume_weight: float = 0.7,
        interview_weight: float = 0.3
    ) -> List[float]:
        """
        Build aggregated candidate profile vector.
        
        Args:
            resume_embedding: Resume embedding vector
            interview_summary_embedding: Interview summary embedding (optional)
            resume_weight: Weight for resume embedding
            interview_weight: Weight for interview embedding
            
        Returns:
            Aggregated profile vector
        """
        if interview_summary_embedding:
            # Weighted average
            profile = np.array(resume_embedding) * resume_weight + np.array(interview_summary_embedding) * interview_weight
            # Normalize
            norm = np.linalg.norm(profile)
            if norm > 0:
                profile = profile / norm
            return profile.tolist()
        else:
            return resume_embedding
    
    def find_similar_jobs(
        self,
        candidate_profile: List[float],
        top_k: int = 20,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar jobs using vector similarity search.
        
        Args:
            candidate_profile: Candidate profile embedding
            top_k: Number of jobs to retrieve
            filter: Optional metadata filter
            
        Returns:
            List of similar jobs with scores
        """
        self.logger.info(f"Finding top {top_k} similar jobs")
        
        # Add filter for job postings only
        if filter is None:
            filter = {"type": "job"}
        else:
            filter["type"] = "job"
        
        results = self.vector_db.query(
            vector=candidate_profile,
            top_k=top_k,
            filter=filter
        )
        
        self.logger.info(f"Found {len(results)} similar jobs")
        return results
    
    def re_rank_jobs(
        self,
        candidate_summary: str,
        candidate_jobs: List[Dict[str, Any]],
        job_details: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank jobs using LLM for better matching.
        
        Args:
            candidate_summary: Text summary of candidate profile
            candidate_jobs: Initial job matches from vector search
            job_details: Full job details (from database)
            
        Returns:
            Re-ranked jobs with scores and rationales
        """
        self.logger.info(f"Re-ranking {len(candidate_jobs)} jobs")
        
        re_ranked = []
        
        for job_match, job_detail in zip(candidate_jobs, job_details):
            job_id = job_match.get("id") or job_detail.get("id")
            
            # Use LLM to evaluate match
            try:
                prompt = format_job_re_ranker_prompt(
                    candidate_summary=candidate_summary,
                    job_title=job_detail.get("title", ""),
                    job_company=job_detail.get("company", ""),
                    job_description=job_detail.get("description", ""),
                    required_skills=", ".join(job_detail.get("required_skills", [])),
                    seniority_level=job_detail.get("seniority_level", "")
                )
                
                llm_result = self.llm_client.complete_json(prompt)
                
                # Combine vector similarity score with LLM score
                vector_score = job_match.get("score", 0) * 100  # Convert to 0-100
                llm_score = float(llm_result.get("score", 70))
                
                # Weighted combination (60% LLM, 40% vector)
                final_score = (llm_score * 0.6) + (vector_score * 0.4)
                
                re_ranked.append({
                    "job_id": job_id,
                    "score": round(final_score, 2),
                    "rationale": llm_result.get("rationale", "Good match based on skills and experience."),
                    "matched_skills": llm_result.get("matched_skills", job_detail.get("required_skills", [])[:5])
                })
            
            except Exception as e:
                self.logger.warning(f"Failed to re-rank job {job_id}: {e}. Using vector score.")
                # Fallback: use vector score
                re_ranked.append({
                    "job_id": job_id,
                    "score": round(job_match.get("score", 0) * 100, 2),
                    "rationale": "Match based on vector similarity.",
                    "matched_skills": job_detail.get("required_skills", [])[:5]
                })
        
        # Sort by score descending
        re_ranked.sort(key=lambda x: x["score"], reverse=True)
        
        self.logger.info(f"Re-ranked {len(re_ranked)} jobs")
        return re_ranked
    
    def recommend_jobs(
        self,
        resume_embedding: List[float],
        interview_summary_embedding: Optional[List[float]] = None,
        candidate_summary: str = "",
        top_k: int = 5,
        job_details_provider: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Main recommendation method.
        
        Args:
            resume_embedding: Resume embedding vector
            interview_summary_embedding: Interview summary embedding (optional)
            candidate_summary: Text summary of candidate
            top_k: Number of recommendations to return
            job_details_provider: Function to get job details by ID (job_id -> job_dict)
            
        Returns:
            List of recommended jobs with scores and rationales
        """
        self.logger.info("Generating job recommendations")
        
        # Build candidate profile
        profile = self.build_candidate_profile(
            resume_embedding=resume_embedding,
            interview_summary_embedding=interview_summary_embedding
        )
        
        # Find similar jobs
        similar_jobs = self.find_similar_jobs(profile, top_k=20)
        
        if not similar_jobs:
            self.logger.warning("No similar jobs found")
            return []
        
        # Get job details
        if job_details_provider:
            job_details = []
            for job_match in similar_jobs:
                job_id = job_match.get("id")
                # Extract job_id from vector_id if needed
                if job_id and job_id.startswith("job_"):
                    try:
                        job_id_int = int(job_id.split("_")[-1])
                        job_detail = job_details_provider(job_id_int)
                        if job_detail:
                            job_details.append(job_detail)
                    except:
                        pass
        else:
            # Use metadata from vector DB
            job_details = [job_match.get("metadata", {}) for job_match in similar_jobs]
        
        # Re-rank
        re_ranked = self.re_rank_jobs(
            candidate_summary=candidate_summary,
            candidate_jobs=similar_jobs,
            job_details=job_details
        )
        
        # Return top k
        return re_ranked[:top_k]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method.
        
        Expected input:
        {
            "resume_embedding": list,
            "interview_summary_embedding": list (optional),
            "candidate_summary": str,
            "top_k": int,
            "job_details_provider": callable (optional)
        }
        """
        if not self.validate_input(input_data, ["resume_embedding"]):
            raise ValueError("Missing required field: resume_embedding")
        
        recommendations = self.recommend_jobs(
            resume_embedding=input_data["resume_embedding"],
            interview_summary_embedding=input_data.get("interview_summary_embedding"),
            candidate_summary=input_data.get("candidate_summary", ""),
            top_k=input_data.get("top_k", 5),
            job_details_provider=input_data.get("job_details_provider")
        )
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations)
        }

