"""
Streamlit frontend for Smart Hiring Suite.

Single-page flow:
1. Upload resume → see parsed data & score
2. Start mock interview → answer questions → get feedback
3. View job recommendations
"""

import streamlit as st
import requests
import json
import os
from typing import Optional, Dict, Any

# Page config
st.set_page_config(
    page_title="Smart Hiring Suite",
    page_icon="🎯",
    layout="wide"
)

# Backend URL - Default to localhost, can be overridden via environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize session state
if "resume_id" not in st.session_state:
    st.session_state.resume_id = None
if "interview_session_id" not in st.session_state:
    st.session_state.interview_session_id = None
if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = {}
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "job_recommendations" not in st.session_state:
    st.session_state.job_recommendations = []


def upload_resume(file, target_jd_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Upload resume to backend."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {}
        if target_jd_id:
            data["target_jd_id"] = target_jd_id
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/resume/upload",
            files=files,
            data=data,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to upload resume: {str(e)}")
        return None


def start_interview(resume_id: int, role_id: int, n_questions: int = 5) -> Optional[Dict[str, Any]]:
    """Start interview session."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/interview/start",
            json={
                "resume_id": resume_id,
                "role_id": role_id,
                "n_questions": n_questions
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to start interview: {str(e)}")
        return None


def submit_answer(session_id: int, question_id: str, answer_text: str) -> Optional[Dict[str, Any]]:
    """Submit interview answer."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/interview/{session_id}/answer",
            json={
                "question_id": question_id,
                "answer_text": answer_text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to submit answer: {str(e)}")
        return None


def get_job_recommendations(resume_id: int, interview_session_id: Optional[int] = None, top_k: int = 5) -> Optional[Dict[str, Any]]:
    """Get job recommendations."""
    try:
        params = {"resume_id": resume_id, "top_k": top_k}
        if interview_session_id:
            params["interview_session_id"] = interview_session_id
        
        response = requests.get(
            f"{BACKEND_URL}/api/v1/jobs/recommend",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to get recommendations: {str(e)}")
        return None


def get_jobs() -> list:
    """Get list of available jobs."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/jobs/", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return []


# Main UI
st.title("🎯 Smart Hiring Suite")
st.markdown("Upload your resume, take a mock interview, and get personalized job recommendations!")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Resume Upload", "Mock Interview", "Job Recommendations"]
)

# Resume Upload Section
if page == "Resume Upload" or st.session_state.resume_id is None:
    st.header("📄 Upload Resume")
    
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx", "txt"],
        help="Upload your resume in PDF, DOCX, or TXT format"
    )
    
    # Get available jobs for scoring
    jobs = get_jobs()
    job_options = {f"{job['title']} at {job['company']}": job['id'] for job in jobs[:10]}
    
    selected_job = st.selectbox(
        "Score against job description (optional)",
        ["None"] + list(job_options.keys())
    )
    
    target_jd_id = job_options.get(selected_job) if selected_job != "None" else None
    
    if st.button("Upload & Analyze", type="primary") and uploaded_file:
        with st.spinner("Processing resume..."):
            result = upload_resume(uploaded_file, target_jd_id)
            
            if result:
                st.session_state.resume_id = result["resume_id"]
                st.success("Resume uploaded successfully!")
                
                # Display parsed data
                from components import render_parsed_resume, render_resume_score
                
                render_parsed_resume(result["parsed_data"])
                
                if result.get("score") is not None:
                    render_resume_score(result["score"], result.get("score_breakdown"))
                
                if result.get("top_matched_skills"):
                    st.write("**Top Matched Skills:**")
                    st.write(", ".join(result["top_matched_skills"][:10]))

# Mock Interview Section
if page == "Mock Interview" or (st.session_state.resume_id and not st.session_state.interview_complete):
    st.header("🎤 Mock Interview")
    
    if st.session_state.resume_id is None:
        st.warning("Please upload a resume first!")
        st.stop()
    
    # Start interview if not started
    if st.session_state.interview_session_id is None:
        st.write("Ready to start your mock interview? Select a role and click Start.")
        
        jobs = get_jobs()
        if not jobs:
            st.warning("No jobs available. Please add job postings first.")
            st.stop()
        
        job_options = {f"{job['title']} at {job['company']}": job['id'] for job in jobs}
        selected_role = st.selectbox("Select role for interview", list(job_options.keys()))
        n_questions = st.slider("Number of questions", 3, 10, 5)
        
        if st.button("Start Interview", type="primary"):
            with st.spinner("Generating interview questions..."):
                result = start_interview(
                    resume_id=st.session_state.resume_id,
                    role_id=job_options[selected_role],
                    n_questions=n_questions
                )
                
                if result:
                    st.session_state.interview_session_id = result["session_id"]
                    st.session_state.interview_questions = result["questions"]
                    st.session_state.current_question_index = 0
                    st.session_state.interview_answers = {}
                    st.rerun()
    
    # Interview in progress
    elif not st.session_state.interview_complete and st.session_state.interview_questions:
        current_idx = st.session_state.current_question_index
        
        if current_idx < len(st.session_state.interview_questions):
            question = st.session_state.interview_questions[current_idx]
            
            st.subheader(f"Question {current_idx + 1} of {len(st.session_state.interview_questions)}")
            st.write(f"**{question.get('question', '')}**")
            
            if question.get("difficulty"):
                st.caption(f"Difficulty: {question.get('difficulty', 'N/A')}")
            
            answer = st.text_area("Your answer", height=200, key=f"answer_{current_idx}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Submit Answer", type="primary"):
                    if answer.strip():
                        with st.spinner("Evaluating your answer..."):
                            result = submit_answer(
                                session_id=st.session_state.interview_session_id,
                                question_id=question["id"],
                                answer_text=answer
                            )
                            
                            if result:
                                st.session_state.interview_answers[question["id"]] = {
                                    "answer": answer,
                                    "score": result["score"],
                                    "feedback": result["score"]["feedback"]
                                }
                                
                                # Show feedback
                                st.success(f"Score: {result['score']['score']:.1f}/100")
                                st.info(f"Feedback: {result['score']['feedback']}")
                                
                                if result["is_complete"]:
                                    st.session_state.interview_complete = True
                                    st.session_state.current_question_index = len(st.session_state.interview_questions)
                                    
                                    if result.get("session_summary"):
                                        st.balloons()
                                        st.header("Interview Complete!")
                                        st.write(f"**Average Score:** {result['session_summary']['avg_score']:.1f}/100")
                                        st.write(f"**Summary:** {result['session_summary']['summary']}")
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write("**Strengths:**")
                                            for strength in result['session_summary'].get('strengths', []):
                                                st.write(f"✅ {strength}")
                                        with col2:
                                            st.write("**Areas for Improvement:**")
                                            for weakness in result['session_summary'].get('weaknesses', []):
                                                st.write(f"📝 {weakness}")
                                else:
                                    st.session_state.current_question_index += 1
                                
                                st.rerun()
                    else:
                        st.warning("Please provide an answer before submitting.")
        else:
            st.info("Interview complete! Check the Job Recommendations section.")

# Job Recommendations Section
if page == "Job Recommendations" or st.session_state.interview_complete:
    st.header("💼 Job Recommendations")
    
    if st.session_state.resume_id is None:
        st.warning("Please upload a resume first!")
        st.stop()
    
    if st.button("Get Recommendations", type="primary") or st.session_state.job_recommendations:
        with st.spinner("Finding the best job matches for you..."):
            result = get_job_recommendations(
                resume_id=st.session_state.resume_id,
                interview_session_id=st.session_state.interview_session_id,
                top_k=5
            )
            
            if result and result.get("recommendations") and len(result["recommendations"]) > 0:
                st.session_state.job_recommendations = result["recommendations"]
                st.success(f"Found {len(result['recommendations'])} job recommendations!")
                
                from components import render_job_recommendation
                
                for i, job in enumerate(result["recommendations"]):
                    render_job_recommendation(job, i)
            else:
                st.warning("No job recommendations found.")
                st.info(
                    "💡 **To get job recommendations, you can:**\n\n"
                    "1. **Add local job postings:** Use sample jobs or add via API\n"
                    "2. **Configure external APIs:** See `QUICK_API_SETUP.md` for free API keys\n"
                    "3. **Load sample jobs:** Run `python -m utils.load_sample_jobs`"
                )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Smart Hiring Suite** v1.0")
st.sidebar.markdown("Built with FastAPI & Streamlit")

