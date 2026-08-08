@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Photoshop bridge (port 8189)
"%~dp0python_embeded\python.exe" -s ps_bridge.py
echo.
echo Bridge stopped. Press any key to close.
pause >nul
