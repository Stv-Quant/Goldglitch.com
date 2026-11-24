@echo off
chcp 65001 >nul
REM Publica TikToks YA (solo en TikTok): reels, noticias, sabias que, picks, mito vs dato, NBA y memes, en rotacion.
REM Uso: publicar_tiktok.bat            (pregunta cuantos)
REM      publicar_tiktok.bat 5          (5 TikToks)
REM      publicar_tiktok.bat 2 noticia  (2 de un formato: reel, noticia, sabias_que, picks_dia, mito_dato, nba, meme, pregunta)
cd /d "%~dp0"
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
set N=%~1
if "%N%"=="" set /p N="Cuantos TikToks publico ahora? (1-10, Enter = 3): "
if "%N%"=="" set N=3
%PY% goldglitch_social.py tiktok %N% %~2
echo.
echo Detalle en redes.log
pause
