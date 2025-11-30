"""
API route registration.
"""

from fastapi import APIRouter

from backend.api.v1 import resume, interview, jobs

api_router = APIRouter()

# Register v1 routes
api_router.include_router(resume.router, prefix="/v1")
api_router.include_router(interview.router, prefix="/v1")
api_router.include_router(jobs.router, prefix="/v1")

