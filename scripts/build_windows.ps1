$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name BooBoo `
    --icon icons/booboo.png `
    --add-data 'assets;assets' `
    desktop_pet.py

if (-not (Test-Path -LiteralPath 'dist/BooBoo/BooBoo.exe')) {
    throw 'BooBoo.exe was not built.'
}
