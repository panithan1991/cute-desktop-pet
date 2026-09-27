@echo off
setlocal
cd /d "%~dp0\.."

python -m pip install "pyinstaller==6.22.3" "Pillow>=10,<13"
if errorlevel 1 exit /b %errorlevel%

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name MooKrata ^
    --icon icons/mookrata.ico ^
    --add-data "assets\booboo-motion-windows.png;assets" ^
    --add-data "assets\booboo-motion-left-windows.png;assets" ^
    --add-data "assets\moo-krata-motion-windows.png;assets" ^
    --add-data "assets\moo-krata-motion-left-windows.png;assets" ^
    desktop_pet.py
if errorlevel 1 exit /b %errorlevel%

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name BooBoo ^
    --icon icons/booboo.ico ^
    --add-data "assets\booboo-motion-windows.png;assets" ^
    --add-data "assets\booboo-motion-left-windows.png;assets" ^
    --add-data "assets\moo-krata-motion-windows.png;assets" ^
    --add-data "assets\moo-krata-motion-left-windows.png;assets" ^
    desktop_pet.py
if errorlevel 1 exit /b %errorlevel%

powershell -Command "Compress-Archive -Path dist\MooKrata.exe, dist\BooBoo.exe -DestinationPath CuteDesktopPet-Windows.zip -Force"
if errorlevel 1 exit /b %errorlevel%
