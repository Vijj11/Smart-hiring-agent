"""
Centralized prompt templates for all LLM interactions.

All prompts use placeholders that should be filled before sending to LLM.
"""

# Resume Parsing Post-Processing Prompt
RESUME_PARSING_PROMPT = """
You are a resume parsing assistant. Given raw extracted text from a resume, extract structured information.

Extract the following information:
- Name: Full name of the candidate
- Contact: Phone numbers and addresses
- Emails: All email addresses found
- Education: List of education entries with degree, institution, and years
- Experience: List of work experience with title, company, start/end dates, and key bullet points
- Skills: Technical and professional skills
- Certifications: Professional certifications

Resume Text:
{resume_text}

Return a JSON object with the following structure:
{{
    "name": "string or null",
    "contact": {{"phone": "string", "address": "string"}},
    "emails": ["email1", "email2"],
    "phones": ["phone1", "phone2"],
    "education": [
        {{
            "degree": "string",
            "institution": "string",
            "years": "string",
            "field": "string"
        }}
    ],
    "experience": [
        {{
            "title": "string",
            "company": "string",
            "start": "string",
            "end": "string",
            "bullets": ["bullet1", "bullet2"],
            "duration_years": float
        }}
    ],
    "skills": ["skill1", "skill2"],
    "certifications": ["cert1", "cert2"]
}}

Only return valid JSON, no additional text.
"""

# Interview Question Generation Prompt
INTERVIEW_QUESTION_GENERATION_PROMPT = """
You are an expert technical interviewer. Generate {n_questions} interview questions for a candidate applying for the following role.

Job Title: {job_title}
Job Description: {job_description}
Required Skills: {required_skills}

Candidate Resume Highlights:
{resume_highlights}

Generate {n_questions} UNIQUE and DIVERSE questions that:
1. Test technical knowledge relevant to the role
2. Assess problem-solving abilities
3. Evaluate experience depth
4. Cover different difficulty levels (mix of easy, medium, hard)
5. Are tailored to the candidate's specific resume and the job requirements
6. Vary in style and approach - avoid generic questions

IMPORTANT: Make each question unique and specific. Do NOT use generic or template questions. 
Vary the wording, focus areas, and question types to ensure randomness and diversity.

For each question, provide:
- A clear, specific, and unique question
- Difficulty level (easy, medium, hard)
- Category (technical, behavioral, problem-solving, system-design, etc.)

Return a JSON array of questions:
[
    {{
        "id": "q1",
        "question": "Question text here",
        "difficulty": "medium",
        "category": "technical"
    }},
    ...
]

Only return valid JSON array, no additional text.
"""

# Answer Scoring Prompt
ANSWER_SCORING_PROMPT = """
You are an expert interviewer evaluating a candidate's answer. Score the answer on clarity, depth, correctness, and directness.

Question: {question}
Answer: {answer}
Expected Focus Areas: {expected_focus}

Evaluate the answer on:
1. Clarity (0-25): How clear and well-structured is the answer?
2. Depth (0-25): Does it show deep understanding or just surface knowledge?
3. Correctness (0-25): Is the information accurate and relevant?
4. Directness (0-25): Does it directly address the question?

Provide:
- Overall score (0-100)
- Detailed feedback (2-3 sentences)
- Tags: list of relevant tags like ["clarity", "depth", "correctness", "needs_examples", "too_vague"]

Return JSON:
{{
    "score": 75,
    "feedback": "The answer demonstrates good understanding but could benefit from specific examples...",
    "tags": ["clarity", "depth", "needs_examples"]
}}

Only return valid JSON, no additional text.
"""

# Job Re-ranker Prompt
JOB_RE_RANKER_PROMPT = """
You are a job matching expert. Evaluate how well a candidate profile matches a job posting.

Candidate Profile Summary:
{candidate_summary}

Job Posting:
Title: {job_title}
Company: {job_company}
Description: {job_description}
Required Skills: {required_skills}
Seniority Level: {seniority_level}

Evaluate the match and provide:
1. Match score (0-100)
2. Rationale (2-3 sentences explaining the match)
3. Top matched skills (list of skills that align)

Return JSON:
{{
    "score": 85,
    "rationale": "Strong match due to 5+ years of relevant experience in Python and cloud technologies...",
    "matched_skills": ["Python", "AWS", "Docker", "Kubernetes"]
}}

Only return valid JSON, no additional text.
"""

# Interview Summary Generation Prompt
INTERVIEW_SUMMARY_PROMPT = """
You are summarizing an interview session. Based on the questions and answers, provide a comprehensive summary.

Interview Questions and Answers:
{qa_pairs}

Provide:
1. Average score
2. Overall summary (3-4 sentences)
3. Top 3 strengths
4. Top 3 areas for improvement

Return JSON:
{{
    "avg_score": 72.5,
    "summary": "The candidate demonstrated solid technical knowledge but struggled with system design questions...",
    "strengths": ["Strong Python skills", "Good problem-solving approach", "Clear communication"],
    "weaknesses": ["Limited experience with distributed systems", "Could provide more concrete examples", "Needs improvement in architecture discussions"]
}}

Only return valid JSON, no additional text.
"""


def format_resume_parsing_prompt(resume_text: str) -> str:
    """Format resume parsing prompt with resume text."""
    return RESUME_PARSING_PROMPT.format(resume_text=resume_text)


def format_question_generation_prompt(
    n_questions: int,
    job_title: str,
    job_description: str,
    required_skills: str,
    resume_highlights: str
) -> str:
    """Format interview question generation prompt."""
    return INTERVIEW_QUESTION_GENERATION_PROMPT.format(
        n_questions=n_questions,
        job_title=job_title,
        job_description=job_description,
        required_skills=required_skills,
        resume_highlights=resume_highlights
    )


def format_answer_scoring_prompt(
    question: str,
    answer: str,
    expected_focus: str = ""
) -> str:
    """Format answer scoring prompt."""
    return ANSWER_SCORING_PROMPT.format(
        question=question,
        answer=answer,
        expected_focus=expected_focus or "Technical knowledge and problem-solving"
    )


def format_job_re_ranker_prompt(
    candidate_summary: str,
    job_title: str,
    job_company: str,
    job_description: str,
    required_skills: str,
    seniority_level: str
) -> str:
    """Format job re-ranker prompt."""
    return JOB_RE_RANKER_PROMPT.format(
        candidate_summary=candidate_summary,
        job_title=job_title,
        job_company=job_company,
        job_description=job_description,
        required_skills=required_skills,
        seniority_level=seniority_level or "Not specified"
    )


def format_interview_summary_prompt(qa_pairs: str) -> str:
    """Format interview summary prompt."""
    return INTERVIEW_SUMMARY_PROMPT.format(qa_pairs=qa_pairs)

