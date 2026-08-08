@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  RENDER BY POSE  (ControlNet depth)
echo.
echo  1. Put any image with the pose into:  depth\donor\
echo  2. Run this file. That's it.
echo.
echo  Depth map    -^> depth\map.png   (overwritten every run)
echo  Prompt       -^> prompt.txt      Negative -^> negative.txt
echo  Pose grip    -^> config.txt : depth_strength  (0.6 default)
echo  Result       -^> ComfyUI\output\YYYY-MM-DD\depth_*.png
echo.
echo  Optional: RENDER_POSE.bat 12345      (fixed seed)
echo            drag an image onto this file to use it once
echo ============================================================
.\python_embeded\python.exe run_depth.py %1 %2
if errorlevel 1 pause
