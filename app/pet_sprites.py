"""Pre-rendered pet atlases; runtime uses only Tk, not image libraries."""

from pathlib import Path
from collections import OrderedDict
import sys
import tkinter as tk

from app.animation_clips import ALL_POSES
from app.dragon_animation import DRAGON_POSES,DRAGON_CLIPS
from app.behavior_art import EXTRA_POSES,EXTRA_CLIPS
from app.dragon_personality import NEW_ACTIVITIES, PERCH_CLIPS

CELL = 160
COLUMNS = 5
PAGE_FRAMES = 40
FILENAME = {
    "bunny": "booboo-motion", "mookrata": "moo-krata-motion",
    "bibi": "bibi-motion", "kitten": "kitten-motion", "dragon": "dragon-motion",
}
GRID_COLUMNS = dict.fromkeys(FILENAME, COLUMNS)
POSES = dict.fromkeys(FILENAME, ALL_POSES)
POSES["dragon"] = DRAGON_POSES
POSES = {character: base + EXTRA_POSES[character] for character, base in POSES.items()}
DIRECT_DRAGON_POSES=frozenset((*DRAGON_CLIPS['fire'],*EXTRA_CLIPS['dragon']['ignition_reaction'],
                             *(p for n in (*NEW_ACTIVITIES,*PERCH_CLIPS) for p in EXTRA_CLIPS['dragon'][n])))


def atlas_path(character: str, facing: int, platform: str | None = None) -> Path:
    platform = sys.platform if platform is None else platform
    suffix = ("-left" if facing < 0 else "") + ("-windows" if platform == "win32" else "")
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "assets" / f"{FILENAME[character]}{suffix}.png"


class PetSprites:
    def __init__(self, root: tk.Misc, character: str) -> None:
        self.frames: dict[tuple[str, int], tk.PhotoImage] = {}
        self.root, self.character = root, character
        if character == "dragon":
            self.frames = OrderedDict()
            self.pages = OrderedDict()
            self.indices = {pose:index for index,pose in enumerate(POSES[character])}
            return
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
        key = (pose, 1 if facing >= 0 else -1)
        if self.character != "dragon":
            return self.frames[key]
        if key in self.frames:
            self.frames.move_to_end(key)
            return self.frames[key]
        from app.dragon_flight_joins import FLIGHT_JOIN_POSES,LANDING_JOIN_POSES
        if pose in DIRECT_DRAGON_POSES or pose in FLIGHT_JOIN_POSES or pose in LANDING_JOIN_POSES:
            base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
            platform='windows' if sys.platform=='win32' else 'macos'
            side='left' if facing<0 else 'right'
            extension='ppm' if platform=='windows' else 'png'
            image=tk.PhotoImage(master=self.root,file=str(base/f'assets/runtime/dragon-{platform}/body-fx/{side}/{pose}.{extension}'))
            if (image.width(),image.height()) != (CELL,CELL):raise ValueError('Invalid dragon effect body frame')
            self.frames[key]=image
            if len(self.frames)>80:self.frames.popitem(last=False)
            return image
        index = self.indices[pose]
        page, local = divmod(index, PAGE_FRAMES)
        page_key = (key[1], page)
        if page_key not in self.pages:
            atlas = tk.PhotoImage(master=self.root, file=str(dragon_page_path(key[1], page)))
            rows = min(PAGE_FRAMES, len(POSES["dragon"])-page*PAGE_FRAMES)//COLUMNS
            if (atlas.width(),atlas.height()) != (COLUMNS*CELL,rows*CELL):
                raise ValueError("Invalid dragon sprite page size")
            self.pages[page_key] = atlas
            if len(self.pages) > 2:
                self.pages.popitem(last=False)
        self.pages.move_to_end(page_key)
        atlas = self.pages[page_key]
        image = tk.PhotoImage(master=self.root, width=CELL, height=CELL)
        x,y = local%COLUMNS*CELL, local//COLUMNS*CELL
        self.root.tk.call(str(image),"copy",str(atlas),"-from",x,y,x+CELL,y+CELL,"-to",0,0)
        self.frames[key] = image
        if len(self.frames) > 80:
            self.frames.popitem(last=False)
        return image


def dragon_page_path(facing, page, platform=None):
    platform = sys.platform if platform is None else platform
    base = Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
    family = "dragon-windows" if platform == "win32" else "dragon-macos"
    side = "left" if facing < 0 else "right"
    return base / "assets/runtime" / family / f"{side}-{page:02d}.png"
