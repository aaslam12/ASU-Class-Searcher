@echo off
REM Quick start script for ASU Class Searcher Bot (Windows)

echo ================================
echo ASU Class Searcher Bot
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if token file exists
if not exist "Discord_Bot\token_disc.py" (
    echo [ERROR] Bot token file not found
    echo Please create Discord_Bot\token_disc.py with your Discord bot token:
    echo   echo TOKEN = 'your-token-here' ^> Discord_Bot\token_disc.py
    pause
    exit /b 1
)

echo [OK] Virtual environment found
echo [OK] Bot token configured
echo.
echo Starting bot...
echo.

call venv\Scripts\activate.bat
cd Discord_Bot
python main.py

REM Deactivate on exit
call deactivate
