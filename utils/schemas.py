"""
Pydantic schemas for request/response validation across the application.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# Resume Schemas
class ResumeUploadRequest(BaseModel):
    """Request schema for resume upload."""
    target_jd_id: Optional[int] = None


class EducationItem(BaseModel):
    """Education entry schema."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    years: Optional[str] = None
    field: Optional[str] = None


class ExperienceItem(BaseModel):
    """Work experience entry schema."""
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    bullets: Optional[List[str]] = None
    duration_years: Optional[float] = None


class ParsedResumeData(BaseModel):
    """Parsed resume data structure."""
    name: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    emails: Optional[List[str]] = None
    phones: Optional[List[str]] = None
    education: Optional[List[EducationItem]] = []
    experience: Optional[List[ExperienceItem]] = []
    skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []


class ScoreBreakdown(BaseModel):
    """Resume score breakdown."""
    skill_match: float = Field(ge=0, le=100, description="Skill overlap score")
    seniority_match: float = Field(ge=0, le=100, description="Seniority match score")
    recency: float = Field(ge=0, le=100, description="Experience recency score")
    keywords: float = Field(ge=0, le=100, description="Keyword match score")


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload."""
    resume_id: int
    parsed_data: ParsedResumeData
    score: Optional[float] = Field(None, ge=0, le=100, description="Overall resume score")
    score_breakdown: Optional[ScoreBreakdown] = None
    top_matched_skills: List[str] = []
    evidence_spans: Optional[List[str]] = None


# Interview Schemas
class InterviewStartRequest(BaseModel):
    """Request to start an interview session."""
    resume_id: int
    role_id: int
    n_questions: int = Field(default=5, ge=1, le=10)


class InterviewQuestion(BaseModel):
    """Interview question schema."""
    id: str
    question: str
    difficulty: Optional[str] = None
    category: Optional[str] = None


class InterviewStartResponse(BaseModel):
    """Response for starting interview."""
    session_id: int
    questions: List[InterviewQuestion]
    status: str


class AnswerSubmitRequest(BaseModel):
    """Request to submit an interview answer."""
    question_id: str
    answer_text: str


class AnswerScore(BaseModel):
    """Answer scoring result."""
    score: float = Field(ge=0, le=100)
    feedback: str
    tags: List[str]


class AnswerSubmitResponse(BaseModel):
    """Response for answer submission."""
    answer_id: int
    score: AnswerScore
    is_complete: bool
    next_question: Optional[InterviewQuestion] = None
    session_summary: Optional[Dict[str, Any]] = None


class InterviewSummary(BaseModel):
    """Interview session summary."""
    session_id: int
    avg_score: float
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    completed_at: datetime


# Job Schemas
class JobPostingSchema(BaseModel):
    """Job posting schema."""
    id: int
    title: str
    company: str
    location: Optional[str] = None
    description: str
    required_skills: Optional[List[str]] = None
    seniority_level: Optional[str] = None
    application_url: Optional[str] = None


class JobRecommendation(BaseModel):
    """Job recommendation with match details."""
    job_id: Optional[int] = None  # None for external API jobs
    title: str
    company: str
    location: Optional[str] = None
    score: float = Field(ge=0, le=100, description="Match score")
    rationale: str
    matched_skills: List[str]
    application_url: Optional[str] = None
    source: Optional[str] = None  # "local" or "external_api"
    description: Optional[str] = None  # Full description for external jobs


class JobRecommendationResponse(BaseModel):
    """Response for job recommendations."""
    recommendations: List[JobRecommendation]
    candidate_profile_summary: Optional[str] = None


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    status_code: int

