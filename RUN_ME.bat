@echo off
echo ========================================
echo Smart Hiring Suite - Setup & Run Script
echo ========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 3: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 4: Running setup...
python setup.py

echo.
echo Step 5: Loading sample jobs...
python -m utils.load_sample_jobs

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Keep this window open
echo 2. Open a NEW command prompt window
echo 3. Navigate to this directory
echo 4. Run: venv\Scripts\activate
echo 5. Run: uvicorn backend.app:app --reload --port 8000
echo.
echo Then open ANOTHER command prompt for frontend:
echo 1. Navigate to this directory
echo 2. Run: venv\Scripts\activate
echo 3. Run: streamlit run frontend/app.py --server.port 8501
echo.
pause

