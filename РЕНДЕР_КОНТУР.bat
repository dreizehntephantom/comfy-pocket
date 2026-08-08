@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  RENDER BY CONTOUR  (ControlNet canny)
echo.
echo  1. Put any image with the pose/lines into:  canny\donor\
echo  2. Run this file. That's it.
echo.
echo  Contour map  -^> canny\map.png   (overwritten every run)
echo  Prompt       -^> prompt.txt      Negative -^> negative.txt
echo  Contour grip -^> config.txt : canny_strength  (0.6 default)
echo  Result       -^> ComfyUI\output\YYYY-MM-DD\canny_*.png
echo.
echo  Optional: RENDER_CONTOUR.bat 12345   (fixed seed)
echo            drag an image onto this file to use it once
echo ============================================================
.\python_embeded\python.exe run_canny.py %1 %2
if errorlevel 1 pause
