"""Moo Krata the Bernese Mountain Dog puppy desktop animation and sprites."""

from __future__ import annotations

import base64
import math
from pathlib import Path
import sys
import tkinter as tk

from booboo_art import (
    CELL_SIZE,
    DISPLAY_SCALE,
    GRID_SIZE,
    POSES,
    _display_png,
    _read_rgba_png,
)


def choose_mookrata_pose(
    now: float,
    *,
    walking: bool,
    airborne: bool,
    jump_velocity: float,
    just_landed: bool,
    blink: bool,
    resting_remaining: float,
    paused: bool,
    walk_time: float = 0.0,
) -> str:
    """Select the best puppy pose for Moo Krata's current state."""
    if paused:
        return "sleepy"
    if airborne:
        if jump_velocity > 105:
            return "hop_start"
        if jump_velocity < -105:
            return "hop_land"
        return "hop_air"
    if just_landed:
        return "hop_land"
    if resting_remaining > 4.5:
        return "curious"
    if resting_remaining > 3.6:
        return "stretch"
    if resting_remaining > 0:
        return "sleepy"
    if walking:
        # Smooth 4-stage quadruped gallop cycle: reach -> flight leap -> ground plant -> drive stride
        phase = int((walk_time * 8) % 4)
        if phase == 0:
            return "hop_start"
        if phase == 1:
            return "hop_air"
        if phase == 2:
            return "hop_land"
        return "happy"
    if blink:
        return "smile"
    if now % 7.0 < 1.8:
        return "curious"
    return "idle"


class MooKrataSprites:
    """Keep all Tk frames alive for Moo Krata and mirror them for left/right facing."""

    def __init__(self, root: tk.Misc) -> None:
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        path = base_dir / "assets" / "mookrata-sprites.png"
        width, height, pixels = _read_rgba_png(path)
        expected = CELL_SIZE * GRID_SIZE
        if (width, height) != (expected, expected):
            raise ValueError(f"Moo Krata sprite sheet must be {expected}x{expected}")

        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        size = (CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE
        for pose, (col, row) in POSES.items():
            png = _display_png(pixels, width, col, row)
            frame = tk.PhotoImage(master=root, data=base64.b64encode(png))
            self.frames[(pose, 1)] = frame
            mirrored = tk.PhotoImage(master=root, width=size, height=size)
            root.tk.call(
                str(mirrored), "copy", str(frame), "-from",
                0, 0, size, size, "-to", 0, 0, "-subsample", -1, 1
            )
            self.frames[(pose, -1)] = mirrored

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
