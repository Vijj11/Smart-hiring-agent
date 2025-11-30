# Smart Hiring Suite

A full-stack MVP implementing a multi-agent system for resume analysis, mock interviews, and job recommendations.

## Architecture

- **Frontend**: Streamlit web app (single-page flow)
- **Backend**: FastAPI (multi-agent orchestration layer, REST)
- **Agents**: ResumeAgent, InterviewAgent, JobRecAgent
- **Persistence**: Vector DB (Chroma/Pinecone) for embeddings; SQLite/Postgres for metadata
- **Embeddings & LLM**: Pluggable providers (default: OpenAI)

## Features

1. **Resume Upload & Analysis**: Upload PDF/DOCX/TXT resumes → parse → score against job descriptions
2. **Mock Interview**: 5-question role-specific interviews with AI-powered scoring and feedback
3. **Job Recommendations**: AI-powered job matching with rationale and skill alignment

## Requirements

- Python 3.9+
- Virtual environment (venv)
- OpenAI API key (optional, for LLM features)
- Pinecone API key (optional, for cloud vector DB)

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Run the setup script to create necessary directories and .env file:

```bash
python setup.py
```

Edit `.env` file with your API keys (optional for local development):
```
OPENAI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENV=your_pinecone_env
VECTOR_DB=chroma
CHROMA_DIR=./chroma
DATABASE_URL=sqlite:///./data/smart_hiring.db
```

**Note**: The system works without OpenAI API keys using fallback methods, but LLM features will be limited.

### 3. Initialize Database

```bash
# Create data directories
mkdir -p data/uploads data/sample_resumes data/sample_jobs

# Run database initialization (will be done automatically on first run)
```

### 4. Load Sample Data

```bash
# Load sample job postings (run from project root)
python -m utils.load_sample_jobs
```

This will load 5 sample job postings into the database for testing.

### 5. Run the Application

**Terminal 1 - Backend (FastAPI):**
```bash
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2 - Frontend (Streamlit):**
```bash
streamlit run frontend/app.py --server.port 8501
```

Access the app at: http://localhost:8501

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:8501
```

## API Endpoints

### Resume Upload
```bash
POST /v1/resume/upload
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/v1/resume/upload" \
  -F "file=@resume.pdf" \
  -F "target_jd_id=1"
```

### Start Interview
```bash
POST /v1/interview/start
Content-Type: application/json

curl -X POST "http://localhost:8000/api/v1/interview/start" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": 1, "role_id": 1, "n_questions": 5}'
```

### Submit Answer
```bash
POST /v1/interview/{session_id}/answer
Content-Type: application/json

curl -X POST "http://localhost:8000/api/v1/interview/1/answer" \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "answer_text": "My answer here..."}'
```

### Get Job Recommendations
```bash
GET /v1/jobs/recommend?resume_id=1&interview_session_id=1&top_k=5

curl "http://localhost:8000/api/v1/jobs/recommend?resume_id=1&interview_session_id=1&top_k=5"
```

## Project Structure

```
.
├── backend/
│   ├── app.py                 # FastAPI main app
│   ├── api/                   # API routes
│   ├── services/              # Business logic services
│   ├── db/                    # Database models and session
│   └── deps.py                # Dependency injection
├── agents/
│   ├── agent_base.py          # Base agent interface
│   ├── resume_agent.py        # Resume parsing and scoring
│   ├── interview_agent.py     # Interview question generation and scoring
│   └── job_reco_agent.py      # Job recommendation engine
├── utils/
│   ├── parsing.py             # Resume parsing utilities
│   ├── embeddings.py          # Embedding provider wrapper
│   ├── vector_db.py           # Vector DB adapter (Chroma/Pinecone)
│   ├── llm_client.py          # LLM client wrapper
│   ├── prompts.py             # Prompt templates
│   └── schemas.py             # Pydantic schemas
├── frontend/
│   ├── app.py                 # Streamlit main app
│   └── components.py          # UI components
├── data/
│   ├── sample_resumes/        # Sample resume files
│   ├── sample_jobs/           # Sample job descriptions
│   └── uploads/               # User uploaded resumes
├── tests/                     # Unit tests
└── requirements.txt           # Python dependencies
```

## Demo Scenarios

### Scenario 1: Strong Candidate
- Upload a well-formatted resume with relevant experience
- Score should be 70-90
- Interview questions will be role-appropriate
- Job recommendations will show high matches

### Scenario 2: Borderline Candidate
- Upload a resume with some relevant skills but limited experience
- Score should be 40-60
- Interview will test depth of knowledge
- Job recommendations will include entry-level positions

### Scenario 3: Weak Candidate
- Upload a resume with minimal relevant experience
- Score should be 20-40
- Interview will focus on basic qualifications
- Job recommendations will suggest skill-building opportunities

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_parsing.py

# Run with coverage
pytest tests/ --cov=backend --cov=agents --cov=utils
```

## Development

### Adding New Agents

1. Inherit from `AgentBase` in `agents/agent_base.py`
2. Implement required methods
3. Register in `backend/services/orchestrator.py`
4. Add corresponding service in `backend/services/`

### Adding New Vector DB Provider

1. Implement adapter in `utils/vector_db.py`
2. Add provider selection logic based on `VECTOR_DB` env var
3. Update `.env.example` with new provider config

## Troubleshooting

### Issue: "No module named 'backend'"
- Ensure you're running from project root
- Activate virtual environment
- Install requirements: `pip install -r requirements.txt`

### Issue: "OpenAI API key not found"
- Check `.env` file exists and contains `OPENAI_API_KEY`
- For local dev without OpenAI, the system will use fallback keyword matching

### Issue: "Vector DB connection failed"
- For Chroma: ensure `CHROMA_DIR` directory is writable
- For Pinecone: verify API key and environment in `.env`

## License

MIT

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Submit a pull request


