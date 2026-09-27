"""Fast, pre-rendered animation atlases for the desktop pets."""

from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk


CELL = 160
COLUMNS = 5
GRID_COLUMNS = {"bunny": 5, "mookrata": 5, "bibi": 6}
POSES = {
    "bunny": (
        "idle", "blink", "happy", "sleep", "hop_up",
        "hop_air", "curious", "tilt", "stretch", "sit",
        "side_idle", "run_a", "run_b", "crouch", "roll_a",
        "roll_b", "roll_c", "dizzy", "playbow", "wave",
        "groom", "yawn", "sniff", "alert", "loaf",
    ),
    "mookrata": (
        "idle", "happy", "playbow", "hop", "run_a",
        "run_b", "tilt", "sleep", "stand_3q", "stand_side",
        "paw_up", "tilt_left", "tilt_right", "sniff_low", "sniff_air",
        "happy_sit", "awake_rest", "curled_sleep", "stretch", "playbow_two",
        "trot_a", "trot_b", "hop_two", "land", "sniff_close",
    ),
    "bibi": (
        "idle", "wink", "happy", "tilt_right", "tilt_left", "curious",
        "crouch", "wings_half", "wings_up", "bow", "takeoff", "launch",
        "fly_glide", "fly_flap", "fly_cheer", "fly_turn", "fly_glide_low", "fly_dive",
        "hover_happy", "hover_wink", "hover_turn", "land", "sleep_start", "sit",
        "hover_wings", "wings_happy", "wave", "cheer", "sleepy", "sleep",
    ),
}
FILENAME = {"bunny": "booboo-motion", "mookrata": "moo-krata-motion", "bibi": "bibi-motion"}


def atlas_path(character: str, facing: int, platform: str | None = None) -> Path:
    platform = sys.platform if platform is None else platform
    suffix = ("-left" if facing < 0 else "") + ("-windows" if platform == "win32" else "")
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "assets" / f"{FILENAME[character]}{suffix}.png"


class PetSprites:
    def __init__(self, root: tk.Misc, character: str) -> None:
        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        columns = GRID_COLUMNS[character]
        rows = len(POSES[character]) // columns
        for facing in (1, -1):
            atlas = tk.PhotoImage(master=root, file=str(atlas_path(character, facing)))
            if (atlas.width(), atlas.height()) != (CELL * columns, CELL * rows):
                raise ValueError(f"Invalid {character} sprite atlas size")
            for index, pose in enumerate(POSES[character]):
                frame = tk.PhotoImage(master=root, width=CELL, height=CELL)
                x = (index % columns) * CELL
                y = (index // columns) * CELL
                root.tk.call(str(frame), "copy", str(atlas), "-from",
                             x, y, x + CELL, y + CELL, "-to", 0, 0)
                self.frames[(pose, facing)] = frame

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
