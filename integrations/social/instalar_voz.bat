@echo off
chcp 65001 >nul
REM Instala la VOZ de EGG para los reels: Kokoro, modelo abierto que corre gratis en tu PC (sin suscripciones).
REM Descarga unos 500 MB una sola vez y genera una prueba en redes_salida\voz_prueba.wav
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_voz.py instalar
echo.
echo Escucha redes_salida\voz_prueba.wav. Desde el proximo reel los videos salen narrados.
pause
