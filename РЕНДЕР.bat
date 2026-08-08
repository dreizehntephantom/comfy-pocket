@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  РЕНДЕР через ComfyUI (синхро с tensor.art)
echo  Промпт -> prompt.txt   Негатив -> negative.txt
echo  Сид: перетащи число в окно или запусти "РЕНДЕР.bat 2645234451"
echo  Без сида = случайный. Картинки -> ComfyUI\output\
echo ============================================================
.\python_embeded\python.exe run_workflow.py %1
