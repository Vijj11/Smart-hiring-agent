@echo off
echo Starting Frontend (Streamlit)...
echo.
call venv\Scripts\activate.bat
streamlit run frontend/app.py --server.port 8501
pause

