@echo off
echo Starting EUCLOUD Backend...
cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask\" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

REM Run Flask app
echo Starting Flask server on http://localhost:5000
python app.py
