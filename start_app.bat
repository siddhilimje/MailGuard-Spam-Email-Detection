@echo off
echo ========================================================
echo   MailGuard - Spam Email Detection System (MLOps)
echo ========================================================
echo.
echo [1/2] Launching FastAPI Backend on http://localhost:8000...
start "MailGuard Backend" cmd /k "cd /d %~dp0 && D:\MLOps\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Launching React Frontend on http://localhost:5173...
start "MailGuard Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================================
echo   MailGuard is running!
echo   Frontend Web App : http://localhost:5173
echo   Swagger API Docs : http://localhost:8000/docs
echo   Health Check     : http://localhost:8000/health
echo   Model Info       : http://localhost:8000/model/info
echo   Operational Stats: http://localhost:8000/metrics
echo ========================================================
