@echo off
REM Instala lo que necesitan los agentes de redes (una sola vez).
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% -m pip install -r requirements-redes.txt
%PY% -m playwright install chromium
echo.
echo Listo. Prueba el diseno con:  %PY% goldglitch_social.py prueba
pause
