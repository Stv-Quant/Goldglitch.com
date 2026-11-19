@echo off
REM Prueba completa SIN publicar: arma una pieza y recorre Instagram, Facebook y TikTok con la ventana a la vista,
REM llegando hasta el boton "Compartir/Publicar" sin pulsarlo. Si un paso falla, deja captura en redes_salida\errores.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_social.py ensayo
echo.
echo Revisa redes.log y, si hubo errores, la carpeta redes_salida\errores
pause
