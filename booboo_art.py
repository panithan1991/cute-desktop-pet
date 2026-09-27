"""BooBoo's transparent, reference-matched sprite poses and animation choices.

Tk's built-in PNG decoder keeps alpha transparency, so the desktop app needs
no imaging dependency at runtime. The 3x2 sheet is cut and mirrored in memory.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk


CELL_SIZE = 512
DISPLAY_SCALE = 3
POSES = {
    "idle": (0, 0),
    "smile": (1, 0),
    "happy": (2, 0),
    "curious": (0, 1),
    "hop": (1, 1),
    "sleepy": (2, 1),
}


def choose_pose(
    now: float,
    *,
    walking: bool,
    airborne: bool,
    blink: bool,
    resting_remaining: float,
    paused: bool,
) -> str:
    """Choose a readable pose without flashing frames on every 33 ms tick."""
    if paused:
        return "sleepy"
    if airborne:
        return "hop"
    if blink:
        return "smile"
    if resting_remaining > 0.7:
        return "curious"
    if resting_remaining > 0:
        return "sleepy"
    if walking and now % 5.2 < 0.55:
        return "happy"
    return "idle"


class BooBooSprites:
    """Keep PhotoImages alive for Tk canvas; reverse sampling mirrors a pose."""

    def __init__(self, root: tk.Misc) -> None:
        path = Path(__file__).parent / "assets" / "booboo-sprites.png"
        self.source = tk.PhotoImage(master=root, file=str(path))
        expected = (CELL_SIZE * 3, CELL_SIZE * 2)
        actual = (self.source.width(), self.source.height())
        if actual != expected:
            raise ValueError(f"BooBoo sprite sheet must be {expected}, got {actual}")

        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        size = (CELL_SIZE + DISPLAY_SCALE - 1) // DISPLAY_SCALE
        for pose, (col, row) in POSES.items():
            tile = tk.PhotoImage(master=root, width=CELL_SIZE, height=CELL_SIZE)
            root.tk.call(
                str(tile), "copy", str(self.source), "-from",
                col * CELL_SIZE, row * CELL_SIZE,
                (col + 1) * CELL_SIZE, (row + 1) * CELL_SIZE,
                "-to", 0, 0,
            )
            self.frames[(pose, 1)] = tile.subsample(DISPLAY_SCALE, DISPLAY_SCALE)
            mirrored = tk.PhotoImage(master=root, width=size, height=size)
            root.tk.call(
                str(mirrored), "copy", str(tile), "-from",
                0, 0, CELL_SIZE, CELL_SIZE, "-to", 0, 0,
                "-subsample", -DISPLAY_SCALE, DISPLAY_SCALE,
            )
            self.frames[(pose, -1)] = mirrored

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
