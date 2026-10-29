@echo off
echo ========================================================
echo   Starting MailGuard FastAPI Backend on http://localhost:8000
echo ========================================================
cd /d "%~dp0"
"D:\MLOps\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
