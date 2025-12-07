@echo off
echo.
echo ========================================================
echo       eBook2Audiobook Offline Model Downloader
echo ========================================================
echo.
echo This script will download Argos Translate models (approx. 5-6 GB total)
echo to the 'argos_cache' directory. These models will be automatically
echo detected and installed by the Docker container if present.
echo.
echo checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH. 
    echo Please install Python to run this downloader, or use the online mode.
    pause
    exit /b 1
)

echo Python found. Starting download script...
echo.
python tools/download_models.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download script failed.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo       Download Complete!
echo ========================================================
echo.
echo You can now run 'setup.bat' (assuming it maps the volume) 
echo or 'docker compose up' to start the application.
echo.
pause
