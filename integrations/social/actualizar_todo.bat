@echo off
chcp 65001 >nul
REM ACTUALIZAR TODO A MANO: datos de SQPC -> easygoldglitch.com -> reunion de la firma -> publicaciones.
REM  1) Completo: SQPC descarga datos, predice todo y lo sube a la web (30-40 min).
REM  2) Rapido: sube a la web lo que SQPC ya tiene calculado (1-2 min).
REM Despues la firma se reune con los datos nuevos (rehace el resto del plan de hoy; de noche deja borrador para manana)
REM y se publica lo que toque ya.
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
echo.
echo   1 = Completo (descargar, predecir y subir: 30-40 min)
echo   2 = Rapido   (subir lo ya calculado: 1-2 min)
echo.
choice /c 12 /n /t 20 /d 1 /m "Elige 1 o 2 (si no eliges, en 20 s arranca el 1): "
if errorlevel 2 goto rapido

echo.
echo [1/3] Analisis completo de SQPC y subida a easygoldglitch.com...
echo [%date% %time%] inicio manual >> analisis_goldglitch.log
%PY% analisis_goldglitch.py
echo [%date% %time%] fin manual (codigo %errorlevel%) >> analisis_goldglitch.log
goto comite

:rapido
echo.
echo [1/3] Subiendo a easygoldglitch.com lo que SQPC ya calculo...
echo [%date% %time%] inicio manual >> goldglitch_sync.log
%PY% goldglitch_sync.py
echo [%date% %time%] fin manual (codigo %errorlevel%) >> goldglitch_sync.log

:comite
echo.
echo [2/3] Reunion de la firma de marketing con los datos nuevos (unos minutos)...
%PY% goldglitch_growth.py --extra
echo.
echo [3/3] Publicando lo que toque ahora...
%PY% goldglitch_social.py tick
%PY% goldglitch_oficina.py
echo.
echo Listo. Acta en redes_comite_actas, detalle en redes.log. Abre oficina.bat para ver al equipo.
pause
