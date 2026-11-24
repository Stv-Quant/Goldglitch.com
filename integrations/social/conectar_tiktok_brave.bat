@echo off
chcp 65001 >nul
REM TikTok en Brave: abre Brave con un perfil aparte para los agentes; inicias sesion en TikTok una vez.
REM Desde ahi los agentes publican TikTok en Brave (Instagram, Facebook y YouTube siguen igual).
REM Para pasar otra red a Brave: conectar_tiktok_brave.bat instagram facebook youtube
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
if "%~1"=="" (%PY% goldglitch_social.py conectar_brave tiktok) else (%PY% goldglitch_social.py conectar_brave %*)
pause
