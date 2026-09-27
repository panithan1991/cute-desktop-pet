# BooBoo & Moo Krata — 25-pose desktop pets

BooBoo and Moo Krata now have 25 artwork poses each. They rest, look around,
sniff, play, run and hop with direction-correct left/right frames. BooBoo still
spends more time resting and tilting its head than jumping.

The macOS app prepares its sprites before showing its native floating window,
so it should no longer briefly show an empty `tk` window. A startup failure
opens a diagnostic alert and writes `~/Library/Logs/BooBoo/startup.log`.

- **Windows 10/11:** download `CuteDesktopPet-Windows.zip`, unzip, then open
  `BooBoo.exe` or `MooKrata.exe`.
- **Mac with Apple Silicon:** download `CuteDesktopPet-macOS-Apple-Silicon.zip`.
- **Mac with Intel:** download `CuteDesktopPet-macOS-Intel.zip`.

Unzip the Mac download and open `BooBoo.app`. Right-click the pet to choose
either character. The Mac app is ad-hoc signed and cannot be notarized without
an Apple Developer account. If macOS blocks the first launch, use
**System Settings → Privacy & Security → Open Anyway**.

The download includes Python, Tk and all artwork; no separate installation is
needed. CI checks the extracted Windows executables and visually checks the
Mac app after unpacking it from the ZIP.
