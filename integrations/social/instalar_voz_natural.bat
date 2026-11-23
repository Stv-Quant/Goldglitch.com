@echo off
chcp 65001 >nul
REM VOZ NATURAL para los reels: Chatterbox Multilingual (Resemble AI, licencia MIT), gratis y en tu PC.
REM Se instala en su propio entorno (.venv_voz, unos 4 GB) para no tocar lo demas. Prueba: redes_salida\voz_prueba_natural.wav
REM Opcional: deja un audio voz_referencia.wav (10-15 s, voz de alguien que te dio permiso) para usar ese timbre.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_voz.py instalar_natural
echo.
echo Escucha redes_salida\voz_prueba_natural.wav
pause
