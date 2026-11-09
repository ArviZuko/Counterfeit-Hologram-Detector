@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   AI-POWERED HOLOGRAM AUTHENTICITY DETECTION SYSTEM - WINDOWS BUILD SCRIPT
echo ===============================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

echo [1/4] Checking Python environment...
python --version

:: 2. Install / Verify Dependencies
echo.
echo [2/4] Verifying and installing dependencies from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Some dependencies had warnings, continuing...
)

:: 3. Clean Previous Builds
echo.
echo [3/4] Building standalone executable with PyInstaller...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --clean --noconfirm HologramAuthenticity.spec
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b %ERRORLEVEL%
)

if not exist dist\HologramAuthenticity.exe (
    echo [ERROR] Expected output dist\HologramAuthenticity.exe was not created!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Standalone Windows Executable built:
echo    dist\HologramAuthenticity.exe
echo.

:: 4. Build Inno Setup Installer
echo [4/4] Checking for Inno Setup Compiler (ISCC)...
set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    where iscc >nul 2>&1
    if %ERRORLEVEL% equ 0 set "ISCC_PATH=iscc"
)

if not "%ISCC_PATH%"=="" (
    echo Compiling Windows Installer with: "%ISCC_PATH%"...
    if not exist dist\installer mkdir dist\installer
    "%ISCC_PATH%" installer.iss
    if %ERRORLEVEL% equ 0 (
        echo.
        echo [SUCCESS] Windows Installer created:
        echo    dist\installer\HologramAuthenticity_Setup.exe
    ) else (
        echo [WARNING] Inno Setup compilation encountered an issue.
    )
) else (
    echo [INFO] Inno Setup compiler (ISCC.exe) not found in standard paths.
    echo To build the installer, install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo and re-run this script, or open installer.iss in Inno Setup GUI.
)

echo.
echo ===============================================================================
echo   BUILD PROCESS COMPLETE
echo ===============================================================================
echo Standalone Executable: dist\HologramAuthenticity.exe
if exist dist\installer\HologramAuthenticity_Setup.exe (
    echo Windows Installer:    dist\installer\HologramAuthenticity_Setup.exe
)
echo ===============================================================================
echo.
