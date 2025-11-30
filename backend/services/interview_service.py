"""
Interview service for handling interview-related business logic.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models import InterviewSession, InterviewAnswer, Resume, JobPosting
from backend.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for interview operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = Orchestrator()
    
    def start_interview(
        self,
        resume_id: int,
        role_id: int,
        n_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Start a new interview session.
        
        Args:
            resume_id: Resume ID
            role_id: Job posting ID
            n_questions: Number of questions
            
        Returns:
            Interview session with questions
        """
        logger.info(f"Starting interview: resume_id={resume_id}, role_id={role_id}")
        
        # Get resume and job data
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")
        
        job = self.db.query(JobPosting).filter(JobPosting.id == role_id).first()
        if not job:
            raise ValueError(f"Job posting not found: {role_id}")
        
        # Validate job has required fields
        if not job.title:
            raise ValueError(f"Job posting {role_id} has no title")
        if not job.description:
            raise ValueError(f"Job posting {role_id} has no description")
        
        # Ensure required_skills is a list
        required_skills = job.required_skills
        if required_skills is None or not isinstance(required_skills, list):
            required_skills = []
        
        # Generate questions
        result = self.orchestrator.start_interview(
            resume_id=resume_id,
            role_id=role_id,
            n_questions=n_questions,
            resume_data=resume.parsed_data,  # Can be None, orchestrator handles it
            job_data={
                "title": job.title,
                "description": job.description,
                "required_skills": required_skills
            }
        )
        
        # Create interview session
        session = InterviewSession(
            candidate_id=resume.candidate_id,
            resume_id=resume_id,
            role_id=role_id,
            n_questions=n_questions,
            questions=result["questions"],
            status="started"
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Interview session created: session_id={session.id}")
        
        return {
            "session_id": session.id,
            "questions": result["questions"],
            "status": session.status
        }
    
    def submit_answer(
        self,
        session_id: int,
        question_id: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Submit an answer to an interview question.
        
        Args:
            session_id: Interview session ID
            question_id: Question ID
            answer_text: Answer text
            
        Returns:
            Answer score and feedback
        """
        logger.info(f"Submitting answer: session_id={session_id}, question_id={question_id}")
        
        # Get session
        session = self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Interview session not found: {session_id}")
        
        # Find question
        question = None
        for q in session.questions:
            if q.get("id") == question_id:
                question = q
                break
        
        if not question:
            raise ValueError(f"Question not found: {question_id}")
        
        # Score answer
        result = self.orchestrator.submit_answer(
            question=question.get("question", ""),
            answer=answer_text,
            expected_focus=""
        )
        
        # Create answer record
        answer = InterviewAnswer(
            session_id=session_id,
            question_id=question_id,
            question_text=question.get("question", ""),
            answer_text=answer_text,
            score=result["score"],
            feedback=result["feedback"],
            tags=result["tags"]
        )
        
        self.db.add(answer)
        
        # Update session
        session.current_question_index += 1
        
        # Check if complete
        is_complete = session.current_question_index >= session.n_questions
        
        if is_complete:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            
            # Generate summary
            all_answers = self.db.query(InterviewAnswer).filter(
                InterviewAnswer.session_id == session_id
            ).all()
            
            qa_pairs = []
            for ans in all_answers:
                qa_pairs.append({
                    "question": ans.question_text,
                    "answer": ans.answer_text,
                    "score": ans.score,
                    "feedback": ans.feedback
                })
            
            summary = self.orchestrator.complete_interview(qa_pairs)
            
            session.avg_score = summary["avg_score"]
            session.summary = summary["summary"]
            session.strengths = summary["strengths"]
            session.weaknesses = summary["weaknesses"]
        
        self.db.commit()
        self.db.refresh(session)
        self.db.refresh(answer)
        
        # Get next question if not complete
        next_question = None
        if not is_complete and session.current_question_index < len(session.questions):
            next_question = session.questions[session.current_question_index]
        
        return {
            "answer_id": answer.id,
            "score": {
                "score": result["score"],
                "feedback": result["feedback"],
                "tags": result["tags"]
            },
            "is_complete": is_complete,
            "next_question": next_question,
            "session_summary": {
                "avg_score": session.avg_score,
                "summary": session.summary,
                "strengths": session.strengths,
                "weaknesses": session.weaknesses
            } if is_complete else None
        }
    
    def get_session(self, session_id: int) -> Optional[InterviewSession]:
        """Get interview session by ID."""
        return self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()

