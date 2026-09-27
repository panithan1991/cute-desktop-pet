# Cute Desktop Pet

BooBoo the rabbit and Moo Krata the puppy live on your desktop. Each has 25 poses, including resting, head tilts, walking, and occasional hops. Seven other characters are available from the pet's menu.

## Download

Get the ZIP for your computer from the [latest release](https://github.com/panithan1991/cute-desktop-pet/releases/latest):

| System | Open after extracting the ZIP |
| --- | --- |
| Windows 10/11 | `BooBoo.exe` or `MooKrata.exe` |
| Mac, Apple Silicon | `BooBoo.app` from the Apple Silicon ZIP |
| Mac, Intel | `BooBoo.app` from the Intel ZIP |

The downloads include Python, Tk, and the artwork. Right-click the pet (or Control-click on Mac) to switch characters, pause, or quit. Drag it to move it.

The Mac app is not Apple-notarized. If macOS blocks its first launch, open **System Settings → Privacy & Security → Open Anyway**. If it still does not appear, check `~/Library/Logs/BooBoo/startup.log`.

## Run from source

Install Python 3.10+ with Tkinter, then run `run.bat` on Windows or `run.command` on Mac. No third-party Python packages are needed at runtime.

To build the downloadable apps, install `pyinstaller==6.22.3` and `Pillow>=10,<13`, then run `scripts/build_windows.bat` on Windows or `sh scripts/build_macos.sh` on Mac. Run `python -m unittest discover -s tests -q` to check the code and sprite atlases.
