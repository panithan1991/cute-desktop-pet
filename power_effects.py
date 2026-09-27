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
    tornado: bool = False,
) -> PowerEffect:
    """Start a power at the matching staff, crystal, compass, or pet face."""
    if tornado and character != "astral":
        raise ValueError("Only the astral sage can summon a tornado")
    style = POWER_STYLES[character]
    direction = style.fixed_direction or (1 if facing >= 0 else -1)
    origin_x = style.origin_x
    if character == "ship":
        direction = 1 if ship_dx >= 0 else -1
        origin_x = 165 if direction > 0 else 19
    if tornado:
        return PowerEffect(
            "tornado", "#8fbacb", "#eefafa",
            pet_x + style.origin_x - 62, pet_y + 57,
            -1, width=88, height=104, speed=105, lifetime=2.3,
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

    def close(self) -> None:
        self.window.destroy()
