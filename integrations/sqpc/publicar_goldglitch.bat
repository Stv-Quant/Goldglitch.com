@echo off
REM Publica en easygoldglitch.com lo que SQPC ya calculo (predicciones, metricas y marcadores finales).
REM Lo ejecuta la tarea programada "SQPC Goldglitch" cada hora; tambien puedes darle doble clic.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
echo [%date% %time%] inicio >> goldglitch_sync.log
%PY% goldglitch_sync.py >> goldglitch_sync.log 2>&1
echo [%date% %time%] fin (codigo %errorlevel%) >> goldglitch_sync.log
