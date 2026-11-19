@echo off
REM Instala Claude Code (una sola vez) para que los agentes usen tu plan de Claude (Pro) con Haiku 5.5.
REM Despues abre una terminal, escribe  claude  e inicia sesion con tu cuenta de Claude.
echo Instalando Claude Code...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
echo.
echo Listo. Ahora:
echo   1) Cierra esta ventana y abre una NUEVA ventana de PowerShell o CMD.
echo   2) Escribe:  claude   y presiona Enter.
echo   3) Elige iniciar sesion con tu cuenta de Claude (la del plan Pro) y sigue los pasos del navegador.
echo   4) Cuando veas el chat de Claude Code, escribe  /exit  y luego da doble clic en probar_claude_pro.bat
pause
