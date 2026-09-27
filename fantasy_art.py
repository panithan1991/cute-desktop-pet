"""Original storybook visitors drawn with Tk canvas primitives.

The figures use broad space-fantasy and folklore themes, not franchise assets.
Keeping the art in code lets the desktop pet animate without image files.
"""

from __future__ import annotations

import tkinter as tk


INK = "#2d354b"


def _feet(c: tk.Canvas, y: float, stride: float, jumping: bool, boot: str) -> None:
    step = stride * 6
    if jumping:
        c.create_line(76, 129 + y, 64, 139 + y, fill=INK, width=14, capstyle=tk.ROUND)
        c.create_line(108, 129 + y, 120, 139 + y, fill=INK, width=14, capstyle=tk.ROUND)
        c.create_oval(54, 132 + y, 77, 147 + y, fill=boot, outline=INK, width=2)
        c.create_oval(108, 132 + y, 131, 147 + y, fill=boot, outline=INK, width=2)
    else:
        c.create_line(76, 128 + y, 74 + step, 146 + y, fill=INK, width=13, capstyle=tk.ROUND)
        c.create_line(108, 128 + y, 111 - step, 146 + y, fill=INK, width=13, capstyle=tk.ROUND)
        c.create_oval(58 + step, 141 + y, 86 + step, 156 + y, fill=boot, outline=INK, width=2)
        c.create_oval(98 - step, 141 + y, 126 - step, 156 + y, fill=boot, outline=INK, width=2)


def _shadow(c: tk.Canvas, jumping: bool, color: str = "#b8cbd0") -> None:
    if not jumping:
        c.create_oval(49, 155, 137, 164, fill=color, outline="")


def _eyes(c: tk.Canvas, y: float, blink: bool, facing: int, color: str = INK) -> None:
    for x in (79, 106):
        if blink:
            c.create_line(x - 4, y, x + 4, y, fill=color, width=3, capstyle=tk.ROUND)
        else:
            c.create_oval(x - 4, y - 5, x + 4, y + 5, fill=color, outline="")
            c.create_oval(x - 2 + facing, y - 3, x + facing, y - 1, fill="#fffdf2", outline="")


def draw_trail_scout(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """An upbeat mapmaker with a sun-orange pack and mint scarf."""
    y = -bob
    _shadow(c, jumping, "#d6cbb8")
    _feet(c, y, stride, jumping, "#7a6554")
    c.create_oval(40, 76+y, 92, 133+y, fill="#e49861", outline=INK, width=3)
    c.create_polygon(40, 99+y, 27, 111+y, 44, 124+y,
                     fill="#f7c47c", outline=INK, width=2)
    c.create_oval(58, 96+y, 126, 140+y, fill="#497e86", outline=INK, width=3)
    c.create_polygon(62, 102+y, 122, 102+y, 111, 135+y, 73, 135+y,
                     fill="#6fa8a4", outline="")
    c.create_line(59, 102+y, 47, 114+y, fill="#e1aa87", width=11, capstyle=tk.ROUND)
    c.create_line(123, 103+y, 140, 88+y, fill="#e1aa87", width=11, capstyle=tk.ROUND)
    c.create_oval(37, 108+y, 53, 122+y, fill="#f0ba92", outline=INK, width=2)
    c.create_oval(133, 81+y, 148, 96+y, fill="#f0ba92", outline=INK, width=2)
    # Compass medallion replaces any weapon.
    c.create_oval(130, 55+y, 157, 82+y, fill="#f2c76b", outline=INK, width=2)
    c.create_polygon(143, 60+y, 148, 69+y, 143, 78+y, 138, 69+y,
                     fill="#f9f0d0", outline=INK, width=1)
    c.create_oval(55, 39+y, 130, 100+y, fill="#f0c09a", outline=INK, width=3)
    c.create_oval(60, 41+y, 125, 69+y, fill="#604a49", outline="")
    c.create_polygon(52, 49+y, 64, 25+y, 111, 22+y, 134, 50+y,
                     119, 55+y, 102, 37+y, 78, 45+y,
                     fill="#a66e55", outline=INK, width=3)
    c.create_polygon(51, 51+y, 132, 49+y, 126, 62+y, 58, 62+y,
                     fill="#d99a67", outline=INK, width=2)
    c.create_oval(56, 77+y, 70, 88+y, fill="#e99e8b", outline="")
    c.create_oval(115, 77+y, 129, 88+y, fill="#e99e8b", outline="")
    _eyes(c, 73+y, blink, facing)
    c.create_arc(83, 75+y, 102, 90+y, start=205, extent=130,
                 style=tk.ARC, outline=INK, width=2)
    c.create_polygon(63, 89+y, 90, 98+y, 120, 88+y, 112, 108+y,
                     93, 102+y, 75, 110+y, fill="#8bd0c1", outline=INK, width=2)
    c.create_line(92, 102+y, 104, 125+y, fill="#bfe8d6", width=5)
