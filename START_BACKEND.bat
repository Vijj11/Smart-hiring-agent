@echo off
echo Starting Backend Server...
echo.
call venv\Scripts\activate.bat
uvicorn backend.app:app --reload --port 8000
pause

