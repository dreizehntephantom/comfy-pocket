@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  IPADAPTER render (ComfyUI)
echo  Settings -^> config_ip.txt   References -^> folder ref_dir
echo  Strength -^> weight in config_ip.txt (0.2-0.3 = soft)
echo  Prompt -^> prompt.txt   Negative -^> negative.txt
echo  Seed: drag a number in, or "РЕНДЕР_IP.bat 2645234451"
echo  Output -^> ComfyUI\output\
echo ============================================================
.\python_embeded\python.exe run_workflow_ip.py %1
