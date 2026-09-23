@echo off
setlocal
python --version
if errorlevel 1 (
  echo Python is not installed or is not in PATH.
  pause
  exit /b 1
)
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pause
