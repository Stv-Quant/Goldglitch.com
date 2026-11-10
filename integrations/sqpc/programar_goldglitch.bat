@echo off
REM Crea (o reemplaza) la tarea de Windows que publica en easygoldglitch.com cada hora.
REM Doble clic una sola vez. Para quitarla:  schtasks /Delete /TN "SQPC Goldglitch" /F
cd /d "%~dp0"
schtasks /Create /TN "SQPC Goldglitch" /TR "\"%~dp0publicar_goldglitch.bat\"" /SC HOURLY /MO 1 /F
if %errorlevel%==0 (
  echo.
  echo Listo: SQPC publicara en easygoldglitch.com cada hora mientras el PC este encendido.
  echo Primera publicacion ahora...
  call "%~dp0publicar_goldglitch.bat"
  type goldglitch_sync.log | more +0
) else (
  echo No se pudo crear la tarea. Abre esta ventana con clic derecho ^> Ejecutar como administrador.
)
pause
