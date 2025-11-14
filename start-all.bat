@echo off
echo EUCLOUD - Personal Cloud Storage
echo ================================
echo.
echo This will start both the backend and frontend servers.
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to continue...
pause > nul

REM Start backend in new window
start "EUCLOUD Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in new window
start "EUCLOUD Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting...
echo Check the new command windows for output.
echo.
pause
