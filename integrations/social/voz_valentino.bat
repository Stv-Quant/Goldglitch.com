@echo off
chcp 65001 >nul
REM Voz "Valentino" de ElevenLabs para TODOS los videos (reels, shorts, TikTok).
REM Requiere ELEVENLABS_API_KEY en el .env (plan de pago de ElevenLabs: el gratis no permite uso comercial).
REM Otra voz de ElevenLabs: agrega ELEVENLABS_VOZ=Nombre en el .env. Para volver a la voz local: REDES_VOZ_MOTOR=local
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_voz.py elevenlabs
if exist redes_salida\voz_prueba_valentino.wav start "" redes_salida\voz_prueba_valentino.wav
pause
