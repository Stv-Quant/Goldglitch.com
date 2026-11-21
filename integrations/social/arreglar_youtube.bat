@echo off
REM Los agentes dejan listo el canal de YouTube de EGG: foto de perfil, banner, marca de agua, descripcion y enlace.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_profile.py youtube
echo.
echo Informe: redes_perfil_informe.md
pause
