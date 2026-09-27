"""Small, click-through-looking magic effects that travel across the desktop."""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass


TRANSPARENT = "#ff00ff"


@dataclass(frozen=True)
class PowerStyle:
    kind: str
    outer: str
    inner: str
    origin_x: int
    origin_y: int
    fixed_direction: int = 0


POWER_STYLES = {
    "guardian": PowerStyle("star", "#55bfc4", "#effff2", 151, 57, 1),
    "ship": PowerStyle("pulse", "#61d3d5", "#f4ffff", 165, 88),
    "moss": PowerStyle("leaf", "#8fc866", "#eff9bd", 43, 20, -1),
    "astral": PowerStyle("light", "#87c9e0", "#ffffff", 36, 25, -1),
    "trail": PowerStyle("compass", "#edb956", "#fff4c7", 144, 69, 1),
    "ember": PowerStyle("ember", "#e35a71", "#ffd0ad", 20, 67, -1),
    "cat": PowerStyle("paw", "#eea485", "#ffe6bc", 92, 98),
    "bunny": PowerStyle("bubble", "#a6cfc5", "#ffffff", 92, 100),
}

SPECIAL_POWERS = {
    "guardian": ("lightning", "เรียกฟ้าผ่า"),
    "moss": ("tree", "เสกต้นไม้"),
    "astral": ("tornado", "เสกทอร์นาโด"),
    "ember": ("fire", "พ่นไฟ"),
}


@dataclass
class PowerEffect:
    kind: str
    outer: str
    inner: str
    x: float
    y: float
    direction: int
    width: int = 64
    height: int = 64
    speed: float = 250.0
    lifetime: float = 1.4
    age: float = 0.0

    def step(self, seconds: float, bounds: tuple[int, int, int, int]) -> bool:
        """Advance the effect; return whether it remains visible and alive."""
        seconds = min(max(seconds, 0.0), 0.1)
        self.age += seconds
        self.x += self.direction * self.speed * seconds
        left, top, right, bottom = bounds
        return (
            self.age < self.lifetime
            and self.x + self.width >= left
            and self.x <= right
            and self.y + self.height >= top
            and self.y <= bottom
        )


def launch_power(
    character: str,
    pet_x: float,
    pet_y: float,
    facing: int,
    ship_dx: float = 1.0,
    special: bool = False,
) -> PowerEffect:
    """Start a power at the matching staff, crystal, compass, or pet face."""
    if special and character not in SPECIAL_POWERS:
        raise ValueError(f"{character} has no special power")
    style = POWER_STYLES[character]
    direction = style.fixed_direction or (1 if facing >= 0 else -1)
    origin_x = style.origin_x
    if character == "ship":
        direction = 1 if ship_dx >= 0 else -1
        origin_x = 165 if direction > 0 else 19
    if special:
        if character == "guardian":
            return PowerEffect(
                "lightning", "#74d7e4", "#ffffff",
                pet_x + 138, pet_y - 18, 1,
                width=94, height=192, speed=0, lifetime=0.75,
            )
        if character == "moss":
            return PowerEffect(
                "tree", "#71ac6e", "#dcf2bd",
                pet_x - 76, pet_y + 8, -1,
                width=116, height=156, speed=0, lifetime=2.7,
            )
        if character == "astral":
            return PowerEffect(
                "tornado", "#8fbacb", "#eefafa",
                pet_x + style.origin_x - 62, pet_y + 57,
                -1, width=88, height=104, speed=105, lifetime=2.3,
            )
        direction = 1 if facing >= 0 else -1
        return PowerEffect(
            "fire", "#f36b45", "#ffda74",
            pet_x + (104 if direction > 0 else -22), pet_y + 59,
            direction, width=116, height=76, speed=135, lifetime=0.85,
        )
    return PowerEffect(
        style.kind, style.outer, style.inner,
        pet_x + origin_x - 32, pet_y + style.origin_y - 32,
        direction,
    )


class PowerEffectView:
    """One transparent, borderless window per short-lived flying effect."""

    def __init__(self, parent: tk.Tk, effect: PowerEffect, topmost: bool) -> None:
        self.effect = effect
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(background=TRANSPARENT)
        self.window.wm_attributes("-transparentcolor", TRANSPARENT)
        self.window.wm_attributes("-topmost", topmost)
        self.canvas = tk.Canvas(
            self.window,
            width=effect.width,
            height=effect.height,
            background=TRANSPARENT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.draw()
        self.window.deiconify()

    def draw(self) -> None:
        effect = self.effect
        self.window.geometry(
            f"{effect.width}x{effect.height}{round(effect.x):+d}{round(effect.y):+d}"
        )
        c = self.canvas
        c.delete("all")
        if effect.kind == "tornado":
            self._draw_tornado(c, effect)
        elif effect.kind == "tree":
            self._draw_tree(c, effect)
        elif effect.kind == "fire":
            self._draw_fire(c, effect)
        elif effect.kind == "lightning":
            self._draw_lightning(c, effect)
        else:
            self._draw_orb(c, effect)

    @staticmethod
    def _draw_orb(c: tk.Canvas, effect: PowerEffect) -> None:
        direction = effect.direction
        pulse = math.sin(effect.age * 20) * 2
        cx, cy = 32 + direction * 2, 32
        for index in range(3):
            tx = cx - direction * (14 + index * 11)
            ty = cy + math.sin(effect.age * 18 + index) * 6
            radius = 5 - index
            c.create_oval(tx-radius, ty-radius, tx+radius, ty+radius,
                          fill=effect.outer, outline="")
        c.create_oval(cx-17-pulse, cy-17-pulse, cx+17+pulse, cy+17+pulse,
                      fill=effect.outer, outline="")
        c.create_oval(cx-10, cy-10, cx+10, cy+10, fill=effect.inner, outline="")
        if effect.kind in {"star", "compass", "light"}:
            c.create_polygon(cx, cy-20, cx+5, cy-5, cx+20, cy,
                             cx+5, cy+5, cx, cy+20, cx-5, cy+5,
                             cx-20, cy, cx-5, cy-5,
                             fill=effect.inner, outline=effect.outer, width=2)
        elif effect.kind == "leaf":
            c.create_polygon(cx-11, cy+8, cx-5, cy-10, cx+14, cy-14,
                             cx+9, cy+6, cx-11, cy+8,
                             fill=effect.inner, outline="#568b53", width=2)
            c.create_line(cx-11, cy+8, cx+11, cy-10, fill="#568b53", width=2)
        elif effect.kind == "ember":
            c.create_polygon(cx-11, cy+12, cx-8, cy-7, cx, cy-19,
                             cx+4, cy-6, cx+12, cy+3, cx+7, cy+14,
                             fill=effect.inner, outline="#9f3851", width=2)
        elif effect.kind == "paw":
            c.create_oval(cx-7, cy, cx+7, cy+11, fill="#e68d78", outline="")
            for px in (-9, -3, 4, 10):
                c.create_oval(cx+px-2, cy-9, cx+px+2, cy-3,
                              fill="#e68d78", outline="")
        elif effect.kind == "bubble":
            c.create_oval(cx-9, cy-9, cx+9, cy+9,
                          fill="#ffffff", outline="#82beb6", width=2)
            c.create_oval(cx-5, cy-6, cx-1, cy-2, fill="#e3ffff", outline="")
        else:  # Survey ship pulse.
            c.create_polygon(cx-9, cy-9, cx+14, cy, cx-9, cy+9,
                             fill=effect.inner, outline=effect.outer, width=2)

    @staticmethod
    def _draw_tornado(c: tk.Canvas, effect: PowerEffect) -> None:
        swing = math.sin(effect.age * 11) * 5
        c.create_polygon(
            16+swing, 16, 70+swing, 16, 59-swing, 48,
            52+swing, 78, 45, 96, 38-swing, 76, 29+swing, 48,
            fill="#a9cdd7", outline="#648fa8", width=3,
        )
        c.create_oval(9+swing, 7, 75+swing, 30,
                      fill="#d3e8ed", outline="#648fa8", width=3)
        c.create_arc(15+swing, 19, 69+swing, 40, start=195, extent=290,
                     style=tk.ARC, outline="#ffffff", width=4)
        c.create_arc(22-swing, 38, 64-swing, 60, start=20, extent=290,
                     style=tk.ARC, outline="#e7fbff", width=4)
        c.create_arc(30+swing, 59, 57+swing, 78, start=195, extent=300,
                     style=tk.ARC, outline="#ffffff", width=3)
        c.create_oval(33, 87, 55, 98, fill="#bdd5dc", outline="#648fa8", width=2)
        for sx, sy in ((13, 42), (72, 56), (20, 80)):
            c.create_line(sx-3, sy, sx+3, sy, fill="#e6ffff", width=2)
            c.create_line(sx, sy-3, sx, sy+3, fill="#e6ffff", width=2)

    @staticmethod
    def _draw_tree(c: tk.Canvas, effect: PowerEffect) -> None:
        growth = min(1.0, effect.age / 0.85)
        if growth < 0.08:
            c.create_oval(50, 139, 66, 150, fill="#8b7050", outline="#4b563b", width=2)
            return
        top = 142 - 91 * growth
        crown = 34 * growth
        sway = math.sin(effect.age * 7) * 2
        c.create_oval(18, 140, 99, 151, fill="#b6c4a2", outline="")
        c.create_line(58, 144, 58+sway, top+12*growth,
                      fill="#70563e", width=max(3, round(15*growth)), capstyle=tk.ROUND)
        if growth > 0.4:
            branch_y = 142 - 55 * growth
            c.create_line(58, branch_y, 58-25*growth, branch_y-22*growth,
                          fill="#70563e", width=max(2, round(7*growth)))
            c.create_line(58, branch_y-11*growth, 58+24*growth, branch_y-34*growth,
                          fill="#70563e", width=max(2, round(7*growth)))
        c.create_oval(58-crown+sway, top-crown*0.6, 58+crown+sway, top+crown,
                      fill="#5c9e69", outline="#3b735d", width=3)
        c.create_oval(58-42*growth, top-4*growth,
                      58-2*growth, top+34*growth,
                      fill="#78b778", outline="#3b735d", width=2)
        c.create_oval(58+3*growth, top-12*growth,
                      58+42*growth, top+28*growth,
                      fill="#8cc784", outline="#3b735d", width=2)
        if growth > 0.7:
            for x, yy in ((43, top-2), (72, top-10), (89, top+10)):
                c.create_oval(x-3, yy-3, x+3, yy+3, fill="#e8e9a3", outline="")
        c.create_line(20, 133, 26, 127, fill="#82b671", width=3)
        c.create_line(91, 135, 97, 126, fill="#82b671", width=3)

    @staticmethod
    def _draw_fire(c: tk.Canvas, effect: PowerEffect) -> None:
        width = effect.width
        mirror = lambda x: x if effect.direction > 0 else width-x
        wave = math.sin(effect.age * 27) * 5
        c.create_polygon(
            mirror(3), 38, mirror(27), 17, mirror(42), 22+wave,
            mirror(62), 5, mirror(75), 22-wave, mirror(108), 28,
            mirror(90), 39, mirror(111), 52, mirror(68), 55,
            mirror(48), 72, mirror(32), 55-wave,
            fill="#e95943", outline="#a43e3e", width=2,
        )
        c.create_polygon(
            mirror(9), 38, mirror(42), 28, mirror(59), 19,
            mirror(81), 31, mirror(102), 39, mirror(78), 47,
            mirror(55), 61, mirror(43), 47,
            fill="#ffb750", outline="",
        )
        c.create_polygon(
            mirror(13), 38, mirror(51), 31, mirror(85), 38,
            mirror(56), 47,
            fill="#fff2ae", outline="",
        )
        for x, y in ((69, 8), (95, 18), (97, 63)):
            px = mirror(x)
            c.create_oval(px-3, y-3, px+3, y+3, fill="#fbb560", outline="")

    @staticmethod
    def _draw_lightning(c: tk.Canvas, effect: PowerEffect) -> None:
        flash = math.sin(effect.age * 58) * 5
        c.create_oval(17, 2, 67, 27, fill="#b3d1db", outline="#617e91", width=2)
        c.create_oval(43, 4, 91, 31, fill="#c8e1e5", outline="#617e91", width=2)
        points = (
            52, 24, 42+flash, 61, 58-flash, 62,
            30+flash, 111, 52, 111, 37-flash, 164,
        )
        c.create_line(*points, fill="#5a8fab", width=15, joinstyle=tk.ROUND)
        c.create_line(*points, fill="#e9ffff", width=7, joinstyle=tk.ROUND)
        c.create_line(41+flash, 60, 21, 79, 32, 83,
                      fill="#b9f5f5", width=4)
        c.create_line(51, 112, 74, 131, 61, 136,
                      fill="#b9f5f5", width=4)
        c.create_oval(21, 163, 71, 174, fill="#b1e5e5", outline="")
        for x, y in ((12, 139), (76, 155), (78, 88)):
            c.create_line(x-5, y, x+5, y, fill="#d9fcfa", width=2)
            c.create_line(x, y-5, x, y+5, fill="#d9fcfa", width=2)

    def close(self) -> None:
        self.window.destroy()
