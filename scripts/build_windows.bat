@echo off
setlocal
cd /d "%~dp0\.."

for %%N in (BooBoo MooKrata Bibi Kitten Dragon) do (
    python -m PyInstaller ^
        --noconfirm ^
        --clean ^
        --onefile ^
        --windowed ^
        --name %%N ^
        --icon icons/%%N.ico ^
        --add-data "assets\booboo-motion-windows.png;assets" ^
        --add-data "assets\booboo-motion-left-windows.png;assets" ^
        --add-data "assets\moo-krata-motion-windows.png;assets" ^
        --add-data "assets\moo-krata-motion-left-windows.png;assets" ^
        --add-data "assets\bibi-motion-windows.png;assets" ^
        --add-data "assets\bibi-motion-left-windows.png;assets" ^
        --add-data "assets\kitten-motion-windows.png;assets" ^
        --add-data "assets\kitten-motion-left-windows.png;assets" ^
        --add-data "assets\runtime\dragon-windows;assets\runtime\dragon-windows" ^
        desktop_pet.py
    if errorlevel 1 exit /b 1
)

powershell -Command "Compress-Archive -Path dist\MooKrata.exe, dist\BooBoo.exe, dist\Bibi.exe, dist\Kitten.exe, dist\Dragon.exe -DestinationPath CuteDesktopPet-Windows.zip -Force"
if errorlevel 1 exit /b %errorlevel%
