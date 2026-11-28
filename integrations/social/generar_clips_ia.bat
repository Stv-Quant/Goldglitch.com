@echo off
chcp 65001 >nul
REM CLIPS DE VIDEO CON IA, GRATIS EN KAGGLE: pide los clips (estilos y temas variados), espera y los descarga a redes_clips\
REM Uso: generar_clips_ia.bat [cantidad]   (por defecto 4 para la primera prueba; luego 12-20)
cd /d "%~dp0"
set N=%1
if "%N%"=="" set N=4
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_kaggle.py todo %N%
echo.
if exist redes_clips explorer redes_clips
pause
