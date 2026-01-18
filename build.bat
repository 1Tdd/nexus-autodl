@echo off
echo Building Nexus-AutoDL...
pip install -r requirements.txt
pyinstaller Nexus-AutoDL.spec
echo.
echo Build complete! Executable is in the 'dist' folder.
pause
