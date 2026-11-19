@echo off
REM Los agentes Haiku revisan y arreglan los perfiles de Instagram y de la pagina de Facebook:
REM foto de perfil (logo), portada, biografia, enlace, descripcion, categoria y boton. No publican nada.
REM Informe en redes_perfil_informe.md
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_profile.py
echo.
echo Informe: redes_perfil_informe.md   (detalle paso a paso en redes.log)
pause
