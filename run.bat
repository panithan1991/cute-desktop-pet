@echo off
cd /d "%~dp0"
if exist "%~dp0MooKrata.exe" (
    start "" "%~dp0MooKrata.exe"
    exit /b 0
)
for /f "delims=" %%P in ('where python 2^>nul') do (
    "%%P" -c "import tkinter as tk; root = tk.Tk(); root.destroy()" >nul 2>nul
    if not errorlevel 1 (
        if exist "%%~dpPpythonw.exe" (
            start "" "%%~dpPpythonw.exe" "%~dp0desktop_pet.py"
        ) else (
            start "" "%%P" "%~dp0desktop_pet.py"
        )
        exit /b 0
    )
)
echo Python with a working Tkinter installation was not found.
echo Install the standard Windows Python from https://www.python.org/downloads/
pause
exit /b 1
