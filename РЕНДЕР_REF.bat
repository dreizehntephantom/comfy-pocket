@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  REFERENCE-ONLY render (ComfyUI)
echo  Settings -^> config_ref.txt   References -^> folder ref_dir
echo  Prompt -^> prompt.txt   Negative -^> negative.txt
echo  Seed: drag a number in, or "РЕНДЕР_REF.bat 2645234451"
echo  Output -^> ComfyUI\output\
echo ============================================================
.\python_embeded\python.exe run_workflow_ref.py %1
