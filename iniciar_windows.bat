@echo off
cd /d "%~dp0"
where ffmpeg >nul 2>nul
if errorlevel 1 (
 echo FFmpeg nao encontrado. Instale FFmpeg e adicione ao PATH.
 pause
 exit /b 1
)
if not exist .venv (py -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt
start "" http://127.0.0.1:8765
python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8765
pause
