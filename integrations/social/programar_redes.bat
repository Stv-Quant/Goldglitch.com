@echo off
REM Crea la tarea de Windows que corre los agentes de redes cada 15 minutos (mientras el PC este encendido).
cd /d "%~dp0"
schtasks /Create /F /SC MINUTE /MO 15 /TN "Goldglitch Redes" /TR "\"%~dp0redes_goldglitch.bat\""
if errorlevel 1 (
  echo No se pudo crear la tarea. Clic derecho sobre este archivo ^> Ejecutar como administrador.
) else (
  echo Tarea "Goldglitch Redes" creada: corre cada 15 minutos.
  echo Para pausar sin borrarla, agrega REDES_PAUSA=1 al .env
)
pause
