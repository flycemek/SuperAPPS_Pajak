@echo off
REM Quick Start Script untuk OCR Microservice
REM Menggunakan Python dari Laragon

echo ====================================
echo OCR Microservice - Quick Start
echo DISKOMINFOTIK Bengkulu
echo ====================================
echo.

REM Set Python dari Laragon
set PYTHON_PATH=C:\laragon\bin\python\python-3.13\python.exe
set SCRIPTS_PATH=C:\laragon\bin\python\python-3.13\Scripts

echo [1/5] Checking Python...
%PYTHON_PATH% --version
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    pause
    exit /b 1
)

echo.
echo [2/5] Creating virtual environment...
if not exist "venv" (
    %PYTHON_PATH% -m venv venv
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/5] Installing dependencies...
echo This may take several minutes...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [5/5] Starting OCR Service...
echo.
echo ====================================
echo Service akan berjalan di:
echo http://127.0.0.1:8000
echo Swagger UI: http://127.0.0.1:8000/docs
echo ====================================
echo.
echo Press Ctrl+C to stop the service
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
