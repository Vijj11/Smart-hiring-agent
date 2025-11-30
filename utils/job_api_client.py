"""
Job API Client: Fetches jobs from external job APIs dynamically.

Supports multiple job APIs:
- Adzuna API (adzuna.com)
- Jobs API (jobs.github.com)
- SerpAPI for Google Jobs search (requires API key)
- RapidAPI Job Search (requires API key)
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class JobAPIClient:
    """Client for fetching jobs from external APIs."""
    
    def __init__(self):
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        
    def fetch_jobs_from_apis(
        self,
        keywords: List[str] = None,
        location: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs from available APIs.
        
        Args:
            keywords: List of keywords/skills to search for
            location: Location for job search
            limit: Maximum number of jobs to fetch
            
        Returns:
            List of job dictionaries
        """
        all_jobs = []
        has_api_keys = False
        
        # Check if any API keys are configured
        if self.adzuna_app_id and self.adzuna_app_key:
            has_api_keys = True
            # Try Adzuna API first (free tier available)
            try:
                adzuna_jobs = self.fetch_from_adzuna(keywords, location, limit)
                if adzuna_jobs:
                    all_jobs.extend(adzuna_jobs)
                    logger.info(f"Fetched {len(adzuna_jobs)} jobs from Adzuna")
            except Exception as e:
                logger.warning(f"Failed to fetch from Adzuna: {e}", exc_info=True)
        
        if self.serpapi_key:
            has_api_keys = True
            # Try SerpAPI (Google Jobs search)
            try:
                github_jobs = self.fetch_from_github_jobs(keywords, location, limit // 2)
                if github_jobs:
                    all_jobs.extend(github_jobs)
                    logger.info(f"Fetched {len(github_jobs)} jobs from Google Jobs via SerpAPI")
            except Exception as e:
                logger.warning(f"Failed to fetch from SerpAPI: {e}", exc_info=True)
        
        if not has_api_keys:
            logger.warning(
                "No job API keys configured. To enable dynamic job fetching, "
                "add API keys to .env file. See QUICK_API_SETUP.md for instructions."
            )
        
        # Remove duplicates based on title + company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.get("title", "").lower(), job.get("company", "").lower())
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"Fetched {len(unique_jobs)} unique jobs from APIs")
        return unique_jobs[:limit]
    
    def fetch_from_adzuna(
        self,
        keywords: List[str] = None,
        location: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs from Adzuna API.
        
        Adzuna provides free API access with registration:
        https://developer.adzuna.com/
        """
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.debug("Adzuna API credentials not configured")
            return []
        
        try:
            # Default to US jobs (country code 'us')
            country = "us"
            
            # Build query
            query = " ".join(keywords) if keywords else "software developer"
            
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            params = {
                "app_id": self.adzuna_app_id,
                "app_key": self.adzuna_app_key,
                "results_per_page": min(limit, 50),
                "what": query,
                "content-type": "application/json"
            }
            
            if location:
                params["where"] = location
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get("results", [])[:limit]:
                jobs.append({
                    "title": result.get("title", ""),
                    "company": result.get("company", {}).get("display_name", "Unknown Company"),
                    "location": result.get("location", {}).get("display_name", ""),
                    "description": result.get("description", ""),
                    "application_url": result.get("redirect_url", ""),
                    "required_skills": self._extract_skills_from_text(result.get("description", "")),
                    "seniority_level": self._infer_seniority(result.get("title", "")),
                    "posted_date": result.get("created", ""),
                    "source": "adzuna",
                    "external_id": str(result.get("id", ""))
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching from Adzuna: {e}")
            return []
    
    def fetch_from_github_jobs(
        self,
        keywords: List[str] = None,
        location: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs using SerpAPI to search for tech jobs.
        
        Note: If SerpAPI key is not available, this will return empty list.
        You can get a free SerpAPI key at https://serpapi.com/
        """
        try:
            if not self.serpapi_key:
                logger.debug("SerpAPI key not configured, skipping GitHub Jobs search")
                return []
            
            # Build search query
            query_parts = []
            if keywords:
                query_parts.extend(keywords[:3])  # Limit keywords
            
            query = " ".join(query_parts) if query_parts else "software developer jobs"
            if location:
                query += f" in {location}"
            else:
                query += " remote"
            
            # Use SerpAPI to search for jobs
            jobs = self._fetch_via_serpapi("", query_parts, location, limit)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching jobs via SerpAPI: {e}")
            return []
    
    def _fetch_via_serpapi(
        self,
        site: str,
        keywords: List[str],
        location: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch jobs via SerpAPI (Google Jobs search)."""
        if not self.serpapi_key:
            return []
        
        try:
            query = " ".join(keywords) if keywords else "software developer jobs"
            if location:
                query += f" in {location}"
            elif not location:
                query += " remote"
            
            url = "https://serpapi.com/search"
            params = {
                "engine": "google_jobs",
                "q": query,
                "api_key": self.serpapi_key,
                "num": min(limit, 20)
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for result in data.get("jobs_results", [])[:limit]:
                apply_options = result.get("apply_options", [])
                application_url = ""
                if apply_options and len(apply_options) > 0:
                    application_url = apply_options[0].get("link", "")
                
                jobs.append({
                    "title": result.get("title", ""),
                    "company": result.get("company_name", "Unknown Company"),
                    "location": result.get("location", ""),
                    "description": result.get("description", ""),
                    "application_url": application_url,
                    "required_skills": self._extract_skills_from_text(result.get("description", "")),
                    "seniority_level": self._infer_seniority(result.get("title", "")),
                    "posted_date": result.get("detected_extensions", {}).get("posted_at", ""),
                    "source": "google_jobs",
                    "external_id": result.get("job_id", "")
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching via SerpAPI: {e}")
            return []
    
    def fetch_jobs_by_skills(
        self,
        skills: List[str],
        location: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs based on candidate skills.
        
        Args:
            skills: List of skills from resume
            location: Preferred location
            limit: Number of jobs to fetch
            
        Returns:
            List of job dictionaries
        """
        # Use top 5 skills for search
        keywords = skills[:5] if skills else ["software developer"]
        
        return self.fetch_jobs_from_apis(
            keywords=keywords,
            location=location,
            limit=limit
        )
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skills/keywords from job description."""
        if not text:
            return []
        
        # Common tech skills to look for
        common_skills = [
            "python", "javascript", "java", "react", "node.js", "aws", "docker",
            "kubernetes", "sql", "mongodb", "postgresql", "git", "typescript",
            "angular", "vue", "django", "flask", "spring", "tensorflow", "pytorch",
            "machine learning", "ai", "data science", "devops", "ci/cd",
            "microservices", "rest api", "graphql", "agile", "scrum"
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill.title())
        
        return found_skills[:10]  # Return top 10
    
    def _infer_seniority(self, title: str) -> Optional[str]:
        """Infer seniority level from job title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["senior", "sr.", "lead", "principal", "staff"]):
            return "senior"
        elif any(word in title_lower for word in ["junior", "jr.", "entry", "intern", "graduate"]):
            return "entry"
        elif any(word in title_lower for word in ["mid", "mid-level", "ii", "2"]):
            return "mid"
        elif any(word in title_lower for word in ["executive", "vp", "director", "cto", "ceo"]):
            return "executive"
        else:
            return "mid"  # Default
    
    def normalize_job_for_storage(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data for storage in database."""
        return {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location"),
            "description": job.get("description", ""),
            "required_skills": job.get("required_skills", []),
            "seniority_level": job.get("seniority_level"),
            "application_url": job.get("application_url"),
            "source": job.get("source", "external_api"),
            "external_id": job.get("external_id")
        }

