@echo off
REM Builds dist\NorwinMouseAssist.exe (single file, no console window).
REM Requires Python 3.9+ installed and on PATH.
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller || goto :fail
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name NorwinMouseAssist --icon icon.ico main.py || goto :fail
echo.
echo Done: dist\NorwinMouseAssist.exe
pause
exit /b 0
:fail
echo Build failed.
pause
exit /b 1
