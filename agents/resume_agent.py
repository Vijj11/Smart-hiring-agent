"""
Resume Agent: Handles resume parsing and scoring against job descriptions.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from agents.agent_base import AgentBase
from utils.parsing import parse_resume, extract_text
from utils.embeddings import get_embedding_provider
from utils.vector_db import get_vector_db
from utils.llm_client import get_llm_client
from utils.prompts import format_resume_parsing_prompt

logger = logging.getLogger(__name__)


class ResumeAgent(AgentBase):
    """Agent for resume parsing and scoring."""
    
    def __init__(self):
        super().__init__("ResumeAgent")
        self.embedding_provider = get_embedding_provider()
        self.vector_db = get_vector_db()
        self.llm_client = get_llm_client()
    
    def parse(self, file_path: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Parse resume from file.
        
        Args:
            file_path: Path to resume file
            use_llm: Whether to use LLM for enhanced parsing
            
        Returns:
            Parsed resume data
        """
        self.logger.info(f"Parsing resume: {file_path}")
        
        try:
            # Extract raw text
            raw_text = extract_text(file_path)
            
            # Parse using LLM if available, else use basic parsing
            if use_llm and self.llm_client.api_key:
                prompt = format_resume_parsing_prompt(raw_text)
                parsed_data = self.llm_client.complete_json(prompt)
            else:
                from utils.parsing import parse_resume_basic
                parsed_data = parse_resume_basic(raw_text)
            
            # Add raw text to parsed data
            parsed_data["raw_text"] = raw_text
            
            self.logger.info(f"Successfully parsed resume: {len(parsed_data.get('skills', []))} skills found")
            return parsed_data
        
        except Exception as e:
            self.logger.error(f"Failed to parse resume: {e}")
            raise
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for resume text.
        
        Args:
            text: Resume text
            
        Returns:
            Embedding vector
        """
        return self.embedding_provider.embed(text)
    
    def score_resume(
        self,
        resume_data: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score resume against job description.
        
        Scoring rubric:
        - Skill overlap: 50%
        - Seniority match: 20%
        - Recency: 15%
        - Keywords: 15%
        
        Args:
            resume_data: Parsed resume data
            job_description: Job description data with required_skills, seniority_level, etc.
            
        Returns:
            Score breakdown and evidence
        """
        self.logger.info("Scoring resume against job description")
        
        # Extract data
        resume_skills = [s.lower() for s in resume_data.get("skills", [])]
        job_skills = [s.lower() for s in job_description.get("required_skills", [])]
        job_seniority = job_description.get("seniority_level", "").lower()
        job_keywords = [k.lower() for k in job_description.get("keywords", [])]
        
        # 1. Skill overlap (50%)
        if job_skills:
            matched_skills = [s for s in resume_skills if any(js in s or s in js for js in job_skills)]
            skill_match = (len(matched_skills) / len(job_skills)) * 100
            skill_match = min(skill_match, 100)
        else:
            skill_match = 50  # Default if no skills specified
            matched_skills = []
        
        # 2. Seniority match (20%)
        seniority_scores = {
            "entry": 1,
            "junior": 1,
            "mid": 2,
            "mid-level": 2,
            "senior": 3,
            "lead": 4,
            "principal": 4,
            "executive": 5
        }
        
        job_seniority_score = seniority_scores.get(job_seniority, 2)
        
        # Estimate candidate seniority from experience
        experience_years = 0
        for exp in resume_data.get("experience", []):
            if exp.get("duration_years"):
                experience_years += exp["duration_years"]
            elif exp.get("start") and exp.get("end"):
                # Try to parse years from dates
                try:
                    start_year = int(exp["start"][-4:]) if len(exp["start"]) >= 4 else 0
                    end_year = int(exp["end"][-4:]) if len(exp["end"]) >= 4 else 2024
                    experience_years += (end_year - start_year)
                except:
                    pass
        
        # Map experience to seniority
        if experience_years >= 7:
            candidate_seniority = 4
        elif experience_years >= 4:
            candidate_seniority = 3
        elif experience_years >= 2:
            candidate_seniority = 2
        else:
            candidate_seniority = 1
        
        # Calculate match
        seniority_diff = abs(job_seniority_score - candidate_seniority)
        seniority_match = max(0, 100 - (seniority_diff * 25))
        
        # 3. Recency (15%) - Check if recent experience is relevant
        recent_experience = resume_data.get("experience", [])[:3]  # Last 3 positions
        relevant_recent = 0
        for exp in recent_experience:
            exp_text = " ".join([exp.get("title", ""), exp.get("company", "")] + exp.get("bullets", [])).lower()
            if any(skill in exp_text for skill in job_skills[:5]):  # Check top 5 skills
                relevant_recent += 1
        
        recency = (relevant_recent / min(3, len(recent_experience))) * 100 if recent_experience else 50
        
        # 4. Keywords (15%)
        resume_text = resume_data.get("raw_text", "").lower()
        matched_keywords = [kw for kw in job_keywords if kw in resume_text]
        keywords_score = (len(matched_keywords) / max(len(job_keywords), 1)) * 100 if job_keywords else 50
        
        # Weighted combination
        overall_score = (
            skill_match * 0.50 +
            seniority_match * 0.20 +
            recency * 0.15 +
            keywords_score * 0.15
        )
        
        # Find evidence spans
        evidence_spans = []
        for exp in resume_data.get("experience", []):
            exp_text = " ".join(exp.get("bullets", []))
            if any(skill in exp_text.lower() for skill in matched_skills[:3]):
                evidence_spans.append(exp_text[:200])  # First 200 chars
        
        result = {
            "score": round(overall_score, 2),
            "breakdown": {
                "skill_match": round(skill_match, 2),
                "seniority_match": round(seniority_match, 2),
                "recency": round(recency, 2),
                "keywords": round(keywords_score, 2)
            },
            "top_matched_skills": matched_skills[:10],
            "evidence_spans": evidence_spans[:5]
        }
        
        self.logger.info(f"Resume scored: {overall_score:.2f}/100")
        return result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method.
        
        Expected input:
        {
            "file_path": str,
            "job_description": dict (optional),
            "use_llm": bool (optional)
        }
        
        Returns:
        {
            "parsed_data": dict,
            "score": float,
            "score_breakdown": dict,
            "embedding": list,
            "vector_id": str
        }
        """
        if not self.validate_input(input_data, ["file_path"]):
            raise ValueError("Missing required field: file_path")
        
        file_path = input_data["file_path"]
        job_description = input_data.get("job_description")
        use_llm = input_data.get("use_llm", True)
        
        # Parse resume
        parsed_data = self.parse(file_path, use_llm=use_llm)
        
        # Generate embedding
        resume_text = parsed_data.get("raw_text", "")
        embedding = self.embed(resume_text)
        
        # Score if job description provided
        score_result = None
        if job_description:
            score_result = self.score_resume(parsed_data, job_description)
        
        # Store in vector DB
        vector_id = f"resume_{Path(file_path).stem}_{os.urandom(4).hex()}"
        metadata = {
            "type": "resume",
            "resume_id": None,  # Will be set after DB insert
            "skills": parsed_data.get("skills", []),
            "name": parsed_data.get("name", "")
        }
        
        self.vector_db.upsert(vector_id, embedding, metadata)
        
        result = {
            "parsed_data": parsed_data,
            "embedding": embedding,
            "vector_id": vector_id
        }
        
        if score_result:
            result.update(score_result)
        
        return result

