@echo off
:: ============================================================
::  MAGOS Tunnel — Build script
::  Requires: pip install -r requirements.txt
::  Output:   dist\MAGOSTunnel.exe
:: ============================================================

echo.
echo  ╔══════════════════════════════╗
echo  ║   MAGOS TUNNEL  — Build      ║
echo  ╚══════════════════════════════╝
echo.

:: Run PyInstaller
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name "MAGOSTunnel" ^
  --icon "assets\icon.ico" ^
  --add-data "assets;assets" ^
  --hidden-import win32timezone ^
  --hidden-import win32service ^
  --hidden-import win32serviceutil ^
  --hidden-import win32event ^
  --hidden-import servicemanager ^
  --hidden-import pystray._win32 ^
  src\main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo [OK] Build complete.
echo      Ejecutable: dist\MAGOSTunnel.exe
echo.
pause
