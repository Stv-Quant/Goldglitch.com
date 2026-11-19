@echo off
REM Comprueba que Claude Code esta instalado, con tu sesion de Claude, y que responde con Haiku 5.5.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_claude_cli.py
pause
