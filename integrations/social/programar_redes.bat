@echo off
REM Crea las tareas de Windows de los agentes de redes:
REM  1) "Goldglitch Redes": cada 15 minutos mientras el PC este encendido.
REM  2) "Goldglitch Redes al iniciar": 2 minutos despues de iniciar sesion en Windows, para que si el PC se prende
REM     tarde el comite se reuna y los agentes se pongan al dia de una.
cd /d "%~dp0"
schtasks /Create /F /SC MINUTE /MO 15 /TN "Goldglitch Redes" /TR "\"%~dp0redes_goldglitch.bat\""
if errorlevel 1 (
  echo No se pudo crear la tarea. Clic derecho sobre este archivo ^> Ejecutar como administrador.
  pause
  exit /b 1
)
schtasks /Create /F /SC ONLOGON /DELAY 0002:00 /TN "Goldglitch Redes al iniciar" /TR "\"%~dp0redes_goldglitch.bat\""
if errorlevel 1 (
  echo La tarea de inicio necesita permisos: clic derecho sobre este archivo ^> Ejecutar como administrador.
  echo ^(La de cada 15 minutos ya quedo creada y tambien se pone al dia, solo que puede tardar hasta 15 minutos.^)
) else (
  echo Listo: corre cada 15 minutos y tambien 2 minutos despues de prender el PC.
)
echo Para pausar sin borrarlas, agrega REDES_PAUSA=1 al .env
pause
