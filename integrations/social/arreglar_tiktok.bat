@echo off
chcp 65001 >nul
REM Arregla el perfil de TikTok de EGG: foto de perfil (logo), nombre visible y biografia. No publica nada.
REM La primera vez copia tu sesion de TikTok del Brave instalado al Brave de los agentes (sin contrasenas).
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_profile.py tiktok
echo.
echo Informe: redes_perfil_informe.md
pause
