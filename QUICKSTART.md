# Quick Start Guide - Windows Command Prompt

Follow these steps in order to run the Smart Hiring Suite:

## Step 1: Verify Python Installation

```powershell
python --version
```

Should show Python 3.9 or higher. If not, install Python from python.org

## Step 2: Create Virtual Environment

```powershell
python -m venv venv
```

## Step 3: Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:
```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt.

## Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

This may take a few minutes. Wait for it to complete.

## Step 5: Run Setup Script

```powershell
python setup.py
```

This creates necessary directories and .env file.

## Step 6: Load Sample Job Postings

```powershell
python -m utils.load_sample_jobs
```

You should see messages about jobs being loaded.

## Step 7: Start Backend Server (Terminal 1)

Keep your virtual environment activated, then run:

```powershell
uvicorn backend.app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal window open!**

## Step 8: Start Frontend (Terminal 2)

Open a NEW PowerShell window, navigate to project directory:

```powershell
cd "C:\Users\vijay\OneDrive\Desktop\AI Agent (Smart Hiring Suite)"
```

Activate virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

Start Streamlit:
```powershell
streamlit run frontend/app.py --server.port 8501
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## Step 9: Access the Application

Open your browser and go to:
```
http://localhost:8501
```

## Testing the Application

1. **Upload Resume**: 
   - Click "Resume Upload" in sidebar
   - Upload one of the sample resumes from `data/sample_resumes/`
   - Select a job to score against (optional)
   - Click "Upload & Analyze"

2. **Start Interview**:
   - Click "Mock Interview" in sidebar
   - Select a role
   - Click "Start Interview"
   - Answer questions one by one

3. **Get Recommendations**:
   - After interview, click "Job Recommendations"
   - Click "Get Recommendations"
   - View matched jobs with scores

## Troubleshooting

### Port Already in Use
If port 8000 or 8501 is busy:
- Backend: Change port in command: `--port 8001`
- Frontend: Change in command: `--server.port 8502`

### Module Not Found Errors
Make sure virtual environment is activated (you see `(venv)` in prompt).

### Database Errors
The database is created automatically on first run. If issues occur, delete `data/smart_hiring.db` and restart.

### OpenAI API Key (Optional)
The system works without API keys using fallback methods. For full LLM features, add your key to `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

## Stopping the Application

1. Press `Ctrl+C` in both terminal windows
2. Deactivate virtual environment: `deactivate` (optional)

## Next Steps

- Add your own job postings via API or database
- Customize prompts in `utils/prompts.py`
- Add more sample resumes to `data/sample_resumes/`
- Review API documentation at `http://localhost:8000/docs`

