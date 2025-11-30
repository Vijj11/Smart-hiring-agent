"""
SQLAlchemy models for Smart Hiring Suite.

Models:
- Candidate: User/candidate information
- Resume: Resume metadata and parsed data
- InterviewSession: Interview session tracking
- InterviewAnswer: Individual question-answer pairs
- JobPosting: Job description and metadata
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Candidate(Base):
    """Candidate/user model."""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="candidate", cascade="all, delete-orphan")


class Resume(Base):
    """Resume model storing metadata and parsed content."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    
    # Parsed data stored as JSON
    parsed_data = Column(JSON, nullable=True)  # {name, contact, education, experience, skills, etc.}
    raw_text = Column(Text, nullable=True)
    
    # Scoring data
    score = Column(Float, nullable=True)  # Overall score 0-100
    score_breakdown = Column(JSON, nullable=True)  # {skill_match, seniority_match, recency, keywords}
    matched_skills = Column(JSON, nullable=True)  # List of matched skills
    evidence_spans = Column(JSON, nullable=True)  # Evidence text spans
    
    # Vector DB reference
    vector_id = Column(String(255), nullable=True, index=True)  # ID in vector DB
    
    # Metadata
    target_jd_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    target_job = relationship("JobPosting", foreign_keys=[target_jd_id])


class InterviewSession(Base):
    """Interview session model."""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    
    # Session state
    status = Column(String(50), default="started")  # started, in_progress, completed
    n_questions = Column(Integer, default=5)
    current_question_index = Column(Integer, default=0)
    
    # Questions stored as JSON: [{id, question, difficulty, category}]
    questions = Column(JSON, nullable=False)
    
    # Results
    avg_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)  # Interview summary
    strengths = Column(JSON, nullable=True)  # List of strengths
    weaknesses = Column(JSON, nullable=True)  # List of weaknesses
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="interview_sessions")
    resume = relationship("Resume")
    role = relationship("JobPosting", foreign_keys=[role_id])
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")


class InterviewAnswer(Base):
    """Individual interview question-answer pair."""
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_id = Column(String(50), nullable=False)  # ID from questions array
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    
    # Scoring
    score = Column(Float, nullable=True)  # 0-100
    feedback = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # [clarity, depth, correctness]
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="answers")


class JobPosting(Base):
    """Job posting/description model."""
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    
    # Job description
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    
    # Structured data
    required_skills = Column(JSON, nullable=True)  # List of skills
    seniority_level = Column(String(50), nullable=True)  # entry, mid, senior, executive
    keywords = Column(JSON, nullable=True)  # Top keywords
    
    # Vector DB reference
    vector_id = Column(String(255), nullable=True, index=True)
    
    # Metadata
    posted_date = Column(DateTime, nullable=True)
    application_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

