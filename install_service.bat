@echo off
:: ============================================================
::  Instala MAGOS Tunnel como servicio Windows (auto-inicio)
::  EJECUTAR COMO ADMINISTRADOR
:: ============================================================

net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Este script debe ejecutarse como Administrador.
    pause
    exit /b 1
)

set EXE=%~dp0dist\MAGOSTunnel.exe

if not exist "%EXE%" (
    echo [ERROR] No se encuentra el ejecutable: %EXE%
    echo         Ejecute build.bat primero.
    pause
    exit /b 1
)

echo.
echo  Instalando servicio Windows...
"%EXE%" --install-service

echo  Iniciando servicio...
net start MAGOSTunnel

echo.
echo  [OK] MAGOS Tunnel instalado y corriendo como servicio.
echo       Se iniciará automáticamente con Windows.
echo.
pause
