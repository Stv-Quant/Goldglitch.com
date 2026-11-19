@echo off
REM Reunion del comite de crecimiento (normalmente corre solo cada manana con las redes). Aqui la puedes forzar.
REM El acta queda en redes_comite_actas\ y el plan del dia en redes_plan_comite.json
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_growth.py --forzar
echo.
echo Acta del dia en la carpeta redes_comite_actas
pause
