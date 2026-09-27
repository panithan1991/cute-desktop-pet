@echo off
setlocal
cd /d "%~dp0\.."

python -m pip install "pyinstaller==6.22.3" "Pillow>=10,<13"

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name MooKrata ^
    --icon icons/mookrata.ico ^
    --add-data "assets;assets" ^
    --add-data "icons;icons" ^
    desktop_pet.py

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name BooBoo ^
    --icon icons/booboo.ico ^
    --add-data "assets;assets" ^
    --add-data "icons;icons" ^
    desktop_pet.py

powershell -Command "Compress-Archive -Path dist\MooKrata.exe, dist\BooBoo.exe -DestinationPath CuteDesktopPet-Windows.zip -Force"
