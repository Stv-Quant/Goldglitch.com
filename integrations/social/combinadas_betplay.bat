@echo off
chcp 65001 >nul
REM COMBINADAS: picks del modelo de 80%+ cruzados con las cuotas PUBLICAS de BetPlay (no entra a tu cuenta, no apuesta).
REM Busca primero 2-3 selecciones de UN MISMO partido con cuota total mayor a 2; si no hay, combina partidos.
REM Maximo 3 opciones. Deja el reporte en reportes\ y lo abre.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_combinadas.py
echo.
pause
