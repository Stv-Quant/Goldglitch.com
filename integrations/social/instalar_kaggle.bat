@echo off
chcp 65001 >nul
REM Instala la herramienta de Kaggle (gratis) en el entorno de las redes. Solo hace falta una vez.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% -m pip install -U kaggle six
echo.
echo Listo. Revisa que .env tenga KAGGLE_API_TOKEN=... y corre generar_clips_ia.bat
pause
