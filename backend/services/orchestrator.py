"""
Orchestrator service for routing requests to appropriate agents.
"""

import logging
from typing import Dict, Any, Optional, List

from agents.resume_agent import ResumeAgent
from agents.interview_agent import InterviewAgent
from agents.job_reco_agent import JobRecAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates multi-agent workflows."""
    
    def __init__(self):
        self.resume_agent = ResumeAgent()
        self.interview_agent = InterviewAgent()
        self.job_reco_agent = JobRecAgent()
        logger.info("Orchestrator initialized")
    
    def process_resume_upload(
        self,
        file_path: str,
        job_description: Optional[Dict[str, Any]] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrate resume upload workflow: parse → embed → score.
        
        Args:
            file_path: Path to resume file
            job_description: Optional job description for scoring
            use_llm: Whether to use LLM for parsing
            
        Returns:
            Parsed data, embedding, score, and vector_id
        """
        logger.info(f"Orchestrating resume upload: {file_path}")
        
        result = self.resume_agent.process({
            "file_path": file_path,
            "job_description": job_description,
            "use_llm": use_llm
        })
        
        return result
    
    def start_interview(
        self,
        resume_id: int,
        role_id: int,
        n_questions: int = 5,
        resume_data: Optional[Dict[str, Any]] = None,
        job_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate interview start: generate questions.
        
        Args:
            resume_id: Resume ID
            role_id: Job posting ID
            n_questions: Number of questions
            resume_data: Parsed resume data (optional, will be fetched if not provided)
            job_data: Job posting data (optional, will be fetched if not provided)
            
        Returns:
            Generated questions
        """
        logger.info(f"Orchestrating interview start: resume_id={resume_id}, role_id={role_id}")
        
        # Extract highlights from resume
        resume_highlights = ""
        if resume_data:
            skills = resume_data.get("skills", [])
            if skills is None or not isinstance(skills, list):
                skills = []
            experience = resume_data.get("experience", [])
            if experience is None or not isinstance(experience, list):
                experience = []
            experience = experience[:2]  # Top 2 experiences
            
            if skills:
                resume_highlights = f"Skills: {', '.join(str(s) for s in skills[:10])}\n"
            else:
                resume_highlights = "Skills: Not specified\n"
            
            for exp in experience:
                if exp and isinstance(exp, dict):
                    title = exp.get('title', '')
                    company = exp.get('company', '')
                    if title or company:
                        resume_highlights += f"{title} at {company}\n"
        
        # Ensure required_skills is always a list (handle None case)
        required_skills = []
        if job_data:
            skills = job_data.get("required_skills")
            required_skills = skills if isinstance(skills, list) else []
        
        result = self.interview_agent.process({
            "action": "generate_questions",
            "n_questions": n_questions,
            "job_title": job_data.get("title", "") if job_data else "",
            "job_description": job_data.get("description", "") if job_data else "",
            "required_skills": required_skills,
            "resume_highlights": resume_highlights
        })
        
        return result
    
    def submit_answer(
        self,
        question: str,
        answer: str,
        expected_focus: str = ""
    ) -> Dict[str, Any]:
        """
        Orchestrate answer submission: score answer.
        
        Args:
            question: Interview question
            answer: Candidate's answer
            expected_focus: Expected focus areas
            
        Returns:
            Score, feedback, and tags
        """
        logger.info("Orchestrating answer submission")
        
        result = self.interview_agent.process({
            "action": "score_answer",
            "question": question,
            "answer": answer,
            "expected_focus": expected_focus
        })
        
        return result
    
    def complete_interview(
        self,
        questions_and_answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Orchestrate interview completion: generate summary.
        
        Args:
            questions_and_answers: List of Q&A pairs with scores
            
        Returns:
            Interview summary
        """
        logger.info("Orchestrating interview completion")
        
        result = self.interview_agent.process({
            "action": "generate_summary",
            "questions_and_answers": questions_and_answers
        })
        
        return result
    
    def recommend_jobs(
        self,
        resume_embedding: List[float],
        interview_summary_embedding: Optional[List[float]] = None,
        candidate_summary: str = "",
        top_k: int = 5,
        job_details_provider: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate job recommendations: find similar → re-rank.
        
        Args:
            resume_embedding: Resume embedding vector
            interview_summary_embedding: Interview summary embedding (optional)
            candidate_summary: Text summary of candidate
            top_k: Number of recommendations
            job_details_provider: Function to get job details by ID
            
        Returns:
            Job recommendations with scores and rationales
        """
        logger.info("Orchestrating job recommendations")
        
        result = self.job_reco_agent.process({
            "resume_embedding": resume_embedding,
            "interview_summary_embedding": interview_summary_embedding,
            "candidate_summary": candidate_summary,
            "top_k": top_k,
            "job_details_provider": job_details_provider
        })
        
        return result

