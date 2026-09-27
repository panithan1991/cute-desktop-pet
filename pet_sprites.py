"""Fast, pre-rendered 25-pose animation atlases for BooBoo and Moo Krata."""

from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk


CELL = 160
COLUMNS = 5
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
}
FILENAME = {"bunny": "booboo-motion", "mookrata": "moo-krata-motion"}


def atlas_path(character: str, facing: int, platform: str | None = None) -> Path:
    platform = sys.platform if platform is None else platform
    suffix = ("-left" if facing < 0 else "") + ("-windows" if platform == "win32" else "")
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / "assets" / f"{FILENAME[character]}{suffix}.png"


class PetSprites:
    def __init__(self, root: tk.Misc, character: str) -> None:
        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        for facing in (1, -1):
            atlas = tk.PhotoImage(master=root, file=str(atlas_path(character, facing)))
            if (atlas.width(), atlas.height()) != (CELL * COLUMNS, CELL * COLUMNS):
                raise ValueError(f"Invalid {character} sprite atlas size")
            for index, pose in enumerate(POSES[character]):
                frame = tk.PhotoImage(master=root, width=CELL, height=CELL)
                x = (index % COLUMNS) * CELL
                y = (index // COLUMNS) * CELL
                root.tk.call(str(frame), "copy", str(atlas), "-from",
                             x, y, x + CELL, y + CELL, "-to", 0, 0)
                self.frames[(pose, facing)] = frame

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
