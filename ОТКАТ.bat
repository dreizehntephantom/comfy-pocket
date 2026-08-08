@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
rem ---- ASCII only inside this file (see CLAUDE.md) ----
title Otkat
"%~dp0python_embeded\python.exe" -s launcher.py --rollback
