# Installation Guide - Windows

## Quick Install (Without Build Tools)

The core system works without `chromadb` and `tiktoken`, but some features will be limited.

### Step 1: Install Core Dependencies

```cmd
pip install -r requirements.txt
```

This will install most packages. If `chromadb` or `tiktoken` fail, that's OK - continue to Step 2.

### Step 2: Verify Core Installation

```cmd
python -c "import fastapi, sqlalchemy, streamlit; print('Core packages OK!')"
```

### Step 3: Run Setup

```cmd
python setup.py
python -m utils.load_sample_jobs
```

### Step 4: Start Application

**Terminal 1:**
```cmd
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2:**
```cmd
streamlit run frontend/app.py --server.port 8501
```

## Optional: Install Build Tools (For Full Features)

To enable **job recommendations** and **vector search**, you need:

### Option A: Install Microsoft C++ Build Tools (Recommended)

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++" workload
3. Restart command prompt
4. Run: `pip install chromadb`

### Option B: Use Pinecone Instead (Cloud Vector DB)

1. Sign up at: https://www.pinecone.io/
2. Get API key
3. Set in `.env`: `VECTOR_DB=pinecone` and `PINECONE_API_KEY=your_key`
4. Run: `pip install pinecone-client`

### Option C: Skip Vector DB (Basic Mode)

The system will work for:
- ✅ Resume parsing
- ✅ Resume scoring
- ✅ Mock interviews
- ❌ Job recommendations (requires vector DB)

## Troubleshooting

### "Cannot import chromadb"
- This is OK if you're using Pinecone or skipping vector features
- The system will log warnings but continue working

### "Cannot import tiktoken"
- This is OK - tiktoken is only used for token counting
- OpenAI API works without it

### Port Already in Use
- Change backend port: `--port 8001`
- Change frontend port: `--server.port 8502`

## What Works Without Build Tools

✅ Resume upload and parsing
✅ Resume scoring against job descriptions  
✅ Mock interview (question generation & answer scoring)
✅ All database operations
✅ API endpoints
✅ Frontend UI

❌ Job recommendations (needs vector DB)
❌ Advanced vector similarity search

