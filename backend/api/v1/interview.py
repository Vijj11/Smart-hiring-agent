"""
Interview API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.deps import get_database
from backend.services.interview_service import InterviewService
from utils.schemas import (
    InterviewStartRequest,
    InterviewStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    request: InterviewStartRequest,
    db: Session = Depends(get_database)
):
    """
    Start a new interview session.
    
    - **resume_id**: Resume ID
    - **role_id**: Job posting ID
    - **n_questions**: Number of questions (default: 5)
    """
    try:
        service = InterviewService(db)
        result = service.start_interview(
            resume_id=request.resume_id,
            role_id=request.role_id,
            n_questions=request.n_questions
        )
        
        logger.info(f"Interview session started: session_id={result['session_id']}")
        
        return InterviewStartResponse(
            session_id=result["session_id"],
            questions=result["questions"],
            status=result["status"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/{session_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: int,
    request: AnswerSubmitRequest,
    db: Session = Depends(get_database)
):
    """
    Submit an answer to an interview question.
    
    - **session_id**: Interview session ID
    - **question_id**: Question ID
    - **answer_text**: Answer text
    """
    try:
        service = InterviewService(db)
        result = service.submit_answer(
            session_id=session_id,
            question_id=request.question_id,
            answer_text=request.answer_text
        )
        
        logger.info(f"Answer submitted: answer_id={result['answer_id']}")
        
        return AnswerSubmitResponse(
            answer_id=result["answer_id"],
            score=result["score"],
            is_complete=result["is_complete"],
            next_question=result.get("next_question"),
            session_summary=result.get("session_summary")
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/{session_id}")
async def get_interview_session(
    session_id: int,
    db: Session = Depends(get_database)
):
    """Get interview session details."""
    service = InterviewService(db)
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session not found: {session_id}")
    
    # Get all answers
    from backend.db.models import InterviewAnswer
    answers = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()
    
    return {
        "id": session.id,
        "resume_id": session.resume_id,
        "role_id": session.role_id,
        "status": session.status,
        "questions": session.questions,
        "current_question_index": session.current_question_index,
        "avg_score": session.avg_score,
        "summary": session.summary,
        "strengths": session.strengths,
        "weaknesses": session.weaknesses,
        "answers": [
            {
                "id": ans.id,
                "question_id": ans.question_id,
                "question_text": ans.question_text,
                "answer_text": ans.answer_text,
                "score": ans.score,
                "feedback": ans.feedback,
                "tags": ans.tags
            }
            for ans in answers
        ],
        "created_at": session.created_at,
        "completed_at": session.completed_at
    }

