@echo off
echo 🚀 Starting UnityBot...

REM Optional: activate virtual environment (if exists)
IF EXIST venv (
    call venv\Scripts\activate
)

REM Install dependencies
pip install -r requirements.txt

REM Start the bot
python UnityBot.py

pause
