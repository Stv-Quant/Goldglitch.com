@echo off
chcp 65001 >nul
REM COMBINADAS: picks del modelo de 85%+ cruzados con las cuotas PUBLICAS de BetPlay (no entra a tu cuenta, no apuesta).
REM Deja al menos 5 opciones de 1 a 3 selecciones con cuota total mayor a 2 en reportes\ y abre el reporte.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_combinadas.py
echo.
pause
