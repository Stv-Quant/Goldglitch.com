@echo off
REM Crea (o reemplaza) la tarea de Windows que corre el analisis completo de SQPC a las 6:10 y a las 18:10.
REM Doble clic una sola vez. Para quitarla:  schtasks /Delete /TN "SQPC Analisis" /F
cd /d "%~dp0"
schtasks /Create /TN "SQPC Analisis" /TR "\"%~dp0analisis_goldglitch.bat\"" /SC HOURLY /MO 12 /ST 06:10 /F
if %errorlevel%==0 (
  echo.
  echo Listo: SQPC analizara todo a las 6:10 y a las 18:10 mientras el PC este encendido.
  echo Primer analisis ahora (tarda unos 30-40 minutos, puedes cerrar esta ventana cuando quieras^)...
  start "" /min "%~dp0analisis_goldglitch.bat"
) else (
  echo No se pudo crear la tarea. Abre esta ventana con clic derecho ^> Ejecutar como administrador.
)
pause
