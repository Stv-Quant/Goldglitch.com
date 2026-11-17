@echo off
REM Analisis completo de SQPC (como el boton "Todo" de la app) y publicacion en easygoldglitch.com.
REM Lo ejecuta la tarea programada "SQPC Analisis" dos veces al dia; tambien puedes darle doble clic.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
echo [%date% %time%] inicio >> analisis_goldglitch.log
%PY% analisis_goldglitch.py >> analisis_goldglitch.log 2>&1
echo [%date% %time%] fin (codigo %errorlevel%) >> analisis_goldglitch.log
