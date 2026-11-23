@echo off
chcp 65001 >nul
REM REUNION + PUBLICAR YA: la firma se reune ahora mismo (a cualquier hora), arma el plan y publica de una vez
REM una pieza en todas las redes conectadas (Instagram, Facebook, TikTok y YouTube).
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_growth.py --ya
%PY% goldglitch_oficina.py
echo.
echo Listo. Acta en redes_comite_actas, detalle en redes.log
pause
