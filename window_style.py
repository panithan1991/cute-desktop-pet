"""Platform-specific transparent backgrounds for the desktop overlays."""

from __future__ import annotations

import sys
import tkinter as tk


WINDOWS_TRANSPARENT_COLOR = "#ff00ff"
MAC_TRANSPARENT_COLOR = "systemTransparent"


def configure_pet_window(window: tk.Tk, platform: str | None = None) -> None:
    """Give the Mac pet a native titleless window visible across Spaces."""
    platform = sys.platform if platform is None else platform
    if platform == "darwin":
        try:
            # A native floating window is registered with WindowServer even when
            # launched from Finder. The old override-redirect root could remain
            # invisible on some Macs and could not follow fullscreen Spaces.
            window.tk.call(
                "::tk::unsupported::MacWindowStyle", "style", window._w,
                "floating", "noTitleBar noShadow canJoinAllSpaces",
            )
        except tk.TclError:
            # Older Aqua Tk builds may lack one of these style attributes.
            window.overrideredirect(True)
    else:
        window.overrideredirect(True)


def configure_overlay(window: tk.Tk | tk.Toplevel, platform: str | None = None) -> str:
    """Return the canvas background after enabling a transparent top-level."""
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        window.configure(background=WINDOWS_TRANSPARENT_COLOR)
        window.wm_attributes("-transparentcolor", WINDOWS_TRANSPARENT_COLOR)
        return WINDOWS_TRANSPARENT_COLOR
    if platform == "darwin":
        window.configure(background=MAC_TRANSPARENT_COLOR)
        window.wm_attributes("-transparent", True)
        return MAC_TRANSPARENT_COLOR
    raise RuntimeError(f"Unsupported desktop platform: {platform}")
