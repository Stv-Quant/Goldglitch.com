@echo off
REM Ronda de comunidad YA: los agentes responden comentarios y dan me gusta en YouTube, Instagram, Facebook y TikTok.
REM (Tambien lo hacen solos cada 4 horas entre 10:00 y 22:00.)
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_social.py comunidad
pause
