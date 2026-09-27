"""Three original, more detailed storybook desktop-pet designs."""

from __future__ import annotations

import tkinter as tk

from fantasy_art import INK, _feet, _shadow


def draw_moss_keeper(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A small olive forest elder in layered travel robes with a crystal vine."""
    y = -bob
    _shadow(c, jumping, "#b9c9ad")
    _feet(c, y, stride, jumping, "#7f744d")
    # Pale wrap, warm undershirt and split leaf-lined travelling cloak.
    c.create_polygon(57, 86+y, 120, 85+y, 149+stride*3, 140+y,
                     116, 132+y, 94, 145+y, 62, 135+y, 36-stride*3, 145+y,
                     fill="#b5a481", outline="#4d473b", width=3)
    c.create_polygon(71, 94+y, 112, 94+y, 110, 139+y, 74, 139+y,
                     fill="#9a6848", outline="#584438", width=2)
    c.create_polygon(59, 89+y, 77, 98+y, 73, 135+y, 47, 142+y,
                     fill="#e2d5aa", outline="#594f41", width=2)
    c.create_polygon(125, 88+y, 109, 99+y, 111, 135+y, 139, 139+y,
                     fill="#d6c69b", outline="#594f41", width=2)
    c.create_line(74, 118+y, 110, 118+y, fill="#5d563b", width=4)
    c.create_oval(87, 114+y, 99, 125+y, fill="#c9a96d", outline="#544535", width=2)
    # Broad sleeves, compact hands and the raised arm holding a luminous vine.
    c.create_polygon(57, 89+y, 45, 87+y, 30, 111+y, 46, 124+y,
                     65, 112+y, fill="#d6c79e", outline="#584b3e", width=3)
    c.create_polygon(119, 90+y, 138, 93+y, 149, 116+y, 135, 126+y,
                     114, 113+y, fill="#d6c79e", outline="#584b3e", width=3)
    c.create_oval(30, 107+y, 49, 125+y, fill="#92a963", outline="#4e5d42", width=2)
    c.create_oval(133, 107+y, 151, 124+y, fill="#92a963", outline="#4e5d42", width=2)
    # Its crooked branch ends in an irregular pale crystal, never a straight blade.
    c.create_line(40, 114+y, 32, 91+y, 37, 70+y, 39, 49+y,
                  fill="#594b39", width=6, smooth=True, capstyle=tk.ROUND)
    c.create_line(39, 49+y, 43, 23+y, fill="#bce787", width=8, capstyle=tk.ROUND)
    c.create_line(40, 46+y, 43, 25+y, fill="#efffc4", width=3, capstyle=tk.ROUND)
    c.create_polygon(39, 25+y, 44, 9+y, 50, 23+y, 43, 30+y,
                     fill="#d6f2a0", outline="#668650", width=2)
    c.create_polygon(36, 60+y, 25, 55+y, 34, 48+y,
                     fill="#77ab62", outline="#506846", width=2)
    # Wide swept ears and a low hood frame a broad, old face.
    c.create_polygon(62, 57+y, 26, 39+y, 12, 47+y, 34, 69+y, 62, 76+y,
                     fill="#778d54", outline="#3d4b3a", width=3)
    c.create_polygon(123, 58+y, 159, 39+y, 174, 46+y, 154, 70+y, 123, 77+y,
                     fill="#778d54", outline="#3d4b3a", width=3)
    c.create_polygon(21, 48+y, 49, 55+y, 49, 64+y, 31, 58+y,
                     fill="#ac925f", outline="")
    c.create_polygon(164, 48+y, 137, 55+y, 139, 65+y, 156, 58+y,
                     fill="#ac925f", outline="")
    c.create_oval(56, 32+y, 129, 98+y, fill="#9dae6d", outline="#3e503c", width=3)
    c.create_arc(55, 29+y, 129, 84+y, start=22, extent=137,
                 style=tk.ARC, outline="#65774b", width=5)
    c.create_line(77, 42+y, 91, 34+y, 104, 43+y, fill="#d0d7a0", width=3, smooth=True)
    c.create_line(67, 57+y, 80, 53+y, fill="#4c5b3c", width=3)
    c.create_line(104, 53+y, 117, 57+y, fill="#4c5b3c", width=3)
    for x in (76, 109):
        if blink:
            c.create_line(x-6, 68+y, x+6, 68+y, fill="#3e4938", width=3)
        else:
            c.create_oval(x-8, 59+y, x+8, 76+y, fill="#f6ead1", outline="#4b4c3a", width=2)
            c.create_oval(x-3+facing, 61+y, x+4+facing, 73+y,
                          fill="#493d34", outline="")
            c.create_oval(x-1+facing, 62+y, x+1+facing, 65+y,
                          fill="#fff9ec", outline="")
    c.create_oval(87, 72+y, 100, 82+y, fill="#82965d", outline="#556446", width=1)
    c.create_arc(82, 77+y, 103, 91+y, start=205, extent=130,
                 style=tk.ARC, outline="#4a543e", width=2)
    c.create_line(62, 80+y, 70, 83+y, fill="#7a8859", width=2)
    c.create_line(116, 83+y, 124, 80+y, fill="#7a8859", width=2)


def draw_astral_sage(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A silver-haired star mapper with layered grey cloak and knotwood staff."""
    y = -bob
    _shadow(c, jumping, "#c7c5ca")
    _feet(c, y, stride, jumping, "#514b56")
    # Sweeping cloak is brighter inside and moves slightly with each stride.
    c.create_polygon(63, 75+y, 115, 77+y, 146+stride*4, 143+y,
                     118, 134+y, 88, 150+y, 59, 137+y, 30-stride*4, 145+y,
                     fill="#474653", outline="#2d303f", width=3)
    c.create_polygon(59, 89+y, 117, 89+y, 127, 145+y, 89, 148+y,
                     48, 146+y, fill="#807b83", outline="#4b4955", width=2)
    c.create_polygon(75, 93+y, 105, 92+y, 115, 141+y, 63, 142+y,
                     fill="#aba5a5", outline="")
    c.create_polygon(76, 94+y, 91, 109+y, 103, 94+y,
                     fill="#665b75", outline="")
    c.create_line(62, 121+y, 116, 121+y, fill="#5c5662", width=4)
    c.create_oval(85, 116+y, 100, 128+y, fill="#9ec8c6", outline="#454454", width=2)
    # Staff and sleeve are drawn behind the hair and beard.
    c.create_line(29, 144+y, 34, 81+y, 28, 63+y, 34, 28+y,
                  fill="#785841", width=5, smooth=True, capstyle=tk.ROUND)
    c.create_line(31, 69+y, 24, 53+y, 34, 38+y,
                  fill="#b18a65", width=2, smooth=True)
    c.create_polygon(29, 26+y, 36, 15+y, 43, 26+y, 37, 37+y,
                     fill="#b9c9d2", outline="#655b64", width=2)
    c.create_oval(55, 89+y, 71, 118+y, fill="#9d98a0", outline="#4b4855", width=2)
    c.create_oval(111, 89+y, 128, 119+y, fill="#9d98a0", outline="#4b4855", width=2)
    c.create_oval(25, 89+y, 43, 108+y, fill="#c9aa9e", outline="#4d4852", width=2)
    c.create_oval(120, 108+y, 138, 124+y, fill="#c9aa9e", outline="#4d4852", width=2)
    # Small visible face, wind-swept silver hair and a tapered beard.
    c.create_oval(61, 45+y, 121, 97+y, fill="#d2b5aa", outline="#554f57", width=2)
    c.create_polygon(62, 50+y, 54, 85+y, 66, 91+y, 72, 72+y,
                     74, 45+y, fill="#d7d3ce", outline="#706a72", width=2)
    c.create_polygon(115, 48+y, 127, 85+y, 118, 94+y, 109, 77+y,
                     106, 46+y, fill="#ded9d3", outline="#706a72", width=2)
    c.create_polygon(76, 82+y, 89, 89+y, 104, 82+y, 109, 106+y,
                     96, 126+y, 81, 109+y, fill="#e3ddd3", outline="#6d6870", width=2)
    c.create_line(89, 89+y, 88, 116+y, fill="#bbb5b5", width=2)
    c.create_line(100, 91+y, 97, 115+y, fill="#bbb5b5", width=2)
    c.create_line(71, 71+y, 82, 68+y, fill="#69636a", width=3)
    c.create_line(101, 68+y, 113, 71+y, fill="#69636a", width=3)
    for x in (79, 105):
        if blink:
            c.create_line(x-4, 76+y, x+4, 76+y, fill="#4b4653", width=2)
        else:
            c.create_oval(x-3+facing, 72+y, x+3+facing, 79+y,
                          fill="#4b4653", outline="")
    c.create_oval(89, 78+y, 96, 83+y, fill="#b9948c", outline="")
    # Offset slate hat, curved brim and an eight-point compass emblem.
    c.create_polygon(57, 51+y, 73, 24+y, 78, 12+y, 101, 38+y,
                     120, 50+y, fill="#777887", outline="#454754", width=3)
    c.create_polygon(61, 45+y, 81, 22+y, 99, 41+y, 96, 47+y,
                     fill="#a6a4a7", outline="")
    c.create_oval(47, 44+y, 132, 58+y, fill="#747581", outline="#454754", width=2)
    c.create_line(69, 47+y, 116, 47+y, fill="#514d65", width=5)
    c.create_polygon(89, 36+y, 92, 42+y, 98, 44+y, 92, 46+y,
                     89, 51+y, 86, 46+y, 80, 44+y, 86, 42+y,
                     fill="#c6d7cd", outline="")


def draw_ember_warden(
    c: tk.Canvas, bob: float, stride: float, blink: bool, facing: int, jumping: bool
) -> None:
    """A charcoal comet knight with a red crystal torch and asymmetric helm."""
    y = -bob
    _shadow(c, jumping, "#bdb3bb")
    _feet(c, y, stride, jumping, "#262a35")
    c.create_polygon(57, 82+y, 120, 78+y, 149+stride*4, 142+y,
                     119, 134+y, 78, 136+y, 40-stride*4, 146+y,
                     fill="#4b2837", outline="#232733", width=3)
    c.create_polygon(60, 89+y, 120, 88+y, 122, 135+y, 59, 137+y,
                     fill="#2d323c", outline="#161d2c", width=3)
    c.create_polygon(62, 88+y, 79, 78+y, 108, 78+y, 124, 88+y,
                     108, 99+y, 77, 98+y, fill="#61404c", outline="#171e2b", width=2)
    c.create_polygon(75, 98+y, 108, 97+y, 115, 124+y, 91, 136+y,
                     68, 123+y, fill="#46505a", outline="#191e2b", width=2)
    c.create_polygon(84, 106+y, 100, 105+y, 104, 120+y, 91, 125+y,
                     79, 119+y, fill="#9e5b62", outline="")
    c.create_oval(87, 109+y, 98, 120+y, fill="#f6a1a2", outline="#291e2b", width=2)
    # Segmented shoulder plates and gauntlets.
    c.create_polygon(59, 83+y, 43, 92+y, 50, 111+y, 72, 104+y,
                     fill="#454753", outline="#171d2b", width=3)
    c.create_polygon(122, 83+y, 142, 90+y, 136, 112+y, 115, 104+y,
                     fill="#454753", outline="#171d2b", width=3)
    c.create_line(56, 106+y, 43, 112+y, fill="#343844", width=12, capstyle=tk.ROUND)
    c.create_line(132, 108+y, 147, 114+y, fill="#343844", width=12, capstyle=tk.ROUND)
    c.create_oval(35, 106+y, 50, 120+y, fill="#555662", outline="#151b27", width=2)
    c.create_oval(138, 107+y, 154, 121+y, fill="#555662", outline="#151b27", width=2)
    # Hand-held faceted signal crystal, angled like a short glowing torch.
    c.create_line(42, 112+y, 31, 96+y, 22, 84+y,
                  fill="#1b202d", width=8, capstyle=tk.ROUND)
    c.create_line(22, 84+y, 13, 73+y, fill="#9e303e", width=7, capstyle=tk.ROUND)
    c.create_polygon(9, 71+y, 20, 56+y, 27, 71+y, 18, 83+y,
                     fill="#f35468", outline="#821d34", width=2)
    c.create_polygon(17, 65+y, 20, 60+y, 23, 71+y, 18, 78+y,
                     fill="#ffc0bb", outline="")
    # Curved helmet with offset fin, copper brow and a split turquoise visor.
    c.create_oval(51, 27+y, 130, 99+y, fill="#262b35", outline="#141b29", width=3)
    c.create_polygon(50, 63+y, 54, 32+y, 77, 16+y, 101, 20+y,
                     127, 39+y, 139, 61+y, 125, 72+y, 109, 49+y,
                     73, 49+y, fill="#292c34", outline="#111a27", width=3)
    c.create_polygon(62, 40+y, 77, 23+y, 104, 26+y, 124, 47+y,
                     100, 38+y, 76, 39+y, fill="#6b3d46", outline="")
    c.create_polygon(105, 22+y, 120, 27+y, 135, 43+y, 128, 55+y,
                     fill="#506c74", outline="#1b2630", width=2)
    c.create_line(58, 64+y, 121, 59+y, fill="#a96f62", width=5)
    c.create_polygon(63, 65+y, 88, 61+y, 89, 76+y, 65, 77+y,
                     fill="#72c8ca", outline="#18252e", width=2)
    c.create_polygon(95, 60+y, 121, 64+y, 119, 77+y, 95, 75+y,
                     fill="#72c8ca", outline="#18252e", width=2)
    c.create_line(70+facing, 67+y, 81+facing, 66+y, fill="#e5ffff", width=2)
    c.create_line(101+facing, 65+y, 113+facing, 67+y, fill="#e5ffff", width=2)
    if blink:
        c.create_line(68, 71+y, 83, 70+y, fill="#21313b", width=3)
        c.create_line(99, 69+y, 115, 71+y, fill="#21313b", width=3)
    c.create_polygon(76, 80+y, 106, 78+y, 113, 91+y, 92, 99+y,
                     69, 92+y, fill="#4c5560", outline="#1a202b", width=2)
    c.create_line(84, 86+y, 99, 85+y, fill="#bd8880", width=3)
