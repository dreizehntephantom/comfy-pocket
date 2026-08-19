@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ============================================================
echo  RENDER BY COLOR COMPOSITION  (T2I-Adapter)
echo.
echo  1. Put any image with the color layout into:  color\donor\
echo  2. Run this file. That's it.
echo.
echo  It keeps WHERE THE COLORS SIT, not shapes and not lines.
echo  For shapes use RENDER_POSE, for lines use RENDER_CONTOUR.
echo.
echo  Color grid  -^> color\map.png    (overwritten every run)
echo  Prompt      -^> prompt.txt       Negative -^> negative.txt
echo  Color grip  -^> config.txt : color_strength     (0.6 default)
echo  Grid size   -^> config.txt : color_resolution   (512 default)
echo  Result      -^> ComfyUI\output\YYYY-MM-DD\color_*.png
echo.
echo  Optional: RENDER_COLOR.bat 12345   (fixed seed)
echo            drag an image onto this file to use it once
echo ============================================================
.\python_embeded\python.exe run_color.py %1 %2
if errorlevel 1 pause
