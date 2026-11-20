@echo off
REM Abre la oficina de EGG: el equipo de marketing trabajando (plan, tendencias, actas, cuadernos y lo que pasa en vivo).
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_oficina.py --abrir
