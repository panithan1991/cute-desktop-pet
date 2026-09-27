# Cute Desktop Pet

[![Mac and Windows builds](https://github.com/panithan1991/cute-desktop-pet/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/panithan1991/cute-desktop-pet/actions/workflows/release.yml)

BooBoo the rabbit, Moo Krata the puppy, and Bibi the bald eagle live on your desktop. BooBoo and Moo Krata each have 25 poses; Bibi has 30 and flies across and up the screen before landing. Seven other characters are available from the pet's menu.

| BooBoo | Moo Krata | Bibi |
| :---: | :---: | :---: |
| <img src="assets/readme/booboo.png" alt="BooBoo the white rabbit" width="180"> | <img src="assets/readme/moo-krata.png" alt="Moo Krata the puppy" width="180"> | <img src="assets/readme/bibi.png" alt="Bibi the bald eagle" width="180"> |

## Download

Choose a ZIP from the [latest release](https://github.com/panithan1991/cute-desktop-pet/releases/latest):

| Download for Window | Download for MAC |
| --- | --- |
| [Windows 10/11 ZIP](https://github.com/panithan1991/cute-desktop-pet/releases/latest/download/CuteDesktopPet-Windows.zip) | [Apple Silicon ZIP](https://github.com/panithan1991/cute-desktop-pet/releases/latest/download/CuteDesktopPet-macOS-Apple-Silicon.zip) · [Intel ZIP](https://github.com/panithan1991/cute-desktop-pet/releases/latest/download/CuteDesktopPet-macOS-Intel.zip) |

Extract the ZIP. On Windows, open `BooBoo.exe`, `MooKrata.exe`, or `Bibi.exe`. On Mac, open `BooBoo.app` and select Bibi from the menu. The downloads include Python, Tk, and the artwork. Right-click the pet (or Control-click on Mac) to switch characters, pause, or quit. Drag it to move it.

Every release ZIP has a [SHA-256 checksum](https://github.com/panithan1991/cute-desktop-pet/releases/latest/download/SHA256SUMS.txt) and a GitHub build attestation. Compare `Get-FileHash FILE.zip -Algorithm SHA256` (Windows) or `shasum -a 256 FILE.zip` (Mac) with the checksum file. To confirm the build came from this repository, run `gh attestation verify FILE.zip -R panithan1991/cute-desktop-pet` with the [GitHub CLI](https://cli.github.com/).

These checks do not replace OS publisher verification. Windows may warn about the unsigned executables. The Mac app is not Apple-notarized; if macOS blocks its first launch, open **System Settings → Privacy & Security → Open Anyway**. If it still does not appear, check `~/Library/Logs/BooBoo/startup.log`.

## Run from source

Install Python 3.10+ with Tkinter, then run `run.bat` on Windows or `run.command` on Mac. No third-party Python packages are needed at runtime.

To build the downloadable apps, install `pyinstaller==6.22.3` and `Pillow>=10,<13`, then run `scripts/build_windows.bat` on Windows or `sh scripts/build_macos.sh` on Mac. Run `python -m unittest discover -s tests -q` to check the code and sprite atlases.
