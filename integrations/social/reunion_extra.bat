@echo off
REM Reunion EXTRAORDINARIA del comite, a cualquier hora:
REM  - Entre 7:00 a.m. y 10:00 p.m.: rehacen el resto del plan de HOY (lo ya publicado se respeta).
REM  - De noche: dejan un BORRADOR y la reunion normal de la manana igual se hace, teniendo en cuenta ese borrador.
REM El acta queda en redes_comite_actas\  (archivo ..._extraordinaria_HHMM.md)
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_growth.py --extra
echo.
echo Acta en la carpeta redes_comite_actas
pause
