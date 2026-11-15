@echo off
REM Lo ejecuta la tarea programada "Goldglitch Redes" cada 15 minutos: planea, publica y responde comentarios.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_social.py tick >> redes_tarea.log 2>&1
