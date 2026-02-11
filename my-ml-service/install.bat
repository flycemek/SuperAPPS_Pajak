@echo off
REM Manual Installation Script
REM Jika start.bat tidak bekerja, gunakan script ini step by step

set PYTHON_PATH=C:\laragon\bin\python\python-3.13\python.exe

echo ====================================
echo OCR Microservice - Manual Setup
echo ====================================
echo.

echo Step 1: Create virtual environment
%PYTHON_PATH% -m venv venv

echo.
echo Step 2: Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo Step 3: Upgrade pip
python -m pip install --upgrade pip

echo.
echo Step 4: Install dependencies (this will take time)
pip install -r requirements.txt

echo.
echo ====================================
echo Installation complete!
echo ====================================
echo.
echo To run the service, use:
echo   start-service.bat
echo.
echo Or manually:
echo   venv\Scripts\activate.bat
echo   uvicorn app.main:app --reload
echo.
pause
