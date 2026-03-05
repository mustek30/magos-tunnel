@echo off
:: ============================================================
::  Desinstala el servicio MAGOS Tunnel
::  EJECUTAR COMO ADMINISTRADOR
:: ============================================================

net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

echo  Deteniendo servicio...
net stop MAGOSTunnel 2>nul

set EXE=%~dp0dist\MAGOSTunnel.exe
echo  Eliminando servicio...
"%EXE%" --uninstall-service

echo.
echo  [OK] Servicio MAGOS Tunnel eliminado.
echo.
pause
