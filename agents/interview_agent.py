"""
Interview Agent: Generates interview questions and scores answers.
"""

import logging
from typing import Dict, Any, List, Optional
import json

from agents.agent_base import AgentBase
from utils.llm_client import get_llm_client
from utils.prompts import (
    format_question_generation_prompt,
    format_answer_scoring_prompt,
    format_interview_summary_prompt
)

logger = logging.getLogger(__name__)


class InterviewAgent(AgentBase):
    """Agent for interview question generation and answer scoring."""
    
    def __init__(self):
        super().__init__("InterviewAgent")
        self.llm_client = get_llm_client()
    
    def generate_questions(
        self,
        n_questions: int,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        resume_highlights: str
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions for a role.
        
        Args:
            n_questions: Number of questions to generate
            job_title: Job title
            job_description: Full job description
            required_skills: List of required skills
            resume_highlights: Key highlights from candidate resume
            
        Returns:
            List of question dictionaries
        """
        self.logger.info(f"Generating {n_questions} interview questions")
        
        # Ensure required_skills is always a list
        if required_skills is None:
            required_skills = []
        if not isinstance(required_skills, list):
            required_skills = []
        
        # Format prompt
        prompt = format_question_generation_prompt(
            n_questions=n_questions,
            job_title=job_title,
            job_description=job_description,
            required_skills=", ".join(required_skills) if required_skills else "Not specified",
            resume_highlights=resume_highlights
        )
        
        # Check if API key is available - use fallback if not
        if not self.llm_client.api_key:
            self.logger.warning("OpenAI API key not found. Using fallback questions.")
            return self._generate_fallback_questions(
                n_questions=n_questions,
                job_title=job_title,
                required_skills=required_skills
            )
        
        # Generate questions using LLM with higher temperature for randomness
        try:
            # Use higher temperature (0.9) for more creative/random questions
            questions = self.llm_client.complete_json(
                prompt,
                temperature=0.9,  # Higher temperature for more randomness
                max_tokens=2000
            )
            
            # Ensure it's a list
            if isinstance(questions, dict) and "questions" in questions:
                questions = questions["questions"]
            
            # Validate format
            if not isinstance(questions, list):
                raise ValueError("LLM returned invalid format. Expected a list of questions.")
            
            # Ensure we have enough questions
            if len(questions) < n_questions:
                self.logger.warning(f"LLM generated {len(questions)} questions, requested {n_questions}")
            
            # Ensure all questions have required fields
            for i, q in enumerate(questions):
                if "id" not in q:
                    q["id"] = f"q{i+1}"
                if "question" not in q:
                    raise ValueError(f"Question {i} missing 'question' field")
                # Ensure question field exists
                if not q.get("question"):
                    raise ValueError(f"Question {i} has empty 'question' field")
            
            # Return requested number of questions
            questions = questions[:n_questions]
            self.logger.info(f"Generated {len(questions)} unique questions using OpenAI API")
            return questions
        
        except ValueError as e:
            # Re-raise ValueError if it's a validation error
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate questions with OpenAI API: {e}")
            self.logger.warning("Falling back to default questions due to API error.")
            # Use fallback instead of raising error
            return self._generate_fallback_questions(
                n_questions=n_questions,
                job_title=job_title,
                required_skills=required_skills
            )
    
    def _generate_fallback_questions(
        self,
        n_questions: int,
        job_title: str,
        required_skills: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate fallback questions when LLM is unavailable."""
        base_questions = [
            {
                "id": "q1",
                "question": f"Tell me about your experience with {required_skills[0] if required_skills else 'the technologies'} mentioned in the job description.",
                "difficulty": "medium",
                "category": "technical"
            },
            {
                "id": "q2",
                "question": "Describe a challenging project you worked on and how you solved it.",
                "difficulty": "medium",
                "category": "problem-solving"
            },
            {
                "id": "q3",
                "question": "How do you stay updated with industry trends and new technologies?",
                "difficulty": "easy",
                "category": "behavioral"
            },
            {
                "id": "q4",
                "question": "Explain a time when you had to learn a new technology or framework quickly.",
                "difficulty": "medium",
                "category": "behavioral"
            },
            {
                "id": "q5",
                "question": "What is your approach to debugging complex issues in production?",
                "difficulty": "hard",
                "category": "technical"
            }
        ]
        
        # Return requested number of questions (repeat if needed)
        questions = []
        for i in range(n_questions):
            base_q = base_questions[i % len(base_questions)].copy()
            base_q["id"] = f"q{i+1}"
            questions.append(base_q)
        
        self.logger.info(f"Generated {len(questions)} fallback questions")
        return questions
    
    def score_answer(
        self,
        question: str,
        answer: str,
        expected_focus: str = ""
    ) -> Dict[str, Any]:
        """
        Score an interview answer.
        
        Args:
            question: Interview question
            answer: Candidate's answer
            expected_focus: Expected focus areas (optional)
            
        Returns:
            Score, feedback, and tags
        """
        self.logger.info("Scoring interview answer")
        
        # Format prompt
        prompt = format_answer_scoring_prompt(
            question=question,
            answer=answer,
            expected_focus=expected_focus
        )
        
        # Score using LLM
        try:
            result = self.llm_client.complete_json(prompt)
            
            # Validate result
            if "score" not in result:
                result["score"] = 70.0
            if "feedback" not in result:
                result["feedback"] = "Answer received. Consider providing more specific examples."
            if "tags" not in result:
                result["tags"] = []
            
            # Ensure score is in valid range
            result["score"] = max(0, min(100, float(result["score"])))
            
            self.logger.info(f"Answer scored: {result['score']}/100")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to score answer: {e}")
            # Fallback scoring
            return self._fallback_score_answer(question, answer)
    
    def _fallback_score_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Fallback scoring using keyword matching."""
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Extract keywords from question
        question_keywords = [w for w in question_lower.split() if len(w) > 4]
        
        # Check if answer addresses question keywords
        matches = sum(1 for kw in question_keywords if kw in answer_lower)
        score = min(100, 50 + (matches * 10))
        
        feedback = "Answer addresses the question. Consider providing more specific examples and technical details."
        if len(answer) < 50:
            feedback = "Answer is too brief. Please provide more detail and examples."
            score = max(0, score - 20)
        
        tags = []
        if len(answer) > 200:
            tags.append("detailed")
        if any(kw in answer_lower for kw in ["example", "instance", "project", "experience"]):
            tags.append("has_examples")
        else:
            tags.append("needs_examples")
        
        return {
            "score": float(score),
            "feedback": feedback,
            "tags": tags
        }
    
    def generate_summary(
        self,
        questions_and_answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate interview session summary.
        
        Args:
            questions_and_answers: List of {question, answer, score, feedback}
            
        Returns:
            Summary with avg_score, summary text, strengths, weaknesses
        """
        self.logger.info("Generating interview summary")
        
        # Format Q&A pairs
        qa_text = ""
        scores = []
        for qa in questions_and_answers:
            qa_text += f"Q: {qa.get('question', '')}\n"
            qa_text += f"A: {qa.get('answer', '')}\n"
            qa_text += f"Score: {qa.get('score', 0)}\n"
            qa_text += f"Feedback: {qa.get('feedback', '')}\n\n"
            if qa.get('score'):
                scores.append(float(qa['score']))
        
        # Generate summary using LLM
        prompt = format_interview_summary_prompt(qa_text)
        
        try:
            summary = self.llm_client.complete_json(prompt)
            
            # Calculate average if not provided
            if "avg_score" not in summary and scores:
                summary["avg_score"] = sum(scores) / len(scores)
            
            # Ensure required fields
            if "summary" not in summary:
                summary["summary"] = "Interview completed. Review individual answers for details."
            if "strengths" not in summary:
                summary["strengths"] = []
            if "weaknesses" not in summary:
                summary["weaknesses"] = []
            
            self.logger.info(f"Summary generated: avg_score={summary.get('avg_score', 0)}")
            return summary
        
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            # Fallback summary
            avg_score = sum(scores) / len(scores) if scores else 70.0
            return {
                "avg_score": round(avg_score, 2),
                "summary": "Interview completed. The candidate demonstrated knowledge in the areas discussed.",
                "strengths": ["Technical knowledge", "Communication"],
                "weaknesses": ["Could provide more examples", "Needs more detail"]
            }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method.
        
        Expected input:
        {
            "action": "generate_questions" | "score_answer" | "generate_summary",
            ... (action-specific fields)
        }
        """
        action = input_data.get("action")
        
        if action == "generate_questions":
            # Ensure required_skills is always a list
            required_skills = input_data.get("required_skills", [])
            if required_skills is None or not isinstance(required_skills, list):
                required_skills = []
            
            return {
                "questions": self.generate_questions(
                    n_questions=input_data["n_questions"],
                    job_title=input_data["job_title"],
                    job_description=input_data["job_description"],
                    required_skills=required_skills,
                    resume_highlights=input_data.get("resume_highlights", "")
                )
            }
        
        elif action == "score_answer":
            return self.score_answer(
                question=input_data["question"],
                answer=input_data["answer"],
                expected_focus=input_data.get("expected_focus", "")
            )
        
        elif action == "generate_summary":
            return self.generate_summary(
                questions_and_answers=input_data["questions_and_answers"]
            )
        
        else:
            raise ValueError(f"Unknown action: {action}")

