@echo off
chcp 65001 >nul
title ComfyUI - portable
rem ---------------------------------------------------------------------
rem VNIMANIE: vnutri etogo faila TOLKO ASCII.
rem cmd chitaet telo batnika kuskami v odnobaitnoi kodirovke, a kirillica
rem v UTF-8 zanimaet 2 baita. Granica kuska popadaet v seredinu bukvy i
rem komandy razvalivayutsya. Russkii tekst - tolko iz Python.
rem ---------------------------------------------------------------------
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist logs mkdir logs
echo.
echo Starting Photoshop bridge in a separate window (port 8189)
start "" "%~dp0ps_bridge.bat"
echo.
echo Starting ComfyUI at http://127.0.0.1:8188  (browser opens by itself)
echo Server log is written to  logs\comfyui_server.log
echo Do NOT close this window while working. To stop = close the window.
echo (No NVIDIA GPU? ComfyUI switches to CPU automatically - just slower.)
echo.
powershell -NoProfile -Command "& '.\python_embeded\python.exe' -s ComfyUI\main.py --port 8188 --auto-launch 2>&1 | Tee-Object -FilePath 'logs\comfyui_server.log'"
pause
