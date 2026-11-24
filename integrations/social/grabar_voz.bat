@echo off
chcp 65001 >nul
REM Graba la VOZ de EGG (16 s con el microfono): todos los videos usaran ese timbre y acento con la voz natural.
REM Que la grabe alguien que acepte ser la voz de EGG (tu o un amigo), leyendo como relator argentino apasionado.
REM Tambien puedes dejar un audio tuyo de 10-15 s llamado voz_referencia.wav en esta carpeta.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_voz.py grabar
if exist redes_salida\voz_prueba_referencia.wav start "" redes_salida\voz_prueba_referencia.wav
pause
