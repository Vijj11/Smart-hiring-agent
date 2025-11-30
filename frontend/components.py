"""
Reusable Streamlit UI components.
"""

import streamlit as st


def render_resume_score(score: float, breakdown: dict = None):
    """Render resume score with breakdown."""
    st.subheader("Resume Score")
    
    # Overall score
    score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
    st.metric("Overall Score", f"{score:.1f}/100", delta=None)
    
    # Progress bar
    st.progress(score / 100)
    
    # Breakdown
    if breakdown:
        st.write("**Score Breakdown:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Skill Match", f"{breakdown.get('skill_match', 0):.1f}%")
            st.metric("Seniority Match", f"{breakdown.get('seniority_match', 0):.1f}%")
        
        with col2:
            st.metric("Recency", f"{breakdown.get('recency', 0):.1f}%")
            st.metric("Keywords", f"{breakdown.get('keywords', 0):.1f}%")


def render_parsed_resume(parsed_data: dict):
    """Render parsed resume data."""
    st.subheader("Parsed Resume Data")
    
    # Basic info
    if parsed_data.get("name"):
        st.write(f"**Name:** {parsed_data['name']}")
    
    if parsed_data.get("emails"):
        st.write(f"**Email:** {', '.join(parsed_data['emails'])}")
    
    if parsed_data.get("phones"):
        st.write(f"**Phone:** {', '.join(parsed_data['phones'])}")
    
    # Skills
    if parsed_data.get("skills"):
        st.write("**Skills:**")
        st.write(", ".join(parsed_data["skills"][:20]))
    
    # Education
    if parsed_data.get("education"):
        st.write("**Education:**")
        for edu in parsed_data["education"][:3]:
            edu_str = f"- {edu.get('degree', 'N/A')}"
            if edu.get("institution"):
                edu_str += f" from {edu['institution']}"
            if edu.get("years"):
                edu_str += f" ({edu['years']})"
            st.write(edu_str)
    
    # Experience
    if parsed_data.get("experience"):
        st.write("**Experience:**")
        for exp in parsed_data["experience"][:3]:
            exp_str = f"**{exp.get('title', 'N/A')}**"
            if exp.get("company"):
                exp_str += f" at {exp['company']}"
            if exp.get("start") and exp.get("end"):
                exp_str += f" ({exp['start']} - {exp['end']})"
            st.write(exp_str)
            
            if exp.get("bullets"):
                for bullet in exp["bullets"][:3]:
                    st.write(f"  • {bullet}")


def render_job_recommendation(job: dict, index: int):
    """Render a single job recommendation."""
    with st.container():
        # Show source badge for external jobs
        source_badge = ""
        if job.get("source") == "external_api":
            source_badge = " 🌐"
        
        st.markdown(f"### {index + 1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}{source_badge}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if job.get("location"):
                st.write(f"📍 {job['location']}")
            
            if job.get("score"):
                score_color = "green" if job["score"] >= 70 else "orange" if job["score"] >= 50 else "red"
                st.metric("Match Score", f"{job['score']:.1f}%")
            
            # Show description for external jobs
            if job.get("description") and job.get("source") == "external_api":
                with st.expander("View Job Description"):
                    st.write(job["description"])
            
            if job.get("rationale"):
                st.write(f"**Why this match:** {job['rationale']}")
            
            if job.get("matched_skills"):
                st.write("**Matched Skills:**")
                st.write(", ".join(job["matched_skills"][:10]))
        
        with col2:
            if job.get("application_url"):
                st.link_button("Apply", job["application_url"])
            elif job.get("source") == "external_api":
                st.info("🔗 Check company website for application")
        
        st.divider()

