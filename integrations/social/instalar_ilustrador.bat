@echo off
REM Instala el ILUSTRADOR: IA de imagenes que corre gratis en tu PC con tu tarjeta grafica NVIDIA (sin suscripciones).
REM Revisa tu tarjeta, instala PyTorch + diffusers, descarga el modelo abierto (FLUX.1 schnell o Stable Diffusion XL)
REM y pinta la galeria de personajes de EGG. Solo se hace una vez. Necesita espacio en disco (7 a 35 GB) e internet.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
%PY% goldglitch_ilustrador.py instalar
if errorlevel 1 goto fin
echo.
echo Pintando la galeria de personajes (EGG, Mateo, Santiago, Valeria en 5 expresiones)...
%PY% goldglitch_ilustrador.py personajes
echo.
echo Listo: desde la proxima publicacion las piezas llevan ilustraciones pintadas por la IA en tu PC.
echo Prueba en redes_salida\ilustraciones  y personajes en redes_personajes
:fin
pause
