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


def draw_moss_keeper(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A round moss sprite carrying a warm seed lantern."""
    y = -bob
    _shadow(c, jumping, "#cad9cd")
    _feet(c, y, stride, jumping, "#557c69")
    # Leaf cape, small satchel, and coral seed-pod tunic.
    c.create_polygon(65, 89+y, 119, 88+y, 145, 139+y, 109, 128+y,
                     75, 139+y, 40, 138+y, fill="#4c9178", outline=INK, width=3)
    c.create_line(93, 109+y, 93, 137+y, fill="#bce0a6", width=2)
    c.create_oval(60, 88+y, 125, 138+y, fill="#e69870", outline=INK, width=3)
    c.create_polygon(73, 93+y, 92, 106+y, 110, 93+y, 114, 123+y,
                     70, 123+y, fill="#ffca93", outline="")
    c.create_oval(82, 109+y, 102, 128+y, fill="#6eaa84", outline=INK, width=2)
    c.create_line(53, 106+y, 41, 88+y, fill="#6ba783", width=13, capstyle=tk.ROUND)
    c.create_line(131, 105+y, 146, 98+y, fill="#6ba783", width=13, capstyle=tk.ROUND)
    c.create_oval(33, 82+y, 48, 99+y, fill="#91bc8d", outline=INK, width=2)
    c.create_oval(138, 91+y, 154, 105+y, fill="#91bc8d", outline=INK, width=2)
    # A lantern on a bent twig, with petals rather than a blade.
    c.create_line(43, 91+y, 32, 68+y, 36, 58+y, fill="#755c52", width=4, capstyle=tk.ROUND)
    c.create_polygon(24, 49+y, 34, 43+y, 44, 50+y, 42, 65+y,
                     33, 73+y, 23, 63+y, fill="#f7bf76", outline=INK, width=2)
    c.create_oval(29, 50+y, 38, 61+y, fill="#fff2bc", outline="")
    c.create_line(29, 49+y, 23, 42+y, fill="#b9dfaa", width=3)
    c.create_line(39, 48+y, 46, 41+y, fill="#b9dfaa", width=3)
    # Rounded pebble face and one asymmetric seed crest.
    c.create_oval(52, 38+y, 132, 101+y, fill="#a7c993", outline=INK, width=3)
    c.create_polygon(57, 48+y, 65, 18+y, 90, 30+y, 89, 47+y,
                     fill="#62a87e", outline=INK, width=2)
    c.create_polygon(92, 39+y, 112, 14+y, 127, 24+y, 124, 48+y,
                     fill="#79b780", outline=INK, width=2)
    c.create_line(68, 42+y, 82, 38+y, fill="#d5ebb1", width=3)
    c.create_oval(55, 71+y, 68, 82+y, fill="#eeb48f", outline="")
    c.create_oval(117, 71+y, 130, 82+y, fill="#eeb48f", outline="")
    _eyes(c, 69+y, blink, facing)
    c.create_oval(89, 74+y, 96, 79+y, fill="#6b8f6b", outline="")
    c.create_arc(83, 73+y, 101, 88+y, start=205, extent=130,
                 style=tk.ARC, outline=INK, width=2)


def draw_astral_sage(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A young sky-chart keeper with a crescent cowl and floating star globe."""
    y = -bob
    _shadow(c, jumping, "#c8c9dc")
    _feet(c, y, stride, jumping, "#594f79")
    c.create_polygon(66, 88+y, 120, 88+y, 141, 142+y, 115, 135+y,
                     69, 138+y, 44, 144+y, fill="#4e517b", outline=INK, width=3)
    c.create_polygon(70, 93+y, 95, 102+y, 114, 91+y, 118, 133+y,
                     66, 134+y, fill="#8a78a5", outline="")
    c.create_line(93, 106+y, 93, 129+y, fill="#f5c975", width=2)
    c.create_oval(84, 114+y, 101, 130+y, fill="#e7bd70", outline=INK, width=2)
    c.create_oval(53, 87+y, 74, 117+y, fill="#676996", outline=INK, width=2)
    c.create_oval(112, 88+y, 134, 117+y, fill="#676996", outline=INK, width=2)
    c.create_oval(49, 108+y, 68, 123+y, fill="#d2b1a1", outline=INK, width=2)
    c.create_oval(122, 108+y, 141, 123+y, fill="#d2b1a1", outline=INK, width=2)
    # A small star chart held open; the orb drifts above the other hand.
    c.create_polygon(36, 112+y, 53, 105+y, 68, 110+y, 75, 130+y,
                     52, 124+y, 36, 130+y, fill="#f0deba", outline=INK, width=2)
    c.create_line(53, 106+y, 52, 125+y, fill="#a77776", width=2)
    c.create_oval(136, 79+y, 161, 104+y, fill="#7abed1", outline=INK, width=2)
    c.create_polygon(149, 82+y, 152, 89+y, 159, 91+y, 152, 94+y,
                     149, 101+y, 146, 94+y, 139, 91+y, 146, 89+y,
                     fill="#fff2bd", outline="")
    c.create_oval(54, 42+y, 130, 101+y, fill="#dbc0a9", outline=INK, width=3)
    # Collar makes an astral crescent, not a pointed hat or long beard.
    c.create_polygon(50, 61+y, 61, 31+y, 71, 46+y, 91, 22+y,
                     114, 45+y, 131, 32+y, 137, 64+y, 121, 58+y,
                     110, 43+y, 92, 41+y, 74, 55+y,
                     fill="#535984", outline=INK, width=3)
    c.create_polygon(61, 49+y, 71, 32+y, 81, 42+y, 72, 57+y,
                     fill="#bdadce", outline="")
    c.create_oval(53, 79+y, 68, 91+y, fill="#f0ab9f", outline="")
    c.create_oval(116, 79+y, 131, 91+y, fill="#f0ab9f", outline="")
    _eyes(c, 72+y, blink, facing)
    c.create_arc(83, 75+y, 102, 90+y, start=205, extent=125,
                 style=tk.ARC, outline=INK, width=2)
    c.create_polygon(88, 18+y, 92, 10+y, 96, 18+y, 104, 22+y,
                     96, 25+y, 92, 33+y, 88, 25+y, 80, 22+y,
                     fill="#f7d483", outline=INK, width=1)


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


def draw_ember_warden(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A night-sky sentinel with a bronze crescent helm and shield glow."""
    y = -bob
    _shadow(c, jumping, "#bdbcc8")
    _feet(c, y, stride, jumping, "#48546a")
    c.create_polygon(62, 79+y, 121, 81+y, 146, 145+y, 111, 130+y,
                     66, 138+y, 36, 141+y, fill="#863e50", outline=INK, width=3)
    c.create_polygon(62, 82+y, 120, 82+y, 123, 131+y, 59, 132+y,
                     fill="#4a566b", outline=INK, width=3)
    c.create_polygon(81, 91+y, 101, 89+y, 110, 115+y, 92, 130+y,
                     74, 115+y, fill="#b77e61", outline=INK, width=2)
    c.create_oval(85, 106+y, 100, 121+y, fill="#74d6ce", outline=INK, width=2)
    c.create_oval(45, 85+y, 70, 112+y, fill="#b77e61", outline=INK, width=2)
    c.create_oval(115, 85+y, 140, 112+y, fill="#b77e61", outline=INK, width=2)
    c.create_line(52, 108+y, 37, 113+y, fill="#5a6778", width=13, capstyle=tk.ROUND)
    c.create_line(132, 107+y, 144, 102+y, fill="#5a6778", width=13, capstyle=tk.ROUND)
    c.create_oval(31, 105+y, 49, 121+y, fill="#cf9972", outline=INK, width=2)
    c.create_oval(137, 95+y, 154, 112+y, fill="#cf9972", outline=INK, width=2)
    # Small round signal shield: no energy blade or franchise helmet mask.
    c.create_oval(137, 52+y, 168, 83+y, fill="#a75f61", outline=INK, width=3)
    c.create_oval(144, 59+y, 161, 76+y, fill="#f6b970", outline="")
    c.create_oval(149, 64+y, 156, 71+y, fill="#fbe7af", outline="")
    c.create_oval(52, 39+y, 132, 99+y, fill="#d2a584", outline=INK, width=3)
    c.create_polygon(50, 64+y, 54, 36+y, 69, 23+y, 109, 24+y,
                     134, 42+y, 135, 69+y, 119, 55+y, 66, 55+y,
                     fill="#48546a", outline=INK, width=3)
    c.create_polygon(60, 35+y, 77, 24+y, 108, 26+y, 128, 42+y,
                     107, 39+y, 84, 35+y, fill="#c38a67", outline="")
    c.create_polygon(55, 55+y, 66, 49+y, 119, 49+y, 131, 59+y,
                     122, 67+y, 61, 67+y, fill="#5a7e8c", outline=INK, width=2)
    c.create_oval(58, 78+y, 70, 87+y, fill="#e99c84", outline="")
    c.create_oval(114, 78+y, 126, 87+y, fill="#e99c84", outline="")
    _eyes(c, 75+y, blink, facing)
    c.create_arc(83, 78+y, 102, 91+y, start=205, extent=125,
                 style=tk.ARC, outline=INK, width=2)
