@echo off
chcp 65001 >nul
REM COMBINADAS: picks del modelo de 85%+ cruzados con las cuotas PUBLICAS de BetPlay (no entra a tu cuenta, no apuesta).
REM Al menos 3 opciones con cuota total mayor a 2: 1 de un mismo partido y 2 de partidos distintos.
REM Deja el reporte en reportes\ y lo abre.
cd /d "%~dp0"
set COMB_MIN_P=0.85
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_combinadas.py
echo.
pause
