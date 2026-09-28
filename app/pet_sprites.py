"""Pre-rendered pet atlases; runtime uses only Tk, not image libraries."""

from pathlib import Path
import sys
import tkinter as tk

from app.animation_clips import ALL_POSES
from app.dragon_animation import DRAGON_POSES
from app.behavior_art import EXTRA_POSES

CELL = 160
COLUMNS = 5
FILENAME = {
    "bunny": "booboo-motion", "mookrata": "moo-krata-motion",
    "bibi": "bibi-motion", "kitten": "kitten-motion", "dragon": "dragon-motion",
}
GRID_COLUMNS = dict.fromkeys(FILENAME, COLUMNS)
POSES = dict.fromkeys(FILENAME, ALL_POSES)
POSES["dragon"] = DRAGON_POSES
POSES = {character: base + EXTRA_POSES[character] for character, base in POSES.items()}


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
                x, y = (index % columns) * CELL, (index // columns) * CELL
                root.tk.call(str(frame), "copy", str(atlas), "-from",
                             x, y, x + CELL, y + CELL, "-to", 0, 0)
                self.frames[(pose, facing)] = frame

    def get(self, pose: str, facing: int) -> tk.PhotoImage:
        return self.frames[(pose, 1 if facing >= 0 else -1)]
