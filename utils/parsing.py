"""
Resume parsing utilities for PDF, DOCX, and TXT files.

Uses pdfplumber for PDFs, python-docx for DOCX, and plain text reading for TXT.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing parsing libraries
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfplumber not available. PDF parsing will fail.")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX parsing will fail.")


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    if not PDF_AVAILABLE:
        raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
    
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise
    
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text
    """
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx not installed. Install with: pip install python-docx")
    
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {e}")
        raise
    
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from plain text file.
    
    Args:
        file_path: Path to TXT file
        
    Returns:
        File contents
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to read text file: {e}")
        raise


def extract_text(file_path: str) -> str:
    """
    Extract text from resume file (PDF, DOCX, or TXT).
    
    Args:
        file_path: Path to resume file
        
    Returns:
        Extracted text
    """
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def parse_resume_basic(text: str) -> Dict[str, Any]:
    """
    Basic resume parsing using heuristics and regex.
    
    This is a fallback parser that works without LLM. For better results,
    use LLM-based parsing in the ResumeAgent.
    
    Args:
        text: Raw resume text
        
    Returns:
        Parsed resume data dictionary
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    parsed = {
        "name": None,
        "contact": {},
        "emails": [],
        "phones": [],
        "education": [],
        "experience": [],
        "skills": [],
        "certifications": []
    }
    
    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    parsed["emails"] = list(set(emails))
    
    # Phone regex (various formats)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    parsed["phones"] = [p[0] if isinstance(p, tuple) else p for p in phones if p]
    
    # Name detection (first non-empty line that looks like a name)
    for line in lines[:5]:
        if len(line.split()) <= 4 and line[0].isupper() and not '@' in line:
            parsed["name"] = line
            break
    
    # Education keywords
    education_keywords = ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd', 'diploma']
    education_section = False
    current_edu = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detect education section
        if any(keyword in line_lower for keyword in education_keywords) and 'education' in line_lower[:20]:
            education_section = True
            continue
        
        if education_section:
            # Look for degree patterns
            degree_pattern = r'(bachelor|master|phd|doctorate|diploma|degree|b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?)'
            if re.search(degree_pattern, line_lower, re.IGNORECASE):
                if current_edu:
                    parsed["education"].append(current_edu)
                current_edu = {"degree": line}
            
            # Look for institution names (often in caps or after degree)
            if current_edu and not current_edu.get("institution"):
                if line and len(line) > 3:
                    current_edu["institution"] = line
            
            # Year pattern
            year_pattern = r'\b(19|20)\d{2}\b'
            years = re.findall(year_pattern, line)
            if years and current_edu:
                current_edu["years"] = years[0] + years[-1] if len(years) > 1 else years[0]
    
    if current_edu:
        parsed["education"].append(current_edu)
    
    # Experience section
    experience_keywords = ['experience', 'employment', 'work history', 'professional experience']
    experience_section = False
    current_exp = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detect experience section
        if any(keyword in line_lower for keyword in experience_keywords):
            experience_section = True
            continue
        
        if experience_section:
            # Job title patterns (often in caps or bold-like)
            if line and len(line.split()) <= 6 and not line.endswith('.') and not line.endswith(','):
                if current_exp and current_exp.get("title"):
                    parsed["experience"].append(current_exp)
                    current_exp = {}
                current_exp = {"title": line, "bullets": []}
            
            # Company name (often after title)
            if current_exp and not current_exp.get("company") and line:
                if len(line) > 2 and not line.startswith('-') and not line.startswith('•'):
                    current_exp["company"] = line
            
            # Bullet points
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                bullet = line.lstrip('-•*').strip()
                if current_exp:
                    if not current_exp.get("bullets"):
                        current_exp["bullets"] = []
                    current_exp["bullets"].append(bullet)
    
    if current_exp:
        parsed["experience"].append(current_exp)
    
    # Skills section (common skill keywords)
    skills_keywords = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'linux', 'agile', 'scrum', 'machine learning', 'ai',
        'tensorflow', 'pytorch', 'mongodb', 'postgresql', 'redis', 'elasticsearch'
    ]
    
    skills_section = False
    for line in lines:
        line_lower = line.lower()
        if 'skill' in line_lower[:20]:
            skills_section = True
            continue
        
        if skills_section:
            # Extract skills (comma-separated or listed)
            if ',' in line:
                skills = [s.strip() for s in line.split(',')]
                parsed["skills"].extend(skills)
            else:
                # Check for individual skill keywords
                for skill in skills_keywords:
                    if skill in line_lower and skill not in parsed["skills"]:
                        parsed["skills"].append(skill)
    
    # Clean up
    parsed["skills"] = list(set([s.lower() for s in parsed["skills"] if s]))
    
    return parsed


def parse_resume(file_path: str, use_llm: bool = False) -> Dict[str, Any]:
    """
    Parse resume from file path.
    
    Args:
        file_path: Path to resume file
        use_llm: Whether to use LLM for enhanced parsing (default: False)
        
    Returns:
        Parsed resume data dictionary
    """
    # Extract text
    text = extract_text(file_path)
    
    if use_llm:
        # Use LLM-based parsing (implemented in ResumeAgent)
        from utils.llm_client import get_llm_client
        from utils.prompts import format_resume_parsing_prompt
        
        llm = get_llm_client()
        prompt = format_resume_parsing_prompt(text)
        
        try:
            parsed = llm.complete_json(prompt)
            return parsed
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}. Falling back to basic parsing.")
            return parse_resume_basic(text)
    else:
        return parse_resume_basic(text)

