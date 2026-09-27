"""Platform-specific transparent backgrounds for the desktop overlays."""

from __future__ import annotations

import sys
import tkinter as tk


WINDOWS_TRANSPARENT_COLOR = "#ff00ff"
MAC_TRANSPARENT_COLOR = "systemTransparent"


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
