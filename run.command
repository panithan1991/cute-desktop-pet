#!/bin/sh
# Double-click in Finder or run from Terminal to start the macOS desktop pet.
cd "$(dirname "$0")" || exit 1

for python in \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    python3
do
    if command -v "$python" >/dev/null 2>&1 && \
       "$python" -c 'import sys, tkinter as tk; r=tk.Tk(); r.withdraw(); ok=sys.version_info >= (3, 10) and tk.TkVersion >= 8.6 and r.tk.call("tk", "windowingsystem") == "aqua"; r.destroy(); sys.exit(0 if ok else 1)' >/dev/null 2>&1
    then
        "$python" desktop_pet.py
        status=$?
        if [ "$status" -ne 0 ]; then
            printf '\nBooBoo stopped with an error. Press Return to close this window.\n'
            read -r unused
        fi
        exit "$status"
    fi
done

printf 'BooBoo needs Python 3.10+ with Aqua Tk 8.6+ on macOS.\n'
printf 'Install the current macOS Python from https://www.python.org/downloads/macos/\n'
printf 'Press Return to close this window.\n'
read -r unused
exit 1
