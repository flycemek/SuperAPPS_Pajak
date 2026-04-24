@echo off
REM Start Service Script (setelah install)

echo Starting OCR Microservice...
echo.

call venv\Scripts\activate.bat

echo ====================================
echo Service berjalan di:
echo http://127.0.0.1:8000
echo.
echo API Documentation:
echo http://127.0.0.1:8000/docs
echo ====================================
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
