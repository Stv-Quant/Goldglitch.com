@echo off
chcp 65001 >nul
REM PUBLICAR YA: los agentes publican una pieza en este momento en todas las redes conectadas.
REM Sin nada: la proxima pendiente del plan de hoy (o un meme del momento). Tambien: publicar_ya.bat reel / meme / picks_dia
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_social.py ya %1
echo.
echo Detalle en redes.log
pause
