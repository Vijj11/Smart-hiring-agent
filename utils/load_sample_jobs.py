"""
Script to load sample job postings into the database.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.session import get_db_session, init_db
from backend.services.job_service import JobService
from backend.db.models import JobPosting

def load_sample_jobs():
    """Load sample jobs from JSON files."""
    # Initialize database
    init_db()
    
    # Get database session
    db = get_db_session()
    service = JobService(db)
    
    # Load jobs from sample_jobs directory
    sample_jobs_dir = Path(__file__).parent.parent / "data" / "sample_jobs"
    
    if not sample_jobs_dir.exists():
        print(f"Sample jobs directory not found: {sample_jobs_dir}")
        return
    
    loaded_count = 0
    skipped_count = 0
    for job_file in sample_jobs_dir.glob("*.json"):
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            # Check if job already exists (by title and company)
            existing = db.query(JobPosting).filter(
                JobPosting.title == job_data.get("title"),
                JobPosting.company == job_data.get("company")
            ).first()
            
            if existing:
                print(f"⏭️  Skipping existing job: {job_data['title']} at {job_data['company']}")
                skipped_count += 1
                continue
            
            # Create job
            job = service.create_job(
                title=job_data["title"],
                company=job_data["company"],
                description=job_data["description"],
                location=job_data.get("location"),
                required_skills=job_data.get("required_skills", []),
                seniority_level=job_data.get("seniority_level"),
                application_url=job_data.get("application_url")
            )
            
            print(f"✅ Loaded job: {job.title} at {job.company} (ID: {job.id})")
            loaded_count += 1
        
        except Exception as e:
            print(f"❌ Error loading {job_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    print(f"\n{'='*50}")
    print(f"✅ Successfully loaded {loaded_count} job postings!")
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} existing jobs")
    print(f"{'='*50}")

if __name__ == "__main__":
    load_sample_jobs()

