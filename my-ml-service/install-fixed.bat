@echo off
REM Fixed Installation Script untuk Windows
REM Mengatasi masalah Pillow build error

echo ====================================
echo OCR Microservice - Fixed Install
echo Fixing Pillow Build Error
echo ====================================
echo.

set PYTHON_PATH=C:\laragon\bin\python\python-3.13\python.exe

echo [1/6] Checking Python...
%PYTHON_PATH% --version
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    pause
    exit /b 1
)

echo.
echo [2/6] Creating virtual environment...
if exist "venv" (
    echo Removing old venv...
    rmdir /s /q venv
)
%PYTHON_PATH% -m venv venv
echo Virtual environment created!

echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/6] Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel

echo.
echo [5/6] Installing dependencies in correct order...
echo This may take 5-10 minutes, please wait...
echo.

REM Install base packages first
echo Installing base packages...
pip install fastapi uvicorn[standard] python-multipart pydantic pydantic-settings python-dotenv

REM Install image processing (with pre-built wheels)
echo Installing image processing libraries...
pip install --upgrade Pillow numpy opencv-python-headless

REM Install PyTorch (CPU version, lebih kecil)
echo Installing PyTorch (CPU version)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

REM Install EasyOCR last
echo Installing EasyOCR...
pip install easyocr

echo.
echo [6/6] Verifying installation...
python -c "import fastapi; import easyocr; import PIL; print('All packages installed successfully!')"

if errorlevel 1 (
    echo.
    echo WARNING: Some packages may not be installed correctly.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo To start the service, run:
echo   start-service.bat
echo.
echo Or manually:
echo   venv\Scripts\activate.bat
echo   uvicorn app.main:app --reload
echo.
pause
