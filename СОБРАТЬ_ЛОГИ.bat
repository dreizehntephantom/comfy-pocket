@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
rem ---- ASCII only inside (see CLAUDE.md) ----
title Collect logs
"%~dp0python_embeded\python.exe" -s _diag.py
echo.
pause
