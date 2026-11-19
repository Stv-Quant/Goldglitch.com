@echo off
REM Una sola vez: abre el navegador de los agentes para que inicies sesion en Instagram, Facebook y TikTok.
REM Las contrasenas las escribes tu en las paginas oficiales; el programa nunca las ve ni las guarda.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_social.py conectar
pause
