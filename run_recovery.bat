@echo off
echo IMPORTANT: This batch file needs to be run "as Administrator"
echo for the recovery tool to have the necessary permissions to read disk partitions.
echo Right-click on this .bat file and select "Run as administrator".
echo.

REM Change directory to the script's own directory
cd /d "%~dp0"

echo Running Python recovery script...
python recovery_tool.py

echo.
echo Script execution finished or encountered an error.
pause
