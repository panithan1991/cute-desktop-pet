"""Regenerate the SVG concept sheet from the app's actual canvas drawings."""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

from desktop_pet import DesktopPet


class SvgCanvas:
    def __init__(self) -> None:
        self.parts: list[str] = []

    @staticmethod
    def _style(options: dict[str, object]) -> str:
        fill = options.get("fill", "none") or "none"
        stroke = options.get("outline", "none") or "none"
        width = options.get("width", 1)
        return f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"'

    def create_oval(self, x1: float, y1: float, x2: float, y2: float, **options: object) -> None:
        self.parts.append(
            f'<ellipse cx="{(x1 + x2) / 2}" cy="{(y1 + y2) / 2}" '
            f'rx="{abs(x2 - x1) / 2}" ry="{abs(y2 - y1) / 2}" {self._style(options)}/>'
        )

    def create_polygon(self, *coordinates: float, **options: object) -> None:
        points = " ".join(
            f"{coordinates[index]},{coordinates[index + 1]}"
            for index in range(0, len(coordinates), 2)
        )
        self.parts.append(f'<polygon points="{points}" {self._style(options)} stroke-linejoin="round"/>')

    def create_line(self, *coordinates: float, **options: object) -> None:
        points = " ".join(
            f"{coordinates[index]},{coordinates[index + 1]}"
            for index in range(0, len(coordinates), 2)
        )
        stroke = options.get("fill", "#30394f")
        width = options.get("width", 1)
        self.parts.append(
            f'<polyline points="{points}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def create_arc(self, x1: float, y1: float, x2: float, y2: float, **options: object) -> None:
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        rx, ry = abs(x2 - x1) / 2, abs(y2 - y1) / 2
        start = math.radians(float(options["start"]))
        end = math.radians(float(options["start"]) + float(options["extent"]))
        sx, sy = cx + rx * math.cos(start), cy - ry * math.sin(start)
        ex, ey = cx + rx * math.cos(end), cy - ry * math.sin(end)
        large = int(float(options["extent"]) > 180)
        stroke = options.get("outline", "#30394f")
        width = options.get("width", 1)
        self.parts.append(
            f'<path d="M {sx} {sy} A {rx} {ry} 0 {large} 0 {ex} {ey}" '
            f'fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round"/>'
        )


def main() -> None:
    guardian = SvgCanvas()
    ship = SvgCanvas()
    DesktopPet._draw_guardian(None, guardian, 0, 0.5, False, 1, False)
    dummy = SimpleNamespace(flight=SimpleNamespace(paused=False))
    DesktopPet._draw_ship(dummy, ship, 0.5, 1, -0.5)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 245">
<rect width="500" height="245" rx="24" fill="#17243a"/>
<circle cx="37" cy="42" r="2" fill="#8adce2"/><circle cx="252" cy="36" r="2" fill="#f7d379"/>
<circle cx="467" cy="67" r="2" fill="#8adce2"/><circle cx="429" cy="188" r="1.5" fill="#f7d379"/>
<ellipse cx="137" cy="173" rx="83" ry="14" fill="#263953"/>
<ellipse cx="366" cy="142" rx="83" ry="14" fill="#263953"/>
<g transform="translate(44 10)">{''.join(guardian.parts)}</g>
<g transform="translate(273 8)">{''.join(ship.parts)}</g>
<text x="136" y="217" text-anchor="middle" fill="#f5e6c9" font-family="Arial,sans-serif" font-size="14" font-weight="bold">STAR GUARDIAN</text>
<text x="366" y="217" text-anchor="middle" fill="#f5e6c9" font-family="Arial,sans-serif" font-size="14" font-weight="bold">ORBIT SCOUT</text>
</svg>'''
    Path(__file__).with_name("preview.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
