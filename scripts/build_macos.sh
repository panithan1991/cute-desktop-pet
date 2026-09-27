#!/bin/sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
    printf 'Build BooBoo.app on macOS, not on this operating system.\n' >&2
    exit 1
fi

cd "$(dirname "$0")/.."

# PyInstaller's windowed onedir build includes Python and Aqua Tcl/Tk.
# Pillow is needed only while converting the PNG to a macOS app icon.
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name BooBoo \
    --osx-bundle-identifier com.panithan1991.booboo \
    --icon icons/booboo.png \
    --add-data 'assets/booboo-motion.png:assets' \
    --add-data 'assets/booboo-motion-left.png:assets' \
    --add-data 'assets/moo-krata-motion.png:assets' \
    --add-data 'assets/moo-krata-motion-left.png:assets' \
    --add-data 'assets/bibi-motion.png:assets' \
    --add-data 'assets/bibi-motion-left.png:assets' \
    desktop_pet.py

test -x dist/BooBoo.app/Contents/MacOS/BooBoo
