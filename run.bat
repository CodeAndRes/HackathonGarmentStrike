@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Activando entorno virtual...
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
) else (
    echo [!] ERROR: No se encontro la carpeta .venv.
    pause
    exit /b
)

echo [2/2] Iniciando Garment Strike...
python main.py

if errorlevel 1 (
    echo.
    echo [!] La aplicacion se cerro con errores.
    pause
)
